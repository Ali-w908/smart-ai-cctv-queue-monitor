import yaml
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class CameraConfig:
    id: str
    name: str
    source: str | int
    zone: list[list[int]] = field(default_factory=list)

@dataclass  
class ModelConfig:
    weights: str = "yolov8n.pt"
    confidence: float = 0.50
    tracker: str = "bytetrack.yaml"

@dataclass
class StreamConfig:
    fps: int = 20
    jpeg_quality: int = 75

@dataclass
class AppConfig:
    model: ModelConfig
    stream: StreamConfig
    cameras: list[CameraConfig]
    db_path: str = "queue_history.db"

def load_config(path: str = "config.yaml") -> AppConfig:
    """Parse and validate config.yaml, return AppConfig."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    model_data = data.get("model", {})
    stream_data = data.get("stream", {})
    cameras_data = data.get("cameras", [])
    
    cameras = []
    for c in cameras_data:
        cameras.append(CameraConfig(
            id=c["id"],
            name=c["name"],
            source=c["source"],
            zone=c.get("zone", [])
        ))
        
    return AppConfig(
        model=ModelConfig(**model_data),
        stream=StreamConfig(**stream_data),
        cameras=cameras,
        db_path=data.get("db_path", "queue_history.db")
    )
