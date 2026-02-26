# /gen-init - Initialize AI SDLC Workspace

Scaffolds the `.ai-workspace` directory structure and initializes the event log.

<!-- Implements: REQ-TOOL-007 (Project Scaffolding), REQ-UX-002 (Progressive Disclosure) -->

## Instructions

1. Create the directory structure:
    - `graph/` and `edges/` for topology
    - `context/` and `adrs/` for constraints
    - `features/`, `active/`, and `completed/` for vectors
    - `profiles/` for graph subsets
    - `fold-back/` for child results
    - `events/` for the immutable log
    - `tasks/` for planning
    - `intents/` for problem statements
    - `snapshots/` for checkpoints

2. `Step 4b`: Resolve Context Sources (copy external collections into context/ dirs).
3. Copy `graph_topology.yml`, `edge_params/`, and `profiles/` to workspace.
4. Scaffold `project_constraints.yml` with auto-detection of `ecosystem_compatibility` (language) and `build_system`. Check `constraint_dimensions`.
5. Create `specification/INTENT.md` placeholder. If a dimension is undetected, mark as `TODO`.
6. Create the initial `STATUS.md`.
7. Emit the `project_initialized` event with `event_type: "project_initialized"`.
8. Initialization report shows `Dimensions` status and `three-layer structure`:
    - `Layer 2`: Graph Package
    - `Layer 3`: Project Binding
