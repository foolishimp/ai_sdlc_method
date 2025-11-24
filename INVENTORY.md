# AI SDLC Method - Component Inventory

**Version:** 2.0.0
**Last Updated:** 2025-11-24
**Purpose:** Track all deployable components, versions, and dependencies

> **📊 Auto-Generation Available**
> Per our methodology (REQ-NFR-TRACE-001), this can be auto-generated:
> ```bash
> python installers/validate_traceability.py --inventory > INVENTORY.md
> ```
> The Requirements Agent generates:
> - `docs/TRACEABILITY_MATRIX.md` - Requirement-level coverage (20 implementation requirements)
> - `INVENTORY.md` - Component-level inventory (generated from filesystem scan)
>
> This document is currently maintained manually for version history and deployment guidance.
> Component counts and requirement mappings can be regenerated from actual code.

---

## Overview

The AI SDLC Method consists of 4 major component categories:

1. **Templates** - Foundation structure for project workspaces
2. **Plugins** - Claude Code plugins with 7-stage SDLC methodology
3. **Installers** - Python scripts for offline/CI/CD deployment
4. **Marketplace** - Plugin registry for Claude Code discovery

---

## 1. Templates (`templates/claude/`)

**Version:** 2.0.0
**Location:** `/templates/claude/`
**Purpose:** Base structure deployed to each project
**Update Method:** Python installers

### 1.1 Workspace Templates

```
templates/claude/.ai-workspace/
├── README.md                                    # v2.0.0 - Workspace guide
├── config/
│   └── workspace_config.yml                     # v2.0.0 - Workspace configuration
├── tasks/
│   ├── todo/
│   │   └── TODO_LIST.md                         # v2.0.0 - Quick capture template
│   ├── active/
│   │   └── ACTIVE_TASKS.md                      # v2.0.0 - Formal tasks template
│   ├── finished/                                # (empty - for completed task docs)
│   └── archive/                                 # (empty - for old tasks)
└── templates/
    ├── TASK_TEMPLATE.md                         # v2.0.0 - Task creation template
    ├── FINISHED_TASK_TEMPLATE.md                # v2.0.0 - Completion documentation
    ├── SESSION_TEMPLATE.md                      # v2.0.0 - Development session template
    ├── SESSION_STARTER.md                       # v2.0.0 - Session startup checklist
    ├── PAIR_PROGRAMMING_GUIDE.md                # v2.0.0 - AI pair programming patterns
    └── AISDLC_METHOD_REFERENCE.md               # v2.0.0 - Context refresh for Claude ⭐ NEW
```

**File Count:** 12 files
**Total Lines:** ~1,100 lines

### 1.2 Command Templates

```
templates/claude/.claude/commands/
├── aisdlc-start-session.md                      # v2.0.0 - Start development session
├── aisdlc-status.md                             # v2.0.0 - Show 7-stage SDLC status
├── aisdlc-checkpoint-tasks.md                   # v2.0.0 - Auto-update task status
├── aisdlc-refresh-context.md                    # v2.0.0 - Refresh Claude's context ⭐ NEW
├── aisdlc-todo.md                               # v2.0.0 - Quick todo capture
├── aisdlc-finish-task.md                        # v2.0.0 - Complete task with docs
├── aisdlc-commit-task.md                        # v2.0.0 - Generate commit message
├── apply-persona.md                             # v2.0.0 - Apply development persona
├── switch-persona.md                            # v2.0.0 - Switch persona
├── list-personas.md                             # v2.0.0 - List available personas
├── persona-checklist.md                         # v2.0.0 - Persona-specific checklist
├── current-context.md                           # v2.0.0 - Show current context
├── load-context.md                              # v2.0.0 - Load project configuration
├── switch-context.md                            # v2.0.0 - Switch project context
├── show-full-context.md                         # v2.0.0 - Show complete context
├── list-projects.md                             # v2.0.0 - List available projects
└── .claude/hooks.json                           # v2.0.0 - Claude Code hooks config
```

**File Count:** 17 commands
**Total Lines:** ~320 lines

### 1.3 Agent Templates

```
templates/claude/.claude/agents/
├── requirements-agent.md                        # v2.0.0 - Requirements Stage agent (10,093 lines)
├── design-agent.md                              # v2.0.0 - Design Stage agent (1,263 lines)
├── tasks-agent.md                               # v2.0.0 - Tasks Stage agent (867 lines)
├── code-agent.md                                # v2.0.0 - Code Stage agent (10,775 lines)
├── system-test-agent.md                         # v2.0.0 - System Test Stage agent (860 lines)
├── uat-agent.md                                 # v2.0.0 - UAT Stage agent (817 lines)
└── runtime-feedback-agent.md                    # v2.0.0 - Runtime Feedback Stage agent (1,208 lines)
```

**File Count:** 7 agents (one per SDLC stage)
**Total Lines:** ~25,883 lines

### 1.4 Project Template

```
templates/claude/
├── CLAUDE.md.template                           # v2.0.0 - Project guidance template
└── README.md                                    # v2.0.0 - Template documentation
```

**Total Template Files:** 38 files
**Total Template Lines:** ~27,400 lines

---

## 2. Plugins (`plugins/`)

**Version:** 2.0.0
**Location:** `/plugins/`
**Purpose:** Claude Code plugins with SDLC methodology
**Update Method:** Claude marketplace or Python installers

### 2.1 Core Plugins

#### aisdlc-methodology v2.0.0 ⭐

**Description:** Complete 7-Stage AI SDLC Methodology
**Path:** `plugins/aisdlc-methodology/`
**Dependencies:** None (foundation plugin)

**Contents:**
```
plugins/aisdlc-methodology/
├── .claude-plugin/
│   └── plugin.json                              # Plugin metadata
├── config/
│   ├── stages_config.yml                        # v2.0.0 - 7-stage agent specs (1,273 lines)
│   └── config.yml                               # v2.0.0 - Key Principles + Code stage
├── docs/
│   ├── principles/
│   │   └── KEY_PRINCIPLES.md                    # v2.0.0 - The 7 core principles
│   └── processes/
│       └── TDD_WORKFLOW.md                      # v2.0.0 - TDD cycle documentation
└── README.md                                    # v2.0.0 - Plugin overview
```

**Key Features:**
- 7-stage AI SDLC (Requirements → Design → Tasks → Code → System Test → UAT → Runtime Feedback)
- AI agent configurations (1,273 lines)
- Key Principles principles (TDD, Fail Fast, Modular, etc.)
- Requirement traceability (REQ-* keys)
- TDD workflow (RED → GREEN → REFACTOR)
- BDD testing (Given/When/Then)

**Version History:**
- v2.0.0 (2025-11-14): Added complete 7-stage AI SDLC methodology
- v1.0.0 (2025-10-16): Initial release with Key Principles + TDD workflow

#### aisdlc-core v1.0.0

**Description:** Core AI SDLC framework
**Path:** `plugins/aisdlc-core/`
**Dependencies:** None

**Status:** Foundation for all other plugins

### 2.2 Standards Plugins

#### python-standards v1.0.0

**Description:** Python language standards (PEP 8, pytest, type hints)
**Path:** `plugins/python-standards/`
**Dependencies:** `aisdlc-methodology` v2.0.0+

**Contents:**
- PEP 8 style guidelines
- pytest testing practices
- Type hints and documentation standards
- Python tooling (black, mypy, pylint)

#### principles-key v1.0.0

**Description:** Core development principles
**Path:** `plugins/principles-key/`
**Dependencies:** `aisdlc-methodology` v2.0.0+

**The 7 Key Principles:**
1. Test Driven Development
2. Fail Fast & Root Cause
3. Modular & Maintainable
4. Reuse Before Build
5. Open Source First
6. No Legacy Baggage
7. Perfectionist Excellence

### 2.3 Skills Plugins

#### testing-skills v1.0.0
**Path:** `plugins/testing-skills/`
**Dependencies:** `aisdlc-methodology`
**Purpose:** Advanced testing patterns (unit, integration, E2E)

#### code-skills v1.0.0
**Path:** `plugins/code-skills/`
**Dependencies:** `aisdlc-methodology`
**Purpose:** Code quality and refactoring patterns

#### design-skills v1.0.0
**Path:** `plugins/design-skills/`
**Dependencies:** `aisdlc-methodology`
**Purpose:** Architecture and design patterns

#### requirements-skills v1.0.0
**Path:** `plugins/requirements-skills/`
**Dependencies:** `aisdlc-methodology`
**Purpose:** Requirements engineering and elicitation

#### runtime-skills v1.0.0
**Path:** `plugins/runtime-skills/`
**Dependencies:** `aisdlc-methodology`
**Purpose:** Deployment, monitoring, and observability

### 2.4 Plugin Bundles

**Path:** `plugins/bundles/`

#### startup Bundle
**Plugins:** aisdlc-core, aisdlc-methodology, principles-key
**Purpose:** Essential plugins for getting started
**Recommended For:** All new projects

#### datascience Bundle
**Plugins:** aisdlc-core, aisdlc-methodology, python-standards, testing-skills
**Purpose:** ML and data science projects
**Recommended For:** Data science teams

#### qa Bundle
**Plugins:** aisdlc-methodology, testing-skills, code-skills, python-standards
**Purpose:** Quality assurance focus
**Recommended For:** QA engineers

#### enterprise Bundle
**Plugins:** All plugins
**Purpose:** Complete suite
**Recommended For:** Enterprise teams

**Total Plugins:** 10 plugins + 4 bundles

---

## 3. Installers (`installers/`)

**Version:** 1.0.0
**Location:** `/installers/`
**Purpose:** Python scripts for offline/CI/CD deployment
**Language:** Python 3.8+

### 3.1 Installer Scripts

```
installers/
├── setup_all.py                                 # v1.0.0 - Main orchestrator (all-in-one)
├── setup_workspace.py                           # v1.0.0 - Deploy .ai-workspace/
├── setup_commands.py                            # v1.0.0 - Deploy .claude/commands/
├── setup_plugins.py                             # v1.0.0 - Deploy plugins
├── common.py                                    # v1.0.0 - Shared utilities
├── validate_traceability.py                     # v1.0.0 - Verify REQ-* tagging
└── README.md                                    # v1.0.0 - Installer documentation
```

**Total Scripts:** 6 Python files
**Total Lines:** ~2,500 lines

### 3.2 Installation Methods

| Method | Use Case | Network Required | Pros | Cons |
|--------|----------|-----------------|------|------|
| `setup_all.py` | Complete setup | No | One command, offline | Manual updates |
| `setup_workspace.py` | Workspace only | No | Lightweight | No plugins |
| `setup_commands.py` | Commands only | No | Quick refresh | No workspace |
| `setup_plugins.py` | Plugins only | No | Flexible | Requires workspace separately |
| Claude Marketplace | Production | Yes | Auto-updates | Requires network |

### 3.3 Common Installer Commands

**Full Installation:**
```bash
python setup_all.py --with-plugins --bundle startup
```

**Workspace + Commands Only:**
```bash
python setup_all.py
```

**Global Plugins (One-Time):**
```bash
python setup_plugins.py --global --bundle enterprise
```

**Force Refresh:**
```bash
python setup_all.py --force --with-plugins --bundle startup
```

**Selective Components:**
```bash
python setup_workspace.py --force
python setup_commands.py --force
python setup_plugins.py --bundle startup
```

---

## 4. Marketplace (`marketplace.json`)

**Version:** 1.0.0
**Location:** `/marketplace.json`
**Purpose:** Claude Code plugin registry

### 4.1 Marketplace Entry

```json
{
  "name": "AI SDLC Method Marketplace",
  "version": "1.0.0",
  "author": "foolishimp",
  "repository": "https://github.com/foolishimp/ai_sdlc_method",
  "plugins": [...]
}
```

### 4.2 Installation via Marketplace

**Add Marketplace:**
```bash
/plugin marketplace add foolishimp/ai_sdlc_method
```

**Install Plugins:**
```bash
/plugin install @aisdlc/aisdlc-methodology
/plugin install @aisdlc/python-standards
```

**Update Plugins:**
```bash
/plugin update @aisdlc/aisdlc-methodology
```

---

## 5. Documentation

**Location:** `/docs/`
**Total Files:** 15+ markdown files
**Total Lines:** ~12,000 lines

### 5.1 Core Documentation

```
docs/
├── ai_sdlc_overview.md                          # v2.0.0 - High-level intro (~30 min)
├── ai_sdlc_method.md                            # v2.0.0 - Complete methodology (3,300 lines)
├── ai_sdlc_appendices.md                        # v2.0.0 - Technical deep-dives
├── README.md                                    # v2.0.0 - Documentation index
└── guides/                                      # Role-specific guides
    └── README.md                                # v2.0.0 - Guide index
```

### 5.2 Root Documentation

```
/
├── README.md                                    # v2.0.0 - Project overview
├── QUICKSTART.md                                # v2.0.0 - Quick start guide
├── NEW_PROJECT_SETUP.md                         # v2.0.0 - New project setup
├── PLUGIN_GUIDE.md                              # v2.0.0 - Plugin creation guide
├── CLAUDE.md                                    # v2.0.0 - Claude Code guidance
├── INTENT.md                                    # v2.0.0 - Project intent
└── INVENTORY.md                                 # v2.0.0 - This file
```

---

## 6. Examples

**Location:** `/examples/`

### 6.1 Example Projects

```
examples/local_projects/
├── customer_portal/                             # Complete 7-stage example (800+ lines)
│   ├── README.md                                # v2.0.0 - Complete walkthrough
│   ├── INTENT.md                                # Example intent
│   └── config/config.yml                        # 7-stage configuration (650+ lines)
│
└── data_mapper.test02/                          # Dogfooding test project
    ├── INTENT.md                                # Category theory data mapper
    ├── docs/requirements/
    └── docs/design/
```

---

## 7. MCP Service (Non-Claude LLMs)

**Version:** 1.0.0 (Legacy), 2.0.0 (Planned)
**Location:** `/mcp_service/`
**Purpose:** MCP service for non-Claude LLMs
**Language:** Python 3.8+

### 7.1 Current Implementation (v1.0.0)

```
mcp_service/
├── src/ai_sdlc_config/                          # Python package
├── server/                                      # MCP server
├── client/                                      # Client utilities
├── tests/                                       # Test suite
├── setup.py                                     # Package setup
└── README.md                                    # MCP overview
```

### 7.2 Planned 7-Stage Integration (v2.0.0)

**Status:** In Planning
**Roadmap:** See `mcp_service/MCP_SDLC_INTEGRATION_PLAN.md`

**New MCP Tools:**
- `load_stage_context` - Load AI agent config for specific stage
- `list_available_stages` - List all 7 stages
- `trace_requirement_key` - Trace REQ-* through stages
- `get_requirement_lineage` - Get full lineage from intent to runtime
- `load_agent_persona` - Load agent persona for stage
- `switch_agent_persona` - Switch between stage personas

---

## 8. Deployment Matrix

### 8.1 Component Deployment Methods

| Component | Installer | Marketplace | Manual |
|-----------|-----------|-------------|--------|
| .ai-workspace/ | ✅ `setup_workspace.py` | ❌ | ✅ Copy |
| .claude/commands/ | ✅ `setup_commands.py` | ❌ | ✅ Copy |
| .claude/agents/ | ✅ Included in workspace | ❌ | ✅ Copy |
| Plugins | ✅ `setup_plugins.py` | ✅ `/plugin install` | ✅ Copy |
| CLAUDE.md | ✅ `setup_all.py` | ❌ | ✅ Copy |

### 8.2 Update/Refresh Strategies

#### Strategy 1: Python Installer (Recommended for Dogfooding)

**Use Case:** Development, testing, full control
**Network:** Not required
**Command:**
```bash
python /path/to/ai_sdlc_method/installers/setup_all.py --force --with-plugins --bundle startup
```

**Pros:**
- ✅ Offline capable
- ✅ Full control
- ✅ Deterministic
- ✅ Works in enterprise

**Cons:**
- ❌ Manual process
- ❌ No auto-update

#### Strategy 2: Claude Marketplace

**Use Case:** Production, automatic updates
**Network:** Required
**Command:**
```bash
/plugin update @aisdlc/aisdlc-methodology
```

**Pros:**
- ✅ Auto-updates
- ✅ Easy to use
- ✅ Version control

**Cons:**
- ❌ Network required
- ❌ Only plugins (not templates)

#### Strategy 3: Hybrid (Best of Both)

**Use Case:** Flexibility + convenience
**Network:** Optional

**Templates/Commands:** Python installers
```bash
python setup_workspace.py --force
python setup_commands.py --force
```

**Plugins:** Marketplace
```bash
/plugin update @aisdlc/aisdlc-methodology
```

---

## 9. Version History

### v2.0.0 (2025-11-14)
**Major Release - Complete 7-Stage AI SDLC Methodology**

**Added:**
- 7-stage AI SDLC methodology (Requirements → Design → Tasks → Code → System Test → UAT → Runtime Feedback)
- AI agent configurations for all 7 stages (1,273 lines)
- BDD testing guidance (Given/When/Then)
- Requirement traceability system (REQ-* keys from intent to runtime)
- Bidirectional feedback loop (production → requirements)
- Updated templates with 7-stage agent definitions
- `/aisdlc-checkpoint-tasks` command for auto-task status updates
- `/aisdlc-status` command to show current SDLC stage

**Updated:**
- aisdlc-methodology plugin to v2.0.0
- All command templates renamed with `aisdlc-` prefix
- Documentation to reflect 7-stage process
- Examples with complete lifecycle walkthroughs

**Breaking Changes:**
- Renamed slash commands (todo.md → aisdlc-todo.md, etc.)
- Updated config.yml schema for 7-stage configuration

### v1.0.0 (2025-10-16)
**Initial Release**

**Added:**
- Key Principles development principles
- TDD workflow (RED → GREEN → REFACTOR)
- Developer workspace (.ai-workspace/)
- Claude commands (.claude/commands/)
- Python installers
- Plugin system
- MCP service (legacy project/content management)

---

## 10. Dependencies

### 10.1 Runtime Dependencies

**Python Installers:**
- Python 3.8+
- pyyaml (for config parsing)
- pathlib (standard library)

**MCP Service:**
- Python 3.8+
- mcp
- pyyaml

**Claude Code Plugins:**
- Claude Code CLI or VS Code extension
- No additional dependencies

### 10.2 Development Dependencies

**For Contributing:**
- git
- Python 3.8+
- pytest (for testing installers)
- black (for code formatting)
- mypy (for type checking)

---

## 11. File Statistics

### 11.1 Total Component Count

| Category | Files | Lines | Size |
|----------|-------|-------|------|
| Templates | 38 | ~27,400 | ~1.2 MB |
| Plugins | 50+ | ~5,000 | ~500 KB |
| Installers | 6 | ~2,500 | ~100 KB |
| Documentation | 20+ | ~12,000 | ~800 KB |
| Examples | 15+ | ~2,000 | ~150 KB |
| **Total** | **129+** | **~48,900** | **~2.75 MB** |

### 11.2 Lines of Code by Type

```
Configuration (YAML):  ~2,000 lines
Documentation (MD):    ~40,000 lines
Python Code:           ~2,500 lines
JSON:                  ~500 lines
Templates:             ~3,500 lines
```

---

## 12. Maintenance

### 12.1 Update Checklist

When updating AI SDLC Method components:

**Templates:**
- [ ] Update version in template files
- [ ] Update CHANGELOG
- [ ] Test installer with `--force` flag
- [ ] Update examples to use new templates

**Plugins:**
- [ ] Update plugin.json version
- [ ] Update dependencies
- [ ] Update marketplace.json
- [ ] Test plugin installation
- [ ] Update plugin README

**Installers:**
- [ ] Update version in setup scripts
- [ ] Test all installation methods
- [ ] Update installer README
- [ ] Verify traceability validation

**Documentation:**
- [ ] Update version references
- [ ] Update command examples
- [ ] Update file paths
- [ ] Review role-specific guides

### 12.2 Testing Checklist

Before release:

- [ ] Test `setup_all.py` with fresh project
- [ ] Test `setup_all.py --force` with existing project
- [ ] Test global plugin installation
- [ ] Test bundle installations (startup, datascience, qa, enterprise)
- [ ] Test marketplace installation
- [ ] Verify all slash commands work
- [ ] Run traceability validation
- [ ] Test example projects
- [ ] Verify MCP service (if updated)

### 12.3 Release Process

1. **Update version numbers**
   - INVENTORY.md (this file)
   - marketplace.json
   - plugin.json files
   - installer scripts

2. **Update documentation**
   - CHANGELOG.md
   - README.md
   - QUICKSTART.md
   - NEW_PROJECT_SETUP.md

3. **Test all components**
   - Run testing checklist
   - Verify dogfooding projects

4. **Tag release**
   ```bash
   git tag -a v2.0.0 -m "Release v2.0.0 - 7-Stage AI SDLC"
   git push origin v2.0.0
   ```

5. **Publish**
   - Push to GitHub
   - Update marketplace registry
   - Announce in CHANGELOG

---

## 13. Support

### 13.1 Getting Help

- **Issues:** https://github.com/foolishimp/ai_sdlc_method/issues
- **Documentation:** `/docs/`
- **Examples:** `/examples/`
- **Installer Guide:** `/installers/README.md`
- **Plugin Guide:** `/PLUGIN_GUIDE.md`

### 13.2 Contributing

See repository for contribution guidelines.

---

**Last Updated:** 2025-11-23
**Maintained By:** foolishimp
**Repository:** https://github.com/foolishimp/ai_sdlc_method

**"Excellence or nothing"** 🔥
