# /aisdlc-help - AI SDLC Methodology Help

Display comprehensive help for the AI SDLC methodology, including available commands, agents, and workflows.

<!-- Implements: REQ-TOOL-003 (Workflow Commands) -->

## Instructions

First, read the plugin version from the plugin.json file. Try these locations in order:
1. `.claude-plugin/plugin.json` (relative to the command file location)
2. `../plugin.json` (if commands are in a subdirectory)
3. Search for `aisdlc-methodology/.claude-plugin/plugin.json` in the project

Extract the `"version"` field to display in the header.

Then display the full AI SDLC help guide:

```
╔══════════════════════════════════════════════════════════════╗
║               AI SDLC Method - Help Guide                    ║
║                      Version: {version}                      ║
╚══════════════════════════════════════════════════════════════╝

## The 7-Stage Lifecycle

  Intent → Requirements → Design → Tasks → Code → Test → UAT → Runtime
            ↑                                                      ↓
            └───────────────── Feedback Loop ──────────────────────┘

## Available Agents (invoke by describing what you need)

  📋 Requirements Agent  - "Help me create requirements for [feature]"
  🏗️  Design Agent        - "Design a solution for REQ-F-XXX-001"
  📝 Tasks Agent         - "Break down the design into tasks"
  💻 Code Agent          - "Implement [task] using TDD"
  🧪 System Test Agent   - "Create BDD tests for REQ-F-XXX-001"
  ✅ UAT Agent           - "Create UAT test cases for [feature]"
  📡 Runtime Agent       - "Set up observability for [service]"

## Commands

  ### Setup & Status
  /aisdlc-init             Initialize workspace and mandatory artifact placeholders
  /aisdlc-status           Show current project status and active tasks
  /aisdlc-help             This help guide
  /aisdlc-version          Show plugin version information

  ### Task Management
  /aisdlc-finish-task      Mark a task as complete
  /aisdlc-checkpoint-tasks Update task status from conversation context
  /aisdlc-commit-task      Commit with REQ-* tag (traceability)

  ### Release
  /aisdlc-release          Create a new release (tag + changelog)
  /aisdlc-refresh-context  Reload AI SDLC methodology context

## Skills (11 consolidated workflows)

  Skills are invoked automatically when your task matches. Just describe what you need.

  ### Core (3)
  check-requirement-coverage, propagate-req-keys, requirement-traceability

  ### Design (3)
  create-adrs, design-with-traceability, validate-design-coverage

  ### Code (2)
  tdd-workflow (RED→GREEN→REFACTOR), bdd-workflow (Given/When/Then)

  ### Runtime (3)
  create-observability-config, telemetry-tagging, trace-production-issue

## Quick Start Workflows

  ### Starting Fresh
  1. Describe your intent: "I want to build [feature]"
  2. Claude invokes Requirements Agent → generates REQ-* keys
  3. Design Agent → creates solution architecture
  4. Tasks Agent → breaks into work items
  5. Code Agent → TDD implementation (RED → GREEN → REFACTOR)

  ### Continuing Work
  1. /aisdlc-status → see active tasks
  2. Pick a task: "Continue working on Task #X"
  3. /aisdlc-checkpoint-tasks → save progress
  4. /aisdlc-commit-task → commit with traceability

  ### Creating Requirements
  "Help me create requirements for user authentication"
  → Generates: REQ-F-AUTH-001, REQ-NFR-PERF-001, etc.

  ### Creating Designs
  "Design a solution for REQ-F-AUTH-001"
  → Creates: Component diagrams, API specs, ADRs

  ### Writing Code (TDD)
  "Implement login endpoint using TDD"
  → RED: Write failing test
  → GREEN: Implement to pass
  → REFACTOR: Improve quality
  → COMMIT: /aisdlc-commit-task

## Requirement Traceability

  All work is tagged with requirement keys:

  REQ-F-*      Functional requirements
  REQ-NFR-*    Non-functional requirements
  REQ-DATA-*   Data quality requirements
  REQ-BR-*     Business rules

  Example flow:
  Intent → REQ-F-AUTH-001 → Design → Task → Code (# Implements: REQ-F-AUTH-001)
                                           → Test (# Validates: REQ-F-AUTH-001)
                                           → Commit (feat: REQ-F-AUTH-001)

## Key Principles (Code Stage)

  1. Test Driven Development - "No code without tests"
  2. Fail Fast & Root Cause  - "Break loudly, fix completely"
  3. Modular & Maintainable  - "Single responsibility"
  4. Reuse Before Build      - "Check first, create second"
  5. Open Source First       - "Suggest alternatives"
  6. No Legacy Baggage       - "Clean slate, no debt"
  7. Perfectionist Excellence - "Best of breed only"

## Getting Started (Step by Step)

  New to AI SDLC? Follow this path:

  ┌─────────────────────────────────────────────────────────────┐
  │  Step 1: /aisdlc-init                                       │
  │          Initialize workspace and artifact templates        │
  │                          ↓                                  │
  │  Step 2: Edit docs/requirements/INTENT.md                   │
  │          Describe what you want to build                    │
  │                          ↓                                  │
  │  Step 3: "Help me create requirements from INTENT.md"       │
  │          → Generates REQ-F-*, REQ-NFR-*, etc.               │
  │                          ↓                                  │
  │  Step 4: "Design a solution for REQ-F-XXX-001"              │
  │          → Creates components, ADRs, traceability           │
  │                          ↓                                  │
  │  Step 5: "Break down the design into tasks"                 │
  │          → Creates work items in ACTIVE_TASKS.md            │
  │                          ↓                                  │
  │  Step 6: "Work on Task #1 using TDD"                        │
  │          → RED → GREEN → REFACTOR → COMMIT                  │
  │                          ↓                                  │
  │  Step 7: /aisdlc-checkpoint-tasks                           │
  │          → Save progress                                    │
  │                          ↓                                  │
  │  Step 8: /aisdlc-release                                    │
  │          → Create release with changelog                    │
  └─────────────────────────────────────────────────────────────┘

  💡 Not sure where you are? Run /aisdlc-status for next step.

## Troubleshooting

  ### Plugin Not Updating?
  If you're seeing an old version after reinstalling, clear the cache:

  ```bash
  rm -rf ~/.claude/plugins/marketplaces/aisdlc
  ```

  Then restart Claude Code. It will fetch the latest version.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 Full docs: https://github.com/foolishimp/ai_sdlc_method
```

---

**Usage**: Run `/aisdlc-help` to display this guide.
