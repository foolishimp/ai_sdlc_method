#!/usr/bin/env python3
"""
AI SDLC Method - Project Setup and Scaffolding

Self-contained installer that can be run directly from GitHub.

# Implements: REQ-TOOL-009 (Structure Convention), REQ-TOOL-010 (Scaffolding), REQ-TOOL-011 (Validation)

Usage:
    # Default: Plugin + workspace setup (existing behavior)
    python aisdlc-setup.py [--target PATH] [--no-workspace] [--dry-run]

    # Full project scaffolding with design-implementation structure
    python aisdlc-setup.py init --variant my_project_aisdlc --platform claude-code

    # Validate design-implementation binding
    python aisdlc-setup.py validate [--target PATH]

Commands:
    (default)   Plugin + workspace setup (backward compatible)
    init        Create full project scaffold with docs/design and src structure
    validate    Validate IMPLEMENTATION.yaml binding to design

What init creates:
    docs/requirements/          - Requirements templates
    docs/design/{variant}/      - Design templates with ADRs
    docs/TRACEABILITY_MATRIX.md - Traceability template
    src/{variant}/{platform}/   - Implementation with IMPLEMENTATION.yaml
    .ai-workspace/              - Task management workspace
    .claude/                    - Platform integration
    CLAUDE.md                   - Project guidance
"""

import sys
import json
import argparse
import shutil
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional


# =============================================================================
# Configuration
# =============================================================================

GITHUB_REPO = "foolishimp/ai_sdlc_method"
PLUGIN_NAME = "aisdlc-methodology"
PLUGIN_JSON_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/claude-code/.claude-plugin/plugins/{PLUGIN_NAME}/.claude-plugin/plugin.json"

SUPPORTED_PLATFORMS = {
    "claude-code": "Claude Code",
    "codex-code": "Codex",
    "roo-code": "Roo Code",
    "gemini-code": "Gemini Code",
    "copilot-code": "GitHub Copilot",
}


# =============================================================================
# Project Scaffolding Templates (REQ-TOOL-010)
# =============================================================================

IMPLEMENTATION_YAML_TEMPLATE = '''# IMPLEMENTATION.yaml - Design-Implementation Binding
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
  created: "{date}"
  author: AI SDLC Method Installer
  description: |
    Implementation of {variant} for {platform_display}.
    See design_path for architecture and requirements coverage.
'''

REQUIREMENTS_YAML_TEMPLATE = '''# requirements.yaml - Design Variant Requirements Coverage
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
'''

DESIGN_SYNTHESIS_TEMPLATE = '''# {project_name} Implementation Design

**Document Type**: Design Synthesis Document
**Project**: {project_name}
**Variant**: {variant}
**Version**: 0.1.0
**Date**: {date}
**Status**: Draft

---

## Purpose

This document synthesizes all design artifacts into a **coherent technical solution** that implements the requirements defined in [REQUIREMENTS.md](../../requirements/REQUIREMENTS.md).

---

## Requirements Coverage

See [requirements.yaml](requirements.yaml) for the list of REQ-* keys covered by this design.

---

## Architecture Overview

<!-- Add your architecture diagram and description here -->

```
┌─────────────────────────────────────────────────────────────────┐
│                     Your Architecture Here                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

<!-- Define your components here -->

| Component | Purpose | Requirements |
|-----------|---------|--------------|
| Example   | Description | REQ-F-XXX-001 |

---

## Design Decisions

See [adrs/](adrs/) for Architecture Decision Records.

---

## Traceability

See [../../TRACEABILITY_MATRIX.md](../../TRACEABILITY_MATRIX.md) for requirement coverage tracking.

---

**Document Status**: Draft
**Author**: AI SDLC Design Agent
**Last Updated**: {date}
'''

DESIGN_MD_TEMPLATE = '''# {project_name} - Detailed Design

**Variant**: {variant}
**Date**: {date}

---

## 1. Overview

<!-- Detailed design specification -->

---

## 2. Data Structures

<!-- Define your data structures, schemas, models -->

---

## 3. Interfaces

<!-- API definitions, function signatures -->

---

## 4. Implementation Notes

<!-- Platform-specific considerations for {platform_display} -->

---

## 5. Security Considerations

<!-- Security design decisions -->

---

## 6. Performance Considerations

<!-- Performance design decisions -->

---
'''

ADRS_README_TEMPLATE = '''# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the {variant} design.

## ADR Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| ADR-001 | [Template] | Proposed | {date} |

## ADR Template

Create new ADRs using this format:

```markdown
# ADR-NNN: Title

**Status**: Proposed | Accepted | Deprecated | Superseded
**Date**: YYYY-MM-DD
**Deciders**: Names

## Context

What is the issue that we're seeing that is motivating this decision?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?

## Requirements

- REQ-*: Requirement this decision addresses
```
'''

REQUIREMENTS_MD_TEMPLATE = '''# {project_name} - Requirements

**Document Type**: Requirements Specification
**Project**: {project_name}
**Version**: 0.1.0
**Date**: {date}
**Status**: Draft

---

## Purpose

This document defines the requirements for {project_name}.

---

## Requirement Format

Requirements use the format: `REQ-{{TYPE}}-{{DOMAIN}}-{{SEQ}}`

**Types**:
- `F` - Functional requirement
- `NFR` - Non-functional requirement
- `DATA` - Data quality requirement
- `BR` - Business rule

---

## 1. Functional Requirements

### REQ-F-CORE-001: [Title]

**Priority**: High | Medium | Low
**Type**: Functional

**Description**: [What the system shall do]

**Acceptance Criteria**:
- Criterion 1
- Criterion 2

**Traces To**: [Source - user story, business need, etc.]

---

## 2. Non-Functional Requirements

### REQ-NFR-PERF-001: [Title]

**Priority**: High | Medium | Low
**Type**: Non-Functional

**Description**: [Quality attribute]

**Acceptance Criteria**:
- Criterion 1

---

## 3. Data Requirements

<!-- Add data quality requirements here -->

---

## Summary

| Category | Count |
|----------|-------|
| Functional | 0 |
| Non-Functional | 0 |
| Data | 0 |
| **Total** | **0** |

---

**Document Status**: Draft
**Last Updated**: {date}
'''

INTENT_MD_TEMPLATE = '''# {project_name} - Project Intent

**Document Type**: Intent Declaration
**Project**: {project_name}
**Date**: {date}

---

## Vision

<!-- What is the high-level vision for this project? -->

---

## Goals

1. Goal 1
2. Goal 2
3. Goal 3

---

## Non-Goals

1. Non-goal 1 (explicitly out of scope)

---

## Success Criteria

- [ ] Criterion 1
- [ ] Criterion 2

---

## Stakeholders

| Role | Name | Responsibility |
|------|------|----------------|
| Owner | TBD | Final decisions |
| Developer | TBD | Implementation |

---
'''

TRACEABILITY_TEMPLATE = '''# Traceability Matrix

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
'''

INSTALLERS_README_TEMPLATE = '''# Installers

Implementation installers for {variant} ({platform_display}).

## Structure

```
installers/
├── README.md           # This file
└── (your installers)
```

## Usage

<!-- Add installer usage instructions -->
'''

PLUGINS_README_TEMPLATE = '''# Plugins

Plugins for {variant} ({platform_display}).

## Structure

```
plugins/
├── README.md           # This file
└── (your plugins)
```

## Available Plugins

<!-- List plugins here -->
'''

TESTS_README_TEMPLATE = '''# Tests

Test suite for {variant} ({platform_display}).

## Structure

```
tests/
├── README.md           # This file
├── unit/               # Unit tests
├── integration/        # Integration tests
└── features/           # BDD feature files
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/{variant}
```

## Test Requirements

Tests should include `# Validates: REQ-*` tags for traceability.
'''

CLAUDE_MD_TEMPLATE = '''# CLAUDE.md - {project_name}

This file provides guidance to Claude Code when working with this repository.

## Project Overview

**Project**: {project_name}
**Variant**: {variant}
**Platform**: {platform_display}

---

## Structure

```
{project_name}/
├── docs/
│   ├── requirements/           # Project requirements
│   │   ├── REQUIREMENTS.md
│   │   └── INTENT.md
│   ├── design/
│   │   └── {variant}/          # Design variant
│   │       ├── requirements.yaml
│   │       ├── AISDLC_IMPLEMENTATION_DESIGN.md
│   │       ├── design.md
│   │       └── adrs/
│   └── TRACEABILITY_MATRIX.md
│
├── src/
│   └── {variant}/
│       └── {platform}/         # Implementation
│           ├── IMPLEMENTATION.yaml  # Design binding
│           ├── installers/
│           ├── plugins/
│           └── tests/
│
├── .ai-workspace/              # Task management
└── .claude/                    # Claude Code integration
```

---

## Development Methodology

This project follows the **AI SDLC Methodology**:

1. **Requirements** → Define REQ-* keys in docs/requirements/
2. **Design** → Create design artifacts in docs/design/{variant}/
3. **Tasks** → Track in .ai-workspace/tasks/
4. **Code** → TDD (RED → GREEN → REFACTOR), tag with `# Implements: REQ-*`
5. **Test** → BDD scenarios, tag with `# Validates: REQ-*`

---

## Key Principles

1. **Test Driven Development** - No code without tests
2. **Fail Fast & Root Cause** - Fix at source
3. **Modular & Maintainable** - Single responsibility
4. **Reuse Before Build** - Check existing first
5. **Open Source First** - Suggest alternatives
6. **No Legacy Baggage** - Start clean
7. **Perfectionist Excellence** - Excellence or nothing 🔥

---

## Commands

| Command | Purpose |
|---------|---------|
| `/aisdlc-status` | Show task status |
| `/aisdlc-checkpoint-tasks` | Save progress |
| `/aisdlc-help` | Full guide |

---

**"Excellence or nothing"** 🔥
'''


# =============================================================================
# Workspace Templates (existing - for backward compatibility)
# =============================================================================

ACTIVE_TASKS_TEMPLATE = '''# Active Tasks

*Last Updated: {date}*

---

## Summary

**Total Active Tasks**: 0
- High Priority: 0
- Medium Priority: 0
- Not Started: 0
- In Progress: 0

**Recently Completed**: None yet

---

## Recovery Commands

If context is lost, run these commands to get back:
```bash
cat .ai-workspace/tasks/active/ACTIVE_TASKS.md  # This file
git status                                       # Current state
git log --oneline -5                            # Recent commits
/aisdlc-status                                   # Task queue status
```
'''

TASK_TEMPLATE = '''# Task #{ID}: {TITLE}

**Priority**: High | Medium | Low
**Status**: Not Started
**Estimated Time**: X hours
**Dependencies**: None

**Requirements Traceability**:
- REQ-F-XXX-001: Description

---

## Description

What needs to be done and why?

---

## Acceptance Criteria

- [ ] All tests pass (RED → GREEN → REFACTOR)
- [ ] Test coverage ≥ 80%
- [ ] Documentation updated

---

## TDD Checklist

- [ ] RED: Write failing tests
- [ ] GREEN: Implement minimal solution
- [ ] REFACTOR: Improve code quality
- [ ] COMMIT: Save with REQ tags

---

**Created**: {TIMESTAMP}
'''

FINISHED_TASK_TEMPLATE = '''# Task: {TITLE}

**Status**: Completed
**Date**: {DATE}

---

## Problem

What was the issue?

---

## Solution

What was implemented?

---

## Files Modified

- `/path/to/file` - Description

---

## Traceability

- REQ-*: Tests in `test_file.py`
'''

METHOD_REFERENCE = '''# AI SDLC Method Quick Reference

**Version:** 3.1.0

---

## TDD Cycle

```
RED    → Write failing test first
GREEN  → Implement minimal solution
REFACTOR → Improve code quality
COMMIT → Save with REQ tags
```

---

## 7-Stage AI SDLC

```
Intent → Requirements → Design → Tasks → Code → System Test → UAT → Runtime Feedback
```

---

**"Excellence or nothing"** 🔥
'''

WORKSPACE_CONFIG = '''# Developer Workspace Configuration
version: "1.0"

task_tracking:
  enabled: true
  active_file: "tasks/active/ACTIVE_TASKS.md"

tdd:
  enforce: true
  min_coverage: 80

ai_sdlc:
  require_req_keys: false
'''


# =============================================================================
# Helper Functions
# =============================================================================

def print_banner(title: str, version: str = ""):
    """Print setup banner."""
    print()
    print("+" + "=" * 62 + "+")
    title_line = f"AI SDLC Method - {title}"
    padding = (62 - len(title_line)) // 2
    print("|" + " " * padding + title_line + " " * (62 - padding - len(title_line)) + "|")
    if version:
        version_line = f"Version: {version}"
        padding = (62 - len(version_line)) // 2
        print("|" + " " * padding + version_line + " " * (62 - padding - len(version_line)) + "|")
    print("+" + "=" * 62 + "+")
    print()


def print_success(msg: str):
    print(f"  [OK] {msg}")


def print_error(msg: str):
    print(f"  [ERROR] {msg}")


def print_info(msg: str):
    print(f"  {msg}")


def print_warning(msg: str):
    print(f"  [WARN] {msg}")


def get_plugin_version() -> str:
    """Fetch the latest plugin version from GitHub."""
    try:
        with urllib.request.urlopen(PLUGIN_JSON_URL, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('version', 'unknown')
    except (urllib.error.URLError, json.JSONDecodeError, KeyError):
        return 'unknown'


def variant_to_project_name(variant: str) -> str:
    """Convert variant name to human-readable project name."""
    # my_project_aisdlc -> My Project
    name = variant.replace("_aisdlc", "").replace("_", " ")
    return name.title()


def write_file(path: Path, content: str, dry_run: bool, force: bool = False) -> bool:
    """Write file if it doesn't exist (or force is True)."""
    if path.exists() and not force:
        print_info(f"Exists: {path}")
        return True

    if dry_run:
        print_info(f"Would create: {path}")
        return True

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    print_success(f"Created {path}")
    return True


def parse_yaml_simple(content: str) -> dict:
    """Simple YAML parser for IMPLEMENTATION.yaml (no external deps)."""
    result = {}
    current_key = None
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if value:
                result[key] = value
            else:
                current_key = key
                result[key] = {}
    return result


# =============================================================================
# Init Command (REQ-TOOL-010)
# =============================================================================

def get_scaffolding_structure(variant: str, platform: str, date: str) -> Dict[str, str]:
    """Return full project scaffolding structure."""
    platform_display = SUPPORTED_PLATFORMS.get(platform, platform)
    project_name = variant_to_project_name(variant)

    template_vars = {
        "variant": variant,
        "platform": platform,
        "platform_display": platform_display,
        "project_name": project_name,
        "date": date,
    }

    return {
        # docs/requirements/
        f"docs/requirements/REQUIREMENTS.md": REQUIREMENTS_MD_TEMPLATE.format(**template_vars),
        f"docs/requirements/INTENT.md": INTENT_MD_TEMPLATE.format(**template_vars),

        # docs/design/{variant}/
        f"docs/design/{variant}/requirements.yaml": REQUIREMENTS_YAML_TEMPLATE.format(**template_vars),
        f"docs/design/{variant}/AISDLC_IMPLEMENTATION_DESIGN.md": DESIGN_SYNTHESIS_TEMPLATE.format(**template_vars),
        f"docs/design/{variant}/design.md": DESIGN_MD_TEMPLATE.format(**template_vars),
        f"docs/design/{variant}/adrs/README.md": ADRS_README_TEMPLATE.format(**template_vars),

        # docs/
        f"docs/TRACEABILITY_MATRIX.md": TRACEABILITY_TEMPLATE.format(**template_vars),

        # src/{variant}/{platform}/
        f"src/{variant}/{platform}/IMPLEMENTATION.yaml": IMPLEMENTATION_YAML_TEMPLATE.format(**template_vars),
        f"src/{variant}/{platform}/installers/README.md": INSTALLERS_README_TEMPLATE.format(**template_vars),
        f"src/{variant}/{platform}/plugins/README.md": PLUGINS_README_TEMPLATE.format(**template_vars),
        f"src/{variant}/{platform}/tests/README.md": TESTS_README_TEMPLATE.format(**template_vars),

        # Root
        "CLAUDE.md": CLAUDE_MD_TEMPLATE.format(**template_vars),
    }


def get_workspace_structure(date: str) -> Dict[str, str]:
    """Return workspace structure with templates."""
    return {
        ".ai-workspace/tasks/active/ACTIVE_TASKS.md": ACTIVE_TASKS_TEMPLATE.format(date=date),
        ".ai-workspace/tasks/finished/.gitkeep": "",
        ".ai-workspace/templates/TASK_TEMPLATE.md": TASK_TEMPLATE,
        ".ai-workspace/templates/FINISHED_TASK_TEMPLATE.md": FINISHED_TASK_TEMPLATE,
        ".ai-workspace/templates/AISDLC_METHOD_REFERENCE.md": METHOD_REFERENCE,
        ".ai-workspace/config/workspace_config.yml": WORKSPACE_CONFIG,
    }


def cmd_init(args) -> int:
    """Initialize full project scaffold."""
    print_banner("Project Init")

    target = Path(args.target).resolve()
    variant = args.variant
    platform = args.platform
    date = datetime.now().strftime("%Y-%m-%d")

    # Validate variant name
    if not variant.endswith("_aisdlc"):
        print_warning(f"Variant name should end with '_aisdlc' (got: {variant})")
        print_info("Continuing anyway...")

    # Validate platform
    if platform not in SUPPORTED_PLATFORMS:
        print_error(f"Unknown platform: {platform}")
        print_info(f"Supported: {', '.join(SUPPORTED_PLATFORMS.keys())}")
        return 1

    print_info(f"Target: {target}")
    print_info(f"Variant: {variant}")
    print_info(f"Platform: {platform} ({SUPPORTED_PLATFORMS[platform]})")
    if args.dry_run:
        print_warning("DRY RUN - no changes will be made")
    print()

    success = True

    # 1. Create scaffolding structure
    print("--- Project Scaffolding ---")
    scaffolding = get_scaffolding_structure(variant, platform, date)
    for rel_path, content in scaffolding.items():
        if not write_file(target / rel_path, content, args.dry_run, args.force):
            success = False
    print()

    # 2. Create workspace (unless --no-workspace)
    if not args.no_workspace:
        print("--- Workspace Structure ---")
        workspace = get_workspace_structure(date)
        for rel_path, content in workspace.items():
            if not write_file(target / rel_path, content, args.dry_run, args.force):
                success = False
        print()

    # 3. Create .claude/ settings (for plugin)
    print("--- Claude Code Integration ---")
    settings_file = target / ".claude" / "settings.json"
    if not settings_file.exists() or args.force:
        settings = {
            "extraKnownMarketplaces": {
                "aisdlc": {"source": {"source": "github", "repo": GITHUB_REPO}}
            },
            "enabledPlugins": {f"{PLUGIN_NAME}@aisdlc": True}
        }
        if args.dry_run:
            print_info(f"Would create: {settings_file}")
        else:
            settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            print_success(f"Created {settings_file}")
    else:
        print_info(f"Exists: {settings_file}")
    print()

    # Summary
    print("=" * 64)
    if args.dry_run:
        print("  Dry run complete - no changes made")
    elif success:
        print("  Project scaffold created!")
        print()
        print("  Created structure:")
        print(f"    docs/requirements/         - Requirements templates")
        print(f"    docs/design/{variant}/     - Design with ADRs")
        print(f"    docs/TRACEABILITY_MATRIX.md")
        print(f"    src/{variant}/{platform}/  - Implementation")
        print(f"    src/{variant}/{platform}/IMPLEMENTATION.yaml  - Design binding")
        if not args.no_workspace:
            print(f"    .ai-workspace/             - Task management")
        print(f"    CLAUDE.md                  - Project guidance")
        print()
        print("  Next steps:")
        print("    1. Define requirements in docs/requirements/REQUIREMENTS.md")
        print("    2. Update docs/design/{variant}/requirements.yaml with REQ-* keys")
        print("    3. Run: python aisdlc-setup.py validate")
    else:
        print("  Init completed with errors")
    print()

    return 0 if success else 1


# =============================================================================
# Validate Command (REQ-TOOL-011)
# =============================================================================

def find_implementations(target: Path) -> List[Path]:
    """Find all IMPLEMENTATION.yaml files.

    Searches in:
    1. src/ directory (new opinionated structure)
    2. *-code/ directories at root (legacy structure)
    """
    implementations = []

    # New structure: src/{variant}/{platform}/IMPLEMENTATION.yaml
    src_dir = target / "src"
    if src_dir.exists():
        for impl_file in src_dir.rglob("IMPLEMENTATION.yaml"):
            implementations.append(impl_file)

    # Legacy structure: {platform}-code/IMPLEMENTATION.yaml (e.g., claude-code/)
    for platform_dir in target.glob("*-code"):
        if platform_dir.is_dir():
            impl_file = platform_dir / "IMPLEMENTATION.yaml"
            if impl_file.exists():
                implementations.append(impl_file)

    return implementations


def validate_implementation(target: Path, impl_file: Path, strict: bool) -> Tuple[int, int, int]:
    """Validate a single IMPLEMENTATION.yaml file.

    Returns: (passed, warnings, errors)
    """
    passed = 0
    warnings = 0
    errors = 0

    # Read and parse IMPLEMENTATION.yaml
    try:
        with open(impl_file, 'r') as f:
            content = f.read()
        impl = parse_yaml_simple(content)
    except Exception as e:
        print_error(f"Cannot parse {impl_file}: {e}")
        return 0, 0, 1

    print_success(f"IMPLEMENTATION.yaml exists")
    passed += 1

    # Check required fields
    variant = impl.get('variant')
    design_path = impl.get('design_path')
    platform = impl.get('platform')

    if not variant:
        print_error("Missing 'variant' field")
        errors += 1
    else:
        passed += 1

    if not design_path:
        print_error("Missing 'design_path' field")
        errors += 1
    else:
        # Validate design_path exists
        full_design_path = target / design_path
        if full_design_path.exists():
            print_success(f"design_path: {design_path}")
            passed += 1

            # Check required design artifacts
            required_artifacts = [
                "requirements.yaml",
                "AISDLC_IMPLEMENTATION_DESIGN.md",
            ]
            optional_artifacts = [
                "design.md",
            ]

            for artifact in required_artifacts:
                artifact_path = full_design_path / artifact
                if artifact_path.exists():
                    print_success(f"{artifact} exists")
                    passed += 1
                else:
                    print_error(f"Missing required: {artifact}")
                    errors += 1

            for artifact in optional_artifacts:
                artifact_path = full_design_path / artifact
                if artifact_path.exists():
                    print_success(f"{artifact} exists")
                    passed += 1
                else:
                    print_warning(f"Missing optional: {artifact}")
                    warnings += 1

            # Check ADRs directory
            adrs_dir = full_design_path / "adrs"
            if adrs_dir.exists():
                adr_files = list(adrs_dir.glob("ADR-*.md"))
                if adr_files:
                    print_success(f"adrs/ has {len(adr_files)} ADR(s)")
                    passed += 1
                else:
                    print_warning("adrs/ has no ADR files (expected ADR-*.md)")
                    warnings += 1
            else:
                print_warning("adrs/ directory missing")
                warnings += 1
        else:
            print_error(f"design_path does not exist: {design_path}")
            errors += 1

    if not platform:
        print_warning("Missing 'platform' field")
        warnings += 1
    else:
        passed += 1

    return passed, warnings, errors


def cmd_validate(args) -> int:
    """Validate design-implementation binding."""
    print_banner("Structure Validation")

    target = Path(args.target).resolve()
    print_info(f"Scanning: {target}")
    print()

    # Find implementations
    implementations = find_implementations(target)

    if not implementations:
        print_warning("No IMPLEMENTATION.yaml files found in src/")
        print_info("Run 'aisdlc-setup.py init' to create project structure")
        return 1

    print(f"Found {len(implementations)} implementation(s):")
    for impl in implementations:
        rel_path = impl.relative_to(target)
        print_info(f"  - {rel_path.parent}/")
    print()

    total_passed = 0
    total_warnings = 0
    total_errors = 0

    for impl_file in implementations:
        rel_path = impl_file.relative_to(target)
        variant_dir = impl_file.parent
        print(f"--- Validating: {variant_dir.relative_to(target)} ---")

        passed, warnings, errors = validate_implementation(target, impl_file, args.strict)
        total_passed += passed
        total_warnings += warnings
        total_errors += errors
        print()

    # Summary
    print("=" * 64)
    print(f"  Summary: {total_passed} passed, {total_warnings} warning(s), {total_errors} error(s)")

    if args.strict and total_warnings > 0:
        print_warning("Strict mode: treating warnings as errors")
        return 1

    return 0 if total_errors == 0 else 1


# =============================================================================
# Default Command (backward compatible)
# =============================================================================

def clear_plugin_cache(dry_run: bool) -> bool:
    """Clear cached plugin to ensure latest version is fetched."""
    cache_locations = [
        Path.home() / ".claude" / "plugins" / "marketplaces" / "aisdlc",
        Path.home() / ".claude" / "plugins" / "cache" / "aisdlc" / PLUGIN_NAME,
    ]

    found_any = False
    for cache_dir in cache_locations:
        if not cache_dir.exists():
            continue

        found_any = True
        if dry_run:
            print_info(f"Would remove: {cache_dir}")
            continue

        try:
            shutil.rmtree(cache_dir)
            print_success(f"Cleared: {cache_dir}")
        except Exception as e:
            print_warning(f"Could not clear {cache_dir}: {e}")

    if not found_any:
        print_info("No cached plugin found (fresh install)")

    return True


def setup_settings(target: Path, dry_run: bool) -> bool:
    """Create or update .claude/settings.json with plugin configuration."""
    settings_file = target / ".claude" / "settings.json"

    existing = {}
    if settings_file.exists():
        try:
            with open(settings_file, 'r') as f:
                existing = json.load(f)
        except json.JSONDecodeError:
            print_warning("Existing settings.json has invalid JSON, will overwrite")

    marketplace_config = {"source": "github", "repo": GITHUB_REPO}

    if "extraKnownMarketplaces" not in existing:
        existing["extraKnownMarketplaces"] = {}
    existing["extraKnownMarketplaces"]["aisdlc"] = {"source": marketplace_config}

    if "enabledPlugins" not in existing:
        existing["enabledPlugins"] = {}
    existing["enabledPlugins"][f"{PLUGIN_NAME}@aisdlc"] = True

    if dry_run:
        print_info(f"Would create: {settings_file}")
        return True

    settings_file.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_file, 'w') as f:
        json.dump(existing, f, indent=2)

    print_success(f"Created {settings_file}")
    return True


def setup_workspace(target: Path, dry_run: bool) -> bool:
    """Create .ai-workspace/ structure with templates."""
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    workspace_structure = get_workspace_structure(date)

    for rel_path, content in workspace_structure.items():
        file_path = target / rel_path

        if dry_run:
            print_info(f"Would create: {file_path}")
            continue

        file_path.parent.mkdir(parents=True, exist_ok=True)

        if not file_path.exists():
            with open(file_path, 'w') as f:
                f.write(content)
            print_success(f"Created {rel_path}")
        else:
            print_info(f"Exists: {rel_path}")

    return True


def cmd_default(args) -> int:
    """Default command: plugin + workspace setup (backward compatible)."""
    target = Path(args.target).resolve()

    version = get_plugin_version()
    print_banner("Project Setup", version)

    print_info(f"Target: {target}")
    print_info(f"Plugin: {PLUGIN_NAME} v{version}")
    print_info(f"Workspace: {'No' if args.no_workspace else 'Yes (with templates)'}")
    if args.dry_run:
        print_warning("DRY RUN - no changes will be made")
    print()

    success = True

    print("--- Plugin Cache ---")
    if not clear_plugin_cache(args.dry_run):
        success = False
    print()

    print("--- Plugin Configuration ---")
    if not setup_settings(target, args.dry_run):
        success = False
    print()

    if not args.no_workspace:
        print("--- Workspace Structure ---")
        if not setup_workspace(target, args.dry_run):
            success = False
        print()

    print("=" * 64)
    if args.dry_run:
        print("  Dry run complete - no changes made")
    elif success:
        print("  Setup complete!")
        print()
        print("  Next steps:")
        print("    1. Restart Claude Code to load plugin")
        print("    2. Run /aisdlc-help for full guide")
        print()
        print("  For full project scaffolding with design structure:")
        print("    python aisdlc-setup.py init --variant my_project_aisdlc --platform claude-code")
    else:
        print("  Setup completed with errors")
    print()

    return 0 if success else 1


# =============================================================================
# Main
# =============================================================================

def main():
    """Main entry point with subcommands."""
    parser = argparse.ArgumentParser(
        description="AI SDLC Method - Project Setup and Scaffolding",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Init subcommand
    init_parser = subparsers.add_parser(
        "init",
        help="Create full project scaffold with design-implementation structure"
    )
    init_parser.add_argument(
        "--variant", required=True,
        help="Variant name (e.g., my_project_aisdlc)"
    )
    init_parser.add_argument(
        "--platform", required=True,
        choices=list(SUPPORTED_PLATFORMS.keys()),
        help="Platform for implementation"
    )
    init_parser.add_argument("--target", default=".", help="Target directory")
    init_parser.add_argument("--dry-run", action="store_true", help="Preview changes")
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    init_parser.add_argument("--no-workspace", action="store_true", help="Skip .ai-workspace/")

    # Validate subcommand
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate design-implementation binding"
    )
    validate_parser.add_argument("--target", default=".", help="Target directory")
    validate_parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")

    # Default command arguments (for backward compatibility)
    parser.add_argument("--target", default=".", help="Target directory")
    parser.add_argument("--no-workspace", action="store_true", help="Skip .ai-workspace/")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes")

    args = parser.parse_args()

    if args.command == "init":
        return cmd_init(args)
    elif args.command == "validate":
        return cmd_validate(args)
    else:
        return cmd_default(args)


if __name__ == "__main__":
    sys.exit(main())
