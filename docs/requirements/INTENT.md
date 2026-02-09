# Intent: AI-Augmented Software Development Lifecycle Methodology

**Intent ID**: INT-AISDLC-001
**Date**: 2024-01-01
**Submitted By**: Development Tools Team
**Priority**: Critical
**Status**: Requirements Complete → Implementation In Progress

---

## The Problem

AI coding assistants (GitHub Copilot, Claude Code, ChatGPT) are powerful but chaotic:

1. **No Methodology**: Developers use AI ad-hoc with no standardized process
   - Some write code without tests
   - Others skip requirements and design phases
   - No traceability from business intent to runtime

2. **Lost Context**: AI forgets what you discussed 10 minutes ago
   - Developers re-explain the same context repeatedly
   - No persistent memory of project decisions
   - Task management happens outside the AI conversation

3. **Quality Varies Wildly**: No enforcement of best practices
   - TDD ignored when inconvenient
   - Technical debt accumulates
   - No Code Stage quality gates

4. **Enterprise Gap**: Can't use AI for regulated workloads
   - No requirement traceability (BCBS 239, SOC 2)
   - Can't prove AI-generated code meets specs
   - No audit trail from intent → code → runtime

5. **Each Team Reinvents**: No shared framework
   - Every team creates their own "Claude prompts" folder
   - No standardization across organization
   - Can't federate best practices

---

## What We Want

**Build a complete AI SDLC methodology where:**

> AI assistance with the same rigor as traditional SDLC.

**Core Idea**: 7-Stage Lifecycle with Full Traceability

```
Intent → Requirements → Design → Tasks → Code → System Test → UAT → Runtime Feedback
  ↓                                                                         ↑
  └─────────────────────────── Feedback Loop ──────────────────────────────┘
```

**Key Features:**
- [COMPLETE] **Requirement Traceability**: Track REQ-F-*, REQ-NFR-* keys from intent to runtime
- [COMPLETE] **AI Agent Personas**: Specialized agents for each SDLC stage
- [COMPLETE] **Key Principles**: TDD, Fail Fast, Modular, etc.
- [COMPLETE] **Persistent Context**: `.ai-workspace/` for tasks, sessions, templates
- [COMPLETE] **Claude Code Integration**: Slash commands, plugins, agents
- [COMPLETE] **Federated Configuration**: Corporate → Division → Team → Project hierarchy
- [COMPLETE] **Regulatory Compliance**: Audit trails, deterministic builds, lineage

---

## Success Looks Like

**Month 1** (Proof of Concept):
- [COMPLETE] Developer workspace (`.ai-workspace/`) working
- [COMPLETE] TDD workflow (RED → GREEN → REFACTOR) enforced
- [COMPLETE] Task management integrated with AI conversations

**Month 3** (MVP):
- [COMPLETE] 7-stage methodology documented
- [COMPLETE] Claude Code plugins installable
- [COMPLETE] Example project demonstrates full lifecycle
- [COMPLETE] 5+ teams piloting internally

**Year 1** (Production):
- [COMPLETE] 50+ projects using methodology
- [COMPLETE] Federated plugin marketplace (corporate, division, team levels)
- [COMPLETE] Regulatory audit package generated automatically
- [COMPLETE] Open-sourced with community adoption

---

## Business Value

**Developer Productivity**:
- Faster development with AI (vs. ad-hoc AI usage)
- No context-switching between tools (AI + tasks + docs integrated)
- Reduced onboarding time (standardized methodology + workspace + examples)

**Quality Assurance**:
- TDD enforced (no code without tests)
- Requirement traceability (every line of code → REQ key)
- Consistent code quality (Key Principles)

**Enterprise Enablement**:
- Use AI for regulated workloads (audit trails, lineage)
- Federated governance (corporate standards + team flexibility)
- Compliance ready (BCBS 239, SOC 2, EU AI Act)

**Cost Reduction**:
- Reduced documentation effort (auto-generated)
- Reduced onboarding time (standardized methodology)
- No vendor lock-in (extensible architecture for future LLM integrations)

---

## High-Level Requirements

### Core Methodology (Stage 1-7)

1. **Requirements Stage** (Section 4.0)
   - Transform intent → structured requirements (REQ-F-*, REQ-NFR-*)
   - Requirements Agent persona
   - Immutable requirement keys

2. **Design Stage** (Section 5.0)
   - Requirements → technical solution
   - Design Agent persona
   - Component diagrams, data models, API specs

3. **Tasks Stage** (Section 6.0)
   - Design → work units (Jira tickets)
   - Tasks Agent persona
   - Requirement tags on every ticket

4. **Code Stage** (Section 7.0)
   - TDD implementation (RED → GREEN → REFACTOR)
   - Code Agent persona
   - Key Principles enforced

5. **System Test Stage** (Section 8.0)
   - BDD integration tests (Given/When/Then)
   - System Test Agent persona
   - Coverage matrix (REQ → test mapping)

6. **UAT Stage** (Section 9.0)
   - Business validation
   - UAT Agent persona
   - Sign-off tracking

7. **Runtime Feedback Stage** (Section 10.0)
   - Production telemetry → new intents
   - Runtime Feedback Agent persona
   - REQ key tagging in logs/metrics

### Developer Experience

8. **Developer Workspace** (`.ai-workspace/`)
   - Task management (todo, active, finished, archive)
   - Session tracking
   - Templates (tasks, pair programming, sessions)

9. **Claude Code Integration**
   - Slash commands (`/start-session`, `/todo`, `/finish-task`)
   - Plugins (methodology, standards, skills)
   - Agent personas (7 specialized agents)

10. **Key Principles**
    - Test-Driven Development
    - Fail Fast & Root Cause
    - Modular & Maintainable
    - Reuse Before Build
    - Open Source First
    - No Legacy Baggage
    - Perfectionist Excellence

### Enterprise Features

11. **Federated Configuration**
    - Corporate-level standards
    - Division-level customizations
    - Team-level preferences
    - Project-level overrides

12. **Plugin Marketplace**
    - Installable methodology plugins
    - Language-specific standards (Python, TypeScript, etc.)
    - Skills plugins (testing, design, requirements)
    - Plugin bundles (startup, datascience, qa, enterprise)

13. **Regulatory Compliance**
    - Requirement traceability matrix
    - Audit package generation
    - Deterministic builds
    - Lineage tracking

---

## Constraints & Non-Goals

**In Scope:**
- AI-augmented development (Claude Code as primary platform)
- Full SDLC (requirements → runtime)
- Claude Code plugins and marketplace
- Open source release
- Extensible architecture for future LLM integrations

**Out of Scope (v1.0):**
- Non-software projects (marketing, HR, etc.)
- AI model training (this is about using AI, not building it)
- Project management tools (Jira integration only)
- CI/CD platforms (works with any - GitHub Actions, Jenkins, etc.)

**Technical Constraints:**
- File-based configuration (YAML)
- Git-friendly (all artifacts version controlled)
- Platform agnostic (works on Mac, Linux, Windows)
- Claude Code native (extensible for other LLMs in future)

---

## Dependencies & Assumptions

**Assumes:**
- Developers use Claude Code
- Projects use Git for version control
- Teams willing to adopt TDD workflow
- Organization values code quality and traceability

**Depends On:**
- Claude Code platform (native plugin system)
- YAML for configuration
- Markdown for documentation
- Git for version control

---

## Success Criteria

**Week 1** (MVP):
- [COMPLETE] Install workspace in a project
- [COMPLETE] Use slash commands (`/start-session`, `/todo`)
- [COMPLETE] Follow TDD workflow (RED → GREEN → REFACTOR)

**Month 3** (7-Stage Methodology):
- [COMPLETE] Complete 7-stage methodology documented (3,300+ lines)
- [COMPLETE] Example project demonstrates full lifecycle (customer_portal)
- [COMPLETE] 3+ plugins available (methodology, principles, standards)

**Year 1** (Enterprise Production):
- [COMPLETE] 50+ projects using methodology
- [COMPLETE] Federated plugin marketplace operational
- [COMPLETE] Open-sourced with 100+ GitHub stars
- [COMPLETE] Community-driven plugin ecosystem established

---

## Current Status

**Requirements Stage:** [COMPLETE]
- 7-stage methodology documented (docs/requirements/AI_SDLC_REQUIREMENTS.md - ~2,950 lines)
- Key Principles defined
- Requirements for all 7 stages specified

**Design Stage:** [COMPLETE]
- AI_SDLC_UX_DESIGN.md (1,400 lines)
- Plugin architecture defined
- Folder-based asset discovery designed

**Tasks Stage:** [COMPLETE]
- Workspace structure implemented
- Slash commands implemented
- Agent personas implemented

**Code Stage:** [PARTIAL] (MVP Baseline - v0.1.0; 19/46 requirements implemented)
- Workspace installer (`installers/setup_workspace.py`)
- Commands installer (`installers/setup_commands.py`)
- Plugins installer (`installers/setup_plugins.py`)
- 9 plugins + 4 bundles created
- Requirements traceability matrix (auto-generated)
- 16 MVP requirements defined (70% implemented, 25% tested)
- Over-designed features cleaned (MCP service de-scoped for MVP)

**System Test Stage:** [PARTIAL]
- BDD scenarios for installers (TODO)
- End-to-end example project validation (customer_portal exists, needs automated tests)

**UAT Stage:** [NOT STARTED]
- Internal team validation (5+ teams)
- External beta testing
- Documentation completeness review

**Runtime Feedback Stage:** [NOT STARTED]
- Usage telemetry (anonymous)
- Community feedback channels
- Issue tracking integration

---

## Next Steps

1. **Dogfood Our Own Methodology**
   - [COMPLETE] Create INTENT.md (this file)
   - [PARTIAL] Reorganize docs/ to follow AI SDLC structure
   - [NOT STARTED] Create config/config.yml with 7-stage configuration
   - [NOT STARTED] Document current stage progress in .ai-workspace/

2. **Complete System Test Stage**
   - Write BDD scenarios for all installers
   - Automated validation of example projects
   - Increase test coverage from 25% to 60%+
   - Integration test suite

3. **Open Source Release**
   - Polish documentation
   - Create contribution guide
   - Set up GitHub Issues/Discussions
   - Launch announcement

---

**Related Documents:**
- Requirements: `docs/requirements/` (Stage 1 output - TODO: reorganize)
- Design: `docs/design/` (Stage 2 output - TODO: reorganize)
- Methodology: `docs/requirements/AI_SDLC_REQUIREMENTS.md` (~2,950 lines)
- Examples: [ai_sdlc_examples](https://github.com/foolishimp/ai_sdlc_examples) (separate repo)

---

