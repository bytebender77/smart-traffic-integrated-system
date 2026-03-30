<div align="center">

# 🚦 Smart Traffic Integrated System

**AI-Powered Urban Traffic Management · Real-Time Congestion Analysis · Emergency Green Corridors**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

---

*A modular, production-ready platform that combines computer vision, adaptive signal optimization, and emergency corridor routing into a unified command dashboard.*

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Option 1 — Docker (Recommended)](#option-1--docker-recommended)
  - [Option 2 — Manual Setup](#option-2--manual-setup)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [How It Works](#-how-it-works)
- [Environment Variables](#-environment-variables)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚀 Overview

The **Smart Traffic Integrated System** is an end-to-end intelligent traffic management platform designed for smart-city deployments. It merges two complementary engines into a single operational workflow:

| Engine | Purpose |
|--------|---------|
| **AI Intelligence Engine** | Processes live video feeds (RTSP / HTTP / webcam / file upload) using YOLOv8 to detect and classify vehicles, compute weighted congestion densities, and generate adaptive signal plans. |
| **Legacy Simulation Engine** | Runs a SUMO-based digital twin of a 4-junction urban grid, providing physics-accurate traffic simulation with real-time telemetry and MJPEG video streams. |

Both engines feed into a **unified React dashboard** that provides real-time intersection monitoring, congestion heatmaps, signal control, and emergency green corridor activation.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎥 **Real-Time Vehicle Detection** | YOLOv8-powered CV pipeline detects cars, buses, trucks, and motorcycles from any video source |
| ⚡ **Adaptive Signal Control** | Dynamically adjusts green/red durations based on directional traffic load (NS vs EW split) |
| 🚑 **Emergency Green Corridor** | Dijkstra-based congestion-aware routing clears a green wave for ambulances and fire trucks |
| 📊 **Live Congestion Heatmaps** | Color-coded intersection density (LOW / MEDIUM / HIGH / SEVERE) with real-time updates |
| 🖥️ **Unified Command Dashboard** | React-based control center with Leaflet maps, live MJPEG streams, and Recharts analytics |
| 🔄 **SUMO Digital Twin** | Physics-accurate 2×2 grid simulation with TraCI control for development and testing |
| 🐳 **Docker Ready** | One-command deployment with `docker compose up` |
| 🔌 **Auto Port Discovery** | Shell orchestrator finds free ports and auto-configures all services |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        REACT DASHBOARD                         │
│           (Vite · Tailwind · Leaflet · Recharts)               │
│                        Port: 5173                              │
└──────────────┬──────────────────────────┬──────────────────────┘
               │ REST API                  │ REST API
               ▼                           ▼
┌──────────────────────────┐  ┌──────────────────────────────────┐
│   TRAFFIC AI BACKEND     │  │     LEGACY SUMO BACKEND          │
│  ┌────────────────────┐  │  │  ┌───────────────────────────┐   │
│  │ Vehicle Detection  │  │  │  │ SUMO Simulation (TraCI)   │   │
│  │ (YOLOv8 + OpenCV)  │  │  │  │ 4-Junction Urban Grid     │   │
│  ├────────────────────┤  │  │  ├───────────────────────────┤   │
│  │ Density Calculator │  │  │  │ CV Detector (Synthetic)   │   │
│  │ Signal Optimizer   │  │  │  │ MJPEG Video Stream        │   │
│  │ Emergency Router   │  │  │  │ Adaptive Signal Control   │   │
│  │ (Dijkstra/NetworkX)│  │  │  │ Emergency Green Corridor  │   │
│  └────────────────────┘  │  │  └───────────────────────────┘   │
│       FastAPI :8000      │  │         FastAPI :8001             │
└──────────────────────────┘  └──────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18 · Vite · Tailwind CSS · Leaflet · Recharts · Zustand |
| **AI Backend** | Python 3.11 · FastAPI · OpenCV · Ultralytics YOLOv8 · NetworkX · Pandas |
| **Simulation Backend** | Python 3.11 · FastAPI · SUMO · TraCI · OpenCV · NumPy |
| **DevOps** | Docker · Docker Compose · Bash Orchestration |

---

## 🎯 Getting Started

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Python** | 3.10+ | Required for both backends |
| **Node.js** | 18+ | Required for the React frontend |
| **npm** | 9+ | Comes with Node.js |
| **SUMO** | 1.18+ | *Optional* — only needed for the simulation engine |
| **Docker** | 24+ | *Optional* — for containerized deployment |

---

### Option 1 — Docker (Recommended)

The fastest way to get the entire system running.

```bash
# 1. Clone the repository
git clone https://github.com/bytebender77/smart-traffic-integrated-system.git
cd smart-traffic-integrated-system

# 2. Build and start all services
docker compose up --build

# 3. Open the dashboard
#    → http://localhost:5173
```

**Services running:**
| Service | URL |
|---------|-----|
| React Dashboard | http://localhost:5173 |
| Traffic AI API | http://localhost:8000/docs |
| Legacy SUMO API | http://localhost:8001 |

To stop all services:
```bash
docker compose down
```

---

### Option 2 — Manual Setup

#### Step 1: Clone the repository
```bash
git clone https://github.com/bytebender77/smart-traffic-integrated-system.git
cd smart-traffic-integrated-system
```

#### Step 2: Install Python dependencies
```bash
# Traffic AI backend
pip install -r apps/traffic-ai/requirements.txt

# Legacy SUMO backend (requires SUMO installed)
pip install -r apps/legacy-sumo/requirements.txt
```

#### Step 3: Install frontend dependencies
```bash
cd apps/traffic-ai/frontend
npm install
cd ../../..
```

#### Step 4: Launch everything with one command
```bash
bash run.sh
```

This orchestrator script will:
- 🔍 Find free ports for both backends automatically
- 📝 Write the Vite `.env` file with the correct API URLs
- 🚀 Start both FastAPI backends in the background
- ⏳ Wait for health checks to confirm backends are ready
- 🖥️ Launch the React dev server on port `5173`

#### Manual startup (individual services)

If you prefer to start services individually:

```bash
# Terminal 1 — Traffic AI Backend
cd apps/traffic-ai
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — Legacy SUMO Backend
cd apps/legacy-sumo
bash run.sh --port 8001

# Terminal 3 — React Frontend
cd apps/traffic-ai/frontend
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
echo "VITE_LEGACY_API_BASE_URL=http://localhost:8001" >> .env
npm run dev
```

---

## 📡 API Reference

### Traffic AI Backend (`localhost:8000`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/traffic/detect` | Run YOLOv8 vehicle detection on a video/frame |
| `GET` | `/api/v1/traffic/stream` | MJPEG live stream of detection output |
| `POST` | `/api/v1/traffic/density` | Calculate weighted traffic density |
| `POST` | `/api/v1/traffic/signals` | Generate adaptive signal timing plan |
| `POST` | `/api/v1/emergency/check` | Check for emergency vehicles in feed |
| `POST` | `/api/v1/emergency/route` | Compute emergency green corridor route |
| `GET` | `/api/v1/system/status` | System status and metrics |
| `GET` | `/api/v1/system/intersections` | Map intersection data for Leaflet |

> 📖 Full interactive docs: http://localhost:8000/docs

### Legacy SUMO Backend (`localhost:8001`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/traffic-data` | Live lane counts, signals, wait times |
| `GET` | `/cv-data` | YOLOv8-style detection summary |
| `GET` | `/video-feed` | MJPEG stream of intersection view |
| `GET` | `/optimize-signal` | AI signal timing recommendations |
| `GET` | `/emergency` | Ambulance detection & corridor status |
| `GET` | `/history` | Last 60s of simulation snapshots |
| `GET` | `/stats` | Cumulative performance metrics |
| `POST` | `/simulation/restart` | Restart simulation from T=0 |

---

## 📁 Project Structure

```
smart-traffic-integrated-system/
│
├── apps/
│   ├── traffic-ai/                    # AI Detection Engine
│   │   ├── backend/                   #   FastAPI application & routes
│   │   │   ├── main.py                #   App entry point
│   │   │   ├── api_routes.py          #   API endpoint definitions
│   │   │   ├── config.py              #   Environment configuration
│   │   │   └── traffic_simulator.py   #   Background traffic simulator
│   │   ├── frontend/                  #   React Dashboard (Vite)
│   │   │   ├── src/
│   │   │   │   ├── components/        #   Reusable UI components
│   │   │   │   ├── pages/             #   Route pages
│   │   │   │   ├── services/          #   API client layer
│   │   │   │   └── store/             #   Zustand state management
│   │   │   ├── Dockerfile             #   Frontend container
│   │   │   └── package.json
│   │   ├── vision/                    #   YOLOv8 detection pipelines
│   │   ├── traffic_engine/            #   Density, signal & routing logic
│   │   ├── utils/                     #   Logging & helper utilities
│   │   ├── Dockerfile                 #   Backend container
│   │   └── requirements.txt
│   │
│   └── legacy-sumo/                   # SUMO Simulation Engine
│       ├── backend/                   #   FastAPI + TraCI server
│       ├── controller/                #   Adaptive signal controller
│       ├── cv_module/                 #   Synthetic CV detector
│       ├── simulation/                #   SUMO network & route files
│       ├── frontend/                  #   Legacy HTML dashboard
│       ├── Dockerfile                 #   Simulation container
│       └── requirements.txt
│
├── presentation/                      # HTML Pitch Deck (20 slides)
├── scripts/                           # Orchestration & utility scripts
│   └── start-integrated-random-ports.sh
├── logs/                              # Runtime log output
│
├── docker-compose.yml                 # Multi-service Docker orchestration
├── run.sh                             # One-command local launcher
├── LICENSE                            # MIT License
└── README.md                          # This file
```

---

## 🧠 How It Works

### 1. Congestion Detection (PCU Weighted Model)

Each vehicle type has a **Passenger Car Unit (PCU)** weight reflecting its road space:

| Vehicle | PCU Weight |
|---------|-----------|
| Car | 1.0 |
| Motorcycle | 0.5 |
| Bus | 2.5 |
| Truck | 2.0 |

```
weighted_load = Σ (count × pcu_weight)
density_percent = (weighted_load / lane_capacity) × 100
```

| Density | Severity |
|---------|----------|
| 0–30% | 🟢 LOW |
| 30–70% | 🟡 MEDIUM |
| 70–100% | 🟠 HIGH |
| >100% | 🔴 SEVERE |

### 2. Adaptive Signal Timing

Green time is allocated proportionally to directional traffic demand:

```
NS_load = North + South vehicles
EW_load = East + West vehicles
ns_ratio = NS_load / (NS_load + EW_load)
ns_green = clamp(15s, 60s, f(ns_ratio))
```

The system re-evaluates every **3 seconds** and adjusts signal phases dynamically.

### 3. Emergency Green Corridor

When an emergency vehicle is detected:
1. **Route Calculation**: Dijkstra shortest path on a weighted graph (NetworkX), where edge costs increase with congestion
2. **Corridor Activation**: All intersections along the computed route switch to green for the emergency direction
3. **Auto-Resume**: After the emergency vehicle passes, normal adaptive control resumes

```
best_path = argmin Σ(edge_cost_i)
```

---

## ⚙️ Environment Variables

### Traffic AI Backend

| Variable | Default | Description |
|----------|---------|-------------|
| `YOLO_MODEL_PATH` | `yolov8n.pt` | Path to YOLOv8 model weights |
| `EMERGENCY_MODEL_PATH` | `yolov8n.pt` | Path to emergency detection model |
| `UPLOAD_DIR` | `data/uploads` | Directory for uploaded video files |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |

### React Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Traffic AI backend URL |
| `VITE_LEGACY_API_BASE_URL` | `http://localhost:8001` | Legacy SUMO backend URL |

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature`
3. **Commit** your changes: `git commit -m "Add your feature"`
4. **Push** to the branch: `git push origin feature/your-feature`
5. **Open** a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ for smarter, safer cities**

</div>
