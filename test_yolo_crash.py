import cv2
import numpy as np
import traceback
from queue_monitor.config import load_config
from queue_monitor.tracker import VideoProcessor
from queue_monitor.db import QueueDatabase

class MockCap:
    def get(self, prop): return 640 if prop == 3 else 480
    def isOpened(self): return True
    def read(self):
        # Create a mock frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Draw something
        cv2.rectangle(frame, (100, 100), (200, 200), (255, 255, 255), -1)
        return True, frame
    def release(self): pass

# Patch VideoProcessor._connect to use MockCap
def mock_connect(self):
    return MockCap()

VideoProcessor._connect = mock_connect

try:
    print('Loading config...')
    cfg = load_config()
    db = QueueDatabase(':memory:')
    p = VideoProcessor(cfg.cameras[0], cfg.model, cfg.stream, db)
    p._running = True
    print('Running tracker loop once...')
    p._run_loop() # This will loop forever, but let's see if it crashes
except Exception as e:
    traceback.print_exc()
