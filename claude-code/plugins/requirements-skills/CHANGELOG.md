# Changelog - requirements-skills

All notable changes to the `requirements-skills` plugin will be documented in this file.

---

## [1.0.0] - 2025-11-20

### Added

**Requirement Extraction** (1 skill):
- `requirement-extraction` (407 lines) - Transform raw intent into structured REQ-* requirements
  - Extracts REQ-F-*, REQ-NFR-*, REQ-DATA-*, REQ-BR-*
  - Assigns unique sequential keys
  - Creates acceptance criteria
  - Links to original intent (INT-*)
  - Asks clarifying questions if intent vague
  - Creates requirement documents

**Requirement Disambiguation** (4 skills):
- `disambiguate-requirements` (376 lines) - Orchestrator for BR-*, C-*, F-* extraction
  - Coordinates extraction of business rules, constraints, formulas
  - Enables code autogeneration from precise specs
  - Updates requirement documents with detailed specifications

- `extract-business-rules` (239 lines) - Extract BR-* specifications
  - Validation rules (regex, min/max, enum)
  - Business logic (state machines, decisions)
  - Error handling specifications
  - Autogeneration-ready formats

- `extract-constraints` (249 lines) - Extract C-* from ecosystem E(t)
  - API/service constraints (timeouts, rate limits)
  - Compliance constraints (PCI-DSS, GDPR, HIPAA)
  - Platform constraints (language, libraries)
  - Performance constraints (SLAs, resource limits)
  - Security constraints (HTTPS, encryption)

- `extract-formulas` (104 lines) - Extract F-* mathematical formulas
  - Arithmetic calculations
  - Date/time calculations
  - Percentage/ratio calculations
  - Hash/checksum algorithms
  - Autogeneration-ready formulas

**Requirements Refinement Loop** (1 skill):
- `refine-requirements` (359 lines) - Update requirements from discoveries
  - Captures edge cases found during TDD/BDD
  - Adds new BR-*, C-*, F-* from implementation discoveries
  - Tracks discovery source and phase (RED/GREEN/REFACTOR)
  - Updates code and tests with refined specifications
  - Creates refinement log for traceability

**Traceability Management** (2 skills):
- `create-traceability-matrix` (217 lines) - Map INT-* → REQ-* → artifacts
  - Intent to requirements mapping
  - Requirements to design/code/tests/commits/runtime mapping
  - Coverage calculation across all stages
  - Gap detection (missing code, tests, telemetry)
  - Impact analysis support

- `validate-requirements` (202 lines) - Quality gate sensor
  - Validates unique REQ-* keys
  - Validates key format compliance
  - Checks acceptance criteria presence
  - Validates testability
  - Detects ambiguous language
  - Quality gate for Design stage

### Configuration

**Extraction**:
- Auto-extract on intent detection
- Require acceptance criteria
- Ask clarifying questions if vague
- Minimum requirements per intent

**Disambiguation**:
- Auto-disambiguate after extraction
- Minimum business rules per requirement
- Require autogeneration-ready specs
- Optional formulas/constraints

**Refinement**:
- Auto-refine on discovery
- Track discovery source (developer, tester, user)
- Update traceability automatically
- Log all refinements

**Validation**:
- Require unique keys
- Require testable criteria
- Block ambiguous language
- Quality gate enforcement

### Status

**Completion**: 100% (8/8 skills)

**Total Lines**: 2,153 lines of skill documentation

**Skills Complete**:
- ✅ Extraction (1 skill)
- ✅ Disambiguation (4 skills)
- ✅ Refinement Loop (1 skill)
- ✅ Traceability (2 skills)

---

## Complete Workflow Example

**User Intent**: "Add payment processing"

### Step 1: Extraction

```
Claude (requirement-extraction):
  Asking clarifying questions:
  1. Payment methods? → "Credit card"
  2. Provider? → "Stripe"
  3. Compliance? → "PCI-DSS Level 1"

  Creating:
    <REQ-ID>: Credit card payment via Stripe
    REQ-NFR-SEC-001: PCI-DSS compliance
```

### Step 2: Disambiguation

```
Claude (disambiguate-requirements):
  Extracting precise specifications...

  Business Rules:
    BR-001: Card type (Visa, Mastercard)
    BR-002: Luhn validation
    BR-003: CVV 3 digits
    BR-004: Amount $0.01 - $10,000

  Constraints:
    C-001: Never store card numbers (PCI-DSS)
    C-002: Stripe timeout 10 seconds
    C-003: Idempotency keys required

  Formulas:
    F-001: fee = (amount * 0.029) + 0.30
    F-002: key = SHA256(merchant + time + amount)
```

### Step 3: Validation

```
Claude (validate-requirements):
  ✅ Unique keys
  ✅ Valid format
  ✅ Acceptance criteria present
  ✅ Testable specifications
  ✅ Traceability to intent

  Quality gate: PASS ✅
  Ready for Design stage
```

### Step 4: Implementation (code-skills)

```
Claude (tdd-workflow):
  RED: Writing tests for BR-001 through BR-004...

Developer: "Wait, what if user clicks Pay button twice?"

Claude (refine-requirements):
  Great discovery!

  Adding:
    BR-015: Duplicate payment prevention
      - Use Stripe idempotency keys (C-003)
      - Key from F-002
      - Discovered: during TDD GREEN phase

  Updated:
    - docs/requirements/payments.md (added BR-015)
    - src/payments/payment.py (added idempotency handling)
    - tests added for BR-015

  Next developer sees BR-015 in requirements ✓
```

---

## Dependencies

- **Required**: `@aisdlc/aisdlc-core` (^3.0.0) - REQ-* patterns and traceability

**Depends On This**:
- `@aisdlc/code-skills` - Uses BR-*, C-*, F-* for autogeneration
- `@aisdlc/design-skills` - Uses requirements for design
- All plugins need requirements

---

## Roadmap

**v1.0.0** (Current):
- ✅ All 8 skills complete
- ✅ Requirements refinement loop
- ✅ Disambiguation into BR-*, C-*, F-*
- ✅ Traceability and validation

**v1.1.0** (Future):
- AI-assisted requirement generation
- Requirement templates by domain
- Automatic refinement suggestions
- Requirements versioning and history

---

**"Excellence or nothing"** 🔥
