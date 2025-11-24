# AI SDLC Skills Inventory

**Total Skills:** 41 across 7 plugins
**Last Updated:** 2025-11-23
**Purpose:** Master list of all available skills to prevent confusion and duplication

---

## Skills by Plugin

### 🏗️ aisdlc-core (3 skills) - Foundation

**Purpose:** Requirement traceability infrastructure

| Skill | Type | Description |
|-------|------|-------------|
| `requirement-traceability` | Foundation | Define and validate REQ-* key patterns |
| `check-requirement-coverage` | Sensor | Detect requirements without implementation |
| `propagate-req-keys` | Actuator | Auto-tag code/commits with REQ-* keys |

**Location:** `plugins/aisdlc-core/skills/`

---

### 🎯 principles-key (2 skills) - Quality Gate

**Purpose:** Enforce the 7 Key Principles

| Skill | Type | Description |
|-------|------|-------------|
| `apply-key-principles` | Validator | Validate code against 7 principles |
| `seven-questions-checklist` | Quality Gate | Pre-coding checklist (blocks if violated) |

**Location:** `plugins/principles-key/skills/`

**The 7 Principles:**
1. Test Driven Development
2. Fail Fast & Root Cause
3. Modular & Maintainable
4. Reuse Before Build
5. Open Source First
6. No Legacy Baggage
7. Perfectionist Excellence

---

### 📝 requirements-skills (8 skills) - Intent → Requirements

**Purpose:** Transform raw intent into structured requirements

#### Requirement Extraction (1 skill)
| Skill | Type | Description |
|-------|------|-------------|
| `requirement-extraction` | Extractor | Parse intent into structured REQ-* requirements |

#### Requirement Disambiguation (4 skills)
| Skill | Type | Description |
|-------|------|-------------|
| `disambiguate-requirements` | Disambiguator | Break vague requirements into precise components |
| `extract-business-rules` | Extractor | Extract BR-* business rules (auto-generatable) |
| `extract-constraints` | Extractor | Extract C-* constraints (validators) |
| `extract-formulas` | Extractor | Extract F-* formulas (calculations) |

#### Traceability Management (3 skills)
| Skill | Type | Description |
|-------|------|-------------|
| `create-traceability-matrix` | Reporter | Generate requirement → artifact matrix |
| `validate-requirements` | Validator | Ensure unique keys, testable format |
| `refine-requirements` | Updater | Update requirements from TDD/BDD discoveries |

**Location:** `plugins/requirements-skills/skills/`

---

### 🏛️ design-skills (3 skills) - Requirements → Architecture

**Purpose:** Create traceable technical designs

| Skill | Type | Description |
|-------|------|-------------|
| `design-with-traceability` | Designer | Transform requirements → architecture (tagged with REQ-*) |
| `create-adrs` | Documentation | Document architecture decisions with ecosystem E(t) |
| `validate-design-coverage` | Validator | Ensure all requirements have design coverage |

**Location:** `plugins/design-skills/skills/`

---

### 💻 code-skills (21 skills) - TDD, BDD, Code Generation

**Purpose:** Complete code development workflow

#### TDD Workflow (5 skills)
| Skill | Type | Description |
|-------|------|-------------|
| `tdd-workflow` | Orchestrator | Complete RED → GREEN → REFACTOR cycle |
| `red-phase` | TDD Phase | Write failing test first |
| `green-phase` | TDD Phase | Implement minimal code to pass |
| `refactor-phase` | TDD Phase | Improve code quality while keeping tests green |
| `commit-with-req-tag` | TDD Phase | Commit with REQ-* tag in message |

#### BDD Workflow (5 skills)
| Skill | Type | Description |
|-------|------|-------------|
| `bdd-workflow` | Orchestrator | Complete BDD cycle (Given/When/Then) |
| `write-scenario` | BDD Phase | Write Gherkin scenarios |
| `implement-step-definitions` | BDD Phase | Implement step definitions |
| `implement-feature` | BDD Phase | Create complete feature files |
| `refactor-bdd` | BDD Phase | Refactor BDD code |

#### Code Generation (4 skills)
| Skill | Type | Description |
|-------|------|-------------|
| `autogenerate-from-business-rules` | Generator | Auto-generate code from BR-* rules |
| `autogenerate-validators` | Generator | Generate validators from C-* constraints |
| `autogenerate-constraints` | Generator | Generate constraint enforcement |
| `autogenerate-formulas` | Generator | Generate calculators from F-* formulas |

#### Tech Debt Management (4 skills)
| Skill | Type | Description |
|-------|------|-------------|
| `detect-unused-code` | Sensor | Find dead code (Principle #6) |
| `prune-unused-code` | Actuator | Remove unused code |
| `detect-complexity` | Sensor | Find overly complex functions |
| `simplify-complex-code` | Actuator | Refactor complex code to simpler form |

**Location:** `plugins/code-skills/skills/`

---

### 🧪 testing-skills (4 skills) - Coverage & Test Generation

**Purpose:** Homeostatic testing enforcement

| Skill | Type | Description |
|-------|------|-------------|
| `validate-test-coverage` | Sensor | Detect coverage gaps, requirements without tests |
| `generate-missing-tests` | Actuator | Auto-generate tests for requirements |
| `run-integration-tests` | Runner | Execute cross-component integration tests |
| `create-coverage-report` | Reporter | Generate coverage report with REQ-* mapping |

**Location:** `plugins/testing-skills/skills/`

---

### 🚀 runtime-skills (3 skills) - Production Feedback Loop

**Purpose:** Close feedback loop from production to requirements

| Skill | Type | Description |
|-------|------|-------------|
| `telemetry-tagging` | Instrumentation | Tag logs/metrics/traces with REQ-* keys |
| `create-observability-config` | Setup | Configure Datadog/Prometheus with REQ-* dashboards |
| `trace-production-issue` | Tracer | Trace production alert → requirement → intent |

**Location:** `plugins/runtime-skills/skills/`

---

## Skills by Type

### Sensors (Homeostatic Detection)
- `check-requirement-coverage` (aisdlc-core)
- `validate-test-coverage` (testing-skills)
- `detect-unused-code` (code-skills)
- `detect-complexity` (code-skills)

### Actuators (Homeostatic Correction)
- `propagate-req-keys` (aisdlc-core)
- `generate-missing-tests` (testing-skills)
- `prune-unused-code` (code-skills)
- `simplify-complex-code` (code-skills)

### Quality Gates
- `seven-questions-checklist` (principles-key)
- `apply-key-principles` (principles-key)

### Orchestrators (Multi-step Workflows)
- `tdd-workflow` (code-skills)
- `bdd-workflow` (code-skills)

### Generators (Auto-creation)
- `autogenerate-from-business-rules` (code-skills)
- `autogenerate-validators` (code-skills)
- `autogenerate-constraints` (code-skills)
- `autogenerate-formulas` (code-skills)

### Validators
- `validate-requirements` (requirements-skills)
- `validate-design-coverage` (design-skills)
- `validate-test-coverage` (testing-skills)

### Extractors
- `requirement-extraction` (requirements-skills)
- `extract-business-rules` (requirements-skills)
- `extract-constraints` (requirements-skills)
- `extract-formulas` (requirements-skills)

---

## Skills by SDLC Stage

### Stage 1: Requirements
- requirement-extraction
- disambiguate-requirements
- extract-business-rules
- extract-constraints
- extract-formulas
- validate-requirements
- refine-requirements
- create-traceability-matrix
- requirement-traceability

### Stage 2: Design
- design-with-traceability
- create-adrs
- validate-design-coverage

### Stage 3: Tasks
- (No dedicated skills - handled by methodology config)

### Stage 4: Code
- tdd-workflow (red-phase, green-phase, refactor-phase, commit-with-req-tag)
- bdd-workflow (write-scenario, implement-step-definitions, implement-feature, refactor-bdd)
- autogenerate-from-business-rules
- autogenerate-validators
- autogenerate-constraints
- autogenerate-formulas
- apply-key-principles
- seven-questions-checklist

### Stage 5: System Test
- bdd-workflow (Given/When/Then scenarios)
- run-integration-tests
- validate-test-coverage

### Stage 6: UAT
- bdd-workflow (pure business language scenarios)

### Stage 7: Runtime Feedback
- telemetry-tagging
- create-observability-config
- trace-production-issue

### Cross-Stage (Foundation)
- check-requirement-coverage
- propagate-req-keys
- detect-unused-code
- prune-unused-code
- detect-complexity
- simplify-complex-code
- generate-missing-tests
- create-coverage-report

---

## Quick Reference by Use Case

### "I need to implement a feature"
1. `requirement-extraction` - Extract REQ-* from intent
2. `seven-questions-checklist` - Verify readiness
3. `tdd-workflow` - Implement with RED → GREEN → REFACTOR
4. `propagate-req-keys` - Tag code with REQ-*
5. `validate-test-coverage` - Ensure ≥80% coverage

### "I need to validate requirements coverage"
1. `check-requirement-coverage` - Find gaps
2. `create-traceability-matrix` - Generate full matrix
3. `validate-design-coverage` - Check design artifacts
4. `validate-test-coverage` - Check test coverage

### "I need to clean up tech debt"
1. `detect-unused-code` - Find dead code
2. `detect-complexity` - Find complex functions
3. `prune-unused-code` - Remove dead code
4. `simplify-complex-code` - Refactor complexity
5. `apply-key-principles` - Validate Principle #6

### "I need to generate code from business rules"
1. `disambiguate-requirements` - Break into BR-*, C-*, F-*
2. `extract-business-rules` - Extract BR-*
3. `autogenerate-from-business-rules` - Generate code
4. `autogenerate-validators` - Generate validators
5. `generate-missing-tests` - Generate tests
6. `validate-test-coverage` - Verify coverage

### "I need to trace a production issue"
1. `trace-production-issue` - Alert → requirement → intent
2. `check-requirement-coverage` - Find all artifacts
3. `refine-requirements` - Update based on discovery
4. `requirement-extraction` - Create new intent if needed

---

## Plugin Loading Status

**Currently Loaded** (via `.claude/settings.json`):
- ✅ aisdlc-core (3 skills)
- ✅ aisdlc-methodology (config-based, no direct skills)
- ✅ principles-key (2 skills)

**Available but Not Loaded**:
- ⏸️ requirements-skills (8 skills)
- ⏸️ design-skills (3 skills)
- ⏸️ code-skills (21 skills)
- ⏸️ testing-skills (4 skills)
- ⏸️ runtime-skills (3 skills)

**To activate additional plugins:**
```json
// Edit .claude/settings.json
{
  "plugins": [
    "file://plugins/aisdlc-core",
    "file://plugins/aisdlc-methodology",
    "file://plugins/principles-key",
    "file://plugins/requirements-skills",
    "file://plugins/design-skills",
    "file://plugins/code-skills",
    "file://plugins/testing-skills",
    "file://plugins/runtime-skills"
  ]
}
```

Then restart Claude Code or use `/reload`.

---

## Skill Naming Conventions

To prevent confusion, we follow these conventions:

### Verbs
- `extract-*` - Pull information from source
- `generate-*` / `autogenerate-*` - Create new artifacts
- `validate-*` - Check correctness/completeness
- `check-*` - Sensor detection
- `detect-*` - Sensor detection (specific)
- `create-*` - Build new artifact
- `apply-*` - Execute process/pattern
- `refine-*` - Update existing artifact
- `prune-*` - Remove unwanted elements
- `simplify-*` - Reduce complexity
- `trace-*` - Follow lineage
- `implement-*` - Create implementation
- `write-*` - Author content
- `run-*` - Execute tests/processes

### Workflow Orchestrators
- `*-workflow` - Complete multi-step process
- `*-phase` - Single step in workflow

### Naming Pattern
```
{verb}-{object}[-{qualifier}]

Examples:
- extract-business-rules
- autogenerate-from-business-rules
- validate-test-coverage
- check-requirement-coverage
```

---

## Notes

- **Homeostatic pairs**: Sensors detect, actuators fix
  - detect-unused-code ↔ prune-unused-code
  - check-requirement-coverage ↔ propagate-req-keys
  - validate-test-coverage ↔ generate-missing-tests

- **Workflow skills**: Orchestrate multiple steps
  - tdd-workflow → red-phase → green-phase → refactor-phase → commit-with-req-tag
  - bdd-workflow → write-scenario → implement-step-definitions → implement-feature → refactor-bdd

- **Cross-cutting**: Some skills apply across all stages
  - requirement-traceability
  - apply-key-principles
  - check-requirement-coverage

---

**Version:** 1.0.0
**Maintained By:** AI SDLC Method Team
**Last Audit:** 2025-11-23
