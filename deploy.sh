#!/usr/bin/env bash
# deploy.sh — Genesis full-stack deployment
# Installs: Claude Code CLI + Genesis plugin + genesis_monitor
#
# Usage (from ai_sdlc_method root):
#   bash deploy.sh [--target-dir /path/to/project] [--skip-claude] [--skip-monitor]
#
# Idempotent — safe to re-run. Each step checks before installing.

set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RESET='\033[0m'
ok()   { echo -e "${GREEN}  ✓ $*${RESET}"; }
warn() { echo -e "${YELLOW}  ⚠ $*${RESET}"; }
fail() { echo -e "${RED}  ✗ $*${RESET}"; exit 1; }
step() { echo -e "\n${YELLOW}── $* ──${RESET}"; }

# ── Defaults ─────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${TARGET_DIR:-}"
SKIP_CLAUDE=false
SKIP_MONITOR=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --target-dir) TARGET_DIR="$2"; shift 2 ;;
    --skip-claude) SKIP_CLAUDE=true; shift ;;
    --skip-monitor) SKIP_MONITOR=true; shift ;;
    *) warn "Unknown option: $1"; shift ;;
  esac
done

echo ""
echo "  Genesis Full-Stack Deploy"
echo "  ========================="
echo "  Script root : $SCRIPT_DIR"
echo "  Target dir  : ${TARGET_DIR:-(will prompt genesis plugin installer)}"
echo ""

# ── Step 1: Prerequisites ─────────────────────────────────────────────────────
step "1. Prerequisites"

# Python 3.10+
if ! command -v python3 &>/dev/null; then
  fail "python3 not found. Install Python 3.10+ and retry."
fi
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
ok "Python $PYTHON_VERSION"

# Node.js 18+
if ! command -v node &>/dev/null; then
  fail "node not found. Install Node.js 18+ and retry."
fi
NODE_VERSION=$(node --version)
ok "Node.js $NODE_VERSION"

# npm
if ! command -v npm &>/dev/null; then
  fail "npm not found."
fi
ok "npm $(npm --version)"

# git
if ! command -v git &>/dev/null; then
  fail "git not found."
fi
ok "git $(git --version | awk '{print $3}')"

# ── Step 2: Claude Code CLI ───────────────────────────────────────────────────
step "2. Claude Code CLI"

if $SKIP_CLAUDE; then
  warn "Skipping Claude Code CLI install (--skip-claude)"
else
  if command -v claude &>/dev/null; then
    CLAUDE_VERSION=$(claude --version 2>/dev/null || echo "unknown")
    ok "Claude Code already installed: $CLAUDE_VERSION"
  else
    echo "  Installing @anthropic-ai/claude-code globally..."
    npm install -g @anthropic-ai/claude-code
    ok "Claude Code installed: $(claude --version)"
  fi

  # Verify authentication (non-blocking)
  if claude -p --model haiku "echo ok" &>/dev/null 2>&1; then
    ok "Claude CLI authenticated"
  else
    warn "Claude CLI not authenticated — run: claude auth login"
    warn "The genesis plugin and genesis_monitor will still be installed."
  fi
fi

# ── Step 3: MCP server (claude-code-mcp) ─────────────────────────────────────
step "3. MCP server (claude-code-runner)"

MCP_JSON="$SCRIPT_DIR/.mcp.json"
if [[ -f "$MCP_JSON" ]]; then
  ok ".mcp.json present at $SCRIPT_DIR"
else
  warn ".mcp.json not found — creating minimal config"
  cat > "$MCP_JSON" << 'EOF'
{
  "mcpServers": {
    "claude-code-runner": {
      "type": "stdio",
      "command": "npx",
      "args": ["@steipete/claude-code-mcp"]
    }
  }
}
EOF
  ok ".mcp.json written"
fi

PACKAGE_JSON="$SCRIPT_DIR/package.json"
if [[ -f "$PACKAGE_JSON" ]]; then
  echo "  Running npm install for MCP dependencies..."
  (cd "$SCRIPT_DIR" && npm install --silent)
  ok "npm install done"
else
  warn "No package.json found — skipping npm install"
fi

# ── Step 4: Genesis plugin ────────────────────────────────────────────────────
step "4. Genesis plugin"

GEN_SETUP="$SCRIPT_DIR/imp_claude/code/installers/gen-setup.py"
if [[ ! -f "$GEN_SETUP" ]]; then
  fail "Genesis installer not found at $GEN_SETUP"
fi

if [[ -n "$TARGET_DIR" ]]; then
  echo "  Installing genesis plugin into $TARGET_DIR ..."
  python3 "$GEN_SETUP" "$TARGET_DIR"
  ok "Genesis plugin installed to $TARGET_DIR"
else
  echo "  Running genesis installer (interactive — will ask for target directory)..."
  python3 "$GEN_SETUP"
fi

# ── Step 5: Python test dependencies ─────────────────────────────────────────
step "5. Python dependencies (genesis + tests)"

PYPROJECT="$SCRIPT_DIR/pyproject.toml"
if [[ -f "$PYPROJECT" ]]; then
  echo "  Installing ai_sdlc_method[test] in editable mode..."
  pip install -e "$SCRIPT_DIR[test]" --quiet
  ok "Python dependencies installed"
else
  warn "No pyproject.toml at root — skipping python dependency install"
fi

# ── Step 6: genesis_monitor ───────────────────────────────────────────────────
step "6. genesis_monitor"

if $SKIP_MONITOR; then
  warn "Skipping genesis_monitor install (--skip-monitor)"
else
  MONITOR_DIR="$SCRIPT_DIR/projects/genesis_monitor/imp_fastapi"
  if [[ ! -d "$MONITOR_DIR" ]]; then
    warn "genesis_monitor not found at $MONITOR_DIR — skipping"
  else
    MONITOR_PYPROJECT="$MONITOR_DIR/pyproject.toml"
    if [[ -f "$MONITOR_PYPROJECT" ]]; then
      echo "  Installing genesis_monitor in editable mode..."
      pip install -e "$MONITOR_DIR[dev]" --quiet
      ok "genesis_monitor installed"

      # Verify the CLI entry point
      if command -v genesis-monitor &>/dev/null; then
        ok "genesis-monitor CLI available: $(genesis-monitor --version 2>/dev/null || echo 'installed')"
      else
        warn "genesis-monitor CLI not found on PATH after install — check PATH"
      fi
    else
      warn "No pyproject.toml in $MONITOR_DIR — skipping genesis_monitor install"
    fi
  fi
fi

# ── Step 7: Verify ───────────────────────────────────────────────────────────
step "7. Verify"

echo ""
echo "  Component check:"

# Genesis plugin config
GRAPH_TOPOLOGY="$SCRIPT_DIR/imp_claude/code/.claude-plugin/plugins/genesis/config/graph_topology.yml"
[[ -f "$GRAPH_TOPOLOGY" ]] && ok "Genesis graph topology present" || warn "Genesis graph topology not found"

# genesis_monitor
if command -v genesis-monitor &>/dev/null; then
  ok "genesis-monitor on PATH"
else
  warn "genesis-monitor not on PATH — run pip install -e projects/genesis_monitor/imp_fastapi[dev]"
fi

# Claude CLI
if ! $SKIP_CLAUDE && command -v claude &>/dev/null; then
  ok "claude on PATH"
elif $SKIP_CLAUDE; then
  warn "claude check skipped"
else
  warn "claude not on PATH"
fi

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "  ══════════════════════════════════════════════"
echo "  Deploy complete."
echo ""
echo "  Quick start:"
echo "    # Watch e2e runs live:"
echo "    genesis-monitor --watch-dir imp_claude/tests/e2e/runs/ --port 8000 &"
echo ""
echo "    # Run e2e tests (produces a run that monitor can view):"
echo "    unset CLAUDECODE"
echo "    pytest imp_claude/tests/e2e/ -v -m e2e -s"
echo ""
echo "    # View the run:"
echo "    open http://localhost:8000"
echo "  ══════════════════════════════════════════════"
echo ""
