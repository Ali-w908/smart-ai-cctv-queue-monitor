import os
import threading
import time
from typing import Optional
import cv2
import numpy as np
from ultralytics import YOLO
from .config import CameraConfig, ModelConfig, StreamConfig
from .models import QueueState, CameraStatus
from .zone import build_polygon, build_default_polygon, point_in_polygon
from .drawing import draw_overlay
from .db import QueueDatabase

# Set FFmpeg options to avoid timeouts on HTTP/RTSP streams
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;5000"

PERSON_CLASS_ID = 0

class VideoProcessor:
    def __init__(
        self,
        camera_config: CameraConfig,
        model_config: ModelConfig,
        stream_config: StreamConfig,
        database: QueueDatabase,
    ):
        self.cam_cfg = camera_config
        self.model_cfg = model_config
        self.stream_cfg = stream_config
        self.db = database
        
        self.model = YOLO(model_config.weights)
        self.queue_state = QueueState(camera_id=camera_config.id, camera_name=camera_config.name)
        self.camera_status = CameraStatus.CONNECTING
        self.polygon: Optional[np.ndarray] = None
        
        self._frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def start(self) -> None:
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            
    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
    
    @property
    def latest_frame(self) -> Optional[np.ndarray]:
        with self._frame_lock:
            return self._frame.copy() if self._frame is not None else None
    
    def _run(self) -> None:
        """Main loop with reconnection logic."""
        import traceback
        try:
            self._run_loop()
        except Exception as e:
            print(f"[{self.cam_cfg.id}] FATAL ERROR in tracker thread:")
            traceback.print_exc()
            self.camera_status = CameraStatus.OFFLINE

    def _run_loop(self) -> None:
        while self._running:
            cap = self._connect()
            if cap is None:
                continue  # retry after backoff
            self.camera_status = CameraStatus.ONLINE
            
            # Init polygon from config or auto-generate
            if not self.cam_cfg.zone:
                frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self.polygon = build_default_polygon(frame_w, frame_h)
            else:
                self.polygon = build_polygon(self.cam_cfg.zone)
            
            failed_frames = 0
            while self._running:
                ok, frame = cap.read()
                
                if not ok or frame is None or frame.size == 0:
                    failed_frames += 1
                    if failed_frames > 30:
                        self.camera_status = CameraStatus.OFFLINE
                        cap.release()
                        break  # outer loop will reconnect
                    time.sleep(0.1)
                    continue
                
                failed_frames = 0
                
                # YOLO track -> detect persons -> check zone -> update state
                results = self.model.track(
                    frame, 
                    persist=True, 
                    classes=[PERSON_CLASS_ID],
                    conf=self.model_cfg.confidence,
                    tracker=self.model_cfg.tracker,
                    verbose=False
                )
                
                detections = []
                current_ids = set()
                
                if results and len(results) > 0 and results[0].boxes is not None:
                    boxes = results[0].boxes
                    for i in range(len(boxes)):
                        cls_id = int(boxes.cls[i].item())
                        if cls_id != PERSON_CLASS_ID:
                            continue
                            
                        x1, y1, x2, y2 = boxes.xyxy[i].tolist()
                        
                        track_id = -1
                        if boxes.id is not None:
                            track_id = int(boxes.id[i].item())
                            
                        # foot point test
                        foot_point = (int((x1 + x2) / 2), int(y2))
                        in_zone = point_in_polygon(foot_point, self.polygon)
                        
                        detections.append({
                            "bbox": (x1, y1, x2, y2),
                            "track_id": track_id,
                            "in_zone": in_zone
                        })
                        
                        if in_zone and track_id != -1:
                            self.queue_state.person_entered(track_id, foot_point)
                            current_ids.add(track_id)
                            
                # Mark exits (puts them in pending state)
                self.queue_state.mark_exits(current_ids)
                
                # Finalize exits that have passed the 3-second grace period
                exited_persons = self.queue_state.prune_pending(timeout=3.0)
                
                for p in exited_persons:
                    self.db.log_exit(
                        camera_id=self.cam_cfg.id,
                        person_id=p.track_id,
                        entry_time=p.entry_time,
                        exit_time=p.exit_time,
                        wait_seconds=p.wait_seconds
                    )
                
                # Draw overlay
                out_frame = draw_overlay(
                    frame=frame,
                    polygon=self.polygon,
                    queue_state=self.queue_state,
                    detections=detections,
                    camera_name=self.cam_cfg.name
                )
                
                with self._frame_lock:
                    self._frame = out_frame
            
            if cap:
                cap.release()
    
    def _connect(self) -> Optional[cv2.VideoCapture]:
        """Try to open the video source. On failure, wait 5s and return None."""
        self.camera_status = CameraStatus.CONNECTING
        
        source = self.cam_cfg.source
        if isinstance(source, str) and source.isdigit():
            source = int(source)
            
        if isinstance(source, int) and os.name == 'nt':
            cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        elif isinstance(source, str) and (source.startswith("http") or source.startswith("rtsp")):
            cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
        else:
            cap = cv2.VideoCapture(source)
            
        if not cap.isOpened():
            print(f"[{self.cam_cfg.id}] Cannot connect to {self.cam_cfg.source}, retrying in 5s...")
            time.sleep(5)
            return None
        return cap
