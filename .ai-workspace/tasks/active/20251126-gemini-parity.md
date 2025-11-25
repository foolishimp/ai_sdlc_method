# Gemini Parity with Claude-Code

**ID:** 20251126-gemini-parity

## Goal

Achieve parity between the `gemini-code` and `claude-code` implementations of the AI SDLC methodology.

## Plan

This will be done by replicating the functionality of the `claude-code` components for the `gemini-code` environment. Each of the tables below represents a major component of the work required.

### Agents

| Agent | Claude-Code Status | Gemini-Code Status | Notes |
| :--- | :--- | :--- | :--- |
| `aisdlc-code-agent` | ✅ Done | ⬜ ToDo | |
| `aisdlc-design-agent` | ✅ Done | ⬜ ToDo | |
| `aisdlc-requirements-agent` | ✅ Done | ⬜ ToDo | |
| `aisdlc-runtime-feedback-agent` | ✅ Done | ⬜ ToDo | |
| `aisdlc-system-test-agent` | ✅ Done | ⬜ ToDo | |
| `aisdlc-tasks-agent` | ✅ Done | ⬜ ToDo | |
| `aisdlc-uat-agent` | ✅ Done | ⬜ ToDo | |

### Commands

| Command | Claude-Code Status | Gemini-Code Status | Notes |
| :--- | :--- | :--- | :--- |
| `aisdlc-checkpoint-tasks` | ✅ Done | ⬜ ToDo | |
| `aisdlc-commit-task` | ✅ Done | ⬜ ToDo | |
| `aisdlc-finish-task` | ✅ Done | ⬜ ToDo | |
| `aisdlc-refresh-context` | ✅ Done | ⬜ ToDo | |
| `aisdlc-release` | ✅ Done | ⬜ ToDo | |
| `aisdlc-status` | ✅ Done | ⬜ ToDo | |

### Installers

| Installer | Claude-Code Status | Gemini-Code Status | Notes |
| :--- | :--- | :--- | :--- |
| `aisdlc-reset.py` | ✅ Done | ⬜ ToDo | |
| `common.py` | ✅ Done | ⬜ ToDo | |
| `setup_all.py` | ✅ Done | ⬜ ToDo | |
| `setup_commands.py` | ✅ Done | ⬜ ToDo | |
| `setup_plugins.py` | ✅ Done | ⬜ ToDo | |
| `setup_reset.py` | ✅ Done | ⬜ ToDo | |
| `setup_workspace.py` | ✅ Done | ⬜ ToDo | |
| `validate_traceability.py`| ✅ Done | ⬜ ToDo | |

### Plugins

| Plugin | Claude-Code Status | Gemini-Code Status | Notes |
| :--- | :--- | :--- | :--- |
| `aisdlc-core` | ✅ Done | 🟡 In Progress | Scaffolding complete, skills defined. |
| `aisdlc-methodology` | ✅ Done | 🟡 In Progress | Scaffolding complete. |
| `bundles` | ✅ Done | ⬜ ToDo | |
| `code-skills` | ✅ Done | ⬜ ToDo | |
| `design-skills` | ✅ Done | ⬜ ToDo | |
| `principles-key` | ✅ Done | ⬜ ToDo | |
| `python-standards` | ✅ Done | ⬜ ToDo | |
| `requirements-skills` | ✅ Done | ⬜ ToDo | |
| `runtime-skills` | ✅ Done | ⬜ ToDo | |
| `testing-skills` | ✅ Done | ⬜ ToDo | |

### Project Template

| Template File/Directory | Claude-Code Status | Gemini-Code Status | Notes |
| :--- | :--- | :--- | :--- |
| `CLAUDE.md.template` | ✅ Done | ✅ Done | Create `GEMINI.md.template` |
| `.ai-workspace/` | ✅ Done | ✅ Done | |
| `.claude/` | ✅ Done | ✅ Done | Create `.gemini/` equivalent |
| `docs/` | ✅ Done | ✅ Done | |
| `requirements/` | ✅ Done | ✅ Done | |
| `src/` | ✅ Done | ✅ Done | |
| `tests/` | ✅ Done | ✅ Done | |
