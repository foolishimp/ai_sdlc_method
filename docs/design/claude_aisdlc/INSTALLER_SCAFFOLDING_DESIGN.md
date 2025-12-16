# Installer Project Scaffolding Design

**Document Type**: Technical Design Specification
**Project**: ai_sdlc_method (claude_aisdlc solution)
**Version**: 1.0
**Date**: 2025-12-11
**Status**: Draft

---

## 1. Overview

### 1.1 Purpose

This document specifies the design for the `aisdlc-setup.py init` command that creates a complete scaffolded project structure following AI SDLC conventions.

### 1.2 Requirements Covered

| Requirement | Description | Priority |
|-------------|-------------|----------|
| REQ-TOOL-009.0.1.0 | Design-Implementation Structure Convention | High |
| REQ-TOOL-010.0.1.0 | Installer Project Scaffolding | High |
| REQ-TOOL-011.0.1.0 | Installer Design-Implementation Validation | High |

### 1.3 Design Principles

1. **Explicit Binding** - Implementation declares its design source via `IMPLEMENTATION.yaml`
2. **Template-Driven** - All scaffolded files are templates with guidance
3. **Validation-First** - Installer validates structure before and after operations
4. **Idempotent** - Running init multiple times is safe (skip existing files)

---

## 2. Architecture

### 2.1 Command Structure

```
aisdlc-setup.py
├── (existing) default     # Plugin + workspace setup
├── (new) init             # Full project scaffolding
└── (new) validate         # Structure validation
```

### 2.2 Init Command Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     aisdlc-setup.py init                         │
│                                                                  │
│  Input: --variant <name> --platform <platform>                   │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    1. Validate Inputs                            │
│  - Variant name format: {name}_aisdlc                           │
│  - Platform: claude-code | codex-code | roo-code | gemini-code  │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    2. Create docs/requirements/                  │
│  - REQUIREMENTS.md (template)                                    │
│  - INTENT.md (template)                                         │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    3. Create docs/design/{variant}_aisdlc/       │
│  - requirements.yaml                                             │
│  - AISDLC_IMPLEMENTATION_DESIGN.md (template)                    │
│  - design.md (template)                                          │
│  - adrs/README.md                                                │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    4. Create docs/TRACEABILITY_MATRIX.md         │
│  - Template with requirement → design → code → test structure   │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    5. Create src/{variant}_aisdlc/{platform}/    │
│  - IMPLEMENTATION.yaml (binding to design)                       │
│  - installers/README.md                                          │
│  - plugins/README.md                                             │
│  - tests/README.md                                               │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    6. Create .ai-workspace/ (existing)           │
│                    7. Create .claude/ (existing)                 │
│                    8. Create CLAUDE.md                           │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    9. Run Validation                             │
│  - Verify IMPLEMENTATION.yaml → design path valid               │
│  - Verify required design artifacts exist                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Structures

### 3.1 IMPLEMENTATION.yaml Schema

```yaml
# src/{variant}_aisdlc/{platform}/IMPLEMENTATION.yaml
# Explicit binding from implementation to design

# Required fields
variant: string           # e.g., "my_project_aisdlc"
design_path: string       # e.g., "docs/design/my_project_aisdlc/"
platform: string          # e.g., "claude-code"
version: string           # Semantic version, e.g., "0.1.0"

# Optional fields
implements:
  design_synthesis: string    # e.g., "AISDLC_IMPLEMENTATION_DESIGN.md"
  requirements: string        # e.g., "requirements.yaml"

metadata:
  created: string            # ISO date
  author: string
  description: string
```

### 3.2 requirements.yaml Schema (Design Side)

```yaml
# docs/design/{variant}_aisdlc/requirements.yaml
# REQ keys covered by this design variant

solution: string              # e.g., "my_project_aisdlc"
platform: string              # e.g., "Claude Code"
status: string                # draft | active | deprecated

requirements_covered:
  - REQ-*                     # List of requirement keys

# Optional
derived_from: string          # Parent requirements document path
```

---

## 4. Templates

### 4.1 Template Directory Structure

Templates are embedded in the installer for single-file distribution:

```python
TEMPLATES = {
    # docs/requirements/
    "docs/requirements/REQUIREMENTS.md": REQUIREMENTS_TEMPLATE,
    "docs/requirements/INTENT.md": INTENT_TEMPLATE,

    # docs/design/{variant}/
    "docs/design/{variant}/requirements.yaml": REQUIREMENTS_YAML_TEMPLATE,
    "docs/design/{variant}/AISDLC_IMPLEMENTATION_DESIGN.md": DESIGN_SYNTHESIS_TEMPLATE,
    "docs/design/{variant}/design.md": DESIGN_TEMPLATE,
    "docs/design/{variant}/adrs/README.md": ADRS_README_TEMPLATE,

    # docs/
    "docs/TRACEABILITY_MATRIX.md": TRACEABILITY_TEMPLATE,

    # src/{variant}/{platform}/
    "src/{variant}/{platform}/IMPLEMENTATION.yaml": IMPLEMENTATION_YAML_TEMPLATE,
    "src/{variant}/{platform}/installers/README.md": INSTALLERS_README_TEMPLATE,
    "src/{variant}/{platform}/plugins/README.md": PLUGINS_README_TEMPLATE,
    "src/{variant}/{platform}/tests/README.md": TESTS_README_TEMPLATE,

    # Root
    "CLAUDE.md": CLAUDE_MD_TEMPLATE,
}
```

### 4.2 Template Content Examples

#### IMPLEMENTATION.yaml Template

```yaml
# IMPLEMENTATION.yaml - Design-Implementation Binding
# Implements: REQ-TOOL-009

# This file explicitly binds this implementation to its design source.
# The installer validates this binding before setup operations.

variant: {variant}
design_path: docs/design/{variant}/
platform: {platform}
version: 0.1.0

implements:
  design_synthesis: AISDLC_IMPLEMENTATION_DESIGN.md
  requirements: requirements.yaml

metadata:
  created: {date}
  author: AI SDLC Method Installer
  description: |
    Implementation of {variant} for {platform}.
    See design_path for architecture and requirements coverage.
```

#### requirements.yaml Template

```yaml
# requirements.yaml - Design Variant Requirements Coverage
# Implements: REQ-TOOL-009

solution: {variant}
platform: {platform_display}
status: draft

# List the REQ-* keys this design covers
# Add entries as you define requirements in docs/requirements/REQUIREMENTS.md
requirements_covered:
  # Example entries (uncomment and modify):
  # - REQ-F-CORE-001
  # - REQ-NFR-PERF-001
  # - REQ-DATA-001

derived_from: docs/requirements/REQUIREMENTS.md
```

#### TRACEABILITY_MATRIX.md Template

```markdown
# Traceability Matrix

**Project**: {project_name}
**Variant**: {variant}
**Generated**: {date}

---

## Overview

This matrix tracks requirement coverage across all SDLC stages:

```
Requirement → Design → Task → Code → Test → Runtime
```

---

## Coverage Summary

| Stage | Coverage | Details |
|-------|----------|---------|
| Requirements | 0/0 | See docs/requirements/REQUIREMENTS.md |
| Design | 0/0 | See docs/design/{variant}/ |
| Tasks | 0/0 | See .ai-workspace/tasks/ |
| Code | 0/0 | See src/{variant}/ |
| Tests | 0/0 | See src/{variant}/{platform}/tests/ |

---

## Requirement Details

<!-- Add entries as requirements are defined -->

### REQ-F-EXAMPLE-001: Example Requirement

| Stage | Status | Artifact |
|-------|--------|----------|
| Design | ⬜ Pending | |
| Tasks | ⬜ Pending | |
| Code | ⬜ Pending | |
| Tests | ⬜ Pending | |

---

**Legend**: ✅ Complete | 🔄 In Progress | ⬜ Pending | ❌ Blocked
```

---

## 5. Validation

### 5.1 Validate Command

```bash
python aisdlc-setup.py validate [--target PATH]
```

### 5.2 Validation Checks

| Check | Severity | Description |
|-------|----------|-------------|
| IMPLEMENTATION.yaml exists | ERROR | Implementation must have manifest |
| design_path valid | ERROR | Path in manifest must exist |
| Design artifacts exist | ERROR | requirements.yaml, design.md required |
| ADRs directory exists | WARNING | adrs/ should exist |
| Requirements coverage | WARNING | requirements.yaml should list REQ-* keys |

### 5.3 Validation Output

```
$ python aisdlc-setup.py validate

AI SDLC Structure Validation
============================

Scanning: /path/to/project

Found implementations:
  - src/my_project_aisdlc/claude-code/

Validating: my_project_aisdlc (claude-code)
  [OK] IMPLEMENTATION.yaml exists
  [OK] design_path: docs/design/my_project_aisdlc/
  [OK] requirements.yaml exists
  [OK] AISDLC_IMPLEMENTATION_DESIGN.md exists
  [OK] design.md exists
  [WARN] adrs/ has no ADR files (expected ADR-*.md)

Summary: 5 passed, 1 warning, 0 errors
```

---

## 6. Implementation Notes

### 6.1 Backward Compatibility

The existing `aisdlc-setup.py` (no subcommand) behavior is preserved:
- Default: Plugin + workspace setup (current behavior)
- `init`: Full project scaffolding (new)
- `validate`: Structure validation (new)

### 6.2 Template Variables

Templates use `{variable}` placeholders:

| Variable | Description | Example |
|----------|-------------|---------|
| `{variant}` | Variant name | `my_project_aisdlc` |
| `{platform}` | Platform directory | `claude-code` |
| `{platform_display}` | Human-readable platform | `Claude Code` |
| `{date}` | ISO date | `2025-12-11` |
| `{project_name}` | Project name (from variant) | `My Project` |

### 6.3 File Handling

- **Existing files**: Skip with info message (idempotent)
- **Dry run**: Print what would be created
- **Force**: Overwrite existing files (with `--force` flag)

---

## 7. CLI Interface

### 7.1 Init Command

```bash
python aisdlc-setup.py init --variant <name> --platform <platform> [options]

Required:
  --variant NAME       Variant name (e.g., my_project_aisdlc)
  --platform PLATFORM  Platform: claude-code, codex-code, roo-code, gemini-code

Options:
  --target PATH        Target directory (default: current)
  --dry-run            Preview changes without writing
  --force              Overwrite existing files
  --no-workspace       Skip .ai-workspace/ creation
```

### 7.2 Validate Command

```bash
python aisdlc-setup.py validate [options]

Options:
  --target PATH        Target directory (default: current)
  --strict             Treat warnings as errors
```

### 7.3 Default Command (Existing)

```bash
python aisdlc-setup.py [options]

# Existing behavior preserved: plugin + workspace setup
```

---

## 8. Test Specification

### 8.1 Unit Tests

| Test | Description |
|------|-------------|
| test_init_creates_structure | Verify all directories/files created |
| test_init_idempotent | Running twice doesn't duplicate |
| test_init_dry_run | No files created in dry run |
| test_validate_valid_structure | Passes on correct structure |
| test_validate_missing_manifest | Fails without IMPLEMENTATION.yaml |
| test_validate_invalid_design_path | Fails with bad design_path |
| test_template_substitution | Variables replaced correctly |

### 8.2 Integration Tests

| Test | Description |
|------|-------------|
| test_full_workflow | init → validate → passes |
| test_existing_project | init on project with some files |

---

## 9. Traceability

### 9.1 Requirements to Design

| Requirement | Design Section |
|-------------|----------------|
| REQ-TOOL-009.0.1.0 | Section 3 (Data Structures), Section 4 (Templates) |
| REQ-TOOL-010.0.1.0 | Section 2 (Architecture), Section 7 (CLI Interface) |
| REQ-TOOL-011.0.1.0 | Section 5 (Validation) |

### 9.2 Design to Implementation

| Design Section | Implementation File |
|----------------|---------------------|
| Section 2-7 | `claude-code/installers/aisdlc-setup.py` |
| Section 4 | Embedded templates in installer |
| Section 8 | `claude-code/installers/tests/test_aisdlc_setup.py` |

---

**Document Status**: Draft - Ready for Implementation
**Author**: AI SDLC Design Agent
**Last Updated**: 2025-12-11
