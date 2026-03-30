#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTEGRATION_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

get_free_port() {
  python3 - <<'PY'
import socket
s = socket.socket()
s.bind(("", 0))
port = s.getsockname()[1]
s.close()
print(port)
PY
}

PORT_TRAFFIC_AI="$(get_free_port)"
PORT_LEGACY="$(get_free_port)"
while [[ "$PORT_LEGACY" == "$PORT_TRAFFIC_AI" ]]; do
  PORT_LEGACY="$(get_free_port)"
done

TRAFFIC_AI_DIR="$INTEGRATION_DIR/apps/traffic-ai"
LEGACY_DIR="$INTEGRATION_DIR/apps/legacy-sumo"
FRONTEND_DIR="$TRAFFIC_AI_DIR/frontend"

echo ""
echo "Using random ports:"
echo "  Traffic AI backend : $PORT_TRAFFIC_AI"
echo "  Legacy trafik backend: $PORT_LEGACY"
echo ""

ENV_FILE="$FRONTEND_DIR/.env"
cat > "$ENV_FILE" <<EOF
VITE_API_BASE_URL=http://localhost:$PORT_TRAFFIC_AI
VITE_LEGACY_API_BASE_URL=http://localhost:$PORT_LEGACY
EOF

echo "Wrote Vite env: $ENV_FILE"

wait_url() {
  local url="$1"
  local deadline=$((SECONDS+90))
  while (( SECONDS < deadline )); do
    if python3 - "$url" <<'PY'
import sys, urllib.request
url = sys.argv[1]
try:
    urllib.request.urlopen(url, timeout=1).read()
except Exception:
    raise SystemExit(1)
raise SystemExit(0)
PY
    then
      return 0
    fi
    sleep 1
  done
  echo "Timed out waiting for: $url" >&2
  return 1
}

cleanup() {
  if [[ -n "${PID_TRAFFIC_AI:-}" ]]; then kill "$PID_TRAFFIC_AI" 2>/dev/null || true; fi
  if [[ -n "${PID_LEGACY:-}" ]]; then kill "$PID_LEGACY" 2>/dev/null || true; fi
}
trap cleanup EXIT

echo "Starting Traffic AI backend..."
(cd "$TRAFFIC_AI_DIR" && python3 -m uvicorn backend.main:app --host 0.0.0.0 --port "$PORT_TRAFFIC_AI" > "$INTEGRATION_DIR/logs/.traffic_ai_backend.log" 2>&1) &
PID_TRAFFIC_AI=$!

echo "Starting legacy trafik backend..."
(cd "$LEGACY_DIR" && bash run.sh --port "$PORT_LEGACY" > "$INTEGRATION_DIR/logs/.legacy_backend.log" 2>&1) &
PID_LEGACY=$!

echo "Waiting for backends..."
wait_url "http://localhost:${PORT_TRAFFIC_AI}/api/v1/health"
wait_url "http://localhost:${PORT_LEGACY}/"

echo ""
echo "Starting React frontend..."
echo "  Open: http://localhost:5173"
echo ""

cd "$FRONTEND_DIR"
if [[ ! -d "node_modules" ]]; then
  npm install
fi
npm run dev

