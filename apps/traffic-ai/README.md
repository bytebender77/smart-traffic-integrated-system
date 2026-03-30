# Traffic AI Optimizer

AI-powered smart city traffic signal optimization and emergency green corridor system.

## Overview
This project ingests live video (RTSP/HTTP/USB camera) or uploaded clips, detects vehicles and emergency responders, models congestion, and generates adaptive signal plans. The React dashboard provides live telemetry, map views, and a persistent live feed monitor.

## Features
- Live video ingestion (RTSP, HTTP, USB camera, or file upload)
- Real-time vehicle detection and rolling analytics
- Congestion modeling with density scoring
- Adaptive signal timing per lane
- Emergency vehicle detection and green corridor routing
- Persistent live feed monitor across dashboard routes

## Quick Start

### 1. Install backend dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the backend
```bash
uvicorn backend.main:app --reload
```

API docs: http://localhost:8000/docs

### 3. Start the React dashboard
```bash
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:5173

### Optional: Streamlit dashboard (legacy)
```bash
streamlit run dashboard/app.py
```

## Live Feed Inputs
You can provide a live source via the UI's "Live Feed URL" field.

Supported formats:
- RTSP: `rtsp://user:pass@host:554/stream`
- HTTP/HTTPS: `http://host:port/stream`
- USB camera: `camera:0` (or just `0`)
- File upload: use the Upload button, then Start Video Stream

## Demo Workflow (with a single video)
1. Choose an intersection and a lane in the dashboard.
2. Upload a video or paste a live feed URL.
3. Click Start Live Feed or Start Video Stream.
4. Click Run Analytics to update counts, density, signals, and emergency routing.
5. Use the Intersections page to show the selected lane and map location.

Tip: if you only have one clip, assign it to one lane and explain that other lanes would connect to their own cameras in a real deployment.

## Environment Variables

Backend (`backend/config.py`):
- `YOLO_MODEL_PATH` (default: `yolov8n.pt`)
- `EMERGENCY_MODEL_PATH` (default: `yolov8n.pt`)
- `UPLOAD_DIR` (default: `data/uploads`)
- `CORS_ORIGINS` (default: `*`)

Frontend (`frontend/.env`):
- `VITE_API_BASE_URL` (default: `http://localhost:8000`)
- `VITE_TRAFFIC_VIDEO_PATH` (optional: auto-loads a fixed source for the dashboard)

Example `frontend/.env`:
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_TRAFFIC_VIDEO_PATH=
```

## Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/traffic/detect` | Vehicle detection (supports `start_frame`) |
| `GET` | `/api/v1/traffic/stream` | MJPEG live stream |
| `POST` | `/api/v1/traffic/density` | Density calculation |
| `POST` | `/api/v1/traffic/signals` | Adaptive signal plan |
| `POST` | `/api/v1/emergency/check` | Emergency vehicle detection |
| `POST` | `/api/v1/emergency/route` | Green corridor routing |
| `GET` | `/api/v1/system/status` | System status |
| `GET` | `/api/v1/system/intersections` | Map intersection data |

## Project Structure
```
urban_traffic/
├── backend/                 # FastAPI backend and endpoints
├── frontend/                # React dashboard
├── vision/                  # Detection pipelines
├── traffic_engine/          # Density, signals, routing logic
├── data/uploads/            # Uploaded videos
├── models/                  # Optional model weights
├── yolov8n.pt               # Default model weight
└── requirements.txt
```

## Pitch Line
"We built an AI-powered traffic intelligence system that dynamically optimizes traffic signals using computer vision and creates green corridors for emergency vehicles, reducing congestion and critical response time."
