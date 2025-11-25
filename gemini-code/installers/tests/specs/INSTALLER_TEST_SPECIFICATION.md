# Installer Test Specification

**Document Type**: Test Specification (BDD-style test cases)
**Version**: 1.0
**Date**: 2025-11-25
**Status**: Draft - For Review
**Location**: `tests/specs/` (per AI SDLC Section 8.4.3)

---

## AI SDLC Placement Rationale

Per AI SDLC methodology Section 8.4.3 (System Test Assets), test specifications are **test assets** that belong with tests, not in `docs/design/`:

| Asset Type | Location | Rationale |
|------------|----------|-----------|
| Requirements | `docs/requirements/` | Source of truth for REQ-* keys |
| Design | `docs/design/` | Architecture decisions, ADRs |
| **Test Specs** | `tests/specs/` | BDD scenarios tagged with REQ keys |
| Test Code | `tests/<module>/` | Actual test implementations |

Test specifications map 1:1 to requirements (REQ-* → TC-*) and are the "BDD Feature Files" equivalent for unit/integration tests.

---

## Purpose

This document defines the test cases for the AI SDLC Method installer system. It maps requirements to test cases and identifies coverage gaps.

---

## Requirements Coverage Matrix

| Requirement | Description | Test Status | Priority |
|-------------|-------------|-------------|----------|
| REQ-F-PLUGIN-001 | Plugin System with Marketplace | Planned | High |
| REQ-F-PLUGIN-002 | Federated Plugin Loading | Planned | High |
| REQ-F-PLUGIN-003 | Plugin Bundles | Planned | Medium |
| REQ-F-PLUGIN-004 | Plugin Versioning | Planned | High |
| REQ-F-CMD-001 | Slash Commands for Workflow | Planned | High |
| REQ-F-WORKSPACE-001 | Developer Workspace Structure | Planned | High |
| REQ-F-WORKSPACE-002 | Task Management Templates | Planned | High |
| REQ-F-WORKSPACE-003 | Session Tracking Templates | Planned | Medium |
| REQ-F-RESET-001 | Reset-Style Installation | Planned | Critical |
| REQ-F-UPDATE-001 | Framework Updates from GitHub | Planned | Medium |
| REQ-NFR-TRACE-001 | Full Lifecycle Traceability | Planned | Critical |
| REQ-NFR-TRACE-002 | Requirement Key Propagation | Planned | High |

---

## 1. Test Suite: common.py (Base Utilities)

### 1.1 InstallerBase Class Tests

#### TC-COM-001: validate_target - Valid Directory
**Validates**: REQ-F-WORKSPACE-001
```
Given: A valid existing directory path
When: validate_target() is called
Then: Returns True without error
```

#### TC-COM-002: validate_target - Non-existent Directory
**Validates**: REQ-F-WORKSPACE-001
```
Given: A path to a non-existent directory
When: validate_target() is called
Then: Returns False or raises appropriate error
```

#### TC-COM-003: validate_templates - Valid Templates
**Validates**: REQ-F-WORKSPACE-001
```
Given: A valid templates directory with required structure
When: validate_templates() is called
Then: Returns True
```

#### TC-COM-004: copy_directory - Normal Copy
**Validates**: REQ-F-WORKSPACE-001, REQ-F-CMD-001
```
Given: A source directory with files
And: An empty target directory
When: copy_directory() is called
Then: All files are copied preserving structure
And: File contents match source
```

#### TC-COM-005: copy_directory - Force Overwrite
**Validates**: REQ-F-WORKSPACE-001
```
Given: A source directory
And: A target directory with existing files
When: copy_directory() is called with force=True
Then: Existing files are overwritten
And: New structure matches source
```

#### TC-COM-006: copy_directory - Skip Existing
**Validates**: REQ-F-WORKSPACE-001
```
Given: A source directory
And: A target directory with existing files
When: copy_directory() is called with force=False
Then: Existing files are preserved (not overwritten)
And: Only new files are added
```

#### TC-COM-007: update_gitignore - Add Entries
**Validates**: REQ-F-WORKSPACE-001
```
Given: A .gitignore file (or no file)
And: A list of entries to add
When: update_gitignore() is called
Then: Entries are added under appropriate section
And: Duplicates are not added
And: File is properly formatted
```

#### TC-COM-008: backup_file - Creates Backup
**Validates**: REQ-F-RESET-001
```
Given: An existing file
When: backup_file() is called
Then: A timestamped backup is created
And: Original file is unchanged
And: Backup contains identical content
```

### 1.2 Version Utility Tests

#### TC-COM-009: get_ai_sdlc_version - From Git
**Validates**: REQ-F-PLUGIN-004
```
Given: Running in a git repository with tags
When: get_ai_sdlc_version() is called
Then: Returns the latest git tag (e.g., "v0.2.0")
```

#### TC-COM-010: get_ai_sdlc_version - No Git
**Validates**: REQ-F-PLUGIN-004
```
Given: Running outside a git repository
When: get_ai_sdlc_version() is called
Then: Returns "unknown" without error
```

#### TC-COM-011: get_latest_release_tag - From GitHub
**Validates**: REQ-F-UPDATE-001, REQ-F-RESET-001
```
Given: Network connectivity to GitHub
When: get_latest_release_tag() is called
Then: Returns the latest release tag from the repository
```

#### TC-COM-012: get_latest_release_tag - Network Error
**Validates**: REQ-F-RESET-001
```
Given: No network connectivity
When: get_latest_release_tag() is called
Then: Returns None
And: Does not raise exception
```

---

## 2. Test Suite: setup_workspace.py

### 2.1 WorkspaceSetup Class Tests

#### TC-WS-001: Full Workspace Installation
**Validates**: REQ-F-WORKSPACE-001
```
Given: An empty target directory
And: Valid templates directory
When: WorkspaceSetup.run() is called
Then: .ai-workspace/ directory is created
And: tasks/ subdirectories exist (todo/, active/, finished/, archive/)
And: session/ directory exists
And: templates/ directory exists with templates
And: config/ directory exists
```

#### TC-WS-002: Task Templates Installed
**Validates**: REQ-F-WORKSPACE-002
```
Given: A successful workspace installation
Then: TASK_TEMPLATE.md exists in templates/
And: FINISHED_TASK_TEMPLATE.md exists in templates/
And: ACTIVE_TASKS.md exists in tasks/active/
And: Templates contain TDD workflow elements
```

#### TC-WS-003: Session Templates Installed
**Validates**: REQ-F-WORKSPACE-003
```
Given: A successful workspace installation
Then: SESSION_TEMPLATE.md exists in templates/
And: PAIR_PROGRAMMING_GUIDE.md exists in templates/
And: current_session.md placeholder exists
```

#### TC-WS-004: Gitignore Updated
**Validates**: REQ-F-WORKSPACE-001
```
Given: A successful workspace installation
Then: .gitignore includes session/ directory
And: .gitignore includes *.bak files
```

#### TC-WS-005: Idempotent Installation
**Validates**: REQ-F-WORKSPACE-001
```
Given: An existing workspace installation
When: WorkspaceSetup.run() is called without force
Then: Existing files are not modified
And: No errors are raised
And: User is notified workspace exists
```

---

## 3. Test Suite: setup_commands.py

### 3.1 CommandsSetup Class Tests

#### TC-CMD-001: Full Commands Installation
**Validates**: REQ-F-CMD-001
```
Given: An empty target directory
And: Valid templates directory
When: CommandsSetup.run() is called
Then: .claude/commands/ directory is created
And: All command markdown files are installed
```

#### TC-CMD-002: Required Commands Present
**Validates**: REQ-F-CMD-001
```
Given: A successful commands installation
Then: aisdlc-checkpoint-tasks.md exists
And: aisdlc-finish-task.md exists
And: aisdlc-commit-task.md exists
And: aisdlc-status.md exists
And: aisdlc-release.md exists
And: aisdlc-refresh-context.md exists
```

#### TC-CMD-003: Agents Directory Installed
**Validates**: REQ-F-CMD-002
```
Given: A successful commands installation
Then: .claude/agents/ directory exists
And: aisdlc-requirements-agent.md exists
And: aisdlc-design-agent.md exists
And: aisdlc-tasks-agent.md exists
And: aisdlc-code-agent.md exists
And: aisdlc-system-test-agent.md exists
And: aisdlc-uat-agent.md exists
And: aisdlc-runtime-feedback-agent.md exists
```

#### TC-CMD-004: Force Overwrite Commands
**Validates**: REQ-F-CMD-001
```
Given: Existing commands with modifications
When: CommandsSetup.run() is called with force=True
Then: Commands are overwritten with fresh versions
And: Modifications are lost
```

---

## 4. Test Suite: setup_plugins.py

### 4.1 Plugin Discovery Tests

#### TC-PLG-001: Discover Available Plugins
**Validates**: REQ-F-PLUGIN-001
```
Given: A valid plugins directory
When: PluginsSetup._discover_plugins() is called
Then: Returns list of available plugins
And: Each plugin has valid metadata
And: Plugin list includes core plugins (aisdlc-core, aisdlc-methodology)
```

#### TC-PLG-002: List Plugins and Bundles
**Validates**: REQ-F-PLUGIN-003
```
Given: A PluginsSetup instance
When: list_plugins_and_bundles() is called
Then: Displays available plugins with descriptions
And: Displays available bundles (startup, datascience, qa, enterprise)
And: Bundles show their included plugins
```

### 4.2 Bundle Installation Tests

#### TC-PLG-003: Install Startup Bundle
**Validates**: REQ-F-PLUGIN-003
```
Given: An empty target directory
When: PluginsSetup.run() is called with bundle="startup"
Then: aisdlc-core plugin is installed
And: aisdlc-methodology plugin is installed
And: principles-key plugin is installed
```

#### TC-PLG-004: Install Enterprise Bundle
**Validates**: REQ-F-PLUGIN-003
```
Given: An empty target directory
When: PluginsSetup.run() is called with bundle="enterprise"
Then: All plugins are installed
And: Plugin count >= 8
```

#### TC-PLG-005: Bundle Deduplication
**Validates**: REQ-F-PLUGIN-003
```
Given: Installing multiple bundles with overlapping plugins
When: Plugins are installed
Then: Each plugin is installed only once
And: No duplicate directories
```

### 4.3 Plugin Installation Tests

#### TC-PLG-006: Install Individual Plugin
**Validates**: REQ-F-PLUGIN-001
```
Given: An empty target directory
When: PluginsSetup.run() is called with plugins="aisdlc-core"
Then: aisdlc-core plugin directory is created
And: .claude-plugin/plugin.json exists
And: Plugin files are complete
```

#### TC-PLG-007: Global Plugin Installation
**Validates**: REQ-F-PLUGIN-002
```
Given: Global installation flag
When: PluginsSetup.run() is called with global=True
Then: Plugins are installed to ~/.config/claude/plugins/
And: Project directory is not modified
```

#### TC-PLG-008: Project Plugin Installation
**Validates**: REQ-F-PLUGIN-002
```
Given: No global flag
When: PluginsSetup.run() is called
Then: Plugins are installed to ./.claude/plugins/
And: Global directory is not modified
```

### 4.4 Plugin Versioning Tests

#### TC-PLG-009: Plugin Version in Metadata
**Validates**: REQ-F-PLUGIN-004
```
Given: An installed plugin
Then: plugin.json contains version field
And: Version follows semver format (major.minor.patch)
```

#### TC-PLG-010: Plugin Dependencies Declared
**Validates**: REQ-F-PLUGIN-004
```
Given: An installed bundle plugin
Then: plugin.json may contain dependencies field
And: Dependencies reference valid plugin names
```

---

## 5. Test Suite: setup_reset.py

### 5.1 Reset Workflow Tests

#### TC-RST-001: Dry Run Mode
**Validates**: REQ-F-RESET-001
```
Given: An existing installation
When: ResetInstaller.run() is called with dry_run=True
Then: No files are modified
And: Plan is displayed showing what would happen
And: User can see preserve/remove lists
```

#### TC-RST-002: Preserve Active Tasks
**Validates**: REQ-F-RESET-001
```
Given: An existing installation with active tasks
When: ResetInstaller.run() is called
Then: .ai-workspace/tasks/active/ is preserved
And: ACTIVE_TASKS.md is unchanged
And: Task content is identical before and after
```

#### TC-RST-003: Preserve Finished Tasks
**Validates**: REQ-F-RESET-001
```
Given: An existing installation with finished tasks
When: ResetInstaller.run() is called
Then: .ai-workspace/tasks/finished/ is preserved
And: All finished task files are unchanged
```

#### TC-RST-004: Remove Old Commands
**Validates**: REQ-F-RESET-001
```
Given: An existing installation with obsolete commands
When: ResetInstaller.run() is called
Then: .claude/commands/ is completely removed
And: Fresh commands are installed
And: Obsolete commands no longer exist
```

#### TC-RST-005: Remove Old Agents
**Validates**: REQ-F-RESET-001
```
Given: An existing installation with old agent files
When: ResetInstaller.run() is called
Then: .claude/agents/ is completely removed
And: Fresh agents are installed
```

#### TC-RST-006: Create Backup
**Validates**: REQ-F-RESET-001
```
Given: An existing installation
When: ResetInstaller.run() is called (without --no-backup)
Then: Backup is created in temp directory
And: Backup path is displayed
And: Backup contains .claude/ and .ai-workspace/
```

#### TC-RST-007: Reset to Specific Version
**Validates**: REQ-F-RESET-001, REQ-F-UPDATE-001
```
Given: Network access to GitHub
When: ResetInstaller.run() is called with version="v0.1.0"
Then: Files from v0.1.0 tag are installed
And: Version is displayed in summary
```

#### TC-RST-008: Reset from Local Source
**Validates**: REQ-F-RESET-001
```
Given: A local ai_sdlc_method source directory
When: ResetInstaller.run() is called with source="/path/to/source"
Then: Files from local source are installed
And: No GitHub access is required
```

### 5.2 Error Handling Tests

#### TC-RST-009: Invalid Target Directory
**Validates**: REQ-F-RESET-001
```
Given: A non-existent target directory
When: ResetInstaller.run() is called
Then: Error is displayed
And: No files are modified
And: Exit code is non-zero
```

#### TC-RST-010: Invalid Version Tag
**Validates**: REQ-F-RESET-001
```
Given: An invalid version tag
When: ResetInstaller.run() is called
Then: Error is displayed about invalid version
And: No files are modified
```

#### TC-RST-011: Network Failure During Clone
**Validates**: REQ-F-RESET-001
```
Given: Network failure during git clone
When: ResetInstaller.run() is called
Then: Error is displayed
And: Partial files are cleaned up
And: Original installation is unchanged (backup exists)
```

---

## 6. Test Suite: setup_all.py

### 6.1 Orchestration Tests

#### TC-ALL-001: Full Installation
**Validates**: REQ-F-WORKSPACE-001, REQ-F-CMD-001
```
Given: An empty target directory
When: AISDLCSetup.run() is called
Then: .ai-workspace/ is installed
And: .claude/ is installed
And: CLAUDE.md is created
And: Summary shows success
```

#### TC-ALL-002: Installation with Plugins
**Validates**: REQ-F-PLUGIN-001
```
Given: An empty target directory
When: AISDLCSetup.run() is called with with_plugins=True
Then: Workspace is installed
And: Commands are installed
And: Plugins are installed
```

#### TC-ALL-003: Reset Mode Delegation
**Validates**: REQ-F-RESET-001
```
Given: An existing installation
When: AISDLCSetup.run() is called with reset=True
Then: _run_reset_installer() is called
And: Reset workflow is executed
```

#### TC-ALL-004: Workspace Only Mode
**Validates**: REQ-F-WORKSPACE-001
```
Given: workspace_only=True flag
When: AISDLCSetup.run() is called
Then: Only workspace is installed
And: Commands are not installed
And: Plugins are not installed
```

#### TC-ALL-005: Commands Only Mode
**Validates**: REQ-F-CMD-001
```
Given: commands_only=True flag
When: AISDLCSetup.run() is called
Then: Only commands are installed
And: Workspace is not installed
And: Plugins are not installed
```

### 6.2 Argument Parsing Tests

#### TC-ALL-006: Parse Target Argument
**Validates**: All
```
Given: --target /path/to/project argument
When: Arguments are parsed
Then: target is set to /path/to/project
```

#### TC-ALL-007: Parse Reset Arguments
**Validates**: REQ-F-RESET-001
```
Given: --reset --version v0.2.0 arguments
When: Arguments are parsed
Then: reset is True
And: version is "v0.2.0"
```

#### TC-ALL-008: Conflicting Arguments
**Validates**: All
```
Given: --workspace-only and --commands-only together
When: Arguments are parsed
Then: Error is displayed about conflicting options
Or: Both options are honored independently
```

---

## 7. Test Suite: aisdlc-reset.py (Standalone)

### 7.1 Self-Contained Operation Tests

#### TC-CURL-001: No External Dependencies
**Validates**: REQ-F-RESET-001
```
Given: The aisdlc-reset.py file
When: File is analyzed
Then: Only standard library imports are used
And: No imports from common.py
And: File can run standalone
```

#### TC-CURL-002: Latest Version Fetch
**Validates**: REQ-F-UPDATE-001
```
Given: No version argument
When: aisdlc-reset.py is executed
Then: Latest release tag is fetched from GitHub
And: Tag is displayed in banner
```

#### TC-CURL-003: Specific Version Install
**Validates**: REQ-F-RESET-001
```
Given: --version v0.1.0 argument
When: aisdlc-reset.py is executed
Then: v0.1.0 tag is cloned and installed
```

#### TC-CURL-004: Dry Run Output
**Validates**: REQ-F-RESET-001
```
Given: --dry-run argument
When: aisdlc-reset.py is executed
Then: Plan is shown
And: "No changes were made" message appears
And: Files are unchanged
```

---

## 8. Test Suite: validate_traceability.py

### 8.1 Requirement Extraction Tests

#### TC-TRC-001: Extract REQ-* Patterns
**Validates**: REQ-NFR-TRACE-001
```
Given: Requirements document with REQ-F-*, REQ-NFR-* patterns
When: extract_requirements() is called
Then: All requirement keys are extracted
And: Count matches expected requirements
```

#### TC-TRC-002: Extract Implements Tags
**Validates**: REQ-NFR-TRACE-002
```
Given: Code files with "# Implements: REQ-*" comments
When: extract_code_refs() is called
Then: All implementation references are found
And: File paths are included
```

#### TC-TRC-003: Extract Validates Tags
**Validates**: REQ-NFR-TRACE-002
```
Given: Test files with "# Validates: REQ-*" comments
When: extract_test_refs() is called
Then: All test references are found
And: Test file paths are included
```

### 8.2 Matrix Generation Tests

#### TC-TRC-004: Generate Traceability Matrix
**Validates**: REQ-NFR-TRACE-001
```
Given: Requirements, code, and test files
When: generate_traceability_matrix() is called
Then: Matrix shows requirement → design → code → test mapping
And: Coverage percentages are calculated
And: Missing coverage is highlighted
```

---

## 9. Identified Gaps

### 9.1 Requirements Without Implementation

| Gap ID | Description | Missing Requirement |
|--------|-------------|---------------------|
| GAP-001 | Plugin version conflict detection | REQ-F-PLUGIN-004 partial |
| GAP-002 | /aisdlc-update command | REQ-F-UPDATE-001 command |
| GAP-003 | Test generation on gaps | REQ-F-TESTING-002 |

### 9.2 Implementation Without Tests

| Gap ID | Component | Lines of Code | Test Coverage |
|--------|-----------|---------------|---------------|
| GAP-T01 | common.py | 271 | 0% |
| GAP-T02 | setup_workspace.py | 183 | 0% |
| GAP-T03 | setup_commands.py | 188 | 0% |
| GAP-T04 | setup_plugins.py | 415 | 0% |
| GAP-T05 | setup_reset.py | 593 | 0% |
| GAP-T06 | setup_all.py | 558 | 0% |
| GAP-T07 | aisdlc-reset.py | 389 | 0% |
| GAP-T08 | validate_traceability.py | 586 | 0% |
| **TOTAL** | | **3,183** | **0%** |

### 9.3 Recommendations

1. **Critical Priority**: Create tests for setup_reset.py (REQ-F-RESET-001)
   - Most complex installer with preservation logic
   - Highest risk of data loss if bugs exist

2. **High Priority**: Create tests for common.py
   - Base class used by all installers
   - Testing here provides coverage foundation

3. **Medium Priority**: Create tests for individual installers
   - setup_workspace.py
   - setup_commands.py
   - setup_plugins.py

4. **Integration Tests**: Create tests for setup_all.py
   - End-to-end installation scenarios
   - Reset mode integration

---

## 10. Test Implementation Plan

### Phase 1: Foundation (common.py)
- TC-COM-001 through TC-COM-012
- Estimated: 12 test cases

### Phase 2: Core Installers
- TC-WS-001 through TC-WS-005 (workspace)
- TC-CMD-001 through TC-CMD-004 (commands)
- Estimated: 9 test cases

### Phase 3: Reset Installer (Critical)
- TC-RST-001 through TC-RST-011
- Estimated: 11 test cases

### Phase 4: Plugin System
- TC-PLG-001 through TC-PLG-010
- Estimated: 10 test cases

### Phase 5: Orchestrator
- TC-ALL-001 through TC-ALL-008
- Estimated: 8 test cases

### Phase 6: Traceability
- TC-TRC-001 through TC-TRC-004
- Estimated: 4 test cases

**Total Planned Test Cases**: 54

---

## Appendix A: Test File Structure

```
tests/
├── installers/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── test_common.py           # TC-COM-*
│   ├── test_setup_workspace.py  # TC-WS-*
│   ├── test_setup_commands.py   # TC-CMD-*
│   ├── test_setup_plugins.py    # TC-PLG-*
│   ├── test_setup_reset.py      # TC-RST-*
│   ├── test_setup_all.py        # TC-ALL-*
│   ├── test_aisdlc_reset.py     # TC-CURL-*
│   └── test_validate_traceability.py  # TC-TRC-*
└── fixtures/
    ├── sample_workspace/        # Sample workspace for tests
    ├── sample_commands/         # Sample commands for tests
    └── sample_plugins/          # Sample plugins for tests
```

---

## Appendix B: Test Command Reference

```bash
# Run all installer tests
pytest tests/installers/ -v

# Run specific test suite
pytest tests/installers/test_setup_reset.py -v

# Run with coverage
pytest tests/installers/ -v --cov=installers --cov-report=html

# Run specific test case
pytest tests/installers/test_common.py::test_validate_target_valid_directory -v
```

---

**Document Status**: Draft - For Review
**Next Action**: Review test cases, identify missing scenarios, then implement
