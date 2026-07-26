"""Data models for the queue monitoring system."""

import enum
import threading
import time
from dataclasses import dataclass, field
from typing import Optional


class QueueStatus(enum.Enum):
    EMPTY = "empty"
    LOW = "low"            # 1-2 people
    MODERATE = "moderate"  # 3-5
    HIGH = "high"          # 6-9
    CRITICAL = "critical"  # 10+


class CameraStatus(enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    CONNECTING = "connecting"


@dataclass
class PersonRecord:
    """Tracks a single person's presence inside the queue zone."""

    track_id: int
    camera_id: str
    entry_time: float
    exit_time: Optional[float] = None
    last_pos: Optional[tuple[int, int]] = None
    pending_since: Optional[float] = None

    @property
    def wait_seconds(self) -> float:
        end = self.exit_time if self.exit_time is not None else time.time()
        return round(end - self.entry_time, 1)

    @property
    def is_active(self) -> bool:
        return self.exit_time is None


@dataclass
class QueueState:
    """Thread-safe queue state for a single camera."""

    camera_id: str
    camera_name: str = ""
    active: dict[int, PersonRecord] = field(default_factory=dict)
    pending: dict[int, PersonRecord] = field(default_factory=dict)
    history: dict[int, PersonRecord] = field(default_factory=dict)
    
    # Global metrics
    total_served: int = 0
    global_total_wait_seconds: float = 0.0
    global_longest_wait: float = 0.0
    
    lock: threading.RLock = field(default_factory=threading.RLock)

    def person_entered(self, track_id: int, pos: tuple[int, int]) -> None:
        """Handle a person entering or re-appearing. Resolves identity switches."""
        with self.lock:
            if track_id in self.active:
                self.active[track_id].last_pos = pos
                return

            # Spatial Re-ID: check if any pending exit is very close
            best_match_id = None
            min_dist = 100.0  # pixel radius to merge
            
            for pid, rec in list(self.pending.items()):
                if rec.last_pos:
                    dx = rec.last_pos[0] - pos[0]
                    dy = rec.last_pos[1] - pos[1]
                    dist = (dx**2 + dy**2) ** 0.5
                    if dist < min_dist:
                        min_dist = dist
                        best_match_id = pid
                        
            if best_match_id is not None:
                # Merge into the old record!
                rec = self.pending.pop(best_match_id)
                rec.track_id = track_id  # update to new YOLO ID
                rec.last_pos = pos
                rec.pending_since = None
                self.active[track_id] = rec
                return

            # Brand new person
            self.active[track_id] = PersonRecord(
                track_id=track_id,
                camera_id=self.camera_id,
                entry_time=time.time(),
                last_pos=pos
            )

    def person_moved(self, track_id: int, pos: tuple[int, int]) -> None:
        with self.lock:
            if track_id in self.active:
                self.active[track_id].last_pos = pos

    def mark_exits(self, current_ids: set[int]) -> None:
        """Move all active IDs no longer in the zone to pending grace period."""
        with self.lock:
            missing_ids = set(self.active.keys()) - current_ids
            for track_id in missing_ids:
                record = self.active.pop(track_id)
                record.pending_since = time.time()
                self.pending[track_id] = record

    def prune_pending(self, timeout: float = 3.0) -> list[PersonRecord]:
        """Finalize exits for people who have been pending longer than timeout."""
        with self.lock:
            now = time.time()
            finalized = []
            expired_ids = [
                pid for pid, rec in self.pending.items() 
                if now - rec.pending_since >= timeout
            ]
            
            for pid in expired_ids:
                record = self.pending.pop(pid)
                record.exit_time = record.pending_since  # Use the exact time they left the zone
                
                # Update globals
                self.total_served += 1
                self.global_total_wait_seconds += record.wait_seconds
                if record.wait_seconds > self.global_longest_wait:
                    self.global_longest_wait = record.wait_seconds
                    
                self.history[pid] = record
                finalized.append(record)
                
            return finalized

    @property
    def queue_length(self) -> int:
        with self.lock:
            # Pending people are technically still in the "grace period", 
            # but usually we want to show exactly how many are visible.
            # Let's count only active for the dashboard count.
            return len(self.active)

    @property
    def longest_wait(self) -> float:
        with self.lock:
            active_max = max((r.wait_seconds for r in self.active.values()), default=0.0)
            return round(max(self.global_longest_wait, active_max), 1)

    @property
    def avg_wait(self) -> float:
        with self.lock:
            active_total = sum(r.wait_seconds for r in self.active.values())
            total_time = self.global_total_wait_seconds + active_total
            total_people = self.total_served + len(self.active)
            if total_people == 0:
                return 0.0
            return round(total_time / total_people, 1)

    @property
    def status(self) -> QueueStatus:
        length = self.queue_length
        if length == 0:
            return QueueStatus.EMPTY
        if length <= 2:
            return QueueStatus.LOW
        if length <= 5:
            return QueueStatus.MODERATE
        if length <= 9:
            return QueueStatus.HIGH
        return QueueStatus.CRITICAL

    def snapshot(self) -> dict:
        """Return a JSON-serialisable summary of the current state."""
        with self.lock:
            active_list = [
                {"id": r.track_id, "wait_seconds": r.wait_seconds}
                for r in self.active.values()
            ]
            
            recent = list(self.history.values())[-50:]
            exit_list = [
                {"id": r.track_id, "wait_seconds": r.wait_seconds}
                for r in reversed(recent)
            ]
            
            return {
                "camera_id": self.camera_id,
                "camera_name": self.camera_name,
                "queue_length": self.queue_length,
                "longest_wait": self.longest_wait,
                "avg_wait": self.avg_wait,
                "status": self.status.value,
                "total_served": self.total_served,
                "active": active_list,
                "recent_exits": exit_list,
            }
