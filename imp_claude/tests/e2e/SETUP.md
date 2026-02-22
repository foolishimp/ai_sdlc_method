# E2E Convergence Tests — Setup Guide

Setup instructions for running the headless Claude e2e convergence tests on a new machine.

## Prerequisites

| Tool | Minimum Version | Check Command |
|------|----------------|---------------|
| Python | 3.12+ | `python3 --version` |
| pip | any | `pip3 --version` |
| git | 2.39+ | `git --version` |
| Node.js | 18+ | `node --version` |
| Claude Code CLI | 2.1+ | `claude --version` |

## Step 1: Python Dependencies

```bash
cd ai_sdlc_method
pip install -e ".[test]"
```

This installs:
- `pyyaml>=6.0` — YAML parsing for configs and feature vectors
- `pytest>=8.0` — Test runner
- `pytest-bdd>=7.0` — BDD tests (not used by e2e, but declared)

## Step 2: Claude Code CLI

Install and authenticate:

```bash
# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Authenticate (opens browser)
claude auth login
```

Verify authentication works:

```bash
claude -p --model haiku "Say ok"
```

## Step 3: MCP Server — claude-code-mcp

The e2e tests can run two ways:
- **Subprocess mode** (`claude -p`) — used by pytest, CI pipelines
- **MCP mode** (`claude_code` tool) — used interactively from within Claude Code

The MCP dependency is declared in `package.json`. Install it:

```bash
cd ai_sdlc_method
npm install
```

This installs `@steipete/claude-code-mcp` to `node_modules/`. The `.mcp.json` is already configured to use it via `npx`.

The `.mcp.json` in the repo:

```json
{
  "mcpServers": {
    "claude-code-runner": {
      "type": "stdio",
      "command": "npx",
      "args": ["@steipete/claude-code-mcp"]
    }
  }
}
```

Restart Claude Code after `npm install` to pick up the MCP server.

## Step 4: Verify Setup

```bash
# 1. Check all 502 non-e2e tests pass
pytest imp_claude/tests/ -v -m "not e2e"

# 2. Check e2e tests are collected (will skip if claude auth fails)
pytest imp_claude/tests/e2e/ --collect-only -m e2e
```

## Running E2E Tests

### Option A: pytest (subprocess mode)

```bash
# Must run OUTSIDE a Claude Code session, or strip CLAUDECODE env var
unset CLAUDECODE
pytest imp_claude/tests/e2e/ -v -m e2e -s
```

Cost: ~$2-5 per run (sonnet model, 4 edges).

The `-s` flag is important — it shows Claude's progress output.

### Option B: MCP (interactive mode)

From within a Claude Code session, ask Claude to:

1. Scaffold the project:
   ```
   Run the e2e scaffold to /tmp/e2e-temperature-converter
   ```

2. Drive convergence via MCP:
   ```
   Use claude_code tool with workFolder=/tmp/e2e-temperature-converter
   to run /aisdlc-start --auto --feature "REQ-F-CONV-001"
   ```

3. Run validators:
   ```
   Run the e2e validators against /tmp/e2e-temperature-converter
   ```

### Option C: Full suite

```bash
# Everything (502 unit/BDD/UAT + 22 e2e)
unset CLAUDECODE
pytest imp_claude/tests/ -v -s
```

## Environment Variables

| Variable | Purpose | Notes |
|----------|---------|-------|
| `CLAUDECODE` | Nesting guard — Claude CLI refuses to start if set | The test fixture strips it automatically. If running pytest from a terminal inside Claude Code, `unset CLAUDECODE` first. |
| `ANTHROPIC_MAX_BUDGET_USD` | Cost cap for headless runs | Set to `5.00` by the fixture. Override with higher value if convergence needs more iterations. |

## Cost Controls

The headless runner has two safeguards:

| Control | Default | Purpose |
|---------|---------|---------|
| `--max-budget-usd` | $5.00 | Hard cost cap per Claude invocation |
| Wall timeout | 1800s (30 min) | Watchdog thread kills process if exceeded |

Typical run: ~$2-3, ~3-8 minutes for 4 edges.

## What the Test Does

1. **Scaffolds** a temperature converter project in a temp dir:
   - `specification/INTENT.md` with 2 REQ keys (conversions + validation)
   - Full `.ai-workspace/` with graph configs, profiles, edge params
   - Feature vector `REQ-F-CONV-001` (status: pending)
   - All 10 methodology commands in `.claude/commands/`
   - Human evaluators overridden to agent-only

2. **Runs** headless Claude with `/aisdlc-start --auto --feature "REQ-F-CONV-001"`

3. **Validates** 22 checks across 4 categories:
   - Events (9): file exists, valid JSON, required types, timestamps, edge convergence
   - Feature vectors (5): converged status, trajectory metadata, REQ keys
   - Generated code (5): source files, test files, Implements/Validates tags, tests pass
   - Consistency (3): cross-artifact traceability, REQ key coverage

## Troubleshooting

**All 22 tests SKIPPED:**
→ Claude CLI not found or not authenticated. Check `claude --version` and `claude -p --model haiku "Say ok"`.

**Claude exits with code 1:**
→ Check `.e2e-meta/stderr.log` in the temp project dir. Common cause: nesting guard (`unset CLAUDECODE`).

**Wall timeout (1800s):**
→ Claude got stuck or the project is too complex. Check `.e2e-meta/stdout.log` for progress. The fixture tolerates partial convergence — if some edges converged, validation still runs.

**Tests pass but cost > $5:**
→ Increase budget: edit `max_budget_usd` in `conftest.py` `run_claude_headless()` default.

**"No Python code files found":**
→ Claude didn't generate code. Check stdout.log — it may have spent all turns on spec/design without reaching the code edge.
