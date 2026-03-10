# AI SDLC Methodology Plugin — v2.8 (Asset Graph Model — Project Genesis)

## What Changed from v1.x

| Aspect | v1.x | v2.8 |
|--------|------|------|
| Model | 7-stage pipeline | Asset graph with typed transitions |
| Agents | 7 (one per stage) | 4 (1 iterate + 3 observers) |
| Skills | 11 consolidated | Edge parameterisations (YAML) |
| Topology | Hard-coded in agents | Configurable YAML (`graph_topology.yml`) |
| Iteration | Per-stage feedback loops | Universal `iterate(Asset, Context[], Evaluators)` |
| Commands | 9 | 18 (2 primary + 16 advanced) |
| Hooks | ad hoc | 4 formal hooks (iterate/start/stop/post-event) |
| UX | Learn 9 commands | Two verbs: Start (`/gen-start`) + Status (`/gen-status`) |
| Reproducibility | Not addressed | Content-addressable context manifest |

## Structure

```text
code/
├── agents/
│   ├── gen-iterate.md
│   ├── gen-dev-observer.md
│   ├── gen-cicd-observer.md
│   └── gen-ops-observer.md
├── commands/
│   ├── gen-start.md
│   ├── gen-status.md
│   ├── gen-init.md
│   ├── gen-iterate.md
│   ├── gen-spawn.md
│   ├── gen-checkpoint.md
│   ├── gen-review.md
│   ├── gen-spec-review.md
│   ├── gen-escalate.md
│   ├── gen-consensus-open.md
│   ├── gen-comment.md
│   ├── gen-dispose.md
│   ├── gen-vote.md
│   ├── gen-consensus-recover.md
│   ├── gen-zoom.md
│   ├── gen-trace.md
│   ├── gen-gaps.md
│   └── gen-release.md
├── hooks/
│   ├── hooks.json
│   ├── on-iterate-start.sh
│   ├── on-stop-check-protocol.sh
│   ├── on-edge-converged.sh
│   └── on-session-start.sh
├── config/
│   ├── graph_topology.yml
│   ├── evaluator_defaults.yml
│   ├── intentengine_config.yml
│   ├── affect_triage.yml
│   ├── sensory_monitors.yml
│   ├── agent_roles.yml
│   ├── feature_vector_template.yml
│   ├── project_constraints_template.yml
│   ├── edge_params/
│   └── profiles/
├── plugin.json
└── README.md
```

## Quick Start

```bash
/gen-start
/gen-status
```

## Advanced Commands

```bash
/gen-init
/gen-iterate --edge "intent→requirements" --feature "REQ-F-MYFEATURE-001"
/gen-spawn --type feature
/gen-checkpoint
/gen-review
/gen-spec-review --feature "REQ-F-*" --edge "requirements→design"
/gen-escalate
/gen-consensus-open --artifact specification/adrs/ADR-001.md --roster gen-dev-observer,human:alice
/gen-comment --review-id REVIEW-adr-001-1 --content "Need clearer recovery semantics"
/gen-dispose --review-id REVIEW-adr-001-1 --comment-id COMMENT-001 --disposition resolved --rationale "Added the missing recovery note"
/gen-vote --review-id REVIEW-adr-001-1 --verdict approve --participant alice
/gen-consensus-recover --review-id REVIEW-adr-001-1 --path re_open
/gen-zoom --edge "design→code"
/gen-trace
/gen-gaps
/gen-release
```

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md)
- [AISDLC_V2_DESIGN.md](../design/AISDLC_V2_DESIGN.md)
- [FEATURE_VECTORS.md](../../specification/FEATURE_VECTORS.md)
