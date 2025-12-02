---
name: traceability-core
description: Core traceability operations - check coverage, propagate REQ-* keys, validate traceability chain from intent to runtime. Consolidates check-requirement-coverage, propagate-req-keys, requirement-traceability.
allowed-tools: [Read, Write, Edit, Grep, Glob]
---

# Traceability Core

**Skill Type**: Core Infrastructure (All Stages)
**Purpose**: Maintain bidirectional traceability from Intent to Runtime
**Consolidates**: check-requirement-coverage, propagate-req-keys, requirement-traceability

---

## When to Use This Skill

Use this skill when:
- Need to verify traceability chain is intact
- Propagating REQ-* keys through stages
- Checking coverage at any stage
- Validating requirement implementation
- Creating or updating traceability matrix

---

## Traceability Model

### Complete Traceability Chain

```
Intent (INT-*)
    ↓ (extract)
Requirements (REQ-*)
    ↓ (design)
Design (Component, API, ADR)
    ↓ (breakdown)
Tasks (JIRA-*, TASK-*)
    ↓ (implement)
Code (functions, classes)
    ↓ (test)
Tests (unit, integration, BDD)
    ↓ (validate)
UAT (business sign-off)
    ↓ (deploy)
Runtime (metrics, logs, traces)
    ↓ (feedback)
[New Intent] → cycle repeats
```

### Key Propagation Rules

```yaml
# REQ-* keys flow through all artifacts

Requirements Document:
  - REQ-F-AUTH-001: User login with email and password

Design Document:
  - Implements: REQ-F-AUTH-001
  - Component: AuthenticationService
  - API: POST /api/v1/auth/login

Task Ticket:
  - Implements: REQ-F-AUTH-001
  - Ticket: PORTAL-123

Code:
  # Implements: REQ-F-AUTH-001
  def login(email, password): ...

Unit Test:
  # Validates: REQ-F-AUTH-001
  def test_login(): ...

BDD Scenario:
  @REQ-F-AUTH-001
  Scenario: Successful login

Runtime Metrics:
  login_attempts{requirement="REQ-F-AUTH-001"}

Alert:
  Requirement: REQ-F-AUTH-001
```

---

## Core Operations

### 1. Check Requirement Coverage

**Goal**: Verify all requirements have coverage at specified stage.

```python
# traceability/coverage.py

from dataclasses import dataclass
from typing import Dict, List, Set
from enum import Enum

class Stage(Enum):
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    TASKS = "tasks"
    CODE = "code"
    SYSTEM_TEST = "system_test"
    UAT = "uat"
    RUNTIME = "runtime"


@dataclass
class CoverageResult:
    """Coverage analysis result."""
    stage: Stage
    total_requirements: int
    covered_requirements: int
    coverage_percent: float
    covered: List[str]
    uncovered: List[str]


def check_coverage(
    requirements: List[str],
    artifacts: Dict[str, Set[str]],  # artifact_path -> set of REQ-* it covers
    stage: Stage
) -> CoverageResult:
    """Check requirement coverage at a specific stage.

    Implements: REQ-TRACE-001
    """
    covered = set()

    for artifact_path, req_keys in artifacts.items():
        covered.update(req_keys)

    uncovered = set(requirements) - covered

    return CoverageResult(
        stage=stage,
        total_requirements=len(requirements),
        covered_requirements=len(covered),
        coverage_percent=len(covered) / len(requirements) * 100 if requirements else 0,
        covered=sorted(covered),
        uncovered=sorted(uncovered)
    )


# Usage example
def scan_code_coverage(src_dir: str, requirements: List[str]) -> CoverageResult:
    """Scan code files for requirement coverage."""
    import re
    from pathlib import Path

    artifacts = {}
    req_pattern = re.compile(r'(?:Implements|Validates):\s*(REQ-[A-Z]+-[A-Z]+-\d{3})')

    for path in Path(src_dir).rglob("*.py"):
        content = path.read_text()
        matches = req_pattern.findall(content)
        if matches:
            artifacts[str(path)] = set(matches)

    return check_coverage(requirements, artifacts, Stage.CODE)
```

---

### 2. Propagate REQ-* Keys

**Goal**: Ensure REQ-* keys flow from source to downstream artifacts.

```python
# traceability/propagation.py

from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path
import re


@dataclass
class PropagationResult:
    """Result of key propagation operation."""
    source: str
    target: str
    keys_propagated: List[str]
    keys_missing: List[str]
    success: bool


def propagate_to_design(
    requirement_path: str,
    design_path: str
) -> PropagationResult:
    """Propagate REQ-* keys from requirements to design document.

    Implements: REQ-TRACE-002
    """
    # Extract REQ-* from requirements
    req_content = Path(requirement_path).read_text()
    req_pattern = re.compile(r'(REQ-[A-Z]+-[A-Z]+-\d{3})')
    req_keys = set(req_pattern.findall(req_content))

    # Check design document
    design_content = Path(design_path).read_text()
    design_keys = set(req_pattern.findall(design_content))

    missing = req_keys - design_keys

    return PropagationResult(
        source=requirement_path,
        target=design_path,
        keys_propagated=sorted(design_keys),
        keys_missing=sorted(missing),
        success=len(missing) == 0
    )


def propagate_to_code(
    design_path: str,
    src_dir: str
) -> PropagationResult:
    """Propagate REQ-* keys from design to code.

    Implements: REQ-TRACE-002
    """
    # Extract REQ-* from design
    design_content = Path(design_path).read_text()
    req_pattern = re.compile(r'(REQ-[A-Z]+-[A-Z]+-\d{3})')
    design_keys = set(req_pattern.findall(design_content))

    # Scan code
    code_keys = set()
    for path in Path(src_dir).rglob("*.py"):
        content = path.read_text()
        code_keys.update(req_pattern.findall(content))

    missing = design_keys - code_keys

    return PropagationResult(
        source=design_path,
        target=src_dir,
        keys_propagated=sorted(code_keys),
        keys_missing=sorted(missing),
        success=len(missing) == 0
    )


def propagate_to_tests(
    src_dir: str,
    tests_dir: str
) -> PropagationResult:
    """Propagate REQ-* keys from code to tests.

    Implements: REQ-TRACE-002
    """
    req_pattern = re.compile(r'(REQ-[A-Z]+-[A-Z]+-\d{3})')

    # Extract REQ-* from code
    code_keys = set()
    for path in Path(src_dir).rglob("*.py"):
        content = path.read_text()
        matches = re.findall(r'#\s*Implements:\s*(REQ-[A-Z]+-[A-Z]+-\d{3})', content)
        code_keys.update(matches)

    # Extract REQ-* from tests
    test_keys = set()
    for path in Path(tests_dir).rglob("test_*.py"):
        content = path.read_text()
        matches = re.findall(r'#\s*Validates:\s*(REQ-[A-Z]+-[A-Z]+-\d{3})', content)
        test_keys.update(matches)

    missing = code_keys - test_keys

    return PropagationResult(
        source=src_dir,
        target=tests_dir,
        keys_propagated=sorted(test_keys),
        keys_missing=sorted(missing),
        success=len(missing) == 0
    )
```

---

### 3. Validate Full Traceability Chain

**Goal**: Verify complete traceability from Intent to Runtime.

```python
# traceability/validator.py

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class TraceabilityChain:
    """Complete traceability chain for a requirement."""
    requirement: str
    intent: Optional[str]
    design_artifacts: List[str]
    tasks: List[str]
    code_files: List[str]
    tests: List[str]
    uat_status: Optional[str]
    runtime_metrics: List[str]
    chain_complete: bool
    gaps: List[str]


def validate_chain(requirement: str, project_paths: dict) -> TraceabilityChain:
    """Validate complete traceability chain for a requirement.

    Implements: REQ-TRACE-003
    """
    chain = TraceabilityChain(
        requirement=requirement,
        intent=None,
        design_artifacts=[],
        tasks=[],
        code_files=[],
        tests=[],
        uat_status=None,
        runtime_metrics=[],
        chain_complete=False,
        gaps=[]
    )

    # Check intent link
    chain.intent = find_intent_for_requirement(
        requirement,
        project_paths.get("traceability_dir")
    )
    if not chain.intent:
        chain.gaps.append("Missing intent link")

    # Check design
    chain.design_artifacts = find_design_artifacts(
        requirement,
        project_paths.get("design_dir")
    )
    if not chain.design_artifacts:
        chain.gaps.append("No design artifacts")

    # Check tasks
    chain.tasks = find_tasks(
        requirement,
        project_paths.get("tasks_dir")
    )
    if not chain.tasks:
        chain.gaps.append("No task tickets")

    # Check code
    chain.code_files = find_code_files(
        requirement,
        project_paths.get("src_dir")
    )
    if not chain.code_files:
        chain.gaps.append("No code implementation")

    # Check tests
    chain.tests = find_tests(
        requirement,
        project_paths.get("tests_dir")
    )
    if not chain.tests:
        chain.gaps.append("No tests")

    # Check UAT
    chain.uat_status = find_uat_status(
        requirement,
        project_paths.get("uat_dir")
    )
    if not chain.uat_status:
        chain.gaps.append("No UAT sign-off")

    # Check runtime
    chain.runtime_metrics = find_runtime_metrics(
        requirement,
        project_paths.get("observability_config")
    )
    if not chain.runtime_metrics:
        chain.gaps.append("No runtime telemetry")

    chain.chain_complete = len(chain.gaps) == 0
    return chain
```

---

## Traceability Matrix Template

```markdown
# Requirements Traceability Matrix

| REQ ID | Intent | Design | Tasks | Code | Tests | UAT | Runtime | Status |
|--------|--------|--------|-------|------|-------|-----|---------|--------|
| REQ-F-AUTH-001 | INT-042 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Complete |
| REQ-F-AUTH-002 | INT-042 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | Partial |
| REQ-F-PORTAL-001 | INT-042 | ✅ | ⏳ | ❌ | ❌ | ❌ | ❌ | In Design |

## Legend
- ✅ Complete
- ⏳ In Progress
- ❌ Not Started/Missing

## Coverage Summary

| Stage | Coverage |
|-------|----------|
| Requirements | 43/43 (100%) |
| Design | 43/43 (100%) |
| Tasks | 25/43 (58%) |
| Code | 15/43 (35%) |
| Tests | 8/43 (19%) |
| UAT | 0/43 (0%) |
| Runtime | 0/43 (0%) |
```

---

## Output Format

```
[TRACEABILITY VALIDATION - REQ-F-AUTH-001]

Chain Analysis:

Intent:
  ✅ INT-042: Customer self-service portal

Design:
  ✅ docs/design/adrs/ADR-001-session-storage.md
  ✅ docs/design/components/authentication-service.md
  ✅ api/v1/auth.yaml

Tasks:
  ✅ PORTAL-123: Implement login
  ✅ PORTAL-124: Add validation

Code:
  ✅ src/auth/authentication.py (login function)
  ✅ src/auth/validators.py (email validation)

Tests:
  ✅ tests/auth/test_login.py (5 tests)
  ✅ features/authentication.feature (3 scenarios)

UAT:
  ✅ UAT-001: Business sign-off (Approved)

Runtime:
  ✅ login_attempts{requirement="REQ-F-AUTH-001"}
  ✅ login_latency_ms{requirement="REQ-F-AUTH-001"}

Chain Status: COMPLETE
  All stages linked with REQ-F-AUTH-001

Traceability: Intent → Runtime verified
```

---

## CLI Commands

```bash
# Check coverage at all stages
aisdlc traceability check-coverage

# Validate specific requirement chain
aisdlc traceability validate REQ-F-AUTH-001

# Find gaps in traceability
aisdlc traceability find-gaps

# Generate traceability matrix
aisdlc traceability matrix

# Propagate keys from requirements to code
aisdlc traceability propagate --from requirements --to code
```

---

## Configuration

```yaml
# .claude/plugins.yml
plugins:
  - name: "@aisdlc/aisdlc-methodology"
    config:
      traceability:
        require_intent_link: true
        require_design_artifacts: true
        require_task_tickets: false  # Optional for small projects
        require_tests: true
        require_uat_signoff: true
        require_runtime_telemetry: true
        block_deploy_if_incomplete: true
        auto_generate_matrix: true
```

---

## Homeostasis Behavior

**If traceability gap detected**:
- Detect: REQ-* missing in downstream stage
- Signal: "Traceability incomplete"
- Action: List specific gaps
- Block: Prevent deployment until fixed

**If key propagation fails**:
- Detect: REQ-* not found in code/tests
- Signal: "Key propagation incomplete"
- Action: Add missing REQ-* comments
- Verify: Re-scan after fix

---

## Key Principles Applied

- **Test Driven Development**: Tests must validate REQ-*
- **Fail Fast**: Detect traceability gaps early
- **Perfectionist Excellence**: Complete chain or nothing

**"Excellence or nothing"**
