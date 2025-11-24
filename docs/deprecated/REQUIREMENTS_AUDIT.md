# Requirements Audit - ai_sdlc_method

**Date**: 2025-11-24
**Purpose**: Identify in-scope vs out-of-scope requirements for ai_sdlc_method implementation

---

## Problem Statement

The traceability matrix shows **58 requirements**, but only **20 are actual implementation requirements** for building ai_sdlc_method.

The other 38 are **example requirements** used in documentation to demonstrate how to use the methodology.

---

## Requirement Files Analysis

### 1. AISDLC_IMPLEMENTATION_REQUIREMENTS.md ✅ IN SCOPE
**Purpose**: Requirements for building ai_sdlc_method itself
**Location**: `docs/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md`
**Count**: 20 implementation requirements + 10 example requirements (Section 7)

**Implementation Requirements** (20 total):
- **Plugin System** (4): REQ-F-PLUGIN-001/002/003/004
- **Command System** (3): REQ-F-CMD-001/002/003
- **Workspace** (3): REQ-F-WORKSPACE-001/002/003
- **TODO System** (3): REQ-F-TODO-001/002/003
- **Testing** (2): REQ-F-TESTING-001/002
- **Traceability** (2): REQ-NFR-TRACE-001/002
- **Other NFR** (3): REQ-NFR-CONTEXT-001, REQ-NFR-FEDERATE-001, REQ-NFR-COVERAGE-001

### 2. AI_SDLC_REQUIREMENTS.md ❌ OUT OF SCOPE (Examples)
**Purpose**: Example requirements demonstrating the methodology
**Location**: `docs/requirements/AI_SDLC_REQUIREMENTS.md`
**Count**: ~40+ example requirements

**Examples Found** (should be excluded from implementation traceability):
- REQ-ARCH-DATA-001: Event-driven data architecture
- REQ-ARCH-SCALE-001: Support 100k concurrent users
- REQ-ARCH-SEC-001: Zero-trust security model
- REQ-DATA-PIPE-001/002/003: Data pipeline examples
- REQ-DS-MODEL-001/DATA-001/PERF-001: Data science examples (churn prediction)
- REQ-DOC-API-001/DEV-001/USER-001: Documentation examples
- REQ-NFR-SCALE-001: Support 10,000 concurrent users
- REQ-NFR-PERF-005: Performance NFR example
- REQ-SEC-LIB-001: FastAPI version example
- REQ-TEST-PERF-001/SEC-001/UNIT-001: Testing examples
- REQ-UAT-AUTH-001/002: UAT examples
- REQ-UAT-DATA-001: Data validation example

### 3. AI_SDLC_OVERVIEW.md ❌ OUT OF SCOPE (Examples)
**Purpose**: High-level overview with example requirements
**Location**: `docs/requirements/AI_SDLC_OVERVIEW.md`
**Count**: ~10+ example requirements

**Examples Found**:
- REQ-SEC-LIB-001: "FastAPI must be ≥ 0.110.0"
- REQ-BR-CALC-001: Business rule example

### 4. AI_SDLC_CONCEPTS.md ❌ OUT OF SCOPE (Examples)
**Purpose**: Conceptual examples
**Location**: `docs/requirements/AI_SDLC_CONCEPTS.md`
**Count**: ~5+ example requirements

**Examples Found**:
- REQ-F-AUTH-001: User login (example)
- REQ-NFR-PERF-001: Login performance (example)
- REQ-DATA-CQ-001: Data quality (example)

### 5. FOLDER_BASED_REQUIREMENTS.md ❌ OUT OF SCOPE (Examples)
**Purpose**: Example requirements for folder-based discovery
**Location**: `docs/requirements/FOLDER_BASED_REQUIREMENTS.md`
**Count**: ~5+ example requirements

**Examples Found**:
- REQ-F-AUTH-002: Password reset (example)

---

## Categorization Results

### ✅ IN SCOPE - Actual ai_sdlc_method Implementation (20 requirements)

| Requirement | Description | Implementation Status | Notes |
|-------------|-------------|----------------------|-------|
| **Plugin System** | | | |
| REQ-F-PLUGIN-001 | Plugin System with Marketplace Support | ✅ Complete | installers/setup_plugins.py:7 |
| REQ-F-PLUGIN-002 | Federated Plugin Loading | ✅ Complete | installers/setup_plugins.py:8 |
| REQ-F-PLUGIN-003 | Plugin Bundles | ⚠️ No Tests | installers/setup_plugins.py:9 |
| REQ-F-PLUGIN-004 | Plugin Versioning | ⚠️ No Tests | installers/setup_plugins.py:10 |
| **Command System** | | | |
| REQ-F-CMD-001 | Slash Commands for Workflow | ⚠️ No Design/Tests | installers/setup_commands.py:7 |
| REQ-F-CMD-002 | Context Switching | ⚠️ No Design/Tests | installers/setup_commands.py:8 |
| REQ-F-CMD-003 | Persona Management | ⚠️ No Design/Tests | installers/setup_commands.py:9 |
| **Workspace** | | | |
| REQ-F-WORKSPACE-001 | Developer Workspace Structure | ⚠️ No Tests | installers/setup_workspace.py:13 |
| REQ-F-WORKSPACE-002 | Task Management Templates | ⚠️ No Tests | installers/setup_workspace.py:14 |
| REQ-F-WORKSPACE-003 | Session Tracking Templates | ⚠️ No Tests | installers/setup_workspace.py:15 |
| **TODO System** | | | |
| REQ-F-TODO-001 | Create TODO Item | 🚧 Design Only | No implementation found |
| REQ-F-TODO-002 | Mark TODO as Complete | 🚧 Design Only | No implementation found |
| REQ-F-TODO-003 | List All TODOs | 🚧 Design Only | No implementation found |
| **Testing** | | | |
| REQ-F-TESTING-001 | Test Coverage Validation | ⚠️ No Implementation | Tests exist |
| REQ-F-TESTING-002 | Test Generation | 🚧 Design Only | No implementation found |
| **Traceability** | | | |
| REQ-NFR-TRACE-001 | Full Lifecycle Traceability | ⚠️ No Design/Tests | installers/validate_traceability.py:8 |
| REQ-NFR-TRACE-002 | Requirement Key Propagation | ⚠️ No Design/Tests | installers/validate_traceability.py:9 |
| **Other NFR** | | | |
| REQ-NFR-CONTEXT-001 | Persistent Context Across Sessions | ✅ Complete | installers/setup_workspace.py:16 |
| REQ-NFR-FEDERATE-001 | Hierarchical Configuration Composition | ✅ Complete | mcp_service/src/ai_sdlc_config/core/config_manager.py:4 |
| REQ-NFR-COVERAGE-001 | Test Coverage Minimum | 🚧 Design Only | No implementation found |

### ❌ OUT OF SCOPE - Documentation Examples (38 requirements)

**These should be EXCLUDED from implementation traceability:**

1. **Architecture Examples** (3): REQ-ARCH-DATA-001, REQ-ARCH-SCALE-001, REQ-ARCH-SEC-001
2. **Authentication Examples** (4): REQ-F-AUTH-001, REQ-F-AUTH-002, REQ-F-AUTH-003, REQ-BR-AUTH-001
3. **Portal Examples** (3): REQ-F-PORTAL-001, REQ-F-PORTAL-002, REQ-F-PORTAL-003
4. **Payment Examples** (2): REQ-F-PAY-001, REQ-F-PAY-005
5. **GDPR Example** (1): REQ-F-GDPR-001
6. **Data Examples** (6): REQ-DATA-AUTH-001, REQ-DATA-CQ-001, REQ-DATA-PIPE-001/002/003, REQ-BR-CALC-001
7. **Data Science Examples** (3): REQ-DS-MODEL-001, REQ-DS-DATA-001, REQ-DS-PERF-001
8. **Security Examples** (4): REQ-NFR-SEC-001, REQ-NFR-SEC-002, REQ-NFR-SEC-003, REQ-SEC-LIB-001
9. **Performance Examples** (2): REQ-NFR-PERF-001, REQ-NFR-PERF-005
10. **Scaling Examples** (1): REQ-NFR-SCALE-001
11. **Documentation Examples** (3): REQ-DOC-API-001, REQ-DOC-DEV-001, REQ-DOC-USER-001
12. **Testing Examples** (3): REQ-TEST-PERF-001, REQ-TEST-SEC-001, REQ-TEST-UNIT-001
13. **UAT Examples** (3): REQ-UAT-AUTH-001, REQ-UAT-AUTH-002, REQ-UAT-DATA-001

---

## Orphaned Implementations (Code Without Requirements)

**None found** - All implementations trace back to one of the 20 requirements.

**Note**: The command implementations (REQ-F-CMD-*) need design documentation created.

---

## Recommendations

### 1. Separate Example Requirements from Implementation Requirements

**Option A: Move to examples/ directory** ⭐ RECOMMENDED
```bash
mkdir -p docs/requirements/examples/
mv docs/requirements/AI_SDLC_REQUIREMENTS.md docs/requirements/examples/
mv docs/requirements/AI_SDLC_OVERVIEW.md docs/requirements/examples/
mv docs/requirements/AI_SDLC_CONCEPTS.md docs/requirements/examples/
mv docs/requirements/FOLDER_BASED_REQUIREMENTS.md docs/requirements/examples/
```

Update traceability scanner to only scan `docs/requirements/*.md` (not subdirectories).

**Option B: Add exclusion marker**
Add a marker comment to example files:
```markdown
<!-- TRACEABILITY: EXCLUDE - Example requirements for methodology demonstration -->
```

Update scanner to skip files with this marker.

### 2. Clean Up AISDLC_IMPLEMENTATION_REQUIREMENTS.md

Section 7 ("Example Requirements") should be **removed** since examples will be in separate files.

### 3. Add Missing Implementations

**High Priority**:
- REQ-F-TODO-001/002/003: TODO system is documented but not implemented in code
- REQ-F-TESTING-002: Test generation skill
- REQ-NFR-COVERAGE-001: Coverage enforcement

**Design Documentation Needed**:
- REQ-F-CMD-* → Create `docs/design/COMMAND_SYSTEM.md`
- REQ-F-WORKSPACE-* → Already exists: `docs/design/TEMPLATE_SYSTEM.md`

### 4. Update Traceability Matrix Generation

After separating example requirements:
```bash
python installers/validate_traceability.py \
  --requirements docs/requirements \
  --matrix > docs/TRACEABILITY_MATRIX.md
```

**Expected result**:
- Total Requirements: 20 (down from 58)
- Implementation Coverage: ~70% (14/20 implemented)
- Test Coverage: ~25% (5/20 tested)

---

## Action Plan

1. ✅ Create this audit document
2. ⬜ Move example requirements to `docs/requirements/examples/`
3. ⬜ Update AISDLC_IMPLEMENTATION_REQUIREMENTS.md (remove Section 7)
4. ⬜ Regenerate traceability matrix (should show 20 requirements)
5. ⬜ Create COMMAND_SYSTEM.md design doc
6. ⬜ Implement TODO system (REQ-F-TODO-*)
7. ⬜ Add tests for untested requirements

---

**Note**: This audit demonstrates dogfooding - we're using our own traceability tools to clean up our own requirements!
