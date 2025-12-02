---
name: requirements-validation
description: Validate requirements quality - check SMART criteria, completeness, consistency, traceability. Consolidates validate-requirements, create-traceability-matrix.
allowed-tools: [Read, Write, Edit, Grep, Glob]
---

# Requirements Validation

**Skill Type**: Quality Gate (Requirements Stage)
**Purpose**: Ensure requirements meet quality standards before design
**Consolidates**: validate-requirements, create-traceability-matrix

---

## When to Use This Skill

Use this skill when:
- Requirements extraction is complete
- Before moving to Design stage
- Need to verify requirements quality
- Creating or updating traceability matrix

---

## Validation Checklist

### 1. SMART Criteria

For each requirement, verify:

| Criterion | Question | Pass |
|-----------|----------|------|
| **Specific** | Is it clear and unambiguous? | |
| **Measurable** | Can we test it? | |
| **Achievable** | Is it technically feasible? | |
| **Relevant** | Is it linked to business value? | |
| **Testable** | Can we write tests for it? | |

**Example**:
```
REQ-F-AUTH-001: User Login

Specific: Login with email/password
Measurable: AC1-AC5 defined
Achievable: Standard auth pattern
Relevant: Enables self-service portal
Testable: Can write unit + BDD tests

SMART Score: 5/5
```

---

### 2. Completeness Check

**Verify each requirement has**:

```yaml
required_fields:
  - req_key: "REQ-*-*-###"           # Unique identifier
  - type: "Functional | NFR | Data"   # Requirement type
  - description: "Clear statement"    # What it does
  - acceptance_criteria: "1-5 items"  # How to verify
  - intent: "INT-###"                 # Source intent

recommended_fields:
  - business_rules: "BR-###"          # Specific rules
  - constraints: "C-###"              # Limitations
  - user_story: "As a... I want..."   # User perspective
  - priority: "P0-P3"                 # Importance
  - related_requirements: []          # Dependencies
```

---

### 3. Consistency Check

**Verify no conflicts between requirements**:

```yaml
checks:
  - no_duplicate_keys: true           # Each REQ-* unique
  - no_contradictions: true           # No conflicting rules
  - consistent_terminology: true      # Same terms throughout
  - aligned_constraints: true         # C-* don't contradict each other
```

**Example conflict**:
```
REQ-F-AUTH-001: Password minimum 12 characters (BR-002)
REQ-F-REG-001: Password minimum 8 characters (BR-005)

CONFLICT: Different password minimums!
RESOLUTION: Standardize to 12 characters
```

---

### 4. Traceability Check

**Verify bidirectional traceability**:

```yaml
forward_traceability:
  - intent_to_requirements: "INT-* → REQ-*"
  - requirements_to_design: "REQ-* → Component/API"
  - requirements_to_tests: "REQ-* → Test cases"

backward_traceability:
  - tests_to_requirements: "Test → REQ-*"
  - design_to_requirements: "Component → REQ-*"
  - requirements_to_intent: "REQ-* → INT-*"
```

---

## Validation Workflow

### Step 1: Load Requirements

```bash
# Find all requirement files
docs/requirements/*.md
```

### Step 2: Run Validation

For each requirement:

```python
def validate_requirement(req):
    issues = []

    # SMART checks
    if not req.description:
        issues.append("Missing description (not Specific)")
    if not req.acceptance_criteria:
        issues.append("Missing acceptance criteria (not Measurable)")
    if not req.intent:
        issues.append("Missing intent link (not Relevant)")

    # Completeness checks
    if not req.req_key.matches(r'REQ-(F|NFR|DATA|BR)-\w+-\d{3}'):
        issues.append("Invalid REQ key format")

    # Business rule check
    if req.type == 'Functional' and not req.business_rules:
        issues.append("Functional requirement should have business rules")

    return issues
```

### Step 3: Generate Validation Report

```
[REQUIREMENTS VALIDATION REPORT]

Date: 2025-12-03
Requirements Analyzed: 8

SMART Validation:
  REQ-F-AUTH-001: 5/5 (Excellent)
  REQ-F-AUTH-002: 5/5 (Excellent)
  REQ-F-PORTAL-001: 4/5 (Missing business rules)
  REQ-F-PORTAL-002: 5/5 (Excellent)
  REQ-F-PORTAL-003: 5/5 (Excellent)
  REQ-NFR-PERF-001: 5/5 (Excellent)
  REQ-NFR-SEC-001: 5/5 (Excellent)
  REQ-DATA-VAL-001: 5/5 (Excellent)

Completeness:
  With acceptance criteria: 8/8 (100%)
  With business rules: 6/8 (75%)
  With intent link: 8/8 (100%)

Consistency:
  Duplicate keys: 0
  Contradictions: 0
  Terminology issues: 0

Traceability:
  Forward (INT → REQ): 100%
  Backward (REQ → INT): 100%

Issues Found: 1
  - REQ-F-PORTAL-001: Add business rules for balance calculation

Overall Score: 97/100 (Excellent)

Recommendation: Fix 1 issue before Design stage
```

---

## Create Traceability Matrix

**Generate matrix showing requirement coverage across stages**:

```markdown
# Requirements Traceability Matrix

| Req ID | Description | Requirements | Design | Tasks | Code | Test | UAT | Runtime |
|--------|-------------|--------------|--------|-------|------|------|-----|---------|
| REQ-F-AUTH-001 | User login | ✅ | ✅ | ⏳ | ❌ | ❌ | ❌ | ❌ |
| REQ-F-AUTH-002 | Password reset | ✅ | ✅ | ⏳ | ❌ | ❌ | ❌ | ❌ |
| REQ-F-PORTAL-001 | View balance | ✅ | ⏳ | ❌ | ❌ | ❌ | ❌ | ❌ |
...

Coverage Summary:
- Requirements Stage: 8/8 (100%)
- Design Stage: 3/8 (38%)
- Tasks Stage: 2/8 (25%)
- Code Stage: 0/8 (0%)
- System Test: 0/8 (0%)
- UAT: 0/8 (0%)
- Runtime: 0/8 (0%)
```

---

## Output Format

```
[REQUIREMENTS VALIDATION - INT-042]

Requirements Validated: 8

SMART Scores:
  5/5: 7 requirements (Excellent)
  4/5: 1 requirement (Good - needs improvement)

Issues:
  1. REQ-F-PORTAL-001: Missing business rules
     Action: Add BR-* for balance calculation

Traceability:
  All requirements linked to INT-042
  Matrix: docs/TRACEABILITY_MATRIX.md updated

Validation Result: PASS (with 1 minor issue)

Recommendation: Fix REQ-F-PORTAL-001 before Design
```

---

## Configuration

```yaml
# .claude/plugins.yml
plugins:
  - name: "@aisdlc/aisdlc-methodology"
    config:
      validation:
        min_smart_score: 4           # Minimum SMART score (out of 5)
        require_acceptance_criteria: true
        require_business_rules_for_functional: true
        require_intent_link: true
        block_on_contradictions: true
        auto_generate_matrix: true
```

---

## Homeostasis Behavior

**If validation fails**:
- Detect: Requirements don't meet criteria
- Signal: "Requirements need improvement"
- Action: List specific issues
- Block: Do not proceed to Design until fixed

**If traceability gaps**:
- Detect: Requirements without intent link
- Signal: "Traceability incomplete"
- Action: Add missing links

---

## Next Steps

After validation passes:
1. **Design**: Move to Design stage
2. **Track**: Update traceability matrix as stages complete
3. **Monitor**: Re-validate if requirements change

**"Excellence or nothing"**
