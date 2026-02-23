# AI SDLC Method v2 — Quick Start

Get the **Asset Graph Model** methodology running in under a minute.

## Install

```bash
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/imp_claude/code/installers/gen-setup.py | python3 -
```

Restart Claude Code. Done.

## What Gets Created

```
your-project/
├── .claude/settings.json              # Plugin config (GitHub marketplace)
├── .ai-workspace/                     # v2 workspace
│   ├── events/events.jsonl            # Event log (source of truth)
│   ├── features/
│   │   ├── active/                    # Feature vectors in progress
│   │   └── completed/                 # Converged feature vectors
│   ├── context/
│   │   └── project_constraints.yml    # Constraint dimensions
│   ├── tasks/
│   │   ├── active/ACTIVE_TASKS.md     # Current tasks
│   │   └── finished/                  # Completed task docs
│   ├── agents/                        # Per-agent working state
│   └── spec/                          # Derived spec views
└── specification/
    └── INTENT.md                      # Intent template
```

## Verify

```bash
python gen-setup.py verify
```

Or inside Claude Code:

```
/gen-start
```

State detection will report `NEEDS_INTENT` or `UNINITIALISED` and guide you through setup.

## Try It

Just say:

```
/gen-start
```

The state machine detects where you are and routes you to the right action:

| State | What happens |
|-------|-------------|
| `UNINITIALISED` | Progressive init — 5 questions, then workspace created |
| `NEEDS_INTENT` | Prompts you to describe what you're building |
| `NO_FEATURES` | Creates your first feature vector from the intent |
| `IN_PROGRESS` | Selects next feature/edge, runs one iteration |
| `ALL_CONVERGED` | Suggests /gen-gaps, then /gen-release |

Two commands. That's it:
- **`/gen-start`** — "Go."
- **`/gen-status`** — "Where am I?"

## What You Get

**gen-methodology-v2** — The Asset Graph Model methodology:
- **1 universal iterate agent** — parameterised per edge, not hard-coded per stage
- **13 commands** — start, status, init, iterate, spawn, review, spec-review, escalate, zoom, trace, gaps, checkpoint, release
- **4 hooks** — protocol enforcement, stop checks, edge convergence observer, session health
- **Configurable graph** — YAML topology, edge params, profiles (full, standard, poc, spike, hotfix, minimal)
- **Event sourcing** — all state derived from `events.jsonl`, never stored
- **REQ key traceability** — from intent to telemetry

## The Asset Graph

```
Intent → Requirements → Design → Code ↔ Unit Tests → UAT → CI/CD → Running System → Telemetry
                                                                                        ↓
                                                                                      Intent (feedback)
```

One operation: `iterate(Asset, Context[], Evaluators) → Asset'`

Feature vectors (REQ keys) trace trajectories through the graph from intent to runtime.

## Installation Options

```bash
# Full setup (plugin + workspace) — DEFAULT
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/imp_claude/code/installers/gen-setup.py | python3 -

# Plugin only (no workspace)
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/imp_claude/code/installers/gen-setup.py | python3 - --no-workspace

# Preview changes without writing
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/imp_claude/code/installers/gen-setup.py | python3 - --dry-run

# Install to specific directory
python gen-setup.py --target /path/to/project
```

**Safe to re-run**: Existing files (events, feature vectors, tasks) are preserved.

## Manual Installation (Corporate / Air-Gapped)

### Option A: GitHub marketplace

Add to your project's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "aisdlc": {
      "source": {
        "source": "github",
        "repo": "foolishimp/ai_sdlc_method"
      }
    }
  },
  "enabledPlugins": {
    "gen-methodology-v2@aisdlc": true
  }
}
```

Then run `/gen-init` to create the workspace.

### Option B: Local plugin (fully offline)

```bash
git clone https://github.com/foolishimp/ai_sdlc_method.git /path/to/ai_sdlc_method
```

```json
{
  "extraKnownMarketplaces": {
    "aisdlc": {
      "source": {
        "source": "local",
        "path": "/path/to/ai_sdlc_method/imp_claude/code/.claude-plugin"
      }
    }
  },
  "enabledPlugins": {
    "gen-methodology-v2@aisdlc": true
  }
}
```

## Key Commands

| Command | Purpose |
|---------|---------|
| `/gen-start` | Detect state, select feature/edge, iterate |
| `/gen-status` | Show feature progress, Gantt, health |
| `/gen-gaps` | Traceability validation (3 layers) |
| `/gen-spawn` | Create feature/discovery/spike vectors |
| `/gen-review` | Human gate review |
| `/gen-spec-review` | Gradient check at spec boundaries |
| `/gen-escalate` | View/process escalation queue |
| `/gen-zoom` | Zoom into/out of graph edges |
| `/gen-release` | Version release with changelog |

## Next Steps

- **[README.md](README.md)** — Full documentation
- **[CLAUDE.md](CLAUDE.md)** — Project guide
- **[specification/](specification/)** — The formal system
- **[Example Projects](https://github.com/foolishimp/ai_sdlc_examples)** — Working examples
