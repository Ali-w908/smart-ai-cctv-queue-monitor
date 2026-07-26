import time
from .config import AppConfig
from .tracker import VideoProcessor
from .db import QueueDatabase

class CameraManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.db = QueueDatabase(config.db_path)
        self.processors: dict[str, VideoProcessor] = {}
        
        for cam_cfg in config.cameras:
            self.processors[cam_cfg.id] = VideoProcessor(
                camera_config=cam_cfg,
                model_config=config.model,
                stream_config=config.stream,
                database=self.db,
            )
    
    def start_all(self) -> None:
        for p in self.processors.values():
            p.start()
    
    def stop_all(self) -> None:
        for p in self.processors.values():
            p.stop()
        self.db.close()
    
    def get_processor(self, camera_id: str) -> VideoProcessor | None:
        return self.processors.get(camera_id)
    
    def get_all_stats(self) -> dict:
        """Aggregate stats across all cameras."""
        cameras = []
        total_queue = 0
        total_served = 0
        global_wait_sum = 0.0
        active_wait_sum = 0.0
        longest_overall = 0.0
        
        for cam_id, proc in self.processors.items():
            snap = proc.queue_state.snapshot()
            snap["camera_status"] = proc.camera_status.value
            cameras.append(snap)
            total_queue += snap["queue_length"]
            total_served += snap["total_served"]
            
            with proc.queue_state.lock:
                global_wait_sum += proc.queue_state.global_total_wait_seconds
                for r in proc.queue_state.active.values():
                    active_wait_sum += r.wait_seconds
                    
            if snap["longest_wait"] > longest_overall:
                longest_overall = snap["longest_wait"]
                
        total_people = total_served + total_queue
        avg_wait = round((global_wait_sum + active_wait_sum) / total_people, 1) if total_people > 0 else 0.0
        
        return {
            "total_queue_length": total_queue,
            "total_served": total_served,
            "avg_wait": avg_wait,
            "longest_wait": longest_overall,
            "cameras": cameras,
            "timestamp": time.time(),
        }
