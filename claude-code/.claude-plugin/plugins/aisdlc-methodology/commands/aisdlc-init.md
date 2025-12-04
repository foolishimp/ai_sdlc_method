# /aisdlc-init - Initialize AI SDLC Workspace and Artifacts

Initialize the AI SDLC workspace structure and create placeholder files for all mandatory artifacts required for traceability.

<!-- Implements: REQ-TOOL-002 (Developer Workspace), REQ-TRACE-001 (Full Lifecycle Traceability) -->

## Instructions

This command bootstraps a new project with the AI SDLC methodology. It creates:
1. The `.ai-workspace/` task management structure
2. Placeholder files for all mandatory artifacts per stage
3. Templates for requirements, design, and traceability

**IMPORTANT**: This command is safe to re-run. It will NOT overwrite existing files - only create missing ones.

### Step 1: Determine Project Name

Ask the user for the project name (used for the design folder), or infer from:
- The current directory name
- An existing `package.json` name field
- An existing `pyproject.toml` name field

### Step 2: Create Directory Structure

Create these directories if they don't exist:

```
.ai-workspace/
├── tasks/
│   ├── active/
│   └── finished/
├── templates/
└── config/

docs/
├── requirements/
├── design/{project_name}/
│   └── adrs/
├── uat/
├── releases/
├── runtime/
└── test/
```

### Step 3: Create Workspace Files

Create these files if they don't exist:

#### `.ai-workspace/tasks/active/ACTIVE_TASKS.md`
```markdown
# Active Tasks

**Project**: {project_name}
**Last Updated**: {date}

## Summary

| Status | Count |
|--------|-------|
| In Progress | 0 |
| Pending | 0 |
| Blocked | 0 |

## Tasks

<!-- Add tasks here using the format:
### Task #{id}: {title}
**Status**: pending | in_progress | blocked | completed
**Implements**: REQ-*
**Description**: ...
-->

No tasks yet. Start by capturing your intent with the Requirements Agent.

---

## Recently Completed

None yet.
```

#### `.ai-workspace/config/workspace_config.yml`
```yaml
# AI SDLC Workspace Configuration
workspace:
  version: "1.0"
  project: "{project_name}"
  created: "{date}"

paths:
  active_tasks: "tasks/active/ACTIVE_TASKS.md"
  finished_tasks: "tasks/finished/"
  templates: "templates/"

settings:
  auto_checkpoint: true
  require_req_tags: true
```

#### `.ai-workspace/templates/TASK_TEMPLATE.md`
```markdown
### Task #{id}: {title}

**Status**: pending
**Implements**: REQ-*
**Priority**: High | Medium | Low
**Created**: {date}

#### Description
{description}

#### Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

#### Dependencies
None

#### Notes
```

### Step 4: Create Mandatory Artifact Placeholders

Create these placeholder files for the mandatory artifacts (per stages_config.yml):

#### `docs/requirements/INTENT.md`
```markdown
# Project Intent

**Project**: {project_name}
**Date**: {date}
**Status**: Draft

---

## INT-001: {Project Name} Initial Intent

### Problem / Opportunity
<!-- What problem are we solving? What opportunity are we capturing? -->

{Describe the problem or opportunity here}

### Expected Outcomes
<!-- What does success look like? -->

- [ ] Outcome 1
- [ ] Outcome 2

### Stakeholders
<!-- Who cares about this? -->

| Role | Name | Interest |
|------|------|----------|
| Product Owner | TBD | Overall direction |
| Tech Lead | TBD | Technical feasibility |

### Constraints
<!-- Any limitations or boundaries? -->

- Constraint 1

---

## Next Steps

1. Refine this intent with stakeholders
2. Run Requirements Agent to generate REQ-* keys
3. Update AISDLC_IMPLEMENTATION_REQUIREMENTS.md
```

#### `docs/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md`
```markdown
# {Project Name} - Implementation Requirements

**Document Type**: Requirements Specification
**Project**: {project_name}
**Version**: 1.0
**Date**: {date}
**Status**: Draft
**Derived From**: [INTENT.md](INTENT.md)

---

## Purpose

This document defines the implementation requirements for {project_name}. Each requirement has a unique key that propagates through all SDLC stages for full traceability.

---

## Requirement Key Format

```
REQ-{TYPE}-{DOMAIN}-{SEQ}

Types:
- F    = Functional
- NFR  = Non-Functional
- DATA = Data Quality
- BR   = Business Rule
```

---

## Requirements

### Functional Requirements

<!--
Add requirements using this format:

### REQ-F-{DOMAIN}-001: {Title}

**Priority**: Critical | High | Medium
**Type**: Functional

**Description**: {What the system must do}

**Acceptance Criteria**:
- Criterion 1
- Criterion 2

**Traces To**: INT-001
-->

*No requirements yet. Run the Requirements Agent to extract from INTENT.md*

### Non-Functional Requirements

*No requirements yet.*

### Data Requirements

*No requirements yet.*

### Business Rules

*No requirements yet.*

---

## Requirement Summary

| Category | Count | Critical | High | Medium |
|----------|-------|----------|------|--------|
| Functional | 0 | 0 | 0 | 0 |
| Non-Functional | 0 | 0 | 0 | 0 |
| Data | 0 | 0 | 0 | 0 |
| Business Rules | 0 | 0 | 0 | 0 |
| **Total** | **0** | **0** | **0** | **0** |

---

**Document Status**: Draft
**Last Updated**: {date}
```

#### `docs/design/{project_name}/AISDLC_IMPLEMENTATION_DESIGN.md`
```markdown
# {Project Name} - Implementation Design

**Document Type**: Design Specification
**Project**: {project_name}
**Version**: 1.0
**Date**: {date}
**Status**: Draft
**Derived From**: [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md)

---

## Purpose

This document defines the technical design for {project_name}, mapping components to requirements for full traceability.

---

## System Architecture

<!-- Add architecture diagram here -->

```
┌─────────────────────────────────────────┐
│            {Project Name}               │
├─────────────────────────────────────────┤
│                                         │
│   [ Component diagrams go here ]        │
│                                         │
└─────────────────────────────────────────┘
```

---

## Component Design

<!--
Add components using this format:

### Component: {Name}

**Implements**: REQ-F-*, REQ-NFR-*

**Responsibilities**:
- Responsibility 1
- Responsibility 2

**Interfaces**:
- Interface 1

**Dependencies**:
- Dependency 1
-->

*No components yet. Run the Design Agent to create from requirements.*

---

## Architecture Decision Records

See [adrs/](adrs/) for all architectural decisions.

| ADR | Decision | Requirements |
|-----|----------|--------------|
| *None yet* | | |

---

## Design-to-Requirement Traceability

| Component | Requirements |
|-----------|--------------|
| *None yet* | |

---

**Document Status**: Draft
**Last Updated**: {date}
```

#### `docs/design/{project_name}/adrs/ADR-000-template.md`
```markdown
# ADR-000: Template

**Status**: Template (copy and rename to create new ADR)
**Date**: {date}

## Context

<!-- What forces are at play? What problem or decision are we facing? -->

{Describe the context and problem here}

## Decision

<!-- What is the change we're making? -->

We will {describe decision here}.

## Consequences

### Positive
- {Positive consequence 1}

### Negative
- {Negative consequence 1}

### Neutral
- {Neutral consequence 1}

## Requirements Addressed

- REQ-*: {requirement description}

---

**Note**: Copy this template to create a new ADR. Name it `ADR-NNN-{decision-name}.md`.
```

#### `docs/TRACEABILITY_MATRIX.md`
```markdown
# {Project Name} - Traceability Matrix

**Project**: {project_name}
**Version**: 1.0
**Date**: {date}
**Status**: Draft

---

## Purpose

Track requirement coverage across all SDLC stages: Requirements → Design → Tasks → Code → Test → UAT → Runtime.

---

## Coverage Summary

| Stage | Coverage | Status |
|-------|----------|--------|
| **1. Requirements** | 0/0 (0%) | ⏳ Not Started |
| **2. Design** | 0/0 (0%) | ⏳ Not Started |
| **3. Tasks** | 0/0 (0%) | ⏳ Not Started |
| **4. Code** | 0/0 (0%) | ⏳ Not Started |
| **5. System Test** | 0/0 (0%) | ⏳ Not Started |
| **6. UAT** | 0/0 (0%) | ⏳ Not Started |
| **7. Runtime** | 0/0 (0%) | ⏳ Not Started |

---

## Detailed Traceability

| Req ID | Description | Requirements | Design | Tasks | Code | Test | UAT | Runtime | Status |
|--------|-------------|--------------|--------|-------|------|------|-----|---------|--------|
| *No requirements yet* | | | | | | | | | |

---

## Legend

- ✅ Complete
- 🚧 Partial
- ❌ Not Started
- ⏳ Pending

---

## Gap Analysis

### Requirements without Design
*None identified yet*

### Requirements without Tests
*None identified yet*

### Requirements without Code
*None identified yet*

---

**Last Updated**: {date}
```

### Step 5: Report Results

Display a summary of what was created:

```
╔══════════════════════════════════════════════════════════════╗
║           AI SDLC Workspace Initialized                      ║
╚══════════════════════════════════════════════════════════════╝

  Project: {project_name}

  Created:
  ✅ .ai-workspace/tasks/active/ACTIVE_TASKS.md
  ✅ .ai-workspace/config/workspace_config.yml
  ✅ .ai-workspace/templates/TASK_TEMPLATE.md
  ✅ docs/requirements/INTENT.md
  ✅ docs/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md
  ✅ docs/design/{project_name}/AISDLC_IMPLEMENTATION_DESIGN.md
  ✅ docs/design/{project_name}/adrs/ADR-000-template.md
  ✅ docs/TRACEABILITY_MATRIX.md

  Skipped (already exist):
  ⏭️  {list any skipped files}

  Next Steps:
  1. Edit docs/requirements/INTENT.md with your project intent
  2. Ask: "Help me create requirements from INTENT.md"
  3. Ask: "Design a solution for REQ-F-XXX-001"
  4. Run /aisdlc-status to see your task queue

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  💡 Tip: All artifacts use REQ-* tags for traceability.
     Start with INTENT.md → Requirements → Design → Code
```

---

**Usage**: Run `/aisdlc-init` to initialize the workspace.

**Safe to re-run**: Existing files are preserved.
