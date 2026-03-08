# Design: Asset Graph Engine (Unified & Consolidated)

**Version**: 1.2.0
**Date**: 2026-03-09
**Implements**: REQ-F-ENGINE-001, ADR-S-026, ADR-S-027

--- 

## Architecture Overview
The Asset Graph Engine is a state machine that manages the lifecycle of **Intent Vectors**. Following **ADR-S-027**, it strictly enforces an event-first source of truth for the `.ai-workspace/` domain and uses a **Composition Compiler** to bridge methodology abstraction levels.

## Level Separation (ADR-S-026/027)

| Level | Construct | Description |
|-------|-----------|-------------|
| Level 3 | Named Composition | Authoring language (`PLAN`, `POC`, `BUILD`) |
| Level 4 | Compiled Intent | Dispatchable unit with bound parameters |
| Level 5 | Execution Topology | The specific graph nodes and edges to be traversed |

### Component: CompositionCompiler
**Implements**: ADR-S-027 Invariant 6
**Responsibilities**: Compiles Level 3 compositions into Level 5 topologies. Implementation avoids direct execution of Level 3 constructs.
**Compilation Map**:
- `PLAN` 	o `intent 	o requirements` (with specialized PLAN sub-ops)
- `POC` 	o `requirements 	o design 	o code 	o unit_tests` (fast-path)
- `BUILD` 	o `design 	o code \leftrightarrow unit_tests` (standard co-evolution)

## State Reconstruction Invariants
1. **Event-First**: All state in `.ai-workspace/` (trajectories, status, vector registry) is projected from the `events.jsonl` ledger. 
2. **File Authority**: Spec files in `specification/` are the definitive truth for requirements and high-level design. Hash mismatches trigger integrity gaps.

## Traceability Matrix
| REQ Key | Component |
|---------|----------|
| ADR-S-027 | TriageEngine (branching), Projector (event-first), CompositionCompiler |
