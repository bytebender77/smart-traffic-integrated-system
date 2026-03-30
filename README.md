# Smart Traffic Integrated System

AI-powered urban traffic management, congestion analysis, and emergency response platform.

## 🚀 Overview
The **Smart Traffic Integrated System** is a modular platform that combines real-time computer vision (AI) with high-fidelity traffic simulation. It provides city operators with a unified dashboard to monitor intersections, optimize signal timings based on live density, and coordinate emergency "Green Corridors."

This project integrates two primary engines:
1.  **AI Intelligence Engine**: Processes live video feeds to detect vehicles and calculate directional traffic load.
2.  **Legacy Simulation Engine**: A SUMO-based digital twin that models complex urban grid behavior.

## ✨ Key Features
*   **Real-Time Vehicle Detection**: Powered by YOLOv8, detects cars, buses, trucks, and motorcycles from any RTSP/HTTP feed.
*   **Adaptive Signal Control**: Dynamically adjusts green-light durations based on directional demand (NS vs EW load).
*   **Emergency Green Corridor**: Instant priority routing for ambulances and fire trucks, coordinating multiple junctions to clear a path.
*   **Unified Dashboard**: A modern React-based command center with live MJPEG streams, heatmaps, and telemetry.
*   **Scalable Architecture**: Modular backends that can run on any available ports with automatic discovery.

## 🏗️ Architecture
*   **Frontend**: React + Tailwind CSS (Vite)
*   **AI Backend**: FastAPI + OpenCV + YOLOv8
*   **Simulation Backend**: FastAPI + SUMO (Simulation of Urban MObility) + TraCI
*   **Startup Runtime**: Bash-based orchestrator with automatic port assignment.

## 🛠️ Quick Start

### 1. Requirements
*   Python 3.10+
*   Node.js & npm
*   SUMO (optional, for simulation features)

### 2. Launch the System
Run the integrated startup script from the root directory:
```bash
bash run.sh
```
This script will:
*   Identify free ports for both backends and the frontend.
*   Install dependencies if needed.
*   Start the AI Backend, Simulation Backend, and React Dashboard.
*   Open the dashboard in your default browser.

## 📁 Project Structure
```
integrated-system/
├── apps/
│   ├── traffic-ai/          # AI Detection Backend & React Frontend
│   └── legacy-sumo/         # SUMO Simulation Backend
├── presentation/            # Project Pitch Deck (HTML/CSS)
├── scripts/                 # Utility scripts (OSM data, port handling)
├── run.sh                   # Main system orchestrator
└── README.md                # This file
```
