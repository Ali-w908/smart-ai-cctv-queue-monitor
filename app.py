"""
ML Queue Monitoring System v2.0
================================
Multi-camera queue monitoring using YOLOv8 person tracking, configurable
polygon zones, SQLite persistence, and a FastAPI live-streaming dashboard.

Run:
    python app.py                          # default config.yaml on port 8000
    python app.py --config config.yaml --port 9000
"""

from __future__ import annotations

import argparse
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from queue_monitor.config import load_config
from queue_monitor.manager import CameraManager
from queue_monitor.routes import router, set_manager

# ── Lifespan ─────────────────────────────────────────────────────────────────

_manager: CameraManager | None = None


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Start all camera processors on startup, stop them on shutdown."""
    global _manager
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="config.yaml")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    args, _ = parser.parse_known_args()

    config = load_config(args.config)
    _manager = CameraManager(config)
    set_manager(_manager)
    _manager.start_all()

    print(f"[INFO] Queue Monitor started — {len(config.cameras)} camera(s)")
    for cam in config.cameras:
        print(f"  • {cam.id}: {cam.name} → {cam.source}")

    yield

    _manager.stop_all()
    print("[INFO] Queue Monitor stopped.")


# ── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="ML Queue Monitor",
    version="2.0.0",
    lifespan=lifespan,
)
app.include_router(router)


# ── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ML Queue Monitor v2")
    parser.add_argument("--config", type=str, default="config.yaml", help="Config file path")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Bind address")
    args = parser.parse_args()

    uvicorn.run("app:app", host=args.host, port=args.port, reload=False)
