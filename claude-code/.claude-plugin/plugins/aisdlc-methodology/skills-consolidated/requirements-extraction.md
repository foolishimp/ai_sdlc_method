---
name: requirements-extraction
description: Complete requirements extraction workflow - Extract REQ-* keys from intent, disambiguate with BR-*/C-*/F-*, validate quality, create traceability. Consolidates requirement-extraction, disambiguate-requirements, refine-requirements, extract-business-rules, extract-constraints, extract-formulas.
allowed-tools: [Read, Write, Edit, Grep, Glob]
---

# Requirements Extraction

**Skill Type**: Complete Workflow (Requirements Stage)
**Purpose**: Transform raw intent into structured, traceable requirements
**Consolidates**: requirement-extraction, disambiguate-requirements, refine-requirements, extract-business-rules, extract-constraints, extract-formulas

---

## When to Use This Skill

Use this skill when:
- Starting a new feature from user intent
- Analyzing user stories or feature requests
- Need to create REQ-* keys for traceability
- Requirements are vague and need structure

---

## Complete Workflow

### Phase 1: Intent Analysis

**Goal**: Understand what the user wants to achieve.

**Analyze**:
- What is the goal? (capability, feature)
- What problem does it solve?
- Who are the users? (personas)
- What are success criteria?

**Example Intent**:
```
INT-042: "We need a customer self-service portal where users can log in,
view their account balance, update their profile, and download invoices."
```

**Analysis**:
```yaml
Goal: Customer self-service
Problem: High support call volume for basic account info
Personas: Existing customers
Success: Reduce support calls by 40%
Capabilities:
  - User authentication
  - View account data
  - Edit profile
  - Download documents
```

---

### Phase 2: Requirement Extraction

**Goal**: Break intent into discrete, testable requirements.

**Rule**: One requirement = one testable capability

**Extract REQ-* Keys**:

| Intent Capability | REQ Key | Type |
|-------------------|---------|------|
| User login | REQ-F-AUTH-001 | Functional |
| View balance | REQ-F-PORTAL-001 | Functional |
| Update profile | REQ-F-PORTAL-002 | Functional |
| Download invoices | REQ-F-PORTAL-003 | Functional |
| Response time | REQ-NFR-PERF-001 | Non-Functional |
| SSL encryption | REQ-NFR-SEC-001 | Non-Functional |
| Email validation | REQ-DATA-VAL-001 | Data Quality |

**REQ Key Format**:
- `REQ-F-{DOMAIN}-{SEQ}` - Functional requirements
- `REQ-NFR-{CATEGORY}-{SEQ}` - Non-functional requirements
- `REQ-DATA-{CATEGORY}-{SEQ}` - Data quality requirements
- `REQ-BR-{DOMAIN}-{SEQ}` - Business rules

---

### Phase 3: Disambiguation

**Goal**: Add specificity with Business Rules (BR-*), Constraints (C-*), and Formulas (F-*).

**For each requirement, extract**:

#### Business Rules (BR-*)
Specific rules that govern behavior:

```yaml
REQ-F-AUTH-001: User Login
  BR-001: Email must be valid format (regex: ^[^@]+@[^@]+\.[^@]+$)
  BR-002: Password minimum 12 characters
  BR-003: Max 3 login attempts, then 15-minute lockout
  BR-004: Session timeout after 30 minutes of inactivity
```

#### Constraints (C-*)
Technical or business limitations:

```yaml
REQ-F-AUTH-001: User Login
  C-001: Response time < 500ms
  C-002: Must use HTTPS
  C-003: Password must be hashed (bcrypt, cost factor 12)
  C-004: Must support concurrent users (10,000+)
```

#### Formulas (F-*)
Calculations or transformations:

```yaml
REQ-F-PORTAL-001: View Balance
  F-001: available_balance = total_balance - pending_holds
  F-002: display_format = currency_symbol + format(amount, 2 decimals)
```

---

### Phase 4: Requirement Specification

**Goal**: Write complete requirement specifications.

**Template**:

```markdown
## REQ-F-AUTH-001: User Login with Email and Password

**Type**: Functional Requirement
**Domain**: Authentication
**Priority**: P0 (Critical)
**Intent**: INT-042

**Description**:
Users must be able to log in to the customer portal using their
registered email address and password.

**Acceptance Criteria**:
1. User can enter email and password on login page
2. Valid credentials grant access to customer portal
3. Invalid credentials show clear error message
4. Account locks after 3 failed attempts for 15 minutes (BR-003)
5. Session expires after 30 minutes of inactivity (BR-004)

**Business Rules**:
- BR-001: Email must be valid format
- BR-002: Password minimum 12 characters
- BR-003: Max 3 attempts, 15-min lockout
- BR-004: 30-minute session timeout

**Constraints**:
- C-001: Response time < 500ms
- C-002: Must use HTTPS
- C-003: Password hashed with bcrypt

**User Story**:
As a customer
I want to log in with my email and password
So that I can access my account information

**Related Requirements**:
- REQ-NFR-SEC-001: Password encryption
- REQ-NFR-PERF-001: Login performance
- REQ-DATA-VAL-001: Email validation

**Assumptions**:
- Users already registered (registration is separate)
- Email is unique identifier

**Out of Scope**:
- Social login (OAuth)
- Passwordless authentication
- Biometric authentication
```

---

### Phase 5: File Organization

**Create requirements files**:

```
docs/requirements/
├── authentication.md       # REQ-F-AUTH-*
├── customer-portal.md      # REQ-F-PORTAL-*
├── performance.md          # REQ-NFR-PERF-*
├── security.md             # REQ-NFR-SEC-*
└── data-validation.md      # REQ-DATA-*
```

**Group by domain**, not by requirement type.

---

### Phase 6: Traceability Entry

**Create intent-to-requirements mapping**:

```yaml
# docs/traceability/intent-to-requirements.yml

INT-042:
  title: "Customer self-service portal"
  date_created: "2025-12-01"
  status: "In Progress"
  requirements:
    functional:
      - REQ-F-AUTH-001
      - REQ-F-AUTH-002
      - REQ-F-PORTAL-001
      - REQ-F-PORTAL-002
      - REQ-F-PORTAL-003
    non_functional:
      - REQ-NFR-PERF-001
      - REQ-NFR-SEC-001
    data_quality:
      - REQ-DATA-VAL-001
  total_requirements: 8
  completion: 0%
```

---

## Output Format

When requirements extraction completes:

```
[REQUIREMENTS EXTRACTION - INT-042]

Intent: Customer self-service portal

Requirements Extracted:

Functional (5):
  REQ-F-AUTH-001: User login with email/password
    BR-001: Email validation
    BR-002: Password min 12 chars
    BR-003: Account lockout
    C-001: Response < 500ms
  REQ-F-AUTH-002: Password reset via email
  REQ-F-PORTAL-001: View account balance
    F-001: available = total - pending
  REQ-F-PORTAL-002: Update user profile
  REQ-F-PORTAL-003: Download invoices

Non-Functional (2):
  REQ-NFR-PERF-001: Response time < 500ms
  REQ-NFR-SEC-001: SSL encryption required

Data Quality (1):
  REQ-DATA-VAL-001: Email must be valid format

Total: 8 requirements
Business Rules: 6 (BR-001 through BR-006)
Constraints: 4 (C-001 through C-004)
Formulas: 1 (F-001)

Files Created:
  + docs/requirements/authentication.md
  + docs/requirements/customer-portal.md
  + docs/requirements/performance.md
  + docs/requirements/security.md
  + docs/traceability/intent-to-requirements.yml

Traceability: INT-042 → 8 REQ-* keys

Requirements Extraction Complete!
```

---

## Clarifying Questions

**If intent is vague, ask**:

1. **Who** is the user? (persona, role)
2. **What** are they trying to do? (goal, capability)
3. **Why** do they need this? (problem, value)
4. **How** will we know it's done? (acceptance criteria)
5. **What if** edge cases? (error handling, boundaries)

**Example**:
```
Vague: "Add payment processing"

Questions:
1. What payment methods? (credit card, PayPal, crypto?)
2. What provider? (Stripe, Braintree?)
3. What compliance? (PCI-DSS level?)
4. What currencies? (USD only, multi-currency?)
5. What limits? (min/max amounts?)

Refined: "Add credit card payment via Stripe, PCI-DSS Level 1,
USD only, $0.01 to $10,000 per transaction."
```

---

## SMART Requirements Checklist

Good requirements are **SMART**:

- **S**pecific: Clear, unambiguous description
- **M**easurable: Acceptance criteria can be tested
- **A**chievable: Technically feasible
- **R**elevant: Linked to business value
- **T**estable: Can write tests to validate

**Validate each requirement against SMART before committing.**

---

## Configuration

```yaml
# .claude/plugins.yml
plugins:
  - name: "@aisdlc/aisdlc-methodology"
    config:
      requirements:
        auto_extract_on_intent: true
        require_acceptance_criteria: true
        min_requirements_per_intent: 1
        ask_clarifying_questions: true
        max_clarifying_questions: 6
        require_business_rules: true
        require_constraints: false
```

---

## Homeostasis Behavior

**If intent too vague**:
- Detect: Cannot extract specific requirements
- Signal: "Need clarification"
- Action: Ask clarifying questions (max 6)
- Retry: After user provides details

**If requirements incomplete**:
- Detect: Missing acceptance criteria or business rules
- Signal: "Requirements need disambiguation"
- Action: Add BR-*, C-*, F-* as needed

---

## Next Steps

After requirements extraction:
1. **Validate**: Use `requirements-validation` skill
2. **Design**: Move to Design stage
3. **Implement**: Use TDD/BDD workflows

**"Excellence or nothing"**
