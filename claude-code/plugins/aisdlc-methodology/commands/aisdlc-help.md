# /aisdlc-help - AI SDLC Methodology Help

Display comprehensive help for the AI SDLC methodology, including available commands, agents, and workflows.

<!-- Implements: REQ-F-CMD-001 (Slash Commands for Workflow) -->

## Instructions

Display the full AI SDLC help guide:

```
╔══════════════════════════════════════════════════════════════╗
║               AI SDLC Method - Help Guide                    ║
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

  ### Status & Navigation
  /aisdlc-status           Show current project status and active tasks
  /aisdlc-help             This help guide

  ### Task Management
  /aisdlc-add-task         Add a new task to the backlog
  /aisdlc-finish-task      Mark a task as complete
  /aisdlc-checkpoint-tasks Update task status from conversation context

  ### Development
  /aisdlc-commit-task      Commit with REQ-* tag (traceability)
  /aisdlc-create-tcs       Create Test Case Specification

  ### Release
  /aisdlc-release          Create a new release (tag + changelog)

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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Tip: Just describe what you want to do in natural language.
   Claude will invoke the appropriate agent and guide you.

📚 Full docs: https://github.com/foolishimp/ai_sdlc_method
```

---

**Usage**: Run `/aisdlc-help` to display this guide.
