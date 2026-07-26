import traceback
print('Start')
from queue_monitor.config import load_config
from queue_monitor.tracker import VideoProcessor
from queue_monitor.db import QueueDatabase
from queue_monitor.drawing import draw_overlay
from queue_monitor.zone import build_default_polygon

print('Loaded imports')
cfg = load_config()
db = QueueDatabase(':memory:')
p = VideoProcessor(cfg.cameras[0], cfg.model, cfg.stream, db)

print('Connecting...')
cap = p._connect()
print('Connected:', cap is not None)
ok, frame = cap.read()
print('Frame shape:', frame.shape)
poly = build_default_polygon(frame.shape[1], frame.shape[0])

print('Running draw_overlay...')
try:
    out = draw_overlay(frame, poly, p.queue_state, [], 'Main')
    print('Draw ok, shape:', out.shape)
except Exception as e:
    traceback.print_exc()
