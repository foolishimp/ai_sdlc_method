# AI SDLC Method - Documentation

This documentation follows the **AI SDLC 7-stage methodology** that this project defines and dogfoods.

---

## 🎯 Project Intent

**See:** [`../INTENT.md`](../INTENT.md)

### ⚠️ CRITICAL REQUIREMENT: INTENT.md

**Every AI SDLC project MUST have `INTENT.md` at the project root.**

This file:
- ✅ States the business problem in plain language (not technical requirements)
- ✅ Defines success criteria and business value
- ✅ Serves as the **INPUT to Stage 1 (Requirements)**
- ✅ Remains as the "north star" throughout the project lifecycle
- ✅ Provides the traceability root for all downstream artifacts

**Artifact Flow:**
```
INTENT.md (Project Root) - Business problem statement
    ↓
Stage 1: Requirements → docs/requirements/ - REQ-F-*, REQ-NFR-* keys
    ↓
Stage 2: Design → docs/design/ - Component architecture, ADRs
    ↓
Stage 3: Tasks → .ai-workspace/tasks/ - Work units, Jira tickets
    ↓
Stage 4: Code → src/, tests/ - TDD implementation
    ↓
Stage 5: System Test → tests/bdd/ - BDD scenarios (Given/When/Then)
    ↓
Stage 6: UAT → docs/uat/ - Business validation
    ↓
Stage 7: Runtime Feedback → Production telemetry → New intents
    ↓ (feedback loop)
New INTENT.md (if production issues reveal new needs)
```

**Templates:**
- **This project:** [`../INTENT.md`](../INTENT.md)
- **Example:** [`../examples/local_projects/customer_portal/INTENT.md`](../examples/local_projects/customer_portal/INTENT.md)
- **Example:** [`../examples/local_projects/data_mapper.test02/INTENT.md`](../examples/local_projects/data_mapper.test02/INTENT.md)

---

## 📁 Documentation Structure

This `docs/` folder is organized by **AI SDLC stage**, dogfooding our own methodology:

```
docs/
├── README.md                           # This file
│
├── requirements/                       # 📋 STAGE 1 OUTPUT
│   └── FOLDER_BASED_REQUIREMENTS.md   #    Requirements engineering approach
│
├── design/                             # 🎨 STAGE 2 OUTPUT
│   ├── AI_SDLC_UX_DESIGN.md           #    Overall UX design (1,400 lines)
│   ├── FOLDER_BASED_ASSET_DISCOVERY.md #   Asset discovery system
│   ├── CLAUDE_AGENTS_EXPLAINED.md      #    Agent system architecture
│   └── AGENTS_SKILLS_INTEROPERATION.md #    Agent/skill integration
│
├── methodology/                        # 📚 REFERENCE DOCUMENTATION
│   ├── ai_sdlc_method.md              #    Complete 7-stage spec (3,300 lines)
│   ├── ai_sdlc_overview.md            #    High-level introduction (~30 min read)
│   ├── ai_sdlc_concepts.md            #    Core concepts
│   ├── ai_sdlc_full_flow.md           #    End-to-end flow diagrams
│   └── ai_sdlc_appendices.md          #    Technical deep-dives (category theory)
│
├── guides/                             # 👥 USER GUIDES (by role)
│   └── [role-specific guides]
│
└── deprecated/                         # 🗄️ ARCHIVED VERSIONS
```

---

## 🚀 Quick Start

### New to AI SDLC?

**5-Minute Path:**
1. Read the Intent: [`../INTENT.md`](../INTENT.md) - Why this project exists
2. Quick Overview: [`methodology/ai_sdlc_overview.md`](methodology/ai_sdlc_overview.md) - 30-minute read
3. Install: [`../QUICKSTART.md`](../QUICKSTART.md) - 10 minutes
4. Try Example: [`../examples/local_projects/customer_portal/`](../examples/local_projects/customer_portal/) - 1 hour

### Want to Adopt AI SDLC?

1. **Understand Methodology:** [`methodology/ai_sdlc_method.md`](methodology/ai_sdlc_method.md) (2-3 hours)
2. **Install in Your Project:**
   ```bash
   cd /path/to/your/project
   python /path/to/ai_sdlc_method/installers/setup_all.py
   ```
3. **Create INTENT.md:** Use template from [`../examples/local_projects/customer_portal/INTENT.md`](../examples/local_projects/customer_portal/INTENT.md)
4. **Follow Workflow:** Use `.ai-workspace/` and slash commands (`/start-session`, `/finish-task`, etc.)

### Want to Extend AI SDLC?

1. **Plugin Development:** [`../PLUGIN_GUIDE.md`](../PLUGIN_GUIDE.md)
2. **Agent Customization:** [`design/CLAUDE_AGENTS_EXPLAINED.md`](design/CLAUDE_AGENTS_EXPLAINED.md)

---

## 📖 Core Methodology Documents

### ⭐ Three-Tier Documentation

1. **[methodology/ai_sdlc_overview.md](methodology/ai_sdlc_overview.md)** - High-level introduction (~30 min read)
   - Quick overview of AI SDLC concepts
   - Perfect for executives and stakeholders
   - Visual diagrams and examples

2. **[methodology/ai_sdlc_method.md](methodology/ai_sdlc_method.md)** ⭐ - Complete methodology reference (3,300+ lines)
   - Section 1.0: Introduction - What is AI SDLC?
   - Section 2.0: End-to-End Intent Lifecycle
   - Section 3.0: Builder Pipeline Overview
   - **Section 4.0: Requirements Stage** - Intent → Structured requirements
   - **Section 5.0: Design Stage** - Requirements → Technical solution
   - **Section 6.0: Tasks Stage** - Work breakdown + Jira orchestration
   - **Section 7.0: Code Stage** - TDD implementation (RED→GREEN→REFACTOR)
   - **Section 8.0: System Test Stage** - BDD integration testing
   - **Section 9.0: UAT Stage** - Business validation
   - **Section 10.0: Runtime Feedback Stage** - Production telemetry feedback
   - Section 11.0: Personas & Collaboration
   - Section 12.0: Data Quality Integration
   - Section 13.0: Governance & Compliance

3. **[methodology/ai_sdlc_appendices.md](methodology/ai_sdlc_appendices.md)** - Technical deep-dives
   - Category theory foundations
   - Ecosystem requirements integration
   - Advanced technical concepts

👉 **Quick start**: Read [`methodology/ai_sdlc_overview.md`](methodology/ai_sdlc_overview.md) first, then dive into [`methodology/ai_sdlc_method.md`](methodology/ai_sdlc_method.md) for details!

---

## 🎓 Learning Path by Role

### For Business Analysts / Product Owners

**Focus**: Requirements stage and business validation

1. Read [`../INTENT.md`](../INTENT.md) - This project's intent
2. Read [`methodology/ai_sdlc_overview.md`](methodology/ai_sdlc_overview.md) - Get the big picture
3. Read [`methodology/ai_sdlc_method.md`](methodology/ai_sdlc_method.md) - Section 4.0 (Requirements Stage)
4. Read [`methodology/ai_sdlc_method.md`](methodology/ai_sdlc_method.md) - Section 9.0 (UAT Stage)
5. Review [`../examples/local_projects/customer_portal/`](../examples/local_projects/customer_portal/) - Requirements artifacts
6. Review [`../examples/local_projects/customer_portal/config/config.yml`](../examples/local_projects/customer_portal/config/config.yml) - Requirements agent configuration

**Key Concepts**: Intent transformation, requirement keys (REQ-F-*, REQ-NFR-*, REQ-DATA-*), acceptance criteria, traceability

### For Architects / Technical Leads

**Focus**: Design stage and technical solution

1. Read [`../INTENT.md`](../INTENT.md) - This project's intent
2. Read [`methodology/ai_sdlc_overview.md`](methodology/ai_sdlc_overview.md) - Get the big picture
3. Read [`methodology/ai_sdlc_method.md`](methodology/ai_sdlc_method.md) - Section 5.0 (Design Stage)
4. Read [`design/AI_SDLC_UX_DESIGN.md`](design/AI_SDLC_UX_DESIGN.md) - This project's UX design
5. Read [`methodology/ai_sdlc_appendices.md`](methodology/ai_sdlc_appendices.md) - Advanced architectural concepts
6. Review [`../examples/local_projects/customer_portal/`](../examples/local_projects/customer_portal/) - Design artifacts
7. Review [`../plugins/aisdlc-methodology/config/stages_config.yml`](../plugins/aisdlc-methodology/config/stages_config.yml) - Design agent spec

**Key Concepts**: Requirements → Technical solution, component design, data models, API specifications, ADRs, traceability matrix

### For Developers

**Focus**: Code stage (TDD workflow)

1. Read [`../INTENT.md`](../INTENT.md) - This project's intent
2. Read [`methodology/ai_sdlc_overview.md`](methodology/ai_sdlc_overview.md) - Get the big picture
3. Read [`methodology/ai_sdlc_method.md`](methodology/ai_sdlc_method.md) - Section 7.0 (Code Stage)
4. Read [`../plugins/aisdlc-methodology/docs/principles/KEY_PRINCIPLES.md`](../plugins/aisdlc-methodology/docs/principles/KEY_PRINCIPLES.md) - Sacred Seven Principles
5. Read [`../plugins/aisdlc-methodology/docs/processes/TDD_WORKFLOW.md`](../plugins/aisdlc-methodology/docs/processes/TDD_WORKFLOW.md) - TDD cycle
6. Review [`../examples/local_projects/customer_portal/`](../examples/local_projects/customer_portal/) - Code stage walkthrough

**Key Concepts**: TDD (RED→GREEN→REFACTOR), requirement tagging, test coverage (≥80%), Sacred Seven Principles

### For QA Engineers

**Focus**: System Test and UAT stages (BDD testing)

1. Read [`../INTENT.md`](../INTENT.md) - This project's intent
2. Read [`methodology/ai_sdlc_overview.md`](methodology/ai_sdlc_overview.md) - Get the big picture
3. Read [`methodology/ai_sdlc_method.md`](methodology/ai_sdlc_method.md) - Section 8.0 (System Test Stage)
4. Read [`methodology/ai_sdlc_method.md`](methodology/ai_sdlc_method.md) - Section 9.0 (UAT Stage)
5. Review [`../examples/local_projects/customer_portal/`](../examples/local_projects/customer_portal/) - BDD testing examples
6. Review [`../examples/local_projects/customer_portal/config/config.yml`](../examples/local_projects/customer_portal/config/config.yml) - Test agent configurations

**Key Concepts**: BDD (Given/When/Then), requirement coverage (≥95%), scenario-to-requirement matrix, business validation

### For DevOps / SRE

**Focus**: Runtime Feedback stage (observability)

1. Read [`../INTENT.md`](../INTENT.md) - This project's intent
2. Read [`methodology/ai_sdlc_overview.md`](methodology/ai_sdlc_overview.md) - Get the big picture
3. Read [`methodology/ai_sdlc_method.md`](methodology/ai_sdlc_method.md) - Section 10.0 (Runtime Feedback Stage)
4. Read [`methodology/ai_sdlc_method.md`](methodology/ai_sdlc_method.md) - Section 2.0 (End-to-End Intent Lifecycle)
5. Review [`../examples/local_projects/customer_portal/`](../examples/local_projects/customer_portal/) - Runtime feedback section
6. Review [`../examples/local_projects/customer_portal/config/config.yml`](../examples/local_projects/customer_portal/config/config.yml) - Runtime feedback agent config

**Key Concepts**: Release manifests, requirement key tagging in telemetry, alerts → intents feedback loop, observability platforms

### For Project Managers / Scrum Masters

**Focus**: Tasks stage (work breakdown and orchestration)

1. Read [`../INTENT.md`](../INTENT.md) - This project's intent
2. Read [`methodology/ai_sdlc_overview.md`](methodology/ai_sdlc_overview.md) - Get the big picture
3. Read [`methodology/ai_sdlc_method.md`](methodology/ai_sdlc_method.md) - Section 6.0 (Tasks Stage)
4. Read [`methodology/ai_sdlc_method.md`](methodology/ai_sdlc_method.md) - Section 3.0 (Builder Pipeline Overview)
5. Review [`../examples/local_projects/customer_portal/`](../examples/local_projects/customer_portal/) - Tasks stage
6. Review [`../examples/local_projects/customer_portal/config/config.yml`](../examples/local_projects/customer_portal/config/config.yml) - Tasks orchestrator config

**Key Concepts**: Design → Work units, Jira integration, requirement key tagging, dependency tracking, agent orchestration

---

## 📘 Stage-by-Stage Documentation

### Stage 1: Requirements

**Output Location:** `docs/requirements/`

**Agent:** Requirements Agent (`.claude/agents/requirements-agent.md`)

**Input:** `INTENT.md` (raw business intent)

**Output:** Structured requirements with unique keys (REQ-F-*, REQ-NFR-*, REQ-DATA-*, REQ-BR-*)

**Key Documents:**
- [`requirements/FOLDER_BASED_REQUIREMENTS.md`](requirements/FOLDER_BASED_REQUIREMENTS.md)

**Reference:**
- [`methodology/ai_sdlc_method.md - Section 4.0`](methodology/ai_sdlc_method.md#40-requirements-stage)
- [`../plugins/aisdlc-methodology/config/stages_config.yml`](../plugins/aisdlc-methodology/config/stages_config.yml)

### Stage 2: Design

**Output Location:** `docs/design/`

**Agent:** Design Agent (`.claude/agents/design-agent.md`)

**Input:** Structured requirements

**Output:** Component diagrams, data models, API specs, ADRs, traceability matrix

**Key Documents:**
- [`design/AI_SDLC_UX_DESIGN.md`](design/AI_SDLC_UX_DESIGN.md) - Overall UX design (1,400 lines)
- [`design/CLAUDE_AGENTS_EXPLAINED.md`](design/CLAUDE_AGENTS_EXPLAINED.md) - Agent system architecture
- [`design/FOLDER_BASED_ASSET_DISCOVERY.md`](design/FOLDER_BASED_ASSET_DISCOVERY.md) - Asset discovery system
- [`design/AGENTS_SKILLS_INTEROPERATION.md`](design/AGENTS_SKILLS_INTEROPERATION.md) - Agent/skill integration

**Reference:**
- [`methodology/ai_sdlc_method.md - Section 5.0`](methodology/ai_sdlc_method.md#50-design-stage)

### Stage 3: Tasks

**Output Location:** `.ai-workspace/tasks/`

**Agent:** Tasks Agent (`.claude/agents/tasks-agent.md`)

**Input:** Design artifacts

**Output:** Jira tickets with requirement tags, dependency graph, capacity planning

**Key Documents:**
- `.ai-workspace/tasks/active/ACTIVE_TASKS.md` (current work)
- `.ai-workspace/tasks/todo/TODO_LIST.md` (backlog)
- `.ai-workspace/tasks/finished/` (completed tasks)

**Reference:**
- [`methodology/ai_sdlc_method.md - Section 6.0`](methodology/ai_sdlc_method.md#60-tasks-stage)

### Stage 4: Code

**Output Location:** `src/`, `tests/`, `installers/`, `plugins/`

**Agent:** Code Agent (`.claude/agents/code-agent.md`)

**Input:** Work units from Tasks stage

**Output:** Production code with requirement tags, unit tests, integration tests

**Methodology:** TDD (RED → GREEN → REFACTOR) + Sacred Seven Principles

**Key Documents:**
- Source code in `../installers/`, `../plugins/`
- Tests co-located with source

**Reference:**
- [`methodology/ai_sdlc_method.md - Section 7.0`](methodology/ai_sdlc_method.md#70-code-stage)
- [`../plugins/aisdlc-methodology/docs/principles/KEY_PRINCIPLES.md`](../plugins/aisdlc-methodology/docs/principles/KEY_PRINCIPLES.md)
- [`../plugins/aisdlc-methodology/docs/processes/TDD_WORKFLOW.md`](../plugins/aisdlc-methodology/docs/processes/TDD_WORKFLOW.md)

### Stage 5: System Test

**Output Location:** `tests/bdd/` (TODO)

**Agent:** System Test Agent (`.claude/agents/system-test-agent.md`)

**Input:** Deployed code

**Output:** BDD feature files (Gherkin), step definitions, coverage matrix

**Methodology:** BDD (Given/When/Then)

**Reference:**
- [`methodology/ai_sdlc_method.md - Section 8.0`](methodology/ai_sdlc_method.md#80-system-test-stage)

### Stage 6: UAT

**Output Location:** `docs/uat/` (TODO)

**Agent:** UAT Agent (`.claude/agents/uat-agent.md`)

**Input:** System test passed

**Output:** Manual UAT test cases, automated UAT tests, business sign-off

**Methodology:** BDD in pure business language

**Reference:**
- [`methodology/ai_sdlc_method.md - Section 9.0`](methodology/ai_sdlc_method.md#90-uat-stage)

### Stage 7: Runtime Feedback

**Output Location:** Production systems (telemetry, logs, alerts)

**Agent:** Runtime Feedback Agent (`.claude/agents/runtime-feedback-agent.md`)

**Input:** Production deployment

**Output:** Release manifests, runtime telemetry (tagged with REQ keys), alerts, new intents

**Reference:**
- [`methodology/ai_sdlc_method.md - Section 10.0`](methodology/ai_sdlc_method.md#100-runtime-feedback-stage)

---

## 🔗 Related Documentation

### Plugin Documentation

- **[../plugins/aisdlc-methodology/README.md](../plugins/aisdlc-methodology/README.md)** - 7-stage methodology plugin
- **[../plugins/README.md](../plugins/README.md)** - Plugin creation and usage guide

### Example Projects

- **[../examples/local_projects/customer_portal/README.md](../examples/local_projects/customer_portal/README.md)** - Complete 7-stage workflow example (800+ lines)
- **[../examples/local_projects/data_mapper.test02/](../examples/local_projects/data_mapper.test02/)** - Category Theory data mapper (dogfooding AI SDLC)
- **[../examples/README.md](../examples/README.md)** - All examples overview

---

## 🔍 Common Questions

**"What is the AI SDLC methodology?"**
→ [`methodology/ai_sdlc_overview.md`](methodology/ai_sdlc_overview.md) - Quick introduction
→ [`methodology/ai_sdlc_method.md - Section 1.0`](methodology/ai_sdlc_method.md) - Detailed introduction

**"Why is INTENT.md required?"**
→ Every project needs a clear business problem statement that kicks off the Requirements Stage
→ See: [`../INTENT.md`](../INTENT.md) (this project's example)

**"How do the 7 stages work?"**
→ [`methodology/ai_sdlc_overview.md`](methodology/ai_sdlc_overview.md) - High-level overview
→ [`methodology/ai_sdlc_method.md`](methodology/ai_sdlc_method.md) - Sections 4.0-10.0 (detailed)

**"How does requirement traceability work?"**
→ [`methodology/ai_sdlc_method.md - Section 4.3.4`](methodology/ai_sdlc_method.md) - Requirement Keys
→ [`../examples/local_projects/customer_portal/README.md`](../examples/local_projects/customer_portal/README.md) - Traceability section

**"What are the Sacred Seven Principles?"**
→ [`../plugins/aisdlc-methodology/docs/principles/KEY_PRINCIPLES.md`](../plugins/aisdlc-methodology/docs/principles/KEY_PRINCIPLES.md)

**"How does TDD work in this methodology?"**
→ [`methodology/ai_sdlc_method.md - Section 7.0`](methodology/ai_sdlc_method.md) - Code Stage
→ [`../plugins/aisdlc-methodology/docs/processes/TDD_WORKFLOW.md`](../plugins/aisdlc-methodology/docs/processes/TDD_WORKFLOW.md)

**"How does BDD testing work?"**
→ [`methodology/ai_sdlc_method.md - Sections 8.0 & 9.0`](methodology/ai_sdlc_method.md) - System Test & UAT

**"How do I install and use the plugin?"**
→ [`../README.md`](../README.md) - Quick Start section
→ [`../QUICKSTART.md`](../QUICKSTART.md) - Detailed installation

**"How do I create my own project with this methodology?"**
→ [`../PLUGIN_GUIDE.md`](../PLUGIN_GUIDE.md) - Plugin creation guide
→ [`../examples/local_projects/customer_portal/`](../examples/local_projects/customer_portal/) - Complete example

**"What are the advanced technical concepts?"**
→ [`methodology/ai_sdlc_appendices.md`](methodology/ai_sdlc_appendices.md) - Category theory, ecosystem integration

---

## 🤝 Contributing

This project dogfoods its own methodology. When contributing:

1. **Check the Intent:** [`../INTENT.md`](../INTENT.md) - Understand project goals
2. **Review Current Tasks:** `.ai-workspace/tasks/active/ACTIVE_TASKS.md`
3. **Follow Sacred Seven:** Especially TDD (no code without tests)
4. **Maintain Traceability:** Tag commits with REQ keys when appropriate

**When adding new documentation:**

1. **Requirements docs** → Add to `requirements/`
2. **Design docs** → Add to `design/`
3. **Methodology updates** → Update `methodology/ai_sdlc_method.md` or add to `../plugins/aisdlc-methodology/docs/`
4. **Examples** → Add to `../examples/`
5. **Update this README** → Add links to new documentation

**Documentation Versioning:**
- Major methodology changes → Increment version in `methodology/ai_sdlc_method.md` header
- Archive previous versions → Move to `deprecated/`

---

## 📄 License

See [`../LICENSE`](../LICENSE) for license information.

---

*Last updated: 2025-01-22*

**Version**: 2.0 - Documentation reorganized to follow AI SDLC stage structure
- Added explicit INTENT.md requirement
- Reorganized by stage: requirements/, design/, methodology/
- Dogfooding our own methodology

**"Excellence or nothing"** 🔥
