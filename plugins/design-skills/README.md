# design-skills Plugin

**Architecture and ADRs with Requirement Traceability**

Version: 1.0.0

---

## Overview

The `design-skills` plugin transforms requirements into technical solution architecture with complete REQ-* traceability. Documents strategic architecture decisions (ADRs) acknowledging ecosystem E(t) constraints.

**Design Stage**: Requirements → Components + APIs + Data Models (all tagged with REQ-*)

---

## Capabilities

### 1. Solution Design with Traceability

**Skill**: `design-with-traceability`

**Creates**:
- Component architecture (services, modules, classes) tagged with REQ-*
- API specifications (endpoints, contracts, protocols) tagged with REQ-*
- Data models (schemas, entities, relationships) tagged with REQ-*
- Component diagrams showing interactions

**Workflow**:
```
Requirements (REQ-*, BR-*, C-*, F-*)
  ↓ design-with-traceability
Technical Architecture:
  - Components (AuthenticationService → <REQ-ID>)
  - APIs (POST /auth/login → <REQ-ID>)
  - Data Models (User entity → <REQ-ID>)
  - All tagged for traceability
```

---

### 2. Architecture Decision Records

**Skill**: `create-adrs`

**Purpose**: Document strategic decisions acknowledging ecosystem E(t)

**ADR Format**:
```
Context: Requirements + Ecosystem constraints
Decision: Selected option + Rejected alternatives
Ecosystem Acknowledged: Team, timeline, compliance, infrastructure
Constraints Imposed: What downstream stages must follow
```

**Example**:
```
ADR-002: Use bcrypt for password hashing

Context: Need secure hashing, team knows bcrypt, PCI-DSS required
Decision: bcrypt (cost 12) | Rejected: Argon2 (team unfamiliar)
Ecosystem: Team skills, compliance, infrastructure
Downstream: Code must use bcrypt library with cost 12
```

---

### 3. Design Coverage Validation

**Skill**: `validate-design-coverage`

**Purpose**: Homeostatic sensor ensuring all requirements have design

**Validates**:
- All REQ-* mentioned in design docs
- Design includes: components, APIs, data models
- Design coverage >= 100%

**Quality Gate**: Blocks Code stage if design incomplete

---

## Installation

```bash
/plugin install @aisdlc/design-skills
```

---

## Dependencies

- **Required**: `@aisdlc/aisdlc-core`, `@aisdlc/requirements-skills`

---

## Skills Status

| Skill | Lines | Status |
|-------|-------|--------|
| design-with-traceability | 307 | ✅ |
| create-adrs | 292 | ✅ |
| validate-design-coverage | 203 | ✅ |
| **TOTAL** | **802** | **✅** |

---

**"Excellence or nothing"** 🔥
