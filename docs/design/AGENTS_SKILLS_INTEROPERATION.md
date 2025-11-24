# Agents and Skills Interoperation

**How AI SDLC agents and skills work together to execute the 7-stage methodology**

---

## Architecture Overview

The AI SDLC system uses a **two-layer architecture**:

1. **Agents Layer** - WHO Claude is and WHAT stage responsibilities
2. **Skills Layer** - HOW to execute specific tasks using reusable patterns

```
┌─────────────────────────────────────────────────────────────┐
│                      USER REQUEST                            │
│        "Implement authentication feature"                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   AGENTS LAYER                               │
│  (.claude/agents/*.md - Role & Responsibilities)             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Requirements │  │   Design     │  │    Tasks     │      │
│  │    Agent     │→ │    Agent     │→ │    Agent     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         │                  │                  │              │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐      │
│  │    Code      │  │ System Test  │  │     UAT      │      │
│  │    Agent     │→ │    Agent     │→ │    Agent     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                            ▼                                 │
│                  ┌──────────────────┐                        │
│                  │Runtime Feedback  │                        │
│                  │     Agent        │                        │
│                  └─────────┬────────┘                        │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   SKILLS LAYER                               │
│  (plugins/*-skills/ - Reusable Execution Patterns)           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  requirements-skills/        code-skills/                   │
│  ├─ requirement-extraction   ├─ tdd/                        │
│  ├─ disambiguate             │  ├─ red-phase                │
│  ├─ extract-business-rules   │  ├─ green-phase              │
│  ├─ validate-requirements    │  ├─ refactor-phase           │
│  └─ create-traceability      │  └─ commit-with-req-tag      │
│                              ├─ bdd/                        │
│  design-skills/              ├─ generation/                 │
│  ├─ component-design         └─ debt/                       │
│  ├─ api-specification                                        │
│  └─ data-modeling            testing-skills/                │
│                              ├─ bdd-scenarios                │
│  runtime-skills/             ├─ coverage-validation          │
│  ├─ telemetry-setup          └─ test-generation             │
│  ├─ req-key-tagging                                         │
│  └─ feedback-loop                                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Agents (WHO + WHAT)

**Location**: `.claude/agents/*.md` (project-specific) or `templates/claude/.claude/agents/*.md` (installed by installer)

**Purpose**: Define Claude's **role, responsibilities, inputs, outputs** for each SDLC stage

### Available Agents

| Agent File | Stage | Role | Key Responsibilities |
|------------|-------|------|---------------------|
| `requirements-agent.md` | 1 - Requirements | Intent Store & Traceability Hub | Transform intent → REQ-* keys (F, NFR, DATA, BR) |
| `design-agent.md` | 2 - Design | Architecture & Data Design | Create components, APIs, data models, ADRs |
| `tasks-agent.md` | 3 - Tasks | Work Breakdown & Orchestration | Generate Jira tickets, map dependencies |
| `code-agent.md` | 4 - Code | TDD Implementation | Implement using RED→GREEN→REFACTOR cycle |
| `system-test-agent.md` | 5 - System Test | BDD Integration Testing | Create Given/When/Then scenarios, validate ≥95% coverage |
| `uat-agent.md` | 6 - UAT | Business Validation | Generate UAT cases, obtain sign-off |
| `runtime-feedback-agent.md` | 7 - Runtime Feedback | Production Monitoring | Setup telemetry, tag with REQ keys, close feedback loop |

### Agent Activation

Agents can be activated in multiple ways:

**1. Explicit Invocation** (via slash command):
```bash
# Example: Switch to Code Agent context
/agent code-agent
```

**2. Stage-Based Auto-Loading** (via config):
```yaml
# In config/config.yml
ai_sdlc:
  current_stage: code
  # Automatically loads code-agent.md
```

**3. Manual Context** (user specifies):
```
User: "I'm working on the Code stage for REQ-F-DEMO-AUTH-001"
Claude: [Internally loads code-agent.md context]
```

---

## Skills (HOW)

**Location**: `plugins/*-skills/skills/` (installed via plugin system)

**Purpose**: **Reusable execution patterns** that agents invoke to perform work

### Available Skills

#### 1. Requirements Skills (`requirements-skills/`)

**Purpose**: Extract and validate requirements from intent

**Skills**:
- `requirement-extraction` - Extract REQ-F-*, REQ-NFR-*, REQ-DATA-* from intent
- `disambiguate-requirements` - Clarify ambiguous requirements
- `extract-business-rules` - Extract BR-* (business rules)
- `extract-constraints` - Extract C-* (constraints)
- `extract-formulas` - Extract F-* (formulas)
- `validate-requirements` - Check for completeness, consistency
- `create-traceability-matrix` - Generate requirement → artifact mapping

**Used By**: Requirements Agent

---

#### 2. Design Skills (`design-skills/`)

**Purpose**: Create technical solution architecture

**Skills**:
- `component-design` - Create component diagrams (Mermaid)
- `api-specification` - Generate OpenAPI specs
- `data-modeling` - Design conceptual/logical/physical models
- `architecture-decision-records` - Document ADRs with rationale

**Used By**: Design Agent

---

#### 3. Code Skills (`code-skills/`)

**Purpose**: Implement code using TDD, BDD, and auto-generation

**Skills**:

##### TDD Workflow (5 skills)
- `tdd-workflow` - Orchestrator coordinating full TDD cycle
- `red-phase` - Write failing tests first
- `green-phase` - Implement minimal code to pass
- `refactor-phase` - Improve code quality ✅ **COMPLETE**
- `commit-with-req-tag` - Git commits tagged with REQ-* keys

##### BDD Workflow (5 skills)
- `bdd-workflow` - Orchestrator coordinating BDD cycle
- `write-scenario` - Create Gherkin Given/When/Then scenarios
- `implement-step-definitions` - Implement step definitions
- `implement-feature` - Implement feature code
- `refactor-bdd` - Refactor BDD implementation

##### Code Generation (4 skills)
- `autogenerate-from-business-rules` - Generate code from BR-* rules
- `autogenerate-validators` - Generate validation code from BR-*
- `autogenerate-constraints` - Generate constraint checks from C-*
- `autogenerate-formulas` - Generate formula implementations from F-*

##### Tech Debt Management (4 skills) ✅ **COMPLETE**
- `detect-unused-code` - Find unused imports, dead code ✅
- `prune-unused-code` - Auto-delete unused code ✅
- `detect-complexity` - Find over-complex logic (cyclomatic complexity > 10) ✅
- `simplify-complex-code` - Extract functions to reduce complexity ✅

**Used By**: Code Agent, System Test Agent

---

#### 4. Testing Skills (`testing-skills/`)

**Purpose**: Generate and validate tests

**Skills**:
- `bdd-scenarios` - Create BDD scenarios from requirements
- `test-generation` - Auto-generate unit tests
- `coverage-validation` - Ensure ≥95% requirement coverage
- `performance-testing` - Validate NFR performance requirements

**Used By**: Code Agent, System Test Agent, UAT Agent

---

#### 5. Runtime Skills (`runtime-skills/`)

**Purpose**: Setup production monitoring and feedback loops

**Skills**:
- `telemetry-setup` - Configure metrics, logs, traces
- `req-key-tagging` - Tag all telemetry with REQ-* keys
- `feedback-loop` - Generate new intents from production issues
- `alert-configuration` - Setup alerts for requirement violations

**Used By**: Runtime Feedback Agent

---

## Interoperation Examples

### Example 1: Requirements Agent Uses Requirements Skills

```
User: "Create requirements for authentication feature"

┌─────────────────────────────────────────────────────────┐
│ AGENT: requirements-agent.md                            │
│ Role: Intent Store & Traceability Hub                   │
│ Mission: Transform intent into structured requirements  │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ SKILL: requirement-extraction                           │
│ Action: Extract REQ-F-*, REQ-NFR-*, REQ-DATA-*         │
├─────────────────────────────────────────────────────────┤
│ Output:                                                 │
│   REQ-F-DEMO-AUTH-001: User login with email/password       │
│   REQ-F-DEMO-AUTH-002: User registration                    │
│   REQ-NFR-DEMO-PERF-001: Login response < 500ms             │
│   REQ-NFR-DEMO-SEC-001: Passwords hashed with bcrypt        │
│   REQ-DATA-001: Email format validation                │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ SKILL: extract-business-rules                           │
│ Action: Extract BR-* from requirements                  │
├─────────────────────────────────────────────────────────┤
│ Output:                                                 │
│   BR-001: Email regex validation                       │
│   BR-002: Password min 12 characters                   │
│   C-001: Max 3 login attempts, 15min lockout           │
│   F-001: lockout_time = last_attempt + (15 * 60)       │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ SKILL: create-traceability-matrix                       │
│ Action: Generate requirement traceability               │
├─────────────────────────────────────────────────────────┤
│ Output: traceability_matrix.yml                         │
│   REQ-F-DEMO-AUTH-001 → [Components, Tests, Code]           │
└─────────────────────────────────────────────────────────┘
```

---

### Example 2: Code Agent Uses Code Skills (TDD)

```
User: "Implement REQ-F-DEMO-AUTH-001 (user login)"

┌─────────────────────────────────────────────────────────┐
│ AGENT: code-agent.md                                    │
│ Role: TDD-Driven Implementation                         │
│ Mission: Implement using RED→GREEN→REFACTOR cycle       │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ SKILL: red-phase                                        │
│ Action: Write failing test first                        │
├─────────────────────────────────────────────────────────┤
│ Output: test_auth.py                                    │
│   def test_login_with_valid_credentials():             │
│       # Validates: REQ-F-DEMO-AUTH-001                       │
│       result = login("user@example.com", "Pass123!")    │
│       assert result.success == True                     │
│                                                          │
│ Status: ❌ FAILED (RED) ✓                               │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ SKILL: green-phase                                      │
│ Action: Implement minimal code to pass                  │
├─────────────────────────────────────────────────────────┤
│ Output: auth_service.py                                 │
│   # Implements: REQ-F-DEMO-AUTH-001                          │
│   def login(email: str, password: str) -> LoginResult:  │
│       user = UserRepository.find_by_email(email)        │
│       if user and user.check_password(password):        │
│           return LoginResult(success=True, user=user)   │
│       return LoginResult(success=False)                 │
│                                                          │
│ Status: ✅ PASSED (GREEN) ✓                             │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ SKILL: detect-unused-code (Tech Debt Sensor)            │
│ Action: Find unused imports, dead code                  │
├─────────────────────────────────────────────────────────┤
│ Output: Found 3 unused imports, 1 dead function         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ SKILL: prune-unused-code (Tech Debt Actuator)           │
│ Action: Auto-delete unused code                         │
├─────────────────────────────────────────────────────────┤
│ Output: Deleted 3 imports, 1 function, 12 lines         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ SKILL: detect-complexity (Tech Debt Sensor)             │
│ Action: Find over-complex logic                         │
├─────────────────────────────────────────────────────────┤
│ Output: login() complexity 15 (max: 10)                 │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ SKILL: simplify-complex-code (Tech Debt Actuator)       │
│ Action: Extract functions to reduce complexity          │
├─────────────────────────────────────────────────────────┤
│ Output: Extracted 2 helper functions                    │
│   - validate_credentials()                              │
│   - create_session()                                    │
│                                                          │
│ Result: login() complexity 15 → 6 ✓                     │
│ Status: ✅ TESTS STILL PASSING (REFACTOR) ✓             │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ SKILL: commit-with-req-tag                              │
│ Action: Git commit with requirement traceability        │
├─────────────────────────────────────────────────────────┤
│ Output:                                                 │
│   git commit -m "feat: Add user login (REQ-F-DEMO-AUTH-001)" │
│                                                          │
│ Status: ✅ COMMITTED                                    │
└─────────────────────────────────────────────────────────┘
```

---

### Example 3: System Test Agent Uses Testing Skills + Code Skills (BDD)

```
User: "Create BDD scenarios for REQ-F-DEMO-AUTH-001"

┌─────────────────────────────────────────────────────────┐
│ AGENT: system-test-agent.md                             │
│ Role: BDD Integration Testing                           │
│ Mission: Create Given/When/Then scenarios               │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ SKILL: bdd-scenarios (from testing-skills)              │
│ Action: Generate Gherkin scenarios from requirements    │
├─────────────────────────────────────────────────────────┤
│ Output: features/authentication.feature                 │
│   Feature: User Authentication                          │
│     # Validates: REQ-F-DEMO-AUTH-001                         │
│                                                          │
│     Scenario: Successful login                          │
│       Given I am on the login page                      │
│       When I enter "user@example.com" and "Pass123!"    │
│       And I click "Login"                               │
│       Then I should see "Welcome back"                  │
│       And response time should be < 500ms               │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ SKILL: write-scenario (from code-skills/bdd)            │
│ Action: Create step definitions                         │
├─────────────────────────────────────────────────────────┤
│ Output: step_definitions/auth_steps.py                  │
│   @given('I am on the login page')                      │
│   def step_impl(context):                               │
│       context.page = LoginPage()                        │
│                                                          │
│   @when('I enter "{email}" and "{password}"')           │
│   def step_impl(context, email, password):              │
│       context.page.enter_email(email)                   │
│       context.page.enter_password(password)             │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ SKILL: coverage-validation (from testing-skills)        │
│ Action: Validate ≥95% requirement coverage              │
├─────────────────────────────────────────────────────────┤
│ Output:                                                 │
│   REQ-F-DEMO-AUTH-001: ✅ 100% covered (login.feature)       │
│   REQ-F-DEMO-AUTH-002: ✅ 100% covered (register.feature)    │
│   REQ-NFR-DEMO-PERF-001: ✅ Validated (< 500ms)              │
│                                                          │
│ Overall Coverage: 100% ✅                               │
└─────────────────────────────────────────────────────────┘
```

---

### Example 4: Runtime Feedback Agent Uses Runtime Skills

```
Production Issue: "Auth timeout 850ms (target: 500ms)"

┌─────────────────────────────────────────────────────────┐
│ AGENT: runtime-feedback-agent.md                        │
│ Role: Production Monitoring & Feedback Loop             │
│ Mission: Close feedback loop to requirements            │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ SKILL: telemetry-setup (from runtime-skills)            │
│ Action: Tag metrics with REQ keys                       │
├─────────────────────────────────────────────────────────┤
│ Output: Datadog/CloudWatch metrics                      │
│   logger.info('User login', {                           │
│     event: 'USER_LOGIN',                                │
│     requirements: ['REQ-F-DEMO-AUTH-001', 'REQ-NFR-DEMO-PERF-001']│
│     duration: 850,                                      │
│     success: true                                       │
│   });                                                   │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Alert Detected: REQ-NFR-DEMO-PERF-001 violated               │
│   Target: 500ms                                         │
│   Actual: 850ms                                         │
│   Deviation: +70%                                       │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ SKILL: feedback-loop (from runtime-skills)              │
│ Action: Generate new intent from production issue       │
├─────────────────────────────────────────────────────────┤
│ Output: New Intent                                      │
│   INT-042: "Optimize authentication performance"       │
│   Reason: REQ-NFR-DEMO-PERF-001 violated (850ms vs 500ms)    │
│   Priority: HIGH                                        │
│   Impacted Requirements: [REQ-NFR-DEMO-PERF-001]             │
│                                                          │
│ Status: ✅ Feedback loop closed                         │
│ Next: Feed INT-042 back to Requirements Agent           │
└─────────────────────────────────────────────────────────┘
```

---

## Installation

### Install Agents (via installer)

```bash
# Install all templates (including agents)
python /path/to/ai_sdlc_method/installers/setup_all.py

# This copies agents to:
#   .claude/agents/requirements-agent.md
#   .claude/agents/design-agent.md
#   .claude/agents/tasks-agent.md
#   .claude/agents/code-agent.md
#   .claude/agents/system-test-agent.md
#   .claude/agents/uat-agent.md
#   .claude/agents/runtime-feedback-agent.md
```

### Install Skills (via plugin system)

```bash
# Option 1: Install individual skills
python /path/to/ai_sdlc_method/installers/setup_plugins.py --global --plugin requirements-skills
python /path/to/ai_sdlc_method/installers/setup_plugins.py --global --plugin code-skills
python /path/to/ai_sdlc_method/installers/setup_plugins.py --global --plugin testing-skills

# Option 2: Install bundles
python /path/to/ai_sdlc_method/installers/setup_plugins.py --global --bundle startup
# Startup bundle includes:
#   - aisdlc-core (requirement traceability)
#   - requirements-skills
#   - code-skills
#   - testing-skills
#   - principles-key
```

---

## Configuration

### Agent Configuration

Agents can be auto-loaded based on current SDLC stage:

```yaml
# config/config.yml
ai_sdlc:
  current_stage: code  # Auto-loads code-agent.md

  # OR explicitly specify
  agent: "code-agent"  # Loads .claude/agents/code-agent.md
```

### Skills Configuration

Skills are configured via plugin settings:

```yaml
# .claude/plugins.yml
plugins:
  - name: "@aisdlc/code-skills"
    config:
      tdd:
        minimum_coverage: 90
        enforce_red_green_refactor: true

      tech_debt:
        auto_detect_on_refactor: true
        max_complexity: 10

  - name: "@aisdlc/requirements-skills"
    config:
      requirement_format: "REQ-{TYPE}-{DOMAIN}-{SEQUENCE}"
      auto_extract_business_rules: true
```

---

## Skill Invocation

Skills can be invoked in multiple ways:

### 1. Automatic (Agent decides)

```
User: "Implement user login"

Code Agent (autonomously):
  1. Invokes: red-phase skill → writes failing test
  2. Invokes: green-phase skill → implements minimal code
  3. Invokes: refactor-phase skill → improves quality
  4. Invokes: commit-with-req-tag skill → commits with REQ tag
```

### 2. Explicit (User requests)

```
User: "Use the BDD workflow skill to create login scenarios"

System Test Agent:
  → Invokes: bdd-workflow skill
  → Generates: login.feature with Given/When/Then scenarios
```

### 3. Homeostatic (Sensor → Actuator)

```
Code Agent (during refactor):
  → Invokes: detect-unused-code (Sensor)
  → Deviation detected: 5 unused imports
  → Invokes: prune-unused-code (Actuator)
  → Deleted: 5 imports
  → Re-check: detect-unused-code (Sensor)
  → Homeostasis achieved: 0 unused imports ✓
```

---

## Benefits of Agent-Skill Separation

### 1. Reusability
- **Same skills, different agents**: TDD skills used by Code Agent and System Test Agent
- **Cross-stage skills**: BDD skills used by System Test Agent and UAT Agent

### 2. Composability
- **Mix and match**: Code Agent can combine TDD + BDD + Tech Debt skills
- **Extensibility**: Add new skills without modifying agents

### 3. Maintainability
- **Single responsibility**: Agents = context, Skills = execution
- **Clear boundaries**: Easy to understand, test, and debug

### 4. Scalability
- **New stages**: Add new agents without changing skills
- **New capabilities**: Add new skills without changing agents

---

## Skill Development Status

| Plugin | Skills Complete | Total | Status |
|--------|----------------|-------|--------|
| requirements-skills | 8 | 8 | ✅ Complete |
| code-skills | 5 | 18 | 🟡 28% |
| testing-skills | TBD | TBD | ⏳ Pending |
| design-skills | TBD | TBD | ⏳ Pending |
| runtime-skills | TBD | TBD | ⏳ Pending |

---

## Summary

**Agents** = WHO you are + WHAT stage responsibilities
**Skills** = HOW you execute tasks using reusable patterns

**Together**:
```
User Request
  ↓
Agent (loads context + responsibilities)
  ↓
Skills (executes specific tasks)
  ↓
Output (requirement-traceable artifacts)
```

**Example Flow**:
```
INT-001 "Customer Portal"
  ↓
Requirements Agent + requirement-extraction skill
  → REQ-F-DEMO-AUTH-001
  ↓
Design Agent + component-design skill
  → AuthenticationService
  ↓
Code Agent + tdd-workflow skill
  → RED → GREEN → REFACTOR → COMMIT
  ↓
System Test Agent + bdd-scenarios skill
  → login.feature (Given/When/Then)
  ↓
Runtime Feedback Agent + telemetry-setup skill
  → Production metrics tagged with REQ-F-DEMO-AUTH-001
  ↓
Feedback loop closes: New intent generated if issues detected
```

---

**"Excellence or nothing"** 🔥
