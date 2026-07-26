"""OpenCV overlay rendering for camera frames."""

import cv2
import numpy as np

from .models import QueueState

# Colour palette (BGR)
CLR_ZONE_BORDER = (0, 255, 200)   # Cyan-green
CLR_ZONE_FILL = (0, 255, 200)     # Translucent fill
CLR_BBOX_IN = (0, 220, 100)       # Green — person inside zone
CLR_BBOX_OUT = (200, 200, 200)    # Grey  — person outside zone
CLR_ACCENT = (0, 200, 255)        # Orange-yellow HUD accent
CLR_TEXT = (255, 255, 255)


def draw_overlay(
    frame: np.ndarray,
    polygon: np.ndarray,
    queue_state: QueueState,
    detections: list[dict],
    camera_name: str = "",
) -> np.ndarray:
    """Draw zone, bboxes, IDs, wait times, and HUD on the frame."""
    overlay = frame.copy()
    h, w = frame.shape[:2]

    # ── Zone fill (semi-transparent) ─────────────────────────────────────
    poly_2d = polygon.reshape(-1, 2)
    cv2.fillPoly(overlay, [poly_2d], CLR_ZONE_FILL)
    cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)
    cv2.polylines(frame, [poly_2d], True, CLR_ZONE_BORDER, 2, cv2.LINE_AA)

    # Zone label
    zone_label = "QUEUE AREA"
    (tw, th), _ = cv2.getTextSize(zone_label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
    zx = int(poly_2d[:, 0].mean()) - tw // 2
    zy = int(poly_2d[:, 1].min()) - 10
    cv2.putText(
        frame, zone_label, (zx, zy),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, CLR_ZONE_BORDER, 2, cv2.LINE_AA,
    )

    # ── Bounding boxes ───────────────────────────────────────────────────
    for det in detections:
        x1, y1, x2, y2 = map(int, det["bbox"])
        tid = det.get("track_id", -1)
        inside = det.get("in_zone", False)
        colour = CLR_BBOX_IN if inside else CLR_BBOX_OUT

        cv2.rectangle(frame, (x1, y1), (x2, y2), colour, 2, cv2.LINE_AA)

        # ID + wait badge
        label = f"ID {tid}"
        if inside and tid != -1:
            with queue_state.lock:
                rec = queue_state.active.get(tid)
            if rec:
                label += f"  {rec.wait_seconds:.0f}s"

        (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.50, 1)
        cv2.rectangle(frame, (x1, y1 - lh - 8), (x1 + lw + 6, y1), colour, -1)
        cv2.putText(
            frame, label, (x1 + 3, y1 - 4),
            cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 0, 0), 1, cv2.LINE_AA,
        )

    # ── HUD panel (top-left, dark background) ────────────────────────────
    snap = queue_state.snapshot()
    hud_lines = [
        f"Queue: {snap['queue_length']}",
        f"Avg Wait: {snap['avg_wait']}s",
        f"Longest: {snap['longest_wait']}s",
        f"Status: {snap['status'].upper()}",
    ]

    pad, line_h = 12, 28
    panel_h = pad * 2 + line_h * len(hud_lines)
    panel_w = 260

    # Darken background behind HUD text
    sub = frame[0:panel_h, 0:panel_w]
    black = np.zeros(sub.shape, dtype=np.uint8)
    cv2.addWeighted(sub, 0.3, black, 0.7, 0, sub)
    frame[0:panel_h, 0:panel_w] = sub

    for i, line in enumerate(hud_lines):
        cv2.putText(
            frame, line, (pad, pad + line_h * (i + 1) - 6),
            cv2.FONT_HERSHEY_SIMPLEX, 0.60, CLR_ACCENT, 2, cv2.LINE_AA,
        )

    # ── Camera name (top-right) ──────────────────────────────────────────
    if camera_name:
        (nw, nh), _ = cv2.getTextSize(camera_name, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        nx = w - nw - 16
        ny = 30
        # Dark pill behind text
        cv2.rectangle(frame, (nx - 8, ny - nh - 6), (nx + nw + 8, ny + 8), (0, 0, 0), -1)
        cv2.putText(
            frame, camera_name, (nx, ny),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, CLR_TEXT, 2, cv2.LINE_AA,
        )

    return frame
