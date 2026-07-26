# Smart AI CCTV Queue Monitor

A robust, real-time queue monitoring system powered by AI. This project uses YOLOv8 object detection and ByteTrack tracking to monitor CCTV camera streams (RTSP, HTTP, or local webcams), automatically estimate customer wait times, calculate queue lengths, and measure service efficiency.

It features a lightweight web dashboard that streams the live annotated camera feeds and displays historical queue statistics.

## Features

- **Multi-Camera Support:** Connect to multiple IP cameras (RTSP/HTTP) or local webcams simultaneously.
- **Real-Time AI Tracking:** Uses Ultralytics YOLOv8 and ByteTrack for highly accurate human detection and persistence.
- **Smart Queue Logic:** Features spatial re-identification and a customizable grace period to seamlessly handle momentary occlusions and prevent duplicate counting.
- **Configurable Zones:** Define custom polygonal queue zones for each camera using a simple configuration file.
- **Live Web Dashboard:** A beautiful, responsive dashboard to monitor live feeds and metrics without heavy client-side processing.
- **Persistent Global Metrics:** Calculates daily historical average wait times, longest wait times, and total customers served across all cameras.
- **Data Persistence:** Automatically logs all completed queue sessions to a local SQLite database for future analysis.

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn
- **AI / Computer Vision:** OpenCV, Ultralytics YOLOv8, PyTorch
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Database:** SQLite

## Prerequisites

- Python 3.10+
- An NVIDIA GPU is highly recommended for real-time inference (CUDA support), but it can run on CPU.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/smart-ai-cctv-queue-monitor.git
   cd smart-ai-cctv-queue-monitor
   ```

2. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: Ensure you install the appropriate PyTorch version for your CUDA toolkit if you are using a GPU).*

## Configuration

Configure your cameras, tracking zones, and AI model in `config.yaml`:

```yaml
cameras:
  - id: "cam-main"
    name: "Main Camera"
    source: 0  # Use 0 for local webcam, or "http://IP:PORT/video" for IP cameras
    zone: [[100, 100], [500, 100], [500, 400], [100, 400]] # Define your polygon vertices

model:
  weights: "yolov8n.pt"  # Nano model by default for speed
  confidence: 0.3
  tracker: "bytetrack.yaml"
```

## Usage

Start the FastAPI server:

```bash
python app.py
```

Then, open your web browser and navigate to:
**http://localhost:8000**

## How the AI Logic Works

- **Grace Period:** If a person steps out of the defined queue zone or is momentarily lost by the AI, they enter a 3-second grace period. If they return to the zone within that time, their wait timer continues seamlessly.
- **Spatial Re-ID:** If the AI assigns a new tracking ID to a person (e.g., after an occlusion), the system compares their coordinates to recently "lost" IDs and intelligently merges them to prevent double-counting.
- **Global Averages:** Wait times are calculated historically. The system logs the total time spent by all completed customers and aggregates it with the current active queue to provide a true daily average.

## License

This project is licensed under the MIT License.
