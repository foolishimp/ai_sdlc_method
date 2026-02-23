# AI SDLC Methodology Plugin — v2.8 (Asset Graph Model — Project Genesis)

## What Changed from v1.x

| Aspect | v1.x | v2.8 |
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
code/
├── agents/
│   ├── gen-iterate.md          # THE one agent (universal iterate function)
│   ├── gen-dev-observer.md     # Dev observer agent
│   ├── gen-cicd-observer.md    # CI/CD observer agent
│   └── gen-ops-observer.md     # Ops observer agent
├── commands/
│   ├── gen-start.md            # State-driven routing (the "Go" verb)
│   ├── gen-init.md             # Scaffold workspace
│   ├── gen-iterate.md          # Invoke iterate() on an edge
│   ├── gen-status.md           # Feature vector progress (the "Where am I?" verb)
│   ├── gen-checkpoint.md       # Session snapshot + context hash
│   ├── gen-review.md           # Human evaluator review point
│   ├── gen-spec-review.md      # Spec-boundary review
│   ├── gen-escalate.md         # Escalation queue management
│   ├── gen-zoom.md             # Graph zoom (in/out)
│   ├── gen-trace.md            # REQ key trajectory through graph
│   ├── gen-gaps.md             # Test gap analysis
│   ├── gen-release.md          # Release with REQ coverage
│   └── gen-spawn.md            # Spawn feature/spike/hotfix vector
├── config/
│   ├── graph_topology.yml         # Default asset types + transitions
│   ├── evaluator_defaults.yml     # Human/Agent/Deterministic defaults
│   ├── intentengine_config.yml    # IntentEngine parameters
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
├── plugin.json                    # Plugin metadata (v2.8.0)
└── README.md                      # This file
```

## Quick Start (Two Commands)

```bash
# Just two verbs — Start figures out what to do:
/gen-start              # Detects state, initializes if needed, iterates
/gen-status             # Shows where you are across all features
```

Start handles everything: project init, feature creation, edge selection, iteration. It detects your project state and routes to the right action automatically.

## Advanced (9 Power-User Commands)

```bash
/gen-init               # Scaffold workspace manually
/gen-iterate --edge "intent→requirements" --feature "REQ-F-MYFEATURE-001"
/gen-iterate --edge "requirements→design" --feature "REQ-F-MYFEATURE-001"
/gen-iterate --edge "code↔unit_tests" --feature "REQ-F-MYFEATURE-001"
/gen-spawn --type feature   # Create a new feature vector
/gen-checkpoint         # Save session snapshot
/gen-review             # Human evaluator review point
/gen-trace              # Trace REQ keys across artifacts
/gen-gaps               # Check traceability coverage
/gen-release            # Create versioned release
```

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) — Canonical methodology
- [AISDLC_V2_DESIGN.md](../../../design/AISDLC_V2_DESIGN.md) — Implementation design
- [FEATURE_VECTORS.md](../../../../specification/FEATURE_VECTORS.md) — Feature decomposition
