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

---

## 🎤 Presentation Guide

### Detailed 5-Minute Script (Use This On Stage)

Use this version when you get only 5 minutes and need to explain all core concepts clearly.

#### 0:00 - 0:35 | Opening and Vision

"Good [morning/afternoon], respected judges.  
We built a Smart Traffic Integrated System that combines AI traffic detection, live traffic simulation, and emergency route management in one unified dashboard.

Our goal is to reduce congestion and help emergency vehicles move faster through dynamic, data-driven traffic control."

---

#### 0:35 - 1:15 | What Problem We Solve

"Current city traffic systems are often reactive. Signals run fixed cycles, congestion is monitored manually, and emergency vehicles get stuck in regular traffic.

Our system addresses this in real time:
1) estimate traffic load,  
2) classify congestion severity,  
3) adapt signal timing, and  
4) compute a less-congested emergency corridor."

---

#### 1:15 - 2:00 | Architecture in Simple Language

"The product has three runtime parts:

- **React frontend dashboard** for operators (monitoring + control),
- **Traffic AI backend (FastAPI)** for detection, density, signal, and route APIs,
- **Legacy SUMO backend (FastAPI + TraCI)** for simulation-grade traffic behavior.

Both backends run together, and we start everything using one command:
`bash run.sh`.
Ports are assigned automatically to avoid conflicts."

---

#### 2:00 - 3:00 | Congestion Logic (Core Intelligence)

"Congestion is not based on raw count only.  
We use weighted load because each vehicle type occupies road space differently.

Weights used:
{{ ... }}

So severity is mathematically derived from capacity pressure, not manually tagged."

---

#### 3:00 - 3:45 | Dynamic Traffic Light Timing (How It Works)

"Signal timing adapts to directional load at each junction.

If North+South traffic is heavier, N-S green gets more time.  
If East+West is heavier, E-W green gets more time.
{{ ... }}
So this is dynamic control, not fixed-time-only operation.  
In emergency mode, relevant junction phases are forced to create a green corridor."

---

#### 3:45 - 4:25 | Route Planning + Emergency Logic

"For route planning, we use a graph-based shortest path approach with congestion-aware weights.

Algorithm: **Dijkstra (via NetworkX)**.  
Road segments are graph edges, intersections are nodes.  
{{ ... }}

Then corridor control highlights and prioritizes intersections along that route."

---

#### 4:25 - 4:50 | Camera Feed Handling

"Camera/video input supports:
- local video files
- RTSP stream
- HTTP stream
- webcam index (`camera:0`)

The selected node can be updated with real video detection while other nodes continue simulation independently.  
So we combine real input and city-wide simulation in one model."

---

#### 4:50 - 5:00 | Closing

"In short, this prototype behaves like a practical control-room product:  
it senses traffic, computes congestion, adapts signals, and creates emergency corridors in a unified interface.  
Thank you."

---

### Judge Question Bank

#### Product Clarity & Impact

**Q1. In one line, what does your product do?**  
It is an AI-driven traffic command platform that estimates live congestion, dynamically adjusts signal timing, and creates emergency green corridors to reduce response time.

**Q2. What exact problem are you solving?**  
{{ ... }}
**Q6. What measurable outcomes do you target?**  
Reduced average wait time, lower queue build-up, and improved emergency clearance time.

---

#### Technical Depth (Math + Algorithms)

**Q20. How do you calculate congestion?**  
By weighted load and capacity:

`weighted_load = cars*1.0 + motorcycles*0.5 + buses*2.5 + trucks*2.0`  
{{ ... }}
**Q23. Which route algorithm is used?**  
Dijkstra shortest path on a weighted graph (NetworkX), with congestion-aware cost adjustment.

**Q24. What is the routing objective?**  
`best_path = argmin(sum(edge_cost_i))`
.


{{ ... }}
