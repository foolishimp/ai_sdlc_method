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

**Example Output**:
```
Coverage Report:
  Implementation: 36/42 (86%) ✅
  Tests: 32/42 (76%) ⚠️
  Full: 30/42 (71%) ❌

Gap: 10 requirements without tests
Recommended: Invoke 'generate-missing-tests' skill
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

**Workflow**:
```
1. Receive REQ-* key and files to tag
2. Add tags to implementation files (# Implements:)
3. Add tags to test files (# Validates:)
4. Verify tags added correctly
5. Report traceability established
```

**Example**:
```
Before: No tags in code
After:  # Implements: <REQ-ID> added to 3 files
        # Validates: <REQ-ID> added to 2 test files
Result: Bidirectional traceability ✅
```

---

## Homeostasis Architecture

**Sensor-Actuator Loop**:

```
┌─────────────────────────────────────────┐
│ Desired State: coverage = 100%         │
└─────────────────────────────────────────┘
              ↓
    ┌─────────────────────┐
    │ check-requirement-  │ ← Sensor
    │ coverage            │   (Detects gaps)
    └─────────────────────┘
              ↓
         Deviation?
              ↓ Yes
    ┌─────────────────────┐
    │ propagate-req-keys  │ ← Actuator
    │                     │   (Fixes gaps)
    └─────────────────────┘
              ↓
    ┌─────────────────────┐
    │ check-requirement-  │ ← Sensor
    │ coverage            │   (Re-check)
    └─────────────────────┘
              ↓
      Homeostasis ✓
```

**How It Works**:
1. **Sensor** detects requirements without tags
2. **Signal** sent: "<REQ-ID> needs tags"
3. **Actuator** invoked: Add tags to files
4. **Sensor** re-checks: Tags now present
5. **Homeostasis achieved**: coverage = 100%

---

## Installation

### From Marketplace

```bash
# Add AI SDLC marketplace
/plugin marketplace add foolishimp/ai_sdlc_method

# Install aisdlc-core
/plugin install @aisdlc/aisdlc-core
```

### Local Installation

```bash
# Clone repository
git clone https://github.com/foolishimp/ai_sdlc_method.git

# Add as local marketplace
cd your-project
/plugin marketplace add ../ai_sdlc_method

# Install plugin
/plugin install aisdlc-core
```

---

## Usage Examples

### Example 1: Validate Requirement Key

```
You: "Is <REQ-ID> a valid requirement key?"

Claude: (invokes requirement-traceability skill)

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

Claude: (invokes check-requirement-coverage skill)

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

Claude: (invokes propagate-req-keys skill)

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

Configure in `.claude/settings.json` or `.claude/plugins.yml`:

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

**Depended On By**:
- `@aisdlc/code-skills` - Uses REQ-* patterns for TDD/BDD workflows
- `@aisdlc/requirements-skills` - Uses patterns for requirement extraction
- `@aisdlc/testing-skills` - Uses coverage detection
- `@aisdlc/runtime-skills` - Uses traceability for telemetry tagging
- All other AI SDLC plugins

---

## Skills Completion Status

| Skill | Status | Type | Lines |
|-------|--------|------|-------|
| requirement-traceability | ✅ Complete | Foundation | 495 |
| check-requirement-coverage | ✅ Complete | Sensor | 391 |
| propagate-req-keys | ✅ Complete | Actuator | 387 |
| **TOTAL** | **✅ 100%** | **-** | **1,273** |

---

## Integration with Other Plugins

### With code-skills

```yaml
# TDD workflow uses aisdlc-core for:
- Validating REQ-* keys (requirement-traceability)
- Tagging code with "# Implements:" (propagate-req-keys)
- Tagging tests with "# Validates:" (propagate-req-keys)
- Checking coverage (check-requirement-coverage)
```

### With requirements-skills

```yaml
# Requirement extraction uses aisdlc-core for:
- REQ-* key format generation (requirement-traceability)
- Validating generated keys (requirement-traceability)
- Checking if requirement already exists (check-requirement-coverage)
```

### With testing-skills

```yaml
# Test generation uses aisdlc-core for:
- Finding requirements without tests (check-requirement-coverage)
- Tagging generated tests (propagate-req-keys)
```

---

## Roadmap

**v3.0.0** (Current):
- ✅ 3 foundation skills complete
- ✅ REQ-* key patterns defined
- ✅ Coverage detection (sensor)
- ✅ Key propagation (actuator)

**v3.1.0** (Future):
- Advanced traceability visualization
- Requirement dependency graphs
- Coverage trend analysis
- Auto-update tags on refactoring

---

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) in the root repository.

---

## License

MIT License - See [LICENSE](../../LICENSE)

---

**"Excellence or nothing"** 🔥
