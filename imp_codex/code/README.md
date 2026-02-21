# AI SDLC Methodology Plugin — Codex Binding (Asset Graph Model — Project Genesis)

## What Changed from v1.x

| Aspect | v1.x | v2.7 |
|--------|------|------|
| Model | 7-stage pipeline | Asset graph with typed transitions |
| Agents | 7 (one per stage) | 1 (universal iterate agent) |
| Skills | 11 consolidated | Edge parameterisations (YAML) |
| Topology | Hard-coded in agents | Configurable YAML (`graph_topology.yml`) |
| Iteration | Per-stage feedback loops | Universal `iterate(Asset, Context[], Evaluators)` |
| Commands | 9 | 10 (2 primary + 8 advanced) |
| UX | Learn 9 commands | Two verbs: Start ("Go.") + Status ("Where am I?") |
| Reproducibility | Not addressed | Content-addressable context manifest |

## Structure

```
v2/
├── agents/
│   └── aisdlc-iterate.md          # THE one agent (universal iterate function)
├── commands/
│   ├── aisdlc-start.md            # State-driven routing (the "Go" verb)
│   ├── aisdlc-init.md             # Scaffold workspace
│   ├── aisdlc-iterate.md          # Invoke iterate() on an edge
│   ├── aisdlc-status.md           # Feature vector progress (the "Where am I?" verb)
│   ├── aisdlc-checkpoint.md       # Session snapshot + context hash
│   ├── aisdlc-review.md           # Human evaluator review point
│   ├── aisdlc-trace.md            # REQ key trajectory through graph
│   ├── aisdlc-gaps.md             # Test gap analysis
│   ├── aisdlc-release.md          # Release with REQ coverage
│   └── aisdlc-spawn.md            # Spawn feature/spike/hotfix vector
├── config/
│   ├── graph_topology.yml         # Default asset types + transitions
│   ├── evaluator_defaults.yml     # Human/Agent/Deterministic defaults
│   └── edge_params/               # Per-edge parameterisations
│       ├── tdd.yml                # Code ↔ Tests (TDD co-evolution)
│       ├── bdd.yml                # Design → UAT Tests (BDD)
│       ├── adr.yml                # Requirements → Design (ADR generation)
│       ├── code_tagging.yml       # Cross-cutting REQ key tagging
│       ├── intent_requirements.yml
│       ├── requirements_design.yml
│       ├── design_code.yml
│       ├── design_tests.yml
│       └── feedback_loop.yml
├── plugin.json                    # Plugin metadata (v2.7.0)
└── README.md                      # This file
```

## Quick Start (Two Commands)

```bash
# Just two verbs — Start figures out what to do:
/aisdlc-start              # Detects state, initializes if needed, iterates
/aisdlc-status             # Shows where you are across all features
```

Start handles everything: project init, feature creation, edge selection, iteration. It detects your project state and routes to the right action automatically.

## Advanced (9 Power-User Commands)

```bash
/aisdlc-init               # Scaffold workspace manually
/aisdlc-iterate --edge "intent→requirements" --feature "REQ-F-MYFEATURE-001"
/aisdlc-iterate --edge "requirements→design" --feature "REQ-F-MYFEATURE-001"
/aisdlc-iterate --edge "code↔unit_tests" --feature "REQ-F-MYFEATURE-001"
/aisdlc-spawn --type feature   # Create a new feature vector
/aisdlc-checkpoint         # Save session snapshot
/aisdlc-review             # Human evaluator review point
/aisdlc-trace              # Trace REQ keys across artifacts
/aisdlc-gaps               # Check traceability coverage
/aisdlc-release            # Create versioned release
```

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) — Canonical methodology
- [CODEX_GENESIS_DESIGN.md](../design/CODEX_GENESIS_DESIGN.md) — Codex implementation design
- [FEATURE_VECTORS.md](../../specification/FEATURE_VECTORS.md) — Feature decomposition
