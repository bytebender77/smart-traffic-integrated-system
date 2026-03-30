#!/usr/bin/env bash
# ================================================================
# AI Traffic Flow Optimizer — One-command launcher
# Usage: bash run.sh [--gui]
# ================================================================
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   🚦  AI Traffic Flow Optimizer — SUMO Simulation    ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Optional CLI/env overrides
# Usage:
#   PORT=8001 bash run.sh
#   bash run.sh --port 8001
PORT="${PORT:-8000}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)
      PORT="$2"
      shift 2
      ;;
    *)
      shift 1
      ;;
  esac
done

# ── Check SUMO ──
if ! command -v sumo &>/dev/null; then
  echo "❌ SUMO not found. Install via: brew install sumo"
  exit 1
fi
echo "✅ SUMO: $(sumo --version 2>&1 | head -1)"

# ── Set SUMO_HOME ──
SUMO_HOME="$(brew --prefix sumo 2>/dev/null)/share/sumo"
if [ ! -d "$SUMO_HOME" ]; then
  SUMO_HOME="/opt/homebrew/share/sumo"
fi
export SUMO_HOME
echo "✅ SUMO_HOME: $SUMO_HOME"

# ── Install Python deps ──
echo ""
echo "📦 Installing Python dependencies..."
pip3 install -q fastapi uvicorn traci sumolib
# ── Kill any old backend on the same port (avoid killing the other backend) ──
if command -v lsof &>/dev/null; then
  pids="$(lsof -t -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    echo "🛑 Stopping existing process(es) on port $PORT..."
    kill $pids 2>/dev/null || true
    sleep 1
  fi
fi

# ── Launch FastAPI backend (which auto-starts SUMO in background) ──
echo ""
echo "🚀 Starting FastAPI backend + SUMO simulation..."
echo "   API: http://localhost:${PORT}"
echo "   Docs: http://localhost:${PORT}/docs"
echo ""
echo "📊 Open dashboard in browser:"
echo "   file://${PROJECT_DIR}/frontend/index.html"
echo ""
echo "─────────────────────────────────────────────────────────"
echo "  Simulation timeline:"
echo "   T=0–50s  : Normal traffic (N=12 veh, S=6, E=4, W=5)"
echo "   T=50s    : 🚑 AMBULANCE 1 spawns (West → East)"
echo "   T=80s    : 🚑 AMBULANCE 2 spawns (South → North)"
echo "   AI adaptively adjusts green times every 10 sim-seconds"
echo "─────────────────────────────────────────────────────────"
echo ""
echo "Press Ctrl+C to stop."
echo ""

cd "$PROJECT_DIR"
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port "$PORT"
