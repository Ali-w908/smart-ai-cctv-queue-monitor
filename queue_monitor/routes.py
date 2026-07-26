"""FastAPI routes for the queue monitoring dashboard and API."""

import time

import cv2
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from .manager import CameraManager

# Module-level reference — set by app.py during startup.
manager: CameraManager | None = None


def set_manager(mgr: CameraManager) -> None:
    """Wire the CameraManager into the router (called from app.py)."""
    global manager
    manager = mgr


router = APIRouter()


# ── Dashboard ────────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def dashboard():
    from .dashboard import get_dashboard_html

    return HTMLResponse(content=get_dashboard_html())


# ── MJPEG Video Streams ──────────────────────────────────────────────────────

import asyncio

from fastapi import Request

async def _generate_frames(request: Request, proc, fps: int, quality: int):
    """Yield JPEG frames as a multipart MJPEG stream."""
    delay = 1.0 / max(fps, 1)
    while True:
        if await request.is_disconnected():
            break
            
        frame = proc.latest_frame
        if frame is None:
            await asyncio.sleep(0.05)
            continue
            
        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n"
        )
        await asyncio.sleep(delay)


@router.get("/video_feed/{camera_id}")
async def video_feed(request: Request, camera_id: str):
    if not manager:
        raise HTTPException(503, "System not ready")
    proc = manager.get_processor(camera_id)
    if not proc:
        raise HTTPException(404, f"Camera '{camera_id}' not found")

    cfg = manager.config.stream
    return StreamingResponse(
        _generate_frames(request, proc, fps=cfg.fps, quality=cfg.jpeg_quality),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


# ── JSON API ─────────────────────────────────────────────────────────────────

@router.get("/api/cameras")
async def list_cameras():
    """Return the list of configured cameras with their current status."""
    if not manager:
        return JSONResponse({"cameras": []})

    cameras = []
    for cam_id, proc in manager.processors.items():
        cameras.append({
            "id": cam_id,
            "name": proc.cam_cfg.name,
            "status": proc.camera_status.value,
        })
    return JSONResponse({"cameras": cameras})


@router.get("/api/stats")
async def all_stats():
    """Aggregate stats across all cameras."""
    if not manager:
        return JSONResponse({})
    return JSONResponse(manager.get_all_stats())


@router.get("/api/stats/{camera_id}")
async def camera_stats(camera_id: str):
    """Stats for a single camera."""
    if not manager:
        raise HTTPException(503, "System not ready")
    proc = manager.get_processor(camera_id)
    if not proc:
        raise HTTPException(404, f"Camera '{camera_id}' not found")

    snap = proc.queue_state.snapshot()
    snap["camera_status"] = proc.camera_status.value
    return JSONResponse(snap)
