# /aisdlc-init - Initialize AI SDLC v2.5 Workspace

Initialize a project with the AI SDLC Asset Graph Model workspace structure.

<!-- Implements: REQ-TOOL-002 (Developer Workspace), REQ-TOOL-007 (Project Scaffolding) -->

## Usage

```
/aisdlc-init [--force] [--backup]
```

| Option | Description |
|--------|-------------|
| (none) | Create missing files only (safe, default) |
| `--force` | Overwrite framework files (preserves user content) |
| `--backup` | Create backup before making changes |

## Instructions

This command scaffolds a v2.5 AI SDLC workspace: the asset graph configuration (Layer 2: Graph Package), context store and project constraints (Layer 3: Project Binding), feature tracking, and task management.

### Step 1: Determine Project Name

Ask the user for the project name, or infer from:
- The current directory name
- An existing `package.json` name field
- An existing `pyproject.toml` name field

### Step 2: Create Directory Structure

Create these directories if they don't exist:

```
.ai-workspace/
├── graph/
│   └── edges/              # Edge parameterisation configs
├── context/
│   ├── adrs/               # Architecture Decision Records
│   ├── data_models/        # Schemas, contracts
│   ├── templates/          # Patterns, standards
│   └── policy/             # Compliance, security
├── features/
│   ├── active/             # In-progress feature vectors
│   ├── completed/          # Converged feature vectors
│   └── fold-back/          # Child vector fold-back results
├── profiles/               # Projection profiles (full, standard, poc, spike, hotfix, minimal)
├── events/                 # Append-only event log (source of truth)
├── intents/                # Captured intents
├── tasks/
│   ├── active/             # Current work items (derived view)
│   └── finished/           # Completed task docs
└── snapshots/              # Immutable session checkpoints

docs/
├── specification/
└── design/{project_name}/
    └── adrs/
```

### Step 3: Copy Graph Topology Configuration

Copy the default graph topology files from the plugin into the workspace:

#### `.ai-workspace/graph/asset_types.yml`
Copy from plugin `v2/config/graph_topology.yml` — extract the `asset_types` section.

Actually, copy the entire `graph_topology.yml` as a single file:

#### `.ai-workspace/graph/graph_topology.yml`
Copy the plugin's `v2/config/graph_topology.yml` as the project's default graph topology.

#### `.ai-workspace/graph/evaluator_defaults.yml`
Copy the plugin's `v2/config/evaluator_defaults.yml`.

#### `.ai-workspace/graph/edges/`
Copy all files from the plugin's `v2/config/edge_params/` directory.

### Step 4: Scaffold Project Constraints

#### `.ai-workspace/context/project_constraints.yml`

Copy from the plugin's `v2/config/project_constraints_template.yml` and auto-detect values:

1. **Project name**: from directory name, `package.json`, or `pyproject.toml`
2. **Language**: detect from file extensions, `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`
3. **Test runner**: detect from `pyproject.toml` (pytest), `package.json` (jest/vitest), `Cargo.toml` (cargo test)
4. **Linter**: detect from `.ruff.toml`, `.eslintrc`, `rustfmt.toml`
5. **Formatter**: detect from `.prettierrc`, `.ruff.toml`, `rustfmt.toml`
6. **Type checker**: detect from `mypy.ini`, `tsconfig.json`

For any tool not auto-detected, leave the template default and add a comment:
```yaml
# TODO: Configure your test runner
```

7. **Constraint dimensions**: auto-populate from detected values:
   - `ecosystem_compatibility.language`: from detected language
   - `ecosystem_compatibility.version`: from detected version
   - `build_system.tool`: from detected build tool (npm, pip, sbt, cargo, etc.)
   - `build_system.module_structure`: "monolith" (default) or "multi-module" if detected
   - Mark remaining mandatory dimensions as `# TODO: Configure before running requirements→design edge`

Present the scaffolded file to the user for review before writing.

### Step 5: Copy Feature Vector Template and Projection Profiles

#### `.ai-workspace/features/feature_vector_template.yml`
Copy the plugin's `v2/config/feature_vector_template.yml` as the template for new feature vectors.

#### `.ai-workspace/profiles/`
Copy all files from the plugin's `v2/config/profiles/` directory (full.yml, standard.yml, poc.yml, spike.yml, hotfix.yml, minimal.yml). These are the named projection profiles that control graph subset, evaluator composition, convergence criteria, and context density.

#### `.ai-workspace/features/fold-back/`
Create the fold-back directory for child vector results that fold back to parent vectors.

#### `.ai-workspace/events/`
Create the events directory for the append-only event log. The iterate agent writes one JSON event per line to `events.jsonl` on every iteration. This is the **source of truth** — all other views (STATUS.md, ACTIVE_TASKS.md, feature vector trajectories) are derived projections of this event stream.

### Step 6: Create Context Manifest

#### `.ai-workspace/context/context_manifest.yml`
```yaml
# AI SDLC Context Manifest — Spec Reproducibility
# Reference: REQ-INTENT-004
version: "1.0.0"
generated_at: "{timestamp}"
algorithm: "sha256-canonical-v1"

aggregate_hash: "pending"  # Computed on first /aisdlc-checkpoint

entries: []  # Populated as context files are added
```

### Step 6: Create Feature Index

#### `.ai-workspace/features/feature_index.yml`
```yaml
# AI SDLC Feature Vector Index
version: "1.0.0"
project: "{project_name}"

active_features: []
completed_features: []

dependency_graph: {}
```

### Step 7: Create Active Tasks

#### `.ai-workspace/tasks/active/ACTIVE_TASKS.md`
```markdown
# Active Tasks

**Project**: {project_name}
**Methodology**: AI SDLC Asset Graph Model v2.5
**Last Updated**: {date}

## Summary

| Status | Count |
|--------|-------|
| In Progress | 0 |
| Pending | 0 |
| Blocked | 0 |

## Tasks

No tasks yet. Start by capturing your intent.

---

## Recently Completed

None yet.
```

### Step 8: Create Intent Placeholder

#### `docs/specification/INTENT.md`
```markdown
# Project Intent

**Project**: {project_name}
**Date**: {date}
**Status**: Draft

---

## INT-001: {Project Name} Initial Intent

### Problem / Opportunity

{Describe the problem or opportunity here}

### Expected Outcomes

- [ ] Outcome 1
- [ ] Outcome 2

### Constraints

- Constraint 1

---

## Next Steps

1. Refine this intent with stakeholders
2. Run `/aisdlc-iterate --edge "intent→requirements"` to generate REQ-* keys
3. Review and approve requirements
```

### Step 9: Create ADR Template

#### `docs/design/{project_name}/adrs/ADR-000-template.md`
```markdown
# ADR-000: Template

**Status**: Template (copy and rename to create new ADR)
**Date**: {date}

## Context

{What forces are at play? What problem or decision are we facing?}

## Decision

We will {describe decision here}.

## Rationale

{Why this decision over alternatives?}

### Alternatives Considered

1. **{Alternative 1}**: rejected because {reason}
2. **{Alternative 2}**: rejected because {reason}

## Consequences

### Positive
- {Positive consequence}

### Negative
- {Negative consequence}

## Requirements Addressed

- REQ-*: {requirement description}
```

### Step 10: Emit Event

Append a `project_initialized` event to `.ai-workspace/events/events.jsonl`:

```json
{"event_type": "project_initialized", "timestamp": "{ISO 8601}", "project": "{project_name}", "data": {"language": "{detected language}", "tools_detected": ["{test_runner}", "{linter}", "..."], "constraint_dimensions_configured": {count of non-empty mandatory dimensions}, "asset_types": {count from graph_topology}, "transitions": {count from graph_topology}}}
```

Create the `.ai-workspace/events/` directory and `events.jsonl` file if they don't exist yet.

### Step 11: Report Results

Display a summary:

```
AI SDLC v2.5 Workspace Initialized
===================================

Project: {project_name}
Model:   Asset Graph Model v2.5

Graph Topology (Layer 2: Graph Package):
  Asset types:           {count from graph_topology.yml}
  Transitions:           {count from graph_topology.yml}
  Edge configs:          {count of files in edges/}
  Constraint dimensions: {count mandatory}/{count total} mandatory

Project Binding (Layer 3):
  Language:     {detected language}
  Test runner:  {detected or "not configured"}
  Linter:       {detected or "not configured"}
  Coverage min: {threshold}%
  Dimensions configured:  {count of non-empty constraint dimensions}
  Dimensions TODO:        {count of empty mandatory dimensions}

Workspace:
  .ai-workspace/graph/          Graph topology + edge configs (Layer 2)
  .ai-workspace/context/        Context[] store + project constraints (Layer 3)
  .ai-workspace/features/       Feature vector tracking + template
  .ai-workspace/events/         Event log (source of truth)
  .ai-workspace/tasks/          Task management (derived view)
  .ai-workspace/profiles/       Projection profiles
  .ai-workspace/snapshots/      Session recovery

Next Steps:
  1. Review .ai-workspace/context/project_constraints.yml
     — configure your toolchain AND constraint dimensions
  2. Edit docs/specification/INTENT.md with your project intent
  3. Run: /aisdlc-iterate --edge "intent→requirements" --feature "REQ-F-{DOMAIN}-001"
  4. Review generated requirements
  5. Run: /aisdlc-status to see progress
```

## Preserved on --force

| Path | Default | --force |
|------|---------|---------|
| `.ai-workspace/graph/` | Create | Overwrite |
| `.ai-workspace/context/` | Create | **Preserve** |
| `.ai-workspace/features/` | Create | **Preserve** |
| `.ai-workspace/tasks/active/ACTIVE_TASKS.md` | Create | **Preserve** |
| `.ai-workspace/tasks/finished/*` | Create | **Preserve** |
| `docs/specification/*.md` | Create | **Preserve** |
| `docs/design/**/*.md` | Create | **Preserve** |
