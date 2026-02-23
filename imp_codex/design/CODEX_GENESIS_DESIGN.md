# AI SDLC - Codex Genesis Implementation Design (v1.1)

**Version**: 1.1.0  
**Date**: 2026-02-23  
**Derived From**: [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) (v2.8.0)  
**Reference Implementation**: [AISDLC_V2_DESIGN.md](../../imp_claude/design/AISDLC_V2_DESIGN.md)  
**Platform**: Codex (tool-calling coding agent runtime)

---

## Design Intent

This document defines the |design> asset for a Codex-specific Genesis binding. It is a sibling implementation to Claude and Gemini bindings, with explicit feature alignment to Claude as the reference baseline.

Primary objective: preserve methodology semantics and feature coverage while mapping execution to Codex-native primitives (tool calls, shell orchestration, patch application, explicit human review turns).

Core objectives:

1. **Reference parity**: Maintain feature-level compatibility with Claude v2.8 design (all 11 feature vectors).
2. **Native binding**: Map iterate/evaluator/context/tooling to Codex primitives without changing the Asset Graph model.
3. **Spec-first control**: Keep disambiguation at intent/spec/design layers; use code/runtime observability as secondary unblock and validation controls.

---

## 1. Architecture Overview

### 1.1 Three Layers (Codex Mapping)

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        USER (Developer)                            │
│               Natural language requests / /gen command intents       │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION LAYER                           │
│   Codex orchestration prompt + state machine routing               │
│   (init / start / iterate / review / status / restore / trace)     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         TOOLING LAYER                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Asset Graph Engine                        │   │
│  │  - graph_topology.yml + edge params                         │   │
│  │  - universal iterate orchestration                          │   │
│  │  - evaluator execution (human/agent/deterministic)          │   │
│  │  - event emission + derived projections                     │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Codex primitives used:                                             │
│  - exec_command (deterministic operations, tests, scripts)          │
│  - apply_patch (structured file mutation)                           │
│  - multi_tool_use.parallel (parallel reads/checks)                  │
│  - conversational review turn (human evaluator boundary)            │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         WORKSPACE LAYER                            │
│  .ai-workspace/                                                     │
│  ├── specification/     Shared tech-agnostic specification (REQ)    │
│  ├── events/            Shared immutable event log (source of truth)│
│  ├── features/          Shared feature vector tracking              │
│  ├── codex/            Design-specific tenant                      │
│  │   ├── standards/     Codex-specific conventions                  │
│  │   ├── adrs/          Codex design decisions                      │
│  │   ├── data_models/   Codex runtime schemas                       │
│  │   ├── context_manifest.yml                                       │
│  │   └── project_constraints.yml                                    │
│  ├── tasks/             Active/completed tasks (derived views)      │
│  └── snapshots/         Immutable checkpoints                        │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Claude-to-Codex Binding Map

| Concept | Claude Reference | Codex Genesis |
| :--- | :--- | :--- |
| Iterate engine | `gen-iterate.md` universal agent | Universal orchestration routine that reads edge configs and drives tool calls |
| Commands | `/gen-*` slash commands | `/gen-*` workflows invoked from Codex sessions (natural language routed to command specs) |
| Context | `.ai-workspace/context/*` | Same file-based context model; Codex reads workspace directly |
| Deterministic evaluators | Tests/linters/hooks from commands | Same evaluators via shell tools and scripts |
| Human review | `/gen-review` command | Explicit review turn before promote/converge on human-required edges |
| Event log | `.ai-workspace/events/events.jsonl` | Same append-only contract, shared across implementations |

### 1.3 Universal Iterate Orchestration (Codex)

Codex Genesis keeps the Claude invariant: **one iterate operation, parameterized per edge**.

Iterate flow:

1. Resolve current edge + feature vector (`graph_topology.yml`, `edges/*.yml`).
2. Load current asset and effective `Context[]` (including tenant-specific overlays).
3. Construct candidate artifact(s) via Codex file operations.
4. Execute evaluator chain:
   - Agent evaluator (coherence/gap detection),
   - Deterministic checks (tests/lint/validators),
   - Human evaluator where required.
5. Emit mandatory side effects:
   - `iteration_completed`,
   - feature vector state update,
   - `STATUS.md` / task projection updates,
   - process gaps and signal classification.
6. Promote asset or iterate again until convergence policy is satisfied.

---

## 2. Component Design

### 2.1 Asset Graph Engine (REQ-F-ENGINE-001)

**Implements**: REQ-GRAPH-001, REQ-GRAPH-002, REQ-GRAPH-003, REQ-ITER-001, REQ-ITER-002

Codex Genesis uses the same topology and edge parameterization files as Claude to preserve methodology behavior:

- `.ai-workspace/graph/graph_topology.yml`
- `.ai-workspace/graph/evaluator_defaults.yml`
- `.ai-workspace/graph/edges/*.yml`
- `.ai-workspace/profiles/*.yml`

No edge semantics are hard-coded into the orchestrator.

### 2.2 Evaluator Framework (REQ-F-EVAL-001)

**Implements**: REQ-EVAL-001, REQ-EVAL-002, REQ-EVAL-003

Evaluator types are unchanged:

- **Agent**: Codex reasoning pass using edge checklist and context.
- **Deterministic**: shell commands, test suites, schema checks, static analysis.
- **Human**: explicit approval decision before promote/converge where configured.

Convergence remains edge-driven (`human_required`, `max_iterations`, thresholds).

### 2.3 Context Management and Reproducibility (REQ-F-CTX-001)

**Implements**: REQ-CTX-001, REQ-CTX-002, REQ-INTENT-004

- File-based context remains canonical for deterministic replay.
- `context_manifest.yml` hash is checked before iteration.
- Stale context warning when source files are newer than manifest.
- Tenant overlays are resolved in `.ai-workspace/codex/` while preserving shared `specification/`.

### 2.4 Feature Vector Traceability (REQ-F-TRACE-001)

**Implements**: REQ-INTENT-001, REQ-INTENT-002, REQ-FEAT-001, REQ-FEAT-002, REQ-FEAT-003

Codex Genesis preserves REQ-key lineage:

- Feature vectors in `.ai-workspace/features/active|completed/*.yml`
- Structured intent docs under `.ai-workspace/intents/INT-*.yml`
- Code/test tags:
  - `Implements: REQ-*`
  - `Validates: REQ-*`
- `/gen-trace` projection generated from event log + feature files

### 2.5 Edge Parameterisations (REQ-F-EDGE-001)

**Implements**: REQ-EDGE-001, REQ-EDGE-002, REQ-EDGE-003, REQ-EDGE-004

Claude and Codex share parameterized edge patterns:

- TDD co-evolution (`code <-> unit_tests`)
- BDD generation (`design -> test_cases/uat_tests`)
- ADR generation (`requirements -> design`)
- Code tagging and REQ-reference validation

Codex-specific change is execution surface only (tool calls), not edge semantics.

### 2.6 Developer Tooling Surface (REQ-F-TOOL-001)

**Implements**: REQ-TOOL-001 through REQ-TOOL-010

| Operation | Codex Genesis Entry | Purpose |
| :--- | :--- | :--- |
| Initialize workspace | `/gen-init` | Scaffold graph/context/features/events |
| Route next step | `/gen-start` | State-driven edge and feature selection |
| Iterate edge | `/gen-iterate --edge --feature` | Execute universal iterate |
| Review artifact | `/gen-review` | Human evaluator boundary |
| Spec-boundary review | `/gen-spec-review` | Gradient check for spec transitions |
| Escalation queue | `/gen-escalate` | Process queued supervisory signals |
| Graph zoom | `/gen-zoom` | Focused edge-level visibility |
| Status | `/gen-status [--feature] [--health]` | Project and feature observability |
| Checkpoint | `/gen-checkpoint` | Immutable snapshot |
| Trace | `/gen-trace --req` | REQ trajectory reconstruction |
| Gaps | `/gen-gaps` | Coverage and process gap analysis |
| Release | `/gen-release` | REQ coverage release manifest |
| Spawn | `/gen-spawn` | Create feature/discovery/spike/hotfix vectors |

---

## 3. Feature Alignment With Claude Reference

This section is the explicit parity contract.

| Feature Vector | Claude Reference Section | Codex Genesis Section | Alignment |
| :--- | :--- | :--- | :--- |
| REQ-F-ENGINE-001 | Claude §2.1 | Codex §2.1 | Aligned |
| REQ-F-EVAL-001 | Claude §2.2 | Codex §2.2 | Aligned |
| REQ-F-CTX-001 | Claude §2.3 | Codex §2.3 | Aligned |
| REQ-F-TRACE-001 | Claude §2.4 | Codex §2.4 | Aligned |
| REQ-F-EDGE-001 | Claude §2.5 | Codex §2.5 | Aligned |
| REQ-F-TOOL-001 | Claude §2.6 | Codex §2.6 | Aligned |
| REQ-F-LIFE-001 | Claude §3 | Codex §4 | Aligned |
| REQ-F-SENSE-001 | Claude §1.8 | Codex §4.2 | Aligned (phased) |
| REQ-F-UX-001 | Claude §1.9 | Codex §4.3 | Aligned |
| REQ-F-SUPV-001 | Claude §1.9, §2.6 | Codex §2.6, §4.3 | Aligned |
| REQ-F-COORD-001 | Claude §1.10 | Codex §4.4 + ADR-013 | Aligned |

**11/11 feature vectors aligned with Claude reference implementation.**

---

## 4. Lifecycle, Sensing, and UX

### 4.1 Lifecycle Closure

Phase model mirrors Claude:

- **Phase 1**: Development-time consciousness loop fully operational (`intent_raised`, `spec_modified`, protocol side effects).
- **Phase 2**: Production integration (CI/CD, runtime telemetry ingestion, ecosystem intent automation).

### 4.2 Sensory Service Strategy

Codex sessions are interactive and task-scoped. Sensory monitoring is implemented with two modes:

1. **Foreground sensing** on `/gen-status --health` and `/gen-start`.
2. **Optional daemonized watcher** launched via shell tooling for teams that need continuous sensing.

Both modes emit the same event types into `events.jsonl` and preserve the same review boundary: sensors create proposals, humans approve intent creation.

### 4.3 Artifact Write Observation (ADR-CG-006)

The PostToolUse hook on `Write|Edit` provides invariant-level observability independent of the iterate protocol:

| Event | Trigger | Data | Purpose |
|-------|---------|------|---------|
| `artifact_modified` | Every Write/Edit to artifact directory | file_path, asset_type, tool | Real-time progress, audit trail |
| `edge_started` | First write to new asset type per session | edge (inferred), trigger: `artifact_write_detected` | Activity detection |

This sits at the invariant-observation end of the observability sliding scale (§7.7.5). Path-to-asset mapping:

| Directory pattern | Asset type |
|-------------------|-----------|
| `specification/`, `spec/` | requirements |
| `design/`, `design/adrs/` | design |
| `tests/e2e/`, `tests/uat/` | uat_tests |
| `tests/*test*` | unit_tests |
| `code/`, `src/`, `lib/` | code |

Exclusions: `.ai-workspace/`, `.git/`, `node_modules/`, infrastructure files (CLAUDE.md, .gitignore, pyproject.toml, etc.)

Multi-tenant: `imp_<name>/` prefix stripped before mapping.

### 4.4 Two-Command UX Layer

Codex Genesis preserves the UX pattern:

- `/gen-start`: routing layer.
- `/gen-status`: observability layer.

Progressive disclosure is retained: newcomers use start/status, power users invoke direct operations.

---

## 5. Implementation Baseline

### Completed Baseline

1. Codex plugin surface aligned to v2.8 reference: 13 commands, observer agents, 4-hook workflow, and full config set.
2. Iterate protocol, event schema, and derived projections aligned with central spec and Claude reference semantics.
3. Codex test suite aligned to current shared specification and passing.

---

## 6. ADR Set (Codex Genesis)

- [ADR-CG-001-codex-runtime-as-platform.md](adrs/ADR-CG-001-codex-runtime-as-platform.md) - platform binding decision
- [ADR-CG-002-universal-iterate-orchestrator.md](adrs/ADR-CG-002-universal-iterate-orchestrator.md) - universal iterate orchestration in Codex
- [ADR-CG-003-review-boundary-and-disambiguation.md](adrs/ADR-CG-003-review-boundary-and-disambiguation.md) - spec-first disambiguation and human gating
- [ADR-CG-004-event-replay-and-recovery.md](adrs/ADR-CG-004-event-replay-and-recovery.md) - replay-based reconstruction and checkpoint strategy
- [ADR-CG-005-sensory-operating-modes.md](adrs/ADR-CG-005-sensory-operating-modes.md) - foreground/background sensing with shared event contracts
- [ADR-CG-006-artifact-write-observation.md](adrs/ADR-CG-006-artifact-write-observation.md) - PostToolUse hook for artifact write observability

---

## References

- [AISDLC_V2_DESIGN.md](AISDLC_V2_DESIGN.md) - Codex implementation specification (detailed)
- [AISDLC_V2_DESIGN.md](../../imp_claude/design/AISDLC_V2_DESIGN.md) - reference implementation
- [GEMINI_GENESIS_DESIGN.md](../../imp_gemini/design/GEMINI_GENESIS_DESIGN.md) - sibling design
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) - canonical model
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) - requirements baseline
- [FEATURE_VECTORS.md](../../specification/FEATURE_VECTORS.md) - feature vectors
