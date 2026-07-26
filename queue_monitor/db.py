import sqlite3
import threading
from pathlib import Path

class QueueDatabase:
    """Thread-safe SQLite writer for completed queue sessions."""
    
    def __init__(self, db_path: str = "queue_history.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        
        with self.lock:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._create_tables()
            
    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS queue_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camera_id TEXT,
                person_id INTEGER,
                entry_time REAL,
                exit_time REAL,
                wait_seconds REAL
            )
        ''')
        self.conn.commit()
        
    def log_exit(self, camera_id: str, person_id: int, entry_time: float, exit_time: float, wait_seconds: float) -> None:
        """Insert a completed queue session."""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO queue_sessions (camera_id, person_id, entry_time, exit_time, wait_seconds) VALUES (?, ?, ?, ?, ?)",
                (camera_id, person_id, entry_time, exit_time, wait_seconds)
            )
            self.conn.commit()
        
    def get_recent(self, limit: int = 100) -> list[dict]:
        """Return the most recent sessions across all cameras."""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, camera_id, person_id, entry_time, exit_time, wait_seconds FROM queue_sessions ORDER BY exit_time DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [{"id": r[0], "camera_id": r[1], "person_id": r[2], "entry_time": r[3], "exit_time": r[4], "wait_seconds": r[5]} for r in rows]
    
    def get_stats_by_camera(self, camera_id: str) -> dict:
        """Return aggregate stats for a camera: total_served, avg_wait, max_wait."""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*), AVG(wait_seconds), MAX(wait_seconds)
                FROM queue_sessions
                WHERE camera_id = ?
            """, (camera_id,))
            row = cursor.fetchone()
            return {
                "total_served": row[0] or 0,
                "avg_wait": round(row[1], 1) if row[1] else 0.0,
                "max_wait": round(row[2], 1) if row[2] else 0.0
            }
    
    def close(self) -> None:
        with self.lock:
            self.conn.close()
