"""
main.py
=======
FastAPI application entry point for the Traffic AI Optimizer backend.

Integrates:
  • vision.vehicle_detection
  • vision.emergency_vehicle_detection
  • traffic_engine.density_calculator
  • traffic_engine.signal_optimizer
  • traffic_engine.emergency_route

Start the server:
    uvicorn backend.main:app --reload

API documentation:
    http://localhost:8000/docs     (Swagger UI)
    http://localhost:8000/redoc    (ReDoc)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import CORS_ORIGINS
from backend.api_routes import router
from utils.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# APP INITIALISATION
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="🚦 Traffic AI Optimizer",
    description=(
        "AI-powered smart city traffic signal optimisation and emergency "
        "green corridor system.\n\n"
        "**Modules**\n"
        "- Vehicle Detection (YOLOv8)\n"
        "- Traffic Density Calculator\n"
        "- Signal Optimizer\n"
        "- Emergency Vehicle Detection\n"
        "- Green Corridor Engine"
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ─── CORS ────────────────────────────────────────────────────────────────────
# Allows the dashboard (React / Streamlit) to call the API from a
# different origin during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Mount all API routes ────────────────────────────────────────────────────
app.include_router(router, prefix="/api/v1", tags=["Traffic AI"])


# ─── Root redirect ───────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
def root():
    """Root endpoint — redirects to docs."""
    return {
        "message": "🚦 Traffic AI Optimizer is running",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "endpoints": {
            "traffic_detect":  "POST /api/v1/traffic/detect",
            "traffic_density": "POST /api/v1/traffic/density",
            "traffic_signals": "POST /api/v1/traffic/signals",
            "emergency_check": "POST /api/v1/emergency/check",
            "emergency_route": "POST /api/v1/emergency/route",
            "system_status":   "GET  /api/v1/system/status",
        },
    }


# ─── Startup / Shutdown events ───────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    logger.info("🚀 Traffic AI Backend v2.0.0 started")
    logger.info("📖 Swagger docs → http://localhost:8000/docs")
    logger.info("🏙️  City graph loaded with intersections ready")

    # Auto-start traffic simulation so the dashboard has data immediately
    from backend.traffic_simulator import start_simulation
    result = start_simulation(interval=5.0)
    logger.info(f"🎲 Traffic simulator auto-started: {result}")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Traffic AI Backend shutting down")
