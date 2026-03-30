"""
config.py
=========
Central configuration for the Traffic AI backend.

All values can be overridden via environment variables.
"""

import os


# ─── Server ──────────────────────────────────────────────────────────────────
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# ─── CORS (comma-separated origins, or "*" for dev) ─────────────────────────
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# ─── Model paths ─────────────────────────────────────────────────────────────
YOLO_MODEL_PATH      = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")
EMERGENCY_MODEL_PATH = os.getenv("EMERGENCY_MODEL_PATH", "yolov8n.pt")

# ─── Traffic engine defaults ─────────────────────────────────────────────────
DEFAULT_LANE_CAPACITY = int(os.getenv("LANE_CAPACITY", 20))
CYCLE_TIME            = int(os.getenv("CYCLE_TIME", 120))
MIN_GREEN_TIME        = int(os.getenv("MIN_GREEN_TIME", 10))

# ─── Upload directory ────────────────────────────────────────────────────────
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "data/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
