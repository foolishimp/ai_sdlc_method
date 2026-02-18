# AI SDLC Methodology Plugin — v2.1 (Asset Graph Model)

## What Changed from v1.x

| Aspect | v1.x | v2.1 |
|--------|------|------|
| Model | 7-stage pipeline | Asset graph with typed transitions |
| Agents | 7 (one per stage) | 1 (universal iterate agent) |
| Skills | 11 consolidated | Edge parameterisations (YAML) |
| Topology | Hard-coded in agents | Configurable YAML (`graph_topology.yml`) |
| Iteration | Per-stage feedback loops | Universal `iterate(Asset, Context[], Evaluators)` |
| Commands | 9 | 8 (different operations) |
| Reproducibility | Not addressed | Content-addressable context manifest |

## Structure

```
v2/
├── agents/
│   └── aisdlc-iterate.md          # THE one agent (universal iterate function)
├── commands/
│   ├── aisdlc-init.md             # Scaffold workspace
│   ├── aisdlc-iterate.md          # Invoke iterate() on an edge
│   ├── aisdlc-status.md           # Feature vector progress
│   ├── aisdlc-checkpoint.md       # Session snapshot + context hash
│   ├── aisdlc-review.md           # Human evaluator review point
│   ├── aisdlc-trace.md            # REQ key trajectory through graph
│   ├── aisdlc-gaps.md             # Test gap analysis
│   └── aisdlc-release.md          # Release with REQ coverage
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
├── plugin.json                    # Plugin metadata (v2.1.0)
└── README.md                      # This file
```

## Quick Start

```bash
# 1. Initialize a project
/aisdlc-init

# 2. Edit your intent
#    docs/requirements/INTENT.md

# 3. Generate requirements
/aisdlc-iterate --edge "intent→requirements" --feature "REQ-F-MYFEATURE-001"

# 4. Generate design
/aisdlc-iterate --edge "requirements→design" --feature "REQ-F-MYFEATURE-001"

# 5. Implement with TDD
/aisdlc-iterate --edge "code↔unit_tests" --feature "REQ-F-MYFEATURE-001"

# 6. Check progress
/aisdlc-status

# 7. Check coverage gaps
/aisdlc-gaps
```

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../docs/requirements/AI_SDLC_ASSET_GRAPH_MODEL.md) — Canonical methodology
- [AISDLC_V2_DESIGN.md](../../../docs/design/claude_aisdlc/AISDLC_V2_DESIGN.md) — Implementation design
- [FEATURE_VECTORS.md](../../../docs/requirements/FEATURE_VECTORS.md) — Feature decomposition
