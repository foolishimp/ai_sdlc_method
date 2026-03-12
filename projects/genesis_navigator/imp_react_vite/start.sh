#!/usr/bin/env bash
# Start script for Genesis Navigator (backend + frontend)
# Usage: ./start.sh [--root-dir /path/to/scan]
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${1:-/Users/jim/src/apps/ai_sdlc_method/projects}"

# ── Shutdown existing processes ──────────────────────────────────────────────
echo "Stopping existing processes..."
pkill -f "genesis_nav.main" 2>/dev/null && echo "  backend stopped" || echo "  backend not running"
pkill -f "vite"             2>/dev/null && echo "  frontend stopped" || echo "  frontend not running"
pkill -f "esbuild"          2>/dev/null || true
sleep 1

# ── Backend ──────────────────────────────────────────────────────────────────
echo "Starting backend (port 8765, scanning $ROOT_DIR)..."
cd "$SCRIPT_DIR/backend"
python -c "
import genesis_nav.main as m
m._config['root_dir'] = '$ROOT_DIR'
import uvicorn
uvicorn.run(m.app, host='127.0.0.1', port=8765, log_level='info')
" &
BACKEND_PID=$!
echo "  backend PID=$BACKEND_PID"

# ── Frontend ─────────────────────────────────────────────────────────────────
echo "Starting frontend (Vite dev server)..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
echo "  frontend PID=$FRONTEND_PID"

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "Genesis Navigator running:"
echo "  Backend:  http://localhost:8765"
echo "  Frontend: http://localhost:5173"
echo "  Scanning: $ROOT_DIR"
echo ""
echo "Press Ctrl-C to stop both."

wait
