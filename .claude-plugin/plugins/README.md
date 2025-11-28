# AI SDLC Methodology Plugin

Single consolidated plugin providing the complete **AI-Augmented Software Development Lifecycle** with homeostatic control.

**Version**: 4.0.0
**Plugin**: `aisdlc-methodology`

---

## Plugin Architecture

```
aisdlc-methodology v4.0.0
├── hooks/          4 lifecycle hooks
├── commands/       7 slash commands
├── agents/         7 stage agents
├── skills/         42 skills
│   ├── core/           3 (traceability, coverage, propagation)
│   ├── principles/     2 (key principles, seven questions)
│   ├── requirements/   8 (extraction, disambiguation, validation)
│   ├── design/         3 (ADRs, traceability, coverage)
│   ├── code/          18 (tdd/, bdd/, generation/, debt/)
│   ├── testing/        5 (coverage, generation, integration)
│   └── runtime/        3 (telemetry, observability, tracing)
├── config/         Stage configurations
├── docs/           Principles & workflows
└── templates/      .ai-workspace templates
```

---

## What's Included

### Hooks (4)

| Hook | Trigger | Behavior |
|------|---------|----------|
| **SessionStart** | Session opens | Show active tasks, last updated |
| **Stop** | After response | Suggest checkpoint if uncommitted changes |
| **PreToolUse** | Before `git commit` | Warn if missing REQ-* tag |
| **PostToolUse** | After Edit | Auto-format (prettier/black/gofmt) |

### Commands (7)

| Command | Purpose |
|---------|---------|
| `/aisdlc-status` | Show current status |
| `/aisdlc-checkpoint-tasks` | Save task progress |
| `/aisdlc-commit-task` | Commit with REQ traceability |
| `/aisdlc-finish-task` | Mark task complete |
| `/aisdlc-refresh-context` | Reload workspace context |
| `/aisdlc-release` | Create tagged release |
| `/aisdlc-update` | Update methodology |

### Agents (7 - one per SDLC stage)

| Agent | Stage | Methodology |
|-------|-------|-------------|
| `aisdlc-requirements-agent` | Requirements | Intent → REQ-* keys |
| `aisdlc-design-agent` | Design | Architecture + ADRs |
| `aisdlc-tasks-agent` | Tasks | Work breakdown |
| `aisdlc-code-agent` | Code | **TDD** (RED→GREEN→REFACTOR) |
| `aisdlc-system-test-agent` | System Test | **BDD** (Given/When/Then) |
| `aisdlc-uat-agent` | UAT | Business validation |
| `aisdlc-runtime-feedback-agent` | Runtime | Telemetry + feedback loop |

### Skills (42)

#### Core (3)
- `requirement-traceability` - Track REQ-* keys through codebase
- `check-requirement-coverage` - Detect untraced code (sensor)
- `propagate-req-keys` - Auto-tag code with REQ-* keys (actuator)

#### Principles (2)
- `apply-key-principles` - Enforce 7 Key Principles
- `seven-questions-checklist` - Validate principle adherence (sensor)

#### Requirements (8)
- `requirement-extraction` - Transform intent to REQ-* keys
- `disambiguate-requirements` - Extract BR-*, C-*, F-*
- `extract-business-rules` - Extract BR-* from requirements
- `extract-constraints` - Extract C-* constraints
- `extract-formulas` - Extract F-* formulas
- `validate-requirements` - Quality gate for requirements
- `refine-requirements` - Feedback loop from implementation
- `create-traceability-matrix` - Generate traceability docs

#### Design (3)
- `design-with-traceability` - Architecture with REQ-* tags
- `create-adrs` - Architecture Decision Records
- `validate-design-coverage` - Ensure all REQ-* covered

#### Code (18)

**TDD (5)**:
- `tdd-workflow` - Complete RED→GREEN→REFACTOR cycle
- `red-phase` - Write failing tests first
- `green-phase` - Minimal code to pass
- `refactor-phase` - Improve quality
- `commit-with-req-tag` - Commit with traceability

**BDD (5)**:
- `bdd-workflow` - Given/When/Then orchestration
- `write-scenario` - Create Gherkin scenarios
- `implement-step-definitions` - Step implementation
- `implement-feature` - Feature implementation
- `refactor-bdd` - Refactor BDD code

**Generation (4)**:
- `autogenerate-from-business-rules` - Code from BR-*
- `autogenerate-validators` - Validators from rules
- `autogenerate-formulas` - Code from F-*
- `autogenerate-constraints` - Code from C-*

**Debt (4)**:
- `detect-unused-code` - Find dead code (sensor)
- `prune-unused-code` - Remove dead code (actuator)
- `detect-complexity` - Find complex code (sensor)
- `simplify-complex-code` - Reduce complexity (actuator)

#### Testing (5)
- `validate-test-coverage` - Check coverage (sensor)
- `generate-missing-tests` - Auto-generate tests (actuator)
- `run-integration-tests` - Execute BDD tests
- `create-coverage-report` - Coverage with REQ-* mapping
- `create-test-specification` - TCS from requirements

#### Runtime (3)
- `telemetry-tagging` - Tag logs/metrics with REQ-*
- `create-observability-config` - Setup Datadog/Prometheus
- `trace-production-issue` - Link alerts to requirements

---

## Homeostatic Control

The plugin maintains quality automatically through sensors and actuators:

### Sensors (Detect Gaps)
- `check-requirement-coverage` - Detect untraced code
- `seven-questions-checklist` - Validate Key Principles
- `validate-test-coverage` - Detect missing tests
- `detect-unused-code` - Find dead code
- `detect-complexity` - Find over-complex code

### Actuators (Fix Gaps)
- `propagate-req-keys` - Auto-tag with REQ-*
- `generate-missing-tests` - Auto-generate tests
- `prune-unused-code` - Remove dead code
- `simplify-complex-code` - Reduce complexity

```
Sensor detects gap → Actuator fixes gap → Validate → Monitor
        ↑                                              ↓
        └────────────── Continuous Improvement ────────┘
```

---

## The 7 Key Principles

1. **TDD** - "No code without tests"
2. **Fail Fast** - "Break loudly, fix completely"
3. **Modular** - "Single responsibility, loose coupling"
4. **Reuse** - "Check first, create second"
5. **Open Source** - "Suggest alternatives, human decides"
6. **No Debt** - "Clean slate, no debt"
7. **Excellence** - "Best of breed only"

**Ultimate Mantra**: "Excellence or nothing"

---

## Installation

### Option 1: GitHub Source (Recommended)

Add to `.claude/settings.json`:

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
    "aisdlc-methodology@aisdlc": true
  }
}
```

### Option 2: Local Directory (Development)

```bash
git clone https://github.com/foolishimp/ai_sdlc_method.git ~/ai_sdlc_method
```

Add to `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "aisdlc": {
      "source": {
        "source": "directory",
        "path": "~/ai_sdlc_method/claude-code/plugins"
      }
    }
  },
  "enabledPlugins": {
    "aisdlc-methodology@aisdlc": true
  }
}
```

### Verify Installation

```
/plugin
```

Should show `aisdlc-methodology` as "Installed".

---

## The 7-Stage SDLC

```
Intent → Requirements → Design → Tasks → Code → System Test → UAT → Runtime
           ↑                                                            ↓
           └─────────────────── Feedback Loop ──────────────────────────┘
```

### Stage Flow

```
Intent: INT-001 "Customer self-service portal"
  ↓
Requirements: REQ-F-AUTH-001 "User login with email/password"
  ↓
Design: AuthenticationService → REQ-F-AUTH-001
  ↓
Tasks: PORTAL-123 (Jira ticket) → REQ-F-AUTH-001
  ↓
Code: auth_service.py
      # Implements: REQ-F-AUTH-001
  ↓
Tests: test_auth.py # Validates: REQ-F-AUTH-001
       auth.feature # BDD: Given/When/Then
  ↓
UAT: UAT-001 → REQ-F-AUTH-001 (Business sign-off ✅)
  ↓
Runtime: Datadog alert: "ERROR: REQ-F-AUTH-001 - Auth timeout"
  ↓
Feedback: New intent: INT-042 "Fix auth timeout"
  [Cycle repeats...]
```

---

## Task Tracking

The methodology uses a task tracking system:

### Active Tasks
```
.ai-workspace/tasks/active/ACTIVE_TASKS.md
```
- Single file tracking all current work
- Task numbers, priority, status
- REQ-* traceability
- Work breakdown and acceptance criteria

### Finished Tasks
```
.ai-workspace/tasks/finished/YYYYMMDD_HHMM_task_name.md
```
- Historical record with full context
- Implementation details
- Files modified
- Lessons learned

### Recovery Commands
```bash
cat .ai-workspace/tasks/active/ACTIVE_TASKS.md  # Current tasks
git status                                       # Git state
/aisdlc-status                                   # Task queue
```

---

## Plugin Structure

```
aisdlc-methodology/
├── .claude-plugin/
│   └── plugin.json           # Plugin manifest
├── hooks/
│   └── settings.json         # 4 lifecycle hooks
├── commands/                 # 7 slash commands
│   ├── aisdlc-status.md
│   ├── aisdlc-checkpoint-tasks.md
│   ├── aisdlc-commit-task.md
│   ├── aisdlc-finish-task.md
│   ├── aisdlc-refresh-context.md
│   ├── aisdlc-release.md
│   └── aisdlc-update.md
├── agents/                   # 7 stage agents
│   ├── aisdlc-requirements-agent.md
│   ├── aisdlc-design-agent.md
│   ├── aisdlc-tasks-agent.md
│   ├── aisdlc-code-agent.md
│   ├── aisdlc-system-test-agent.md
│   ├── aisdlc-uat-agent.md
│   └── aisdlc-runtime-feedback-agent.md
├── skills/                   # 42 skills
│   ├── core/
│   ├── principles/
│   ├── requirements/
│   ├── design/
│   ├── code/
│   │   ├── tdd/
│   │   ├── bdd/
│   │   ├── generation/
│   │   └── debt/
│   ├── testing/
│   └── runtime/
├── config/
│   ├── stages_config.yml     # 7-stage agent specs
│   └── config.yml            # Key Principles config
├── docs/
│   ├── principles/KEY_PRINCIPLES.md
│   └── processes/TDD_WORKFLOW.md
└── templates/
    └── .ai-workspace/        # Workspace templates
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| **4.0.0** | 2025-11-27 | Consolidated all plugins into single aisdlc-methodology |
| 3.0.0 | 2025-11-25 | Added homeostatic control (sensors/actuators) |
| 2.0.0 | 2025-11-14 | Added 7-stage AI SDLC methodology |
| 1.0.0 | 2025-10-16 | Initial release with Key Principles |

### v4.0.0 Consolidation

**Before** (v3.0.0):
- 7 plugins + 4 bundles
- Complex dependency graph
- 11 marketplace entries

**After** (v4.0.0):
- 1 plugin (aisdlc-methodology)
- No dependencies
- 1 marketplace entry
- 42 skills consolidated

---

## See Also

- [AI SDLC Method Documentation](../../docs/ai_sdlc_method.md) - Complete methodology
- [Key Principles](aisdlc-methodology/docs/principles/KEY_PRINCIPLES.md) - 7 principles
- [TDD Workflow](aisdlc-methodology/docs/processes/TDD_WORKFLOW.md) - RED→GREEN→REFACTOR
- [Example Projects](https://github.com/foolishimp/ai_sdlc_examples) - Complete examples

---

**"Excellence or nothing"**
