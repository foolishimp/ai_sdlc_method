# TCS-009: aisdlc-setup.py Installer

**Status**: 📋 Specified
**Date**: 2025-11-27
**Requirements**: REQ-F-WORKSPACE-001, REQ-F-PLUGIN-001
**ADR Reference**: [ADR-006](../adrs/ADR-006-plugin-configuration-and-discovery.md)
**Implementation**: `claude-code/installers/aisdlc-setup.py`

---

## Purpose

Validate that the one-line installer correctly sets up AISDLC plugins, workspace, and hooks in a project directory.

---

## Installation Command

```bash
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 -
```

---

## Preconditions

- Python 3.6+ installed
- Write access to project directory
- Internet connectivity (for curl and GitHub source)

---

## Test Scenarios

### Basic Installation

| ID | Scenario | Command | Expected Output | Priority |
|----|----------|---------|-----------------|----------|
| IN-001 | Default install | `... \| python3 -` | Creates .claude/settings.json with startup bundle | High |
| IN-002 | All plugins | `... \| python3 - --all` | Enables all 9 plugins | High |
| IN-003 | Enterprise bundle | `... \| python3 - --bundle enterprise` | Enables enterprise bundle | Medium |
| IN-004 | Dry run | `... \| python3 - --dry-run` | Shows preview, no files written | High |

### Workspace Installation

| ID | Scenario | Command | Expected Output | Priority |
|----|----------|---------|-----------------|----------|
| IN-005 | With workspace | `... --workspace` | Creates .ai-workspace/ structure | High |
| IN-006 | Workspace files | `... --workspace` | ACTIVE_TASKS.md created | High |
| IN-007 | Finished dir | `... --workspace` | tasks/finished/ created | Medium |

### Hooks Installation

| ID | Scenario | Command | Expected Output | Priority |
|----|----------|---------|-----------------|----------|
| IN-008 | With hooks | `... --hooks` | Hooks added to settings.json | High |
| IN-009 | Hook types | `... --hooks` | 4 hook types configured | Medium |
| IN-010 | No duplicate hooks | `... --hooks` (twice) | Hooks not duplicated | Medium |

### Combined Options

| ID | Scenario | Command | Expected Output | Priority |
|----|----------|---------|-----------------|----------|
| IN-011 | Full setup | `... --workspace --hooks --all` | Everything installed | High |
| IN-012 | Target dir | `... --target /path` | Installs to specified path | Medium |

### Error Handling

| ID | Scenario | Command | Expected Output | Priority |
|----|----------|---------|-----------------|----------|
| IN-013 | No write access | Permission denied | Error message shown | High |
| IN-014 | Existing settings | settings.json exists | Merges with existing | High |
| IN-015 | Invalid bundle | `--bundle invalid` | Error: invalid bundle name | Medium |

---

## Validation Criteria

### Settings File (.claude/settings.json)
- [ ] File created at correct path
- [ ] Valid JSON format
- [ ] extraKnownMarketplaces configured
- [ ] enabledPlugins configured
- [ ] Existing settings preserved (merged)

### Marketplace Configuration
- [ ] Source: github
- [ ] Repo: foolishimp/ai_sdlc_method
- [ ] Path: claude-code/plugins

### Plugin Bundles
- [ ] startup: aisdlc-core, aisdlc-methodology, principles-key
- [ ] enterprise: all 9 plugins
- [ ] qa: testing-skills, code-skills, requirements-skills, runtime-skills
- [ ] datascience: aisdlc-core, testing-skills, python-standards, runtime-skills

### Workspace Structure (--workspace)
- [ ] .ai-workspace/ created
- [ ] tasks/active/ created
- [ ] tasks/finished/ created
- [ ] ACTIVE_TASKS.md created with template content
- [ ] Timestamp in ACTIVE_TASKS.md

### Hooks (--hooks)
- [ ] SessionStart hook configured
- [ ] Stop hook configured
- [ ] PreToolUse (Bash) hook configured
- [ ] PostToolUse (Edit) hook configured
- [ ] AISDLC marker in hook commands

---

## Expected Settings.json Output

```json
{
  "extraKnownMarketplaces": {
    "aisdlc": {
      "source": {
        "source": "github",
        "repo": "foolishimp/ai_sdlc_method",
        "path": "claude-code/plugins"
      }
    }
  },
  "enabledPlugins": {
    "aisdlc-core@aisdlc": true,
    "aisdlc-methodology@aisdlc": true,
    "principles-key@aisdlc": true
  },
  "hooks": {
    "SessionStart": [...],
    "Stop": [...],
    "PreToolUse": [...],
    "PostToolUse": [...]
  }
}
```

---

## Test Implementation

**Status**: 📋 Not yet implemented

Manual validation steps:

```bash
# Create temp directory
mkdir -p /tmp/test-aisdlc && cd /tmp/test-aisdlc

# Test dry run
python /path/to/aisdlc-setup.py --dry-run

# Test basic install
python /path/to/aisdlc-setup.py
cat .claude/settings.json

# Test with workspace and hooks
rm -rf .claude .ai-workspace
python /path/to/aisdlc-setup.py --workspace --hooks
ls -la .ai-workspace/tasks/

# Cleanup
cd /tmp && rm -rf test-aisdlc
```

---

## Requirement Traceability

| Requirement | How Validated |
|-------------|---------------|
| REQ-F-WORKSPACE-001 | Workspace structure created correctly |
| REQ-F-PLUGIN-001 | Plugin configuration set up correctly |

---

## Notes

- Self-contained script - no external dependencies beyond standard library
- Works via curl pipe to python
- Idempotent - safe to run multiple times
- Preserves existing configuration (merges, doesn't overwrite)
