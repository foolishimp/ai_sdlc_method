# AI SDLC Method Implementation Design (Roo Code Solution)

Document Type: Design Synthesis
Solution: `roo_aisdlc` (Roo Code-native)
Implementation: `roo-code-iclaude/` (iclaude = implemented by Claude)
Status: Draft
Date: 2025-11-25

## Purpose

Describe how the AI SDLC Method is delivered on Roo Code, mirroring the Claude solution while using Roo Code-native custom modes, rules, and memory bank. This design covers all implementation requirements listed in `requirements.yaml`.

## Executive Summary

The Roo Code solution delivers the same 7-stage methodology (Requirements -> Design -> Tasks -> Code -> System Test -> UAT -> Runtime Feedback) via:

- **Custom Modes Layer**: 7 stage-specific modes replacing Claude agents, each with role definition, tool groups, and custom instructions.
- **Rules Library**: Shared instructions in `.roo/rules/` for Key Principles, TDD, BDD, REQ tagging.
- **Memory Bank**: Persistent context via `.roo/memory-bank/` (projectbrief, techstack, activecontext).
- **Workspace Parity**: `.ai-workspace/` structure remains identical to Claude/Codex solutions.

---

## Component-to-Requirement Mapping

### Plugin/Mode System Components

| Component | Location | Requirements | Status |
|-----------|----------|--------------|--------|
| Custom Modes | `.roo/modes/*.json` | REQ-F-PLUGIN-001 | Planned |
| Mode Bundles | `.roomodes` | REQ-F-PLUGIN-003 | Planned |
| Mode Versioning | `plugin.json` metadata | REQ-F-PLUGIN-004 | Planned |
| Federated Loading | Mode layering | REQ-F-PLUGIN-002 | Planned |

### Command System Components

| Component | Location | Requirements | Status |
|-----------|----------|--------------|--------|
| Checkpoint Tasks | Mode instruction | REQ-F-CMD-001 | Planned |
| Finish Task | Mode instruction | REQ-F-CMD-001 | Planned |
| Commit Task | Mode instruction | REQ-F-CMD-001 | Planned |
| Status Report | Mode instruction | REQ-F-CMD-001 | Planned |
| Release Management | Mode instruction | REQ-F-CMD-003 | Planned |
| Stage Personas | 7 custom modes | REQ-F-CMD-002 | Planned |

### Workspace System Components

| Component | Location | Requirements | Status |
|-----------|----------|--------------|--------|
| Workspace Structure | `.ai-workspace/` | REQ-F-WORKSPACE-001 | Shared |
| Task Templates | `.ai-workspace/templates/` | REQ-F-WORKSPACE-002 | Shared |
| Session Tracking | Memory bank | REQ-F-WORKSPACE-003 | Planned |

### Traceability Components

| Component | Location | Requirements | Status |
|-----------|----------|--------------|--------|
| REQ Tagging Rules | `.roo/rules/req-tagging.md` | REQ-NFR-TRACE-001, REQ-NFR-TRACE-002 | Planned |
| Matrix Regeneration | Installer script | REQ-NFR-TRACE-001 | Planned |
| Key Propagation | Mode instructions | REQ-NFR-TRACE-002 | Planned |

### Context & Coverage Components

| Component | Location | Requirements | Status |
|-----------|----------|--------------|--------|
| Memory Bank | `.roo/memory-bank/` | REQ-NFR-CONTEXT-001 | Planned |
| Coverage Enforcement | Mode instructions | REQ-NFR-COVERAGE-001 | Planned |
| TDD/BDD Workflow | `.roo/rules/*.md` | REQ-F-TESTING-001, REQ-F-TESTING-002 | Planned |
| Feedback Protocol | Mode instructions | REQ-NFR-REFINE-001 | Planned |

---

## Architecture Overview

### 1) Custom Modes System (REQ-F-PLUGIN-001/002/003/004)

**Location**: `.roo/modes/` directory or `.roomodes` file

Each SDLC stage is a custom mode with full specification:

| Mode Slug | Stage | Tool Groups | Rule Files | REQ Coverage |
|-----------|-------|-------------|------------|--------------|
| `aisdlc-requirements` | 1 | read, browser | req-tagging, feedback-protocol | REQ-F-CMD-002 |
| `aisdlc-design` | 2 | read, edit | req-tagging, feedback-protocol | REQ-F-CMD-002 |
| `aisdlc-tasks` | 3 | read, edit | req-tagging, feedback-protocol | REQ-F-CMD-002 |
| `aisdlc-code` | 4 | read, edit, command | key-principles, tdd-workflow, req-tagging | REQ-F-CMD-002 |
| `aisdlc-system-test` | 5 | read, edit, command | bdd-workflow, req-tagging | REQ-F-CMD-002 |
| `aisdlc-uat` | 6 | read, browser | bdd-workflow, req-tagging | REQ-F-CMD-002 |
| `aisdlc-runtime` | 7 | read, edit, command, mcp | req-tagging, feedback-protocol | REQ-F-CMD-002 |

**Mode File Schema** (`.roo/modes/aisdlc-code.json`):
```json
{
  "slug": "aisdlc-code",
  "name": "AISDLC Code Agent",
  "roleDefinition": "You are the Code Agent for Stage 4 of the AI SDLC. Your mission is to implement work units using strict TDD workflow (RED-GREEN-REFACTOR). You follow the 7 Key Principles. You tag ALL code with REQ-* keys using '# Implements: REQ-F-*' comments. You never write code without tests first.",
  "groups": ["read", "edit", "command"],
  "customInstructions": "Load and follow these rules:\n- @rules/key-principles.md\n- @rules/tdd-workflow.md\n- @rules/req-tagging.md\n- @rules/workspace-safeguards.md\n\nBefore ANY code change:\n1. Read ACTIVE_TASKS.md for context\n2. Verify REQ-* key exists for the work\n3. Write failing test first (RED)\n4. Implement minimal code (GREEN)\n5. Refactor if needed\n6. Tag code with '# Implements: REQ-*'\n7. Tag tests with '# Validates: REQ-*'\n8. Update ACTIVE_TASKS.md\n\nCoverage requirement: >=80% overall, 100% critical paths."
}
```

### 2) Command Parity System (REQ-F-CMD-001/003)

Roo Code doesn't have slash commands. Commands are embedded as mode instructions with explicit behaviors:

| Claude Command | Roo Mode Instruction | Behavior | Safety |
|----------------|---------------------|----------|--------|
| `/aisdlc-checkpoint-tasks` | "Checkpoint tasks" | Update ACTIVE_TASKS.md with current status | Validate structure before write |
| `/aisdlc-finish-task` | "Finish task [ID]" | Move to finished/, create doc, update status | Preserve existing files |
| `/aisdlc-commit-task` | "Commit task [ID]" | Git commit with REQ tags in message | No force push, no amend others |
| `/aisdlc-status` | "Report status" | Show stage, tasks, coverage | Read-only |
| `/aisdlc-release` | "Execute release" | Preflight, bump, changelog, tag | Backup before changes |
| `/aisdlc-update` | "Update framework" | Pull latest from GitHub | Preserve user data |

**Command Safety Model**:
- All commands are **idempotent** - running twice produces same result
- **No destructive overwrites** - always validate before write
- **Backup before modify** - for release and update operations
- **REQ tagging enforced** - commits must include REQ-* keys

### 3) Persona/Agent System (REQ-F-CMD-002)

Custom modes serve as personas with complete specifications:

**Mode Definition Requirements**:
- `slug`: Unique identifier (aisdlc-<stage>)
- `name`: Human-readable name
- `roleDefinition`: Complete persona description (50-200 words)
- `groups`: Tool categories enabled
- `customInstructions`: Stage-specific rules and workflows

### 4) Rules Library (Skills) (REQ-F-TESTING-001/002)

**Location**: `.roo/rules/`

| Rule File | Purpose | Requirements | Content |
|-----------|---------|--------------|---------|
| `key-principles.md` | 7 Key Principles | REQ-NFR-COVERAGE-001 | TDD, Fail Fast, Modular, Reuse, Open Source, No Legacy, Excellence |
| `tdd-workflow.md` | TDD cycle | REQ-F-TESTING-001 | RED-GREEN-REFACTOR-COMMIT steps |
| `bdd-workflow.md` | BDD patterns | REQ-F-TESTING-002 | Given/When/Then templates |
| `req-tagging.md` | REQ-* format | REQ-NFR-TRACE-001/002 | Tag format, propagation rules |
| `feedback-protocol.md` | Feedback loops | REQ-NFR-REFINE-001 | Upstream/downstream communication |
| `workspace-safeguards.md` | Safety rules | REQ-F-WORKSPACE-001 | Validation, no destructive writes |

### 5) Workspace System (REQ-F-WORKSPACE-001/002/003)

**Location**: `.ai-workspace/` (shared across all AI tool implementations)

```
.ai-workspace/
├── tasks/
│   ├── active/ACTIVE_TASKS.md    # Current work (REQ-F-WORKSPACE-002)
│   ├── finished/                  # Completed task docs
│   └── archive/                   # Historical tasks
├── templates/                     # Document templates
│   ├── TASK_TEMPLATE.md
│   ├── FINISHED_TASK_TEMPLATE.md
│   └── AISDLC_METHOD_REFERENCE.md
├── config/
│   └── workspace_config.yml       # Coverage targets, settings
└── session/                       # Session state (if needed)
```

**Workspace Safeguards** (enforced via rules):
1. **Structure validation**: Before any write, verify target directory exists
2. **No destructive overwrites**: Never overwrite ACTIVE_TASKS.md without reading first
3. **Preserve user data**: finished/, archive/ contents are never deleted
4. **Backup on modify**: Create timestamped backup before release operations
5. **REQ tagging validation**: Warn if code lacks REQ-* tags

### 6) Context Loading System (REQ-NFR-CONTEXT-001)

**Memory Bank** (`.roo/memory-bank/`):

| File | Purpose | Auto-loaded | Update Frequency |
|------|---------|-------------|------------------|
| `projectbrief.md` | Project goals, scope, constraints | Yes | On project changes |
| `techstack.md` | Technology decisions, architecture | Yes | On tech changes |
| `activecontext.md` | Current work items, focus areas | Yes | Each session |
| `methodref.md` | AISDLC method reference (copied) | Yes | On framework update |

**Rules Loading** (`.roo/rules/`):

Rules are loaded via `@rules/<filename>` in mode customInstructions:
```
customInstructions: "@rules/key-principles.md\n@rules/tdd-workflow.md"
```

**Context Refresh Protocol**:
1. On session start: Load memory bank files
2. On mode switch: Load mode-specific rules
3. On "Refresh context": Re-read ACTIVE_TASKS.md and memory bank
4. On framework update: Copy latest method reference to memory bank

### 7) Traceability System (REQ-NFR-TRACE-001/002)

**REQ Tagging Validation**:

Mode instructions enforce tagging:
```
Before committing:
1. Scan modified files for REQ-* tags
2. Warn if any code lacks '# Implements: REQ-*'
3. Warn if any test lacks '# Validates: REQ-*'
4. Include REQ-* keys in commit message
```

**Traceability Matrix Regeneration**:

Installer script `validate_traceability.py` (planned):
- Scan codebase for REQ-* tags
- Update `docs/TRACEABILITY_MATRIX.md`
- Report coverage per requirement
- Flag requirements without implementations

### 8) Testing & Coverage (REQ-F-TESTING-001/002, REQ-NFR-COVERAGE-001)

**Coverage Enforcement**:

Mode instructions include:
```
Coverage requirements:
- Minimum: 80% overall
- Critical paths: 100%
- Before commit: Run tests, check coverage
- Fail commit if coverage drops
```

**TDD Workflow** (enforced in aisdlc-code mode):
1. RED: Write failing test with `# Validates: REQ-*`
2. GREEN: Write minimal code with `# Implements: REQ-*`
3. REFACTOR: Improve without changing behavior
4. COMMIT: Include REQ-* in message

**BDD Workflow** (enforced in aisdlc-system-test, aisdlc-uat modes):
```gherkin
Feature: <Feature Name>
  # Validates: REQ-F-*

  Scenario: <Scenario Name>
    Given <precondition>
    When <action>
    Then <expected result>
```

### 9) Iterative Refinement (REQ-NFR-REFINE-001)

**Feedback Protocol** (in all modes):

```
When you discover issues:

TO UPSTREAM (Requirements/Design):
- Missing requirement: "FEEDBACK: Need REQ for <gap>"
- Ambiguous requirement: "FEEDBACK: Clarify REQ-* - <ambiguity>"
- Conflict: "FEEDBACK: REQ-* conflicts with REQ-* - <details>"

FROM DOWNSTREAM (Code/Test/Runtime):
- Design gap: Update design docs
- Requirement gap: Escalate to Requirements
- Implementation issue: Fix and document
```

---

## Implementation Files

### Modes (`.roo/modes/`)

| File | Stage | Lines | Status |
|------|-------|-------|--------|
| `aisdlc-requirements.json` | 1 | ~30 | Planned |
| `aisdlc-design.json` | 2 | ~30 | Planned |
| `aisdlc-tasks.json` | 3 | ~30 | Planned |
| `aisdlc-code.json` | 4 | ~40 | Planned |
| `aisdlc-system-test.json` | 5 | ~35 | Planned |
| `aisdlc-uat.json` | 6 | ~30 | Planned |
| `aisdlc-runtime.json` | 7 | ~35 | Planned |

### Rules (`.roo/rules/`)

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| `key-principles.md` | 7 Key Principles | ~100 | Planned |
| `tdd-workflow.md` | TDD cycle | ~80 | Planned |
| `bdd-workflow.md` | BDD patterns | ~60 | Planned |
| `req-tagging.md` | REQ-* format | ~50 | Planned |
| `feedback-protocol.md` | Feedback loops | ~70 | Planned |
| `workspace-safeguards.md` | Safety rules | ~40 | Planned |

### Installers (`roo-code-iclaude/installers/`)

| File | Purpose | Status |
|------|---------|--------|
| `setup_workspace.py` | Install .ai-workspace/ | Planned |
| `setup_modes.py` | Install .roo/modes/ | Planned |
| `setup_rules.py` | Install .roo/rules/ | Planned |
| `setup_memory_bank.py` | Initialize memory bank | Planned |
| `setup_all.py` | Complete installation | Planned |
| `setup_reset.py` | Clean uninstall | Planned |
| `validate_traceability.py` | REQ coverage check | Planned |

---

## Design Artifacts

- `README.md` - Solution overview and scope
- `requirements.yaml` - REQ coverage for this solution
- `design.md` - High-level architecture
- `AISDLC_IMPLEMENTATION_DESIGN.md` - This document
- `adrs/` - Roo-specific decisions (ADR-201+)

**Implementation**: `roo-code-iclaude/` at project root (not in design folder)

---

## Implementation Notes

- **Packaging**: Modes/rules distributed as files to copy into `.roo/`
- **Configuration**: Project-level only (no global Roo config layering yet)
- **Safety**: All operations validate before write, backup before destructive changes
- **Idempotency**: All commands can be run multiple times safely
- **Alignment**: Maintain parity with Claude and Codex solutions; divergences require ADR documentation

---

## Roo Code Specific Features

### Tool Groups

Roo Code uses tool groups to control mode capabilities:

| Group | Tools Included | Stages Using |
|-------|---------------|--------------|
| `read` | read_file, search_files, list_files, list_code_definition_names | All |
| `edit` | write_to_file, apply_diff | Design, Tasks, Code, Runtime |
| `command` | execute_command | Code, System Test, Runtime |
| `mcp` | use_mcp_tool, access_mcp_resource | Runtime |
| `browser` | browser_action | Requirements, UAT |

### Mode Switching

Users switch stages by activating the corresponding mode in Roo Code's mode selector. Mode activation:
1. Loads roleDefinition as system context
2. Enables specified tool groups
3. Loads referenced rules via @rules/
4. Loads memory bank files

### File Restrictions (Future)

Modes can restrict file access via `fileRegex` patterns:
```json
{
  "slug": "aisdlc-code",
  "fileRegex": ["src/**/*", "tests/**/*", ".ai-workspace/**/*"]
}
```

---

## Validation Checklist

Before marking implementation complete:

- [ ] All 7 modes created with full specifications
- [ ] All 6 rule files created
- [ ] Memory bank templates created
- [ ] Installers implemented and tested
- [ ] Traceability validation script working
- [ ] All REQ-* mapped to implementation
- [ ] ADR-201+ documenting platform decisions
- [ ] Parity verified against Claude/Codex commands
