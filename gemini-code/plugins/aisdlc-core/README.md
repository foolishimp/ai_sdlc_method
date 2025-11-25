# aisdlc-core Plugin

**Requirement Traceability Foundation for AI SDLC v3.0**

Version: 3.0.0

---

## Overview

The `aisdlc-core` plugin provides the **foundational traceability layer** for AI SDLC methodology. It defines REQ-* key patterns, detects coverage gaps (sensor), and propagates tags (actuator) to enable bidirectional traceability from intent to runtime.

**This is the foundation plugin** - all other AI SDLC plugins depend on it.

---

## Capabilities

### 1. Requirement Traceability (Foundation)

**Skill**: `requirement-traceability`

**Purpose**: Define REQ-* key patterns and validation rules

**Provides**:
- REQ-F-* (Functional requirements)
- REQ-NFR-* (Non-functional requirements: PERF, SEC, SCALE, AVAIL)
- REQ-DATA-* (Data quality: CQ, AQ, PII, LIN)
- REQ-BR-* (Business rules)
- BR-*, C-*, F-* (Nested: business rules, constraints, formulas)

**Key Patterns**:
```
REQ-F-{DOMAIN}-{ID}      Example: <REQ-ID>
REQ-NFR-{TYPE}-{ID}      Example: REQ-NFR-PERF-001
REQ-DATA-{TYPE}-{ID}     Example: REQ-DATA-PII-001
REQ-BR-{DOMAIN}-{ID}     Example: REQ-BR-REFUND-001
```

**Validation**: Validates key format, extracts keys from text, traces through SDLC

---

### 2. Coverage Detection (Sensor)

**Skill**: `check-requirement-coverage`

**Purpose**: Homeostatic sensor detecting requirements without coverage

**Detects**:
- Requirements without implementation (no `# Implements:` tag)
- Requirements without tests (no `# Validates:` tag)
- Coverage percentage below threshold (<80%)

**Workflow**:
```
1. Scan docs/requirements/ for all REQ-* keys
2. Check src/ for "# Implements: REQ-*"
3. Check tests/ for "# Validates: REQ-*"
4. Calculate coverage percentage
5. Report gaps if coverage < 80%
```

---

### 3. Key Propagation (Actuator)

**Skill**: `propagate-req-keys`

**Purpose**: Homeostatic actuator tagging code/tests with REQ-* keys

**Actions**:
- Add `# Implements: REQ-*` to code files
- Add `# Validates: REQ-*` to test files
- Add `# Validates: REQ-*` to BDD feature files
- Tag commits with REQ-* in messages

---
## Installation

### From Marketplace

```bash
# Add AI SDLC marketplace
/tool marketplace add foolishimp/ai_sdlc_method

# Install aisdlc-core
/tool install @aisdlc/aisdlc-core
```

### Local Installation

```bash
# Clone repository
git clone https://github.com/foolishimp/ai_sdlc_method.git

# Add as local marketplace
cd your-project
/tool marketplace add ../ai_sdlc_method

# Install plugin
/tool install aisdlc-core
```

---

## Usage Examples

### Example 1: Validate Requirement Key

```
You: "Is <REQ-ID> a valid requirement key?"

Gemini: (invokes requirement-traceability skill)

Validating: <REQ-ID>

Format Check:
  ✓ Starts with "REQ-"
  ✓ Type: F (Functional)
  ✓ Domain: AUTH (valid, 4 chars)
  ✓ ID: 001 (valid, 3 digits)

Result: ✅ VALID

Pattern: REQ-F-{DOMAIN}-{ID}
```

---

### Example 2: Check Coverage Gaps

```
You: "Check requirement coverage"

Gemini: (invokes check-requirement-coverage skill)

Coverage Report:
  Total Requirements: 42
  Implementation: 36/42 (86%) ✅
  Tests: 32/42 (76%) ⚠️

Gap: 10 requirements without tests

Missing Tests:
  1. <REQ-ID> - Payment processing
  2. REQ-F-CART-001 - Shopping cart
  ... (8 more)

Recommended: Generate missing tests?
```

---

### Example 3: Add Tags to Code

```
You: "Tag login.py with <REQ-ID>"

Gemini: (invokes propagate-req-keys skill)

Tagging Files:
  ✓ src/auth/login.py
    Added: # Implements: <REQ-ID> (line 1)

Traceability:
  Forward: <REQ-ID> → src/auth/login.py ✅
  Backward: src/auth/login.py → <REQ-ID> ✅

Done!
```

---

## Configuration

Configure in `.gemini/settings.json` or `.gemini/plugins.yml`:

```yaml
plugins:
  - name: "@aisdlc/aisdlc-core"
    config:
      # REQ-* key patterns
      req_key_patterns:
        functional: "REQ-F-{DOMAIN}-{ID}"
        non_functional: "REQ-NFR-{DOMAIN}-{ID}"
        data_quality: "REQ-DATA-{DOMAIN}-{ID}"
        business_rule: "REQ-BR-{DOMAIN}-{ID}"

      # Coverage detection (sensor)
      coverage:
        minimum_percentage: 80          # Fail if coverage < 80%
        require_implementation: true    # All REQ-* must have code
        require_tests: true             # All REQ-* must have tests
        auto_detect_missing: true       # Auto-run sensor
        exclude_patterns:
          - "REQ-DATA-*"                # Don't require tests for data reqs

      # Key propagation (actuator)
      propagation:
        auto_propagate_on_commit: true  # Auto-tag before commit
        tag_format: "# Implements: {REQ-KEY}"
        test_tag_format: "# Validates: {REQ-KEY}"
        include_business_rules: true    # Also tag BR-*, C-*, F-*
        placement: "above"              # above | inline | block
```

---

## Dependencies

**None** - This is the foundation plugin.