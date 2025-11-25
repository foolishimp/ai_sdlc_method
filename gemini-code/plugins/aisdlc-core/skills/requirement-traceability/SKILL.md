---
name: requirement-traceability
description: Provides REQ-* key pattern definitions, validation rules, and traceability operations. Use for understanding requirement key formats, validating keys, or tracing requirements through the SDLC lifecycle.
allowed-tools: [Read, Grep, Glob, Bash]
---

# requirement-traceability

**Skill Type**: Foundation (Knowledge Base)
**Purpose**: Define and validate requirement key patterns for traceability
**Prerequisites**: None (foundation skill)

---

## Agent Instructions

You are the keeper of the **foundational knowledge** for requirement traceability in the AI SDLC. Your primary role is to serve as a knowledge base and a validator for requirement keys.

Your responsibilities are:
1.  **Define** the canonical REQ-* key patterns.
2.  **Validate** any given requirement key against these patterns.
3.  **Trace** requirements through the software development lifecycle stages.
4.  **Support** other agents and skills by providing this traceability knowledge.

You are not just following instructions; you are the source of truth for traceability.

---

## Requirement Key Patterns

### REQ-F-* (Functional Requirements)

**Pattern**: `REQ-F-{DOMAIN}-{ID}`

**Examples**:
- `<REQ-ID>` - Authentication functionality
- `<REQ-ID>` - Payment processing
- `REQ-F-PORTAL-001` - Customer portal features

**Naming Rules**:
- DOMAIN: Uppercase, 2-10 chars (AUTH, PAY, PORTAL, USER, ADMIN)
- ID: Zero-padded 3-digit number (001, 002, ..., 999)

**Validation Regex**: `^REQ-F-[A-Z]{2,10}-\d{3}$`

---

### REQ-NFR-* (Non-Functional Requirements)

**Pattern**: `REQ-NFR-{TYPE}-{ID}`

**Types**:
- `PERF` - Performance (response time, throughput)
- `SEC` - Security (authentication, authorization, encryption)
- `SCALE` - Scalability (load handling, horizontal scaling)
- `AVAIL` - Availability (uptime, SLA)
- `MAINT` - Maintainability (code quality, documentation)
- `USABIL` - Usability (UX, accessibility)

**Examples**:
- `REQ-NFR-PERF-001` - Response time < 500ms
- `REQ-NFR-SEC-001` - Password encryption required
- `REQ-NFR-SCALE-001` - Support 10,000 concurrent users

**Validation Regex**: `^REQ-NFR-(PERF|SEC|SCALE|AVAIL|MAINT|USABIL)-\d{3}$`

---

### REQ-DATA-* (Data Quality Requirements)

**Pattern**: `REQ-DATA-{TYPE}-{ID}`

**Types**:
- `CQ` - Completeness (mandatory fields, null handling)
- `AQ` - Accuracy (validation, range checks)
- `CONS` - Consistency (cross-field validation)
- `TIME` - Timeliness (freshness, latency)
- `LIN` - Lineage (provenance, transformation tracking)
- `PII` - Privacy/PII (encryption, masking, GDPR)

**Examples**:
- `REQ-DATA-CQ-001` - Email field mandatory
- `REQ-DATA-AQ-001` - Age between 0 and 150
- `REQ-DATA-PII-001` - Credit card numbers encrypted

**Validation Regex**: `^REQ-DATA-(CQ|AQ|CONS|TIME|LIN|PII)-\d{3}$`

---

### REQ-BR-* (Business Rules)

**Pattern**: `REQ-BR-{DOMAIN}-{ID}`

**Use Cases**:
- Complex business logic requiring separate requirement
- Multi-stage business processes
- Regulatory compliance rules

**Examples**:
- `REQ-BR-REFUND-001` - Refund eligibility rules
- `REQ-BR-DISC-001` - Discount calculation rules
- `REQ-BR-COMP-001` - GDPR compliance rules

**Validation Regex**: `^REQ-BR-[A-Z]{2,10}-\d{3}$`

---

## Subordinate Key Patterns

These are **nested within** requirements for disambiguation:

### BR-* (Business Rules - Nested)

**Pattern**: `BR-{ID}`

**Examples** (nested within <REQ-ID>):
- `BR-001`: Email validation (regex pattern)
- `BR-002`: Password minimum 12 characters
- `BR-003`: Account lockout after 3 attempts

**Use**: Disambiguate vague requirements into specific rules

---

### C-* (Constraints - Nested)

**Pattern**: `C-{ID}`

**Examples** (nested within <REQ-ID>):
- `C-001`: PCI-DSS Level 1 compliance
- `C-002`: Stripe API timeout 10 seconds
- `C-003`: Transaction idempotency required

**Use**: Acknowledge ecosystem E(t) constraints

---

### F-* (Formulas - Nested)

**Pattern**: `F-{ID}`

**Examples** (nested within <REQ-ID>):
- `F-001`: Stripe fee = (amount * 0.029) + 0.30
- `F-002`: Idempotency key = SHA256(merchant_id + timestamp + amount)

**Use**: Define precise calculations for code generation

---

## Traceability Workflow

### Forward Traceability (Intent → Runtime)

**Path**: Intent → Requirements → Design → Code → Tests → Runtime

```
INT-042: "Add user login"
  ↓ (Requirements stage)
<REQ-ID>: User login with email/password
  ↓ (Design stage)
AuthenticationService component
  ↓ (Code stage)
src/auth/login.py:23  # Implements: <REQ-ID>
  ↓ (Test stage)
tests/auth/test_login.py:15  # Validates: <REQ-ID>
  ↓ (Runtime stage)
Datadog metric: auth_success{req="<REQ-ID>"}
```

---

## Tagging Conventions

### Code Implementation Tags

**Format**: `# Implements: {REQ-KEY}`

### Test Validation Tags

**Format**: `# Validates: {REQ-KEY}`

### Commit Message Tags

**Format**: Include REQ-* in commit subject or footer

### Runtime Telemetry Tags

**Logs**:
```python
logger.info(
    "User login successful",
    extra={"req": "<REQ-ID>", "user_id": user.id}
)
```

**Metrics (Datadog)**:
```python
statsd.increment(
    "auth.login.success",
    tags=["req:<REQ-ID>", "env:production"]
)
```

---

## Notes

**Key Principles**:
- REQ-* keys are **immutable** (content can evolve, keys never change)
- REQ-* keys are **unique** (no duplicates)
- REQ-* keys are **human-readable** (domain + sequential ID)
- REQ-* keys are **everywhere** (requirements → code → tests → runtime)