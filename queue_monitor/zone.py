"""Polygon zone helpers for queue area detection."""

import cv2
import numpy as np


def build_polygon(vertices: list[list[int]]) -> np.ndarray:
    """Convert config vertices to OpenCV contour format (N, 1, 2) int32."""
    pts = np.array(vertices, dtype=np.int32)
    return pts.reshape((-1, 1, 2))


def build_default_polygon(frame_w: int, frame_h: int) -> np.ndarray:
    """Fallback: center rectangle occupying ~40% width × ~60% height."""
    cx, cy = frame_w // 2, frame_h // 2
    half_w = int(frame_w * 0.20)
    half_h = int(frame_h * 0.30)
    vertices = [
        [cx - half_w, cy - half_h],
        [cx + half_w, cy - half_h],
        [cx + half_w, cy + half_h],
        [cx - half_w, cy + half_h],
    ]
    return build_polygon(vertices)


def point_in_polygon(point: tuple[int, int], polygon: np.ndarray) -> bool:
    """Test if a point is inside the contour using cv2.pointPolygonTest."""
    return cv2.pointPolygonTest(
        polygon, (float(point[0]), float(point[1])), False
    ) >= 0
