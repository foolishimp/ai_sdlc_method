# Traceability System - Design Document

**Document Type**: Technical Design Specification
**Project**: ai_sdlc_method (claude_aisdlc solution)
**Version**: 1.0
**Date**: 2025-12-03
**Status**: Draft
**Stage**: Design (Section 5.0)

---

## Requirements Traceability

This design implements the following requirements:

| Requirement | Description | Priority | Maps To |
|-------------|-------------|----------|---------|
| REQ-TRACE-001 | Full Lifecycle Traceability | Critical | Sections 2, 3, 4, 5 |
| REQ-TRACE-002 | Requirement Key Propagation | Critical | Sections 3, 6, 7 |
| REQ-TRACE-003 | Traceability Validation | High | Sections 8, 9, 10 |

**Source**: [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) Section 10

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Traceability Data Model](#2-traceability-data-model)
3. [Key Propagation System](#3-key-propagation-system)
4. [Link Discovery Engine](#4-link-discovery-engine)
5. [Traceability Matrix](#5-traceability-matrix)
6. [Validation Engine](#6-validation-engine)
7. [Extraction Patterns](#7-extraction-patterns)
8. [Gap Detection Algorithms](#8-gap-detection-algorithms)
9. [Report Generation](#9-report-generation)
10. [Storage Architecture](#10-storage-architecture)
11. [Implementation Guidance](#11-implementation-guidance)
12. [Examples](#12-examples)

---

## 1. Executive Summary

### 1.1 Purpose

The Traceability System provides **full lifecycle tracking** from intent to runtime, enabling:
- **Forward traceability**: Intent → Requirements → Design → Code → Tests → Runtime
- **Backward traceability**: Alert → Code → Requirement → Intent
- **Gap detection**: Orphan artifacts, missing links, incomplete coverage
- **Impact analysis**: Know what breaks when requirements change
- **Compliance**: Prove all requirements are implemented and tested

### 1.2 Design Principles

1. **Explicit Tagging** - REQ-* keys embedded in all artifacts (comments, metadata, logs)
2. **Immutable Keys** - Once created, REQ-* keys never change (content evolves, keys don't)
3. **Automated Discovery** - Extract links via pattern matching (regex, AST parsing)
4. **File-Based Storage** - No database required, version-controlled, human-readable
5. **CI/CD Integration** - Validation runs on every commit, blocks merge if gaps exist
6. **Bidirectional Navigation** - Query forward (REQ → artifacts) or backward (artifact → REQ)

### 1.3 Key Design Decisions

| Decision | Rationale | Requirement |
|----------|-----------|-------------|
| Comment-based tagging | Simple, language-agnostic, no AST changes | REQ-TRACE-002 |
| Pattern extraction (regex) | Fast, robust, no parsing overhead | REQ-TRACE-002 |
| Link graph structure | Enables bidirectional queries | REQ-TRACE-001 |
| JSON storage for matrix | Easy to generate, query, and diff | REQ-TRACE-001 |
| Severity classification | Distinguish errors vs warnings | REQ-TRACE-003 |
| Git integration | Leverage existing version control | REQ-TRACE-001 |

### 1.4 Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                      Traceability System                       │
└────────────────────────────────────────────────────────────────┘
         │
         ├─ 1. Key Propagation (REQ-* keys embedded everywhere)
         │     └─ Requirements → Design → Code → Tests → Runtime
         │
         ├─ 2. Link Discovery (Extract REQ-* from artifacts)
         │     └─ Regex patterns → AST parsing → Log scraping
         │
         ├─ 3. Link Graph (Bidirectional navigation)
         │     └─ Forward: REQ → artifacts
         │     └─ Backward: artifact → REQ
         │
         ├─ 4. Validation (Gap detection)
         │     └─ Orphan artifacts, missing links, incomplete coverage
         │
         ├─ 5. Matrix Generation (Coverage report)
         │     └─ Markdown table + JSON data + Coverage metrics
         │
         └─ 6. CI/CD Integration (Block merge on gaps)
               └─ Pre-commit hook + GitHub Actions + Exit codes
```

---

## 2. Traceability Data Model

### 2.1 Core Entities

#### 2.1.1 Artifact

**Definition**: Any versioned entity in the SDLC (requirement doc, design doc, code file, test file, commit, log entry)

**Schema**:
```yaml
artifact:
  id: "src/auth/login.py:23"  # Unique identifier
  type: code | test | requirement | design | task | commit | runtime
  path: "src/auth/login.py"
  line_number: 23  # Optional (for code/test)
  commit_sha: "abc123"  # Optional (for commit)
  timestamp: "2025-12-03T14:32:15Z"

  # Extracted metadata
  req_keys:
    - "<REQ-ID>"
    - "REQ-NFR-SEC-001"

  # Classification
  link_type: implements | validates | documents | mentions | tags
```

**Artifact Types**:

| Type | Examples | ID Format |
|------|----------|-----------|
| **requirement** | `docs/requirements/auth.md` | `{path}#{REQ-key}` |
| **design** | `docs/design/auth-service.md` | `{path}:#{section}` |
| **task** | `.ai-workspace/tasks/active/TASK-001.md` | `{path}` |
| **code** | `src/auth/login.py:23` | `{path}:{line}` |
| **test** | `tests/auth/test_login.py:15` | `{path}:{line}` |
| **commit** | Git commit `abc123` | `{commit_sha}` |
| **runtime** | Log entry, metric | `{service}:{metric}` |

---

#### 2.1.2 Link

**Definition**: A relationship between an artifact and a requirement (REQ-*)

**Schema**:
```yaml
link:
  source_artifact: "src/auth/login.py:23"
  target_req: "<REQ-ID>"
  link_type: implements | validates | documents | mentions | tags

  # Discovery metadata
  discovered_by: regex | ast | manual | git
  discovered_at: "2025-12-03T14:32:15Z"
  confidence: high | medium | low

  # Context
  context:
    line_content: "# Implements: <REQ-ID>"
    surrounding_code: "..."  # Optional, for preview
```

**Link Types**:

| Link Type | Source → Target | Meaning |
|-----------|-----------------|---------|
| **implements** | Code → REQ | Code provides the functionality |
| **validates** | Test → REQ | Test verifies the requirement |
| **documents** | Design → REQ | Design specifies how to implement |
| **mentions** | Task → REQ | Task tracks work for requirement |
| **tags** | Runtime → REQ | Telemetry tagged with requirement |
| **derives_from** | REQ → Intent | Requirement derived from intent |
| **depends_on** | REQ → REQ | Requirement depends on another |

---

#### 2.1.3 Link Graph

**Definition**: Directed graph of all traceability links

**Structure**:
```json
{
  "nodes": {
    "<REQ-ID>": {
      "type": "requirement",
      "path": "docs/requirements/auth.md",
      "title": "User login with email/password",
      "created": "2025-12-01"
    },
    "src/auth/login.py:23": {
      "type": "code",
      "path": "src/auth/login.py",
      "line": 23,
      "function": "login"
    }
  },
  "edges": [
    {
      "source": "src/auth/login.py:23",
      "target": "<REQ-ID>",
      "link_type": "implements",
      "confidence": "high"
    }
  ]
}
```

**Indexes** (for fast queries):
```json
{
  "by_req": {
    "<REQ-ID>": [
      "src/auth/login.py:23",
      "tests/auth/test_login.py:15",
      "docs/design/auth-service.md"
    ]
  },
  "by_artifact": {
    "src/auth/login.py:23": ["<REQ-ID>", "REQ-NFR-SEC-001"]
  },
  "by_type": {
    "implements": [...],
    "validates": [...]
  }
}
```

---

### 2.2 Requirement Key Format

**Pattern**: `REQ-{TYPE}-{DOMAIN}-{ID}`

**Types**:

| Type | Meaning | Example |
|------|---------|---------|
| **F** | Functional requirement | `<REQ-ID>` |
| **NFR** | Non-functional requirement | `REQ-NFR-PERF-001` |
| **DATA** | Data quality requirement | `REQ-DATA-PII-001` |
| **BR** | Business rule | `REQ-BR-REFUND-001` |

**Validation Regex**:
```regex
^REQ-(F|NFR|DATA|BR)-[A-Z]{2,10}-\d{3}$
```

**Subordinate Keys** (nested within requirements):

| Pattern | Meaning | Example |
|---------|---------|---------|
| `BR-{ID}` | Business rule (nested) | `BR-001` (email validation) |
| `C-{ID}` | Constraint (nested) | `C-001` (PCI-DSS compliance) |
| `F-{ID}` | Formula (nested) | `F-001` (stripe fee calculation) |

**Intent Keys**:
```regex
^INT-\d{8}-\d{3}$
```
Example: `INT-20251203-001` (date + sequence)

---

## 3. Key Propagation System

### 3.1 Propagation Workflow

```
Requirements Stage
    ↓ (Create REQ-* keys)
    │
Design Stage
    ↓ (Reference REQ-* in design docs)
    │
Tasks Stage
    ↓ (Tag tasks with REQ-*)
    │
Code Stage
    ↓ (Embed REQ-* in code comments)
    │
System Test Stage
    ↓ (Tag tests with REQ-*)
    │
UAT Stage
    ↓ (Reference REQ-* in test cases)
    │
Runtime Feedback Stage
    ↓ (Tag telemetry with REQ-*)
```

---

### 3.2 Embedding Patterns by Artifact Type

#### 3.2.1 Requirements Documents (Markdown)

**Format**: Heading with REQ-* key

```markdown
## <REQ-ID>: User Login with Email/Password

**Type**: Functional Requirement
**Priority**: Critical
**Derived From**: INT-20251203-001

**Description**: Users must be able to log in using email and password.

**Acceptance Criteria**:
- AC-001: Login form accepts email and password
- AC-002: Valid credentials return success
- AC-003: Invalid credentials return error

**Business Rules**:
- BR-001: Email must be valid format
- BR-002: Password minimum 12 characters
- BR-003: Account lockout after 3 failed attempts

**Constraints**:
- C-001: Session timeout after 30 minutes
- C-002: HTTPS required for all requests
```

**Extraction Pattern**:
```regex
^## (REQ-[A-Z]+-[A-Z0-9]+-\d{3}):
```

---

#### 3.2.2 Design Documents (Markdown)

**Format**: Section with "Implements: REQ-*"

```markdown
## Authentication Service

**Implements**: <REQ-ID>, REQ-NFR-SEC-001

### Component Overview

The AuthenticationService handles user login and session management.

**Architecture Decision**: Use JWT tokens (see ADR-003)

**Dependencies**:
- ValidationService (REQ-DATA-CQ-001)
- TokenService (REQ-NFR-SEC-001)
```

**Extraction Pattern**:
```regex
^\*\*Implements\*\*:\s*((REQ-[A-Z]+-[A-Z0-9]+-\d{3})(,\s*REQ-[A-Z]+-[A-Z0-9]+-\d{3})*)
```

---

#### 3.2.3 Task Files (Markdown)

**Format**: Frontmatter with requirements field

```markdown
---
id: TASK-001
title: Implement user login
status: in_progress
requirements:
  - <REQ-ID>
  - REQ-NFR-SEC-001
---

## Task Description

Implement user login functionality with email/password authentication.

## Acceptance Criteria
- [ ] Login endpoint created (<REQ-ID>)
- [ ] Validation implemented (BR-001, BR-002)
- [ ] Tests pass (AC-001, AC-002, AC-003)
```

**Extraction Pattern**:
```yaml
# Parse YAML frontmatter
requirements:
  - (REQ-.*)
```

---

#### 3.2.4 Code Files (Python)

**Format**: Comment with "Implements: REQ-*"

```python
# Implements: <REQ-ID>
# Also satisfies: REQ-NFR-SEC-001
def login(email: str, password: str) -> LoginResult:
    """
    User login with email and password.

    Implements: <REQ-ID> (User Login)
    Business Rules: BR-001 (email validation), BR-002 (password complexity)

    Args:
        email: User email address (BR-001)
        password: User password (BR-002)

    Returns:
        LoginResult with success status and session token

    Raises:
        ValidationError: If email/password invalid (BR-003)
    """
    # Validate email format (BR-001)
    if not validate_email(email):
        raise ValidationError("Invalid email format")

    # Validate password complexity (BR-002)
    if not validate_password(password):
        raise ValidationError("Password too weak")

    # Implementation...
    pass
```

**Extraction Patterns**:
```regex
# Pattern 1: Comment tag
^#\s*Implements:\s*((REQ-[A-Z]+-[A-Z0-9]+-\d{3})(,\s*REQ-[A-Z]+-[A-Z0-9]+-\d{3})*)

# Pattern 2: Docstring tag
^\s*Implements:\s*((REQ-[A-Z]+-[A-Z0-9]+-\d{3})(,\s*REQ-[A-Z]+-[A-Z0-9]+-\d{3})*)
```

---

#### 3.2.5 Test Files (Python - pytest)

**Format**: Comment with "Validates: REQ-*"

```python
# Validates: <REQ-ID>
def test_user_login_with_valid_credentials():
    """
    Test successful login with valid email and password.

    Validates: <REQ-ID> (AC-001, AC-002)
    """
    user = create_test_user(email="test@example.com", password="SecurePass123!")
    result = login(user.email, "SecurePass123!")

    assert result.success == True
    assert result.session_token is not None


# Validates: <REQ-ID> (AC-003)
def test_user_login_with_invalid_credentials():
    """
    Test failed login with invalid credentials.

    Validates: <REQ-ID> (AC-003), BR-003 (lockout)
    """
    user = create_test_user(email="test@example.com", password="SecurePass123!")
    result = login(user.email, "WrongPassword!")

    assert result.success == False
    assert result.error == "Invalid credentials"
```

**Extraction Pattern**:
```regex
^#\s*Validates:\s*((REQ-[A-Z]+-[A-Z0-9]+-\d{3})(,\s*REQ-[A-Z]+-[A-Z0-9]+-\d{3})*)
```

---

#### 3.2.6 BDD Feature Files (Gherkin)

**Format**: Tag with @REQ-*

```gherkin
# Validates: <REQ-ID>
@<REQ-ID> @authentication
Feature: User Login
  As a user
  I want to log in with email and password
  So that I can access the customer portal

  Background:
    Given a user exists with email "test@example.com" and password "SecurePass123!"

  # Validates: AC-001, AC-002
  Scenario: Successful login with valid credentials
    Given I am on the login page
    When I enter email "test@example.com"
    And I enter password "SecurePass123!"
    And I click "Login"
    Then I should see "Welcome back"
    And I should be redirected to "/dashboard"

  # Validates: AC-003, BR-003
  Scenario: Failed login with invalid credentials
    Given I am on the login page
    When I enter email "test@example.com"
    And I enter password "WrongPassword!"
    And I click "Login"
    Then I should see "Invalid credentials"
    And I should remain on the login page
```

**Extraction Pattern**:
```regex
@(REQ-[A-Z]+-[A-Z0-9]+-\d{3})
```

---

#### 3.2.7 Commit Messages

**Format**: Footer with "Implements: REQ-*" or "Validates: REQ-*"

```
feat: Add user login functionality

Implement user authentication with email/password.

Implements: <REQ-ID>
Validates: BR-001, BR-002, BR-003

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Extraction Pattern**:
```regex
^(Implements|Validates):\s*((REQ-[A-Z]+-[A-Z0-9]+-\d{3})(,\s*REQ-[A-Z]+-[A-Z0-9]+-\d{3})*)
```

---

#### 3.2.8 Runtime Telemetry

**Log Entries** (structured logging):
```python
logger.info(
    "User login successful",
    extra={
        "req": "<REQ-ID>",
        "user_id": user.id,
        "latency_ms": 120,
        "success": True
    }
)
```

**Metrics** (Datadog):
```python
statsd.increment(
    "auth.login.success",
    tags=["req:<REQ-ID>", "env:production"]
)

statsd.histogram(
    "auth.login.latency",
    120,
    tags=["req:<REQ-ID>", "env:production"]
)
```

**Metrics** (Prometheus):
```python
auth_success_total{req="<REQ-ID>", env="production"} 1
auth_latency_seconds{req="<REQ-ID>", env="production"} 0.120
```

**Extraction Pattern**:
```regex
# Logs
"req":\s*"(REQ-[A-Z]+-[A-Z0-9]+-\d{3})"

# Datadog
req:(REQ-[A-Z]+-[A-Z0-9]+-\d{3})

# Prometheus
req="(REQ-[A-Z]+-[A-Z0-9]+-\d{3})"
```

---

## 4. Link Discovery Engine

### 4.1 Discovery Pipeline

```
1. File Discovery (Glob patterns)
   ↓
2. Pattern Extraction (Regex)
   ↓
3. AST Parsing (Optional, for complex cases)
   ↓
4. Link Creation (Graph edges)
   ↓
5. Index Building (Fast queries)
   ↓
6. Validation (Confidence scoring)
```

---

### 4.2 Discovery Strategies

#### 4.2.1 Regex-Based Extraction (Fast)

**Pros**: Fast, language-agnostic, simple
**Cons**: Can miss complex cases (multi-line, nested)

**Implementation**:
```python
import re
from pathlib import Path
from typing import List, Tuple

# REQ-* pattern
REQ_PATTERN = re.compile(r'REQ-(F|NFR|DATA|BR)-[A-Z]{2,10}-\d{3}')

# Context patterns by link type
IMPLEMENTS_PATTERN = re.compile(r'#\s*Implements:\s*((REQ-[A-Z]+-[A-Z0-9]+-\d{3})(,\s*REQ-[A-Z]+-[A-Z0-9]+-\d{3})*)')
VALIDATES_PATTERN = re.compile(r'#\s*Validates:\s*((REQ-[A-Z]+-[A-Z0-9]+-\d{3})(,\s*REQ-[A-Z]+-[A-Z0-9]+-\d{3})*)')

def extract_req_links_from_file(file_path: Path) -> List[dict]:
    """Extract all REQ-* links from a file using regex"""
    links = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            # Check for "Implements:" tag
            if match := IMPLEMENTS_PATTERN.search(line):
                req_keys = REQ_PATTERN.findall(match.group(0))
                for req_key in req_keys:
                    links.append({
                        'source': f"{file_path}:{line_num}",
                        'target': f"REQ-{req_key}",
                        'link_type': 'implements',
                        'line': line_num,
                        'context': line.strip(),
                        'discovered_by': 'regex',
                        'confidence': 'high'
                    })

            # Check for "Validates:" tag
            if match := VALIDATES_PATTERN.search(line):
                req_keys = REQ_PATTERN.findall(match.group(0))
                for req_key in req_keys:
                    links.append({
                        'source': f"{file_path}:{line_num}",
                        'target': f"REQ-{req_key}",
                        'link_type': 'validates',
                        'line': line_num,
                        'context': line.strip(),
                        'discovered_by': 'regex',
                        'confidence': 'high'
                    })

    return links
```

---

#### 4.2.2 AST-Based Extraction (Accurate)

**Pros**: Accurate, handles complex cases
**Cons**: Language-specific, slower

**Implementation** (Python):
```python
import ast
from pathlib import Path
from typing import List

def extract_req_links_from_python_ast(file_path: Path) -> List[dict]:
    """Extract REQ-* links from Python file using AST"""
    links = []

    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []  # Skip files with syntax errors

    for node in ast.walk(tree):
        # Check function docstrings
        if isinstance(node, ast.FunctionDef):
            docstring = ast.get_docstring(node)
            if docstring:
                # Extract REQ-* from docstring
                req_keys = REQ_PATTERN.findall(docstring)
                for req_key in req_keys:
                    # Determine link type from context
                    link_type = 'implements'
                    if 'Validates:' in docstring or 'test_' in node.name:
                        link_type = 'validates'

                    links.append({
                        'source': f"{file_path}:{node.lineno}",
                        'target': f"REQ-{req_key}",
                        'link_type': link_type,
                        'line': node.lineno,
                        'function': node.name,
                        'discovered_by': 'ast',
                        'confidence': 'high'
                    })

        # Check comments (via source mapping)
        # Note: AST doesn't preserve comments, use tokenize module

    return links
```

---

#### 4.2.3 Git Log Extraction

**Purpose**: Extract REQ-* from commit messages

**Implementation**:
```bash
#!/bin/bash
# Extract REQ-* from all commits

git log --all --pretty=format:"%H|%s|%b" | \
  grep -oE "REQ-[A-Z]+-[A-Z0-9]+-[0-9]{3}" | \
  sort -u
```

**Python wrapper**:
```python
import subprocess
import re

def extract_req_links_from_git() -> List[dict]:
    """Extract REQ-* links from git commit history"""
    links = []

    result = subprocess.run(
        ['git', 'log', '--all', '--pretty=format:%H|%s|%b'],
        capture_output=True,
        text=True
    )

    for line in result.stdout.split('\n'):
        parts = line.split('|', 2)
        if len(parts) < 3:
            continue

        commit_sha, subject, body = parts
        full_message = f"{subject}\n{body}"

        # Extract REQ-* keys
        req_keys = REQ_PATTERN.findall(full_message)

        for req_key in req_keys:
            # Determine link type from context
            link_type = 'mentions'
            if 'Implements:' in full_message:
                link_type = 'implements'
            elif 'Validates:' in full_message:
                link_type = 'validates'

            links.append({
                'source': commit_sha,
                'target': f"REQ-{req_key}",
                'link_type': link_type,
                'commit_sha': commit_sha,
                'subject': subject,
                'discovered_by': 'git',
                'confidence': 'high'
            })

    return links
```

---

### 4.3 File Discovery (Glob Patterns)

**Artifact Types**:

| Artifact Type | Glob Pattern | Discovery Method |
|---------------|--------------|------------------|
| Requirements | `docs/requirements/**/*.md` | Regex (heading) |
| Design | `docs/design/**/*.md` | Regex (implements) |
| ADRs | `docs/design/**/adrs/*.md` | Regex (implements) |
| Tasks | `.ai-workspace/tasks/**/*.md` | YAML frontmatter |
| Code (Python) | `src/**/*.py` | Regex + AST |
| Tests (Python) | `tests/**/*.py` | Regex + AST |
| BDD Features | `features/**/*.feature` | Regex (tags) |
| Commits | Git log | Git command |
| Logs | `logs/**/*.log` | Regex (structured) |

**Implementation**:
```python
from pathlib import Path
from typing import Dict, List

ARTIFACT_PATTERNS = {
    'requirement': ['docs/requirements/**/*.md'],
    'design': ['docs/design/**/*.md', 'docs/**/adrs/*.md'],
    'task': ['.ai-workspace/tasks/**/*.md'],
    'code': ['src/**/*.py'],
    'test': ['tests/**/*.py', 'features/**/*.feature'],
}

def discover_artifacts(root: Path) -> Dict[str, List[Path]]:
    """Discover all artifacts by type"""
    artifacts = {}

    for artifact_type, patterns in ARTIFACT_PATTERNS.items():
        artifacts[artifact_type] = []
        for pattern in patterns:
            artifacts[artifact_type].extend(root.glob(pattern))

    return artifacts
```

---

## 5. Traceability Matrix

### 5.1 Matrix Structure

**Full Traceability Matrix** (markdown table):

```markdown
# Traceability Matrix

**Generated**: 2025-12-03 14:30:00
**Total Requirements**: 42
**Overall Coverage**: 86%

---

## Summary by Stage

| Stage | Requirements | Covered | Percentage | Status |
|-------|-------------|---------|------------|--------|
| Requirements → Design | 42 | 40 | 95% | ✅ |
| Design → Code | 42 | 36 | 86% | ⚠️ |
| Code → Tests | 42 | 35 | 83% | ⚠️ |
| Tests → Runtime | 42 | 10 | 24% | ❌ |

---

## Full Matrix

| REQ-* | Requirement | Design | Code | Tests | Commits | Runtime | Status |
|-------|-------------|--------|------|-------|---------|---------|--------|
| <REQ-ID> | User login | ✅ AuthService | ✅ login.py:23 | ✅ test_login.py:15 | ✅ 5 | ✅ Datadog | ✅ Complete |
| <REQ-ID> | Password reset | ✅ EmailService | ✅ reset.py:45 | ✅ test_reset.py:22 | ✅ 3 | ⚠️ Partial | ⚠️ Partial |
| REQ-F-PORTAL-001 | View balance | ✅ PortalService | ✅ balance.py:12 | ✅ test_balance.py:8 | ✅ 2 | ❌ None | ⚠️ Partial |
| REQ-F-PORTAL-002 | Update profile | ❌ No design | ❌ None | ❌ None | ❌ 0 | ❌ None | ❌ Not Started |
```

---

### 5.2 Matrix Data Structure (JSON)

**File**: `docs/traceability/matrix.json`

```json
{
  "metadata": {
    "generated_at": "2025-12-03T14:30:00Z",
    "total_requirements": 42,
    "overall_coverage": 0.86,
    "generator_version": "1.0.0"
  },

  "summary": {
    "by_stage": {
      "design": {"total": 42, "covered": 40, "percentage": 0.95},
      "code": {"total": 42, "covered": 36, "percentage": 0.86},
      "tests": {"total": 42, "covered": 35, "percentage": 0.83},
      "runtime": {"total": 42, "covered": 10, "percentage": 0.24}
    },
    "by_priority": {
      "critical": {"total": 10, "covered": 9, "percentage": 0.90},
      "high": {"total": 15, "covered": 14, "percentage": 0.93},
      "medium": {"total": 12, "covered": 10, "percentage": 0.83},
      "low": {"total": 5, "covered": 3, "percentage": 0.60}
    }
  },

  "requirements": [
    {
      "id": "<REQ-ID>",
      "title": "User login with email/password",
      "priority": "critical",
      "type": "functional",

      "links": {
        "design": [
          {"path": "docs/design/auth-service.md", "section": "Authentication Flow"}
        ],
        "code": [
          {"path": "src/auth/login.py", "line": 23, "function": "login"}
        ],
        "tests": [
          {"path": "tests/auth/test_login.py", "line": 15, "test": "test_user_login_with_valid_credentials"},
          {"path": "features/authentication.feature", "line": 5, "scenario": "Successful login"}
        ],
        "commits": [
          {"sha": "abc123", "subject": "feat: Add user login"},
          {"sha": "def456", "subject": "fix: Correct email validation"}
        ],
        "runtime": [
          {"service": "api", "metric": "auth_success", "platform": "datadog"}
        ]
      },

      "coverage": {
        "design": true,
        "code": true,
        "tests": true,
        "commits": true,
        "runtime": true,
        "percentage": 1.0,
        "status": "complete"
      }
    }
  ],

  "gaps": {
    "no_design": [],
    "no_code": ["REQ-F-PORTAL-002", "REQ-F-NOTIF-001"],
    "no_tests": ["REQ-F-CART-001"],
    "no_runtime": ["<REQ-ID>", "REQ-F-PORTAL-001"]
  }
}
```

---

### 5.3 Matrix Generation Algorithm

**Input**: Link graph + Requirement list

**Output**: Matrix JSON + Matrix markdown

**Algorithm**:
```python
from pathlib import Path
from typing import Dict, List
import json

def generate_traceability_matrix(
    requirements: List[dict],
    link_graph: dict,
    output_dir: Path
) -> dict:
    """
    Generate traceability matrix from requirements and link graph.

    Args:
        requirements: List of requirement documents
        link_graph: Graph of traceability links
        output_dir: Directory to write matrix files

    Returns:
        Matrix data structure
    """
    matrix = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_requirements': len(requirements),
            'generator_version': '1.0.0'
        },
        'requirements': [],
        'summary': {},
        'gaps': {}
    }

    # For each requirement, find all linked artifacts
    for req in requirements:
        req_id = req['id']

        # Query link graph for this requirement
        req_data = {
            'id': req_id,
            'title': req['title'],
            'priority': req.get('priority', 'medium'),
            'type': req.get('type', 'functional'),
            'links': {
                'design': [],
                'code': [],
                'tests': [],
                'commits': [],
                'runtime': []
            },
            'coverage': {}
        }

        # Find all artifacts that link to this requirement
        if req_id in link_graph['by_req']:
            for artifact_id in link_graph['by_req'][req_id]:
                artifact = link_graph['nodes'][artifact_id]

                # Categorize by artifact type
                if artifact['type'] == 'design':
                    req_data['links']['design'].append({
                        'path': artifact['path'],
                        'section': artifact.get('section')
                    })
                elif artifact['type'] == 'code':
                    req_data['links']['code'].append({
                        'path': artifact['path'],
                        'line': artifact.get('line'),
                        'function': artifact.get('function')
                    })
                elif artifact['type'] == 'test':
                    req_data['links']['tests'].append({
                        'path': artifact['path'],
                        'line': artifact.get('line'),
                        'test': artifact.get('function')
                    })
                elif artifact['type'] == 'commit':
                    req_data['links']['commits'].append({
                        'sha': artifact['commit_sha'],
                        'subject': artifact.get('subject')
                    })
                elif artifact['type'] == 'runtime':
                    req_data['links']['runtime'].append({
                        'service': artifact.get('service'),
                        'metric': artifact.get('metric'),
                        'platform': artifact.get('platform')
                    })

        # Calculate coverage
        req_data['coverage'] = {
            'design': len(req_data['links']['design']) > 0,
            'code': len(req_data['links']['code']) > 0,
            'tests': len(req_data['links']['tests']) > 0,
            'commits': len(req_data['links']['commits']) > 0,
            'runtime': len(req_data['links']['runtime']) > 0,
        }

        # Calculate percentage
        stages = ['design', 'code', 'tests', 'commits', 'runtime']
        covered = sum(1 for stage in stages if req_data['coverage'][stage])
        req_data['coverage']['percentage'] = covered / len(stages)

        # Determine status
        if req_data['coverage']['percentage'] == 1.0:
            req_data['coverage']['status'] = 'complete'
        elif req_data['coverage']['percentage'] > 0:
            req_data['coverage']['status'] = 'partial'
        else:
            req_data['coverage']['status'] = 'not_started'

        matrix['requirements'].append(req_data)

    # Calculate summary statistics
    matrix['summary'] = calculate_summary(matrix['requirements'])

    # Identify gaps
    matrix['gaps'] = identify_gaps(matrix['requirements'])

    # Write JSON file
    json_path = output_dir / 'matrix.json'
    with open(json_path, 'w') as f:
        json.dump(matrix, f, indent=2)

    # Generate markdown file
    md_path = output_dir / 'TRACEABILITY_MATRIX.md'
    generate_matrix_markdown(matrix, md_path)

    return matrix


def calculate_summary(requirements: List[dict]) -> dict:
    """Calculate summary statistics"""
    total = len(requirements)

    summary = {
        'by_stage': {
            'design': {'total': total, 'covered': 0, 'percentage': 0},
            'code': {'total': total, 'covered': 0, 'percentage': 0},
            'tests': {'total': total, 'covered': 0, 'percentage': 0},
            'runtime': {'total': total, 'covered': 0, 'percentage': 0}
        }
    }

    # Count coverage by stage
    for req in requirements:
        for stage in ['design', 'code', 'tests', 'runtime']:
            if req['coverage'][stage]:
                summary['by_stage'][stage]['covered'] += 1

    # Calculate percentages
    for stage_data in summary['by_stage'].values():
        stage_data['percentage'] = stage_data['covered'] / stage_data['total']

    return summary


def identify_gaps(requirements: List[dict]) -> dict:
    """Identify coverage gaps"""
    gaps = {
        'no_design': [],
        'no_code': [],
        'no_tests': [],
        'no_runtime': []
    }

    for req in requirements:
        if not req['coverage']['design']:
            gaps['no_design'].append(req['id'])
        if not req['coverage']['code']:
            gaps['no_code'].append(req['id'])
        if not req['coverage']['tests']:
            gaps['no_tests'].append(req['id'])
        if not req['coverage']['runtime']:
            gaps['no_runtime'].append(req['id'])

    return gaps
```

---

## 6. Validation Engine

### 6.1 Validation Rules

**Rule Types**:

| Rule ID | Rule Name | Severity | Description |
|---------|-----------|----------|-------------|
| **VAL-001** | Orphan Requirement | ERROR | Requirement with no code/tests |
| **VAL-002** | Orphan Code | WARNING | Code with no requirement tag |
| **VAL-003** | Orphan Test | WARNING | Test with no requirement tag |
| **VAL-004** | Invalid REQ-* Format | ERROR | REQ-* key doesn't match pattern |
| **VAL-005** | Missing Design | WARNING | Code implemented without design |
| **VAL-006** | Missing Tests | ERROR | Code without tests |
| **VAL-007** | Missing Runtime Telemetry | INFO | No telemetry tags for requirement |
| **VAL-008** | Dangling REQ-* Reference | ERROR | REQ-* tag references non-existent requirement |
| **VAL-009** | Duplicate REQ-* Key | ERROR | Multiple requirements with same key |
| **VAL-010** | Circular Dependency | ERROR | REQ-A depends on REQ-B depends on REQ-A |

---

### 6.2 Validation Algorithms

#### 6.2.1 VAL-001: Orphan Requirements

**Definition**: Requirements with no implementing code or validating tests

**Algorithm**:
```python
def validate_orphan_requirements(matrix: dict) -> List[dict]:
    """Find requirements without code or tests"""
    violations = []

    for req in matrix['requirements']:
        has_code = req['coverage']['code']
        has_tests = req['coverage']['tests']

        if not has_code and not has_tests:
            violations.append({
                'rule': 'VAL-001',
                'severity': 'ERROR',
                'req_id': req['id'],
                'message': f"Requirement {req['id']} has no code or tests",
                'suggestion': f"Implement code for {req['id']} or mark as not implemented"
            })

    return violations
```

---

#### 6.2.2 VAL-002: Orphan Code

**Definition**: Code files with no REQ-* tags

**Algorithm**:
```python
def validate_orphan_code(link_graph: dict, code_files: List[Path]) -> List[dict]:
    """Find code files without requirement tags"""
    violations = []

    # Get all code files that have REQ-* links
    linked_files = set()
    for artifact_id, artifact in link_graph['nodes'].items():
        if artifact['type'] == 'code':
            linked_files.add(artifact['path'])

    # Find code files without links
    for code_file in code_files:
        if str(code_file) not in linked_files:
            violations.append({
                'rule': 'VAL-002',
                'severity': 'WARNING',
                'file': str(code_file),
                'message': f"Code file {code_file} has no REQ-* tags",
                'suggestion': f"Add '# Implements: REQ-*' comment to {code_file}"
            })

    return violations
```

---

#### 6.2.3 VAL-004: Invalid REQ-* Format

**Definition**: REQ-* keys that don't match the pattern

**Algorithm**:
```python
import re

REQ_PATTERN = re.compile(r'^REQ-(F|NFR|DATA|BR)-[A-Z]{2,10}-\d{3}$')

def validate_req_key_format(req_keys: List[str]) -> List[dict]:
    """Validate REQ-* key format"""
    violations = []

    for req_key in req_keys:
        if not REQ_PATTERN.match(req_key):
            violations.append({
                'rule': 'VAL-004',
                'severity': 'ERROR',
                'req_key': req_key,
                'message': f"Invalid REQ-* format: {req_key}",
                'suggestion': f"Use format: REQ-(F|NFR|DATA|BR)-DOMAIN-###",
                'pattern': '^REQ-(F|NFR|DATA|BR)-[A-Z]{2,10}-\\d{3}$'
            })

    return violations
```

---

#### 6.2.4 VAL-006: Missing Tests

**Definition**: Code with REQ-* tag but no corresponding test

**Algorithm**:
```python
def validate_missing_tests(link_graph: dict) -> List[dict]:
    """Find code without tests"""
    violations = []

    # Group links by requirement
    by_req = {}
    for edge in link_graph['edges']:
        req_id = edge['target']
        if req_id not in by_req:
            by_req[req_id] = {'implements': [], 'validates': []}

        if edge['link_type'] == 'implements':
            by_req[req_id]['implements'].append(edge['source'])
        elif edge['link_type'] == 'validates':
            by_req[req_id]['validates'].append(edge['source'])

    # Find requirements with code but no tests
    for req_id, links in by_req.items():
        if links['implements'] and not links['validates']:
            violations.append({
                'rule': 'VAL-006',
                'severity': 'ERROR',
                'req_id': req_id,
                'code_files': links['implements'],
                'message': f"Requirement {req_id} has code but no tests",
                'suggestion': f"Add tests for {req_id} with '# Validates: {req_id}' tag"
            })

    return violations
```

---

#### 6.2.5 VAL-008: Dangling References

**Definition**: REQ-* tags that reference non-existent requirements

**Algorithm**:
```python
def validate_dangling_references(
    link_graph: dict,
    requirements: List[dict]
) -> List[dict]:
    """Find REQ-* tags referencing non-existent requirements"""
    violations = []

    # Get all valid requirement IDs
    valid_req_ids = {req['id'] for req in requirements}

    # Check all REQ-* references in link graph
    for edge in link_graph['edges']:
        req_id = edge['target']
        if req_id not in valid_req_ids:
            violations.append({
                'rule': 'VAL-008',
                'severity': 'ERROR',
                'req_id': req_id,
                'source': edge['source'],
                'message': f"REQ-* tag {req_id} references non-existent requirement",
                'suggestion': f"Create requirement {req_id} or remove reference from {edge['source']}"
            })

    return violations
```

---

### 6.3 Validation Report Format

**Markdown**:
```markdown
# Traceability Validation Report

**Generated**: 2025-12-03 14:30:00
**Status**: ❌ FAILED (12 errors, 34 warnings, 56 infos)

---

## Summary

| Severity | Count | Rules Triggered |
|----------|-------|-----------------|
| ERROR | 12 | VAL-001, VAL-004, VAL-006, VAL-008 |
| WARNING | 34 | VAL-002, VAL-003, VAL-005 |
| INFO | 56 | VAL-007 |

---

## Errors (12)

### VAL-001: Orphan Requirements (6)

Requirements with no code or tests:

- **REQ-F-PORTAL-002** (Update profile)
  - **Suggestion**: Implement code for REQ-F-PORTAL-002 or mark as not implemented

- **REQ-F-NOTIF-001** (Email notifications)
  - **Suggestion**: Implement code for REQ-F-NOTIF-001 or mark as not implemented

---

### VAL-006: Missing Tests (6)

Code without tests:

- **<REQ-ID>** (Password reset)
  - **Code**: src/auth/reset.py:45
  - **Suggestion**: Add tests for <REQ-ID> with '# Validates: <REQ-ID>' tag

---

## Warnings (34)

### VAL-002: Orphan Code (34)

Code files without REQ-* tags:

- **src/utils/helpers.py**
  - **Suggestion**: Add '# Implements: REQ-*' comment to src/utils/helpers.py

---

## Info (56)

### VAL-007: Missing Runtime Telemetry (56)

Requirements without runtime telemetry:

- **<REQ-ID>** (User login)
  - **Suggestion**: Add telemetry tags with req="<REQ-ID>"
```

**JSON**:
```json
{
  "generated_at": "2025-12-03T14:30:00Z",
  "status": "failed",
  "counts": {
    "error": 12,
    "warning": 34,
    "info": 56
  },
  "violations": [
    {
      "rule": "VAL-001",
      "severity": "ERROR",
      "req_id": "REQ-F-PORTAL-002",
      "message": "Requirement REQ-F-PORTAL-002 has no code or tests",
      "suggestion": "Implement code for REQ-F-PORTAL-002 or mark as not implemented",
      "file": null,
      "line": null
    }
  ]
}
```

---

## 7. Extraction Patterns

### 7.1 Pattern Library

**Centralized pattern definitions** for consistent extraction:

```python
# patterns.py

import re
from typing import Dict

# REQ-* key patterns
REQ_PATTERNS = {
    'all': re.compile(r'REQ-(F|NFR|DATA|BR)-[A-Z]{2,10}-\d{3}'),
    'functional': re.compile(r'REQ-F-[A-Z]{2,10}-\d{3}'),
    'non_functional': re.compile(r'REQ-NFR-(PERF|SEC|SCALE|AVAIL|MAINT|USABIL)-\d{3}'),
    'data_quality': re.compile(r'REQ-DATA-(CQ|AQ|CONS|TIME|LIN|PII)-\d{3}'),
    'business_rule': re.compile(r'REQ-BR-[A-Z]{2,10}-\d{3}'),
}

# Context patterns (with capture groups)
CONTEXT_PATTERNS = {
    # Code comments
    'implements_comment': re.compile(r'#\s*Implements:\s*((REQ-[A-Z]+-[A-Z0-9]+-\d{3})(,\s*REQ-[A-Z]+-[A-Z0-9]+-\d{3})*)'),
    'validates_comment': re.compile(r'#\s*Validates:\s*((REQ-[A-Z]+-[A-Z0-9]+-\d{3})(,\s*REQ-[A-Z]+-[A-Z0-9]+-\d{3})*)'),

    # Docstrings
    'implements_docstring': re.compile(r'^\s*Implements:\s*((REQ-[A-Z]+-[A-Z0-9]+-\d{3})(,\s*REQ-[A-Z]+-[A-Z0-9]+-\d{3})*)', re.MULTILINE),
    'validates_docstring': re.compile(r'^\s*Validates:\s*((REQ-[A-Z]+-[A-Z0-9]+-\d{3})(,\s*REQ-[A-Z]+-[A-Z0-9]+-\d{3})*)', re.MULTILINE),

    # Markdown
    'req_heading': re.compile(r'^##\s+(REQ-[A-Z]+-[A-Z0-9]+-\d{3}):\s*(.*)$', re.MULTILINE),
    'implements_bold': re.compile(r'\*\*Implements\*\*:\s*((REQ-[A-Z]+-[A-Z0-9]+-\d{3})(,\s*REQ-[A-Z]+-[A-Z0-9]+-\d{3})*)'),

    # Git commits
    'commit_implements': re.compile(r'^Implements:\s*((REQ-[A-Z]+-[A-Z0-9]+-\d{3})(,\s*REQ-[A-Z]+-[A-Z0-9]+-\d{3})*)', re.MULTILINE),
    'commit_validates': re.compile(r'^Validates:\s*((REQ-[A-Z]+-[A-Z0-9]+-\d{3})(,\s*REQ-[A-Z]+-[A-Z0-9]+-\d{3})*)', re.MULTILINE),

    # Gherkin tags
    'gherkin_tag': re.compile(r'@(REQ-[A-Z]+-[A-Z0-9]+-\d{3})'),
    'gherkin_comment': re.compile(r'#\s*Validates:\s*((REQ-[A-Z]+-[A-Z0-9]+-\d{3})(,\s*REQ-[A-Z]+-[A-Z0-9]+-\d{3})*)'),

    # Runtime telemetry
    'log_req_field': re.compile(r'"req":\s*"(REQ-[A-Z]+-[A-Z0-9]+-\d{3})"'),
    'datadog_tag': re.compile(r'req:(REQ-[A-Z]+-[A-Z0-9]+-\d{3})'),
    'prometheus_label': re.compile(r'req="(REQ-[A-Z]+-[A-Z0-9]+-\d{3})"'),
}

# Intent patterns
INTENT_PATTERN = re.compile(r'INT-\d{8}-\d{3}')
```

---

### 7.2 Language-Specific Patterns

#### 7.2.1 Python

```python
PYTHON_PATTERNS = {
    'function_with_tag': re.compile(
        r'#\s*(Implements|Validates):\s*((REQ-[A-Z]+-[A-Z0-9]+-\d{3})(,\s*REQ-[A-Z]+-[A-Z0-9]+-\d{3})*)\n'
        r'def\s+(\w+)',
        re.MULTILINE
    ),

    'class_with_tag': re.compile(
        r'#\s*(Implements|Validates):\s*((REQ-[A-Z]+-[A-Z0-9]+-\d{3})(,\s*REQ-[A-Z]+-[A-Z0-9]+-\d{3})*)\n'
        r'class\s+(\w+)',
        re.MULTILINE
    ),
}
```

---

#### 7.2.2 JavaScript/TypeScript

```python
JS_PATTERNS = {
    'function_with_jsdoc': re.compile(
        r'/\*\*\n'
        r'\s*\*\s*Implements:\s*((REQ-[A-Z]+-[A-Z0-9]+-\d{3})(,\s*REQ-[A-Z]+-[A-Z0-9]+-\d{3})*)\n'
        r'\s*\*/\n'
        r'\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)',
        re.MULTILINE
    ),

    'comment_with_tag': re.compile(
        r'//\s*(Implements|Validates):\s*((REQ-[A-Z]+-[A-Z0-9]+-\d{3})(,\s*REQ-[A-Z]+-[A-Z0-9]+-\d{3})*)'
    ),
}
```

---

#### 7.2.3 Java

```python
JAVA_PATTERNS = {
    'javadoc_with_tag': re.compile(
        r'/\*\*\n'
        r'(?:.*\n)*?'
        r'\s*\*\s*@implements\s+((REQ-[A-Z]+-[A-Z0-9]+-\d{3})(,\s*REQ-[A-Z]+-[A-Z0-9]+-\d{3})*)\n'
        r'(?:.*\n)*?'
        r'\s*\*/\n'
        r'\s*(?:public|private|protected)\s+(?:static\s+)?(?:\w+\s+)?(\w+)\s*\(',
        re.MULTILINE
    ),
}
```

---

## 8. Gap Detection Algorithms

### 8.1 Coverage Gap Detection

**Algorithm**: Find requirements without full coverage

```python
def detect_coverage_gaps(matrix: dict) -> dict:
    """
    Detect requirements without full lifecycle coverage.

    Returns:
        Dictionary of gap types and affected requirements
    """
    gaps = {
        'no_design': [],
        'no_code': [],
        'no_tests': [],
        'no_commits': [],
        'no_runtime': [],
        'incomplete': []  # Has some coverage but not full
    }

    for req in matrix['requirements']:
        req_id = req['id']
        coverage = req['coverage']

        # Check each stage
        if not coverage['design']:
            gaps['no_design'].append({
                'req_id': req_id,
                'title': req['title'],
                'priority': req['priority']
            })

        if not coverage['code']:
            gaps['no_code'].append({
                'req_id': req_id,
                'title': req['title'],
                'priority': req['priority']
            })

        if not coverage['tests']:
            gaps['no_tests'].append({
                'req_id': req_id,
                'title': req['title'],
                'priority': req['priority']
            })

        if not coverage['commits']:
            gaps['no_commits'].append({
                'req_id': req_id,
                'title': req['title'],
                'priority': req['priority']
            })

        if not coverage['runtime']:
            gaps['no_runtime'].append({
                'req_id': req_id,
                'title': req['title'],
                'priority': req['priority']
            })

        # Check for partial coverage
        if 0 < coverage['percentage'] < 1.0:
            gaps['incomplete'].append({
                'req_id': req_id,
                'title': req['title'],
                'priority': req['priority'],
                'percentage': coverage['percentage'],
                'missing_stages': [
                    stage for stage in ['design', 'code', 'tests', 'commits', 'runtime']
                    if not coverage[stage]
                ]
            })

    # Sort by priority (critical first)
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    for gap_list in gaps.values():
        gap_list.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 3))

    return gaps
```

---

### 8.2 Orphan Detection

**Algorithm**: Find artifacts without requirement links

```python
def detect_orphan_artifacts(
    link_graph: dict,
    all_artifacts: Dict[str, List[Path]]
) -> dict:
    """
    Detect artifacts without requirement links.

    Returns:
        Dictionary of orphan artifacts by type
    """
    orphans = {
        'code': [],
        'tests': [],
        'design': []
    }

    # Get all linked artifact paths
    linked_paths = {
        artifact['path']
        for artifact in link_graph['nodes'].values()
        if 'path' in artifact
    }

    # Check code files
    for code_file in all_artifacts.get('code', []):
        if str(code_file) not in linked_paths:
            orphans['code'].append({
                'path': str(code_file),
                'suggestion': f"Add '# Implements: REQ-*' to {code_file}"
            })

    # Check test files
    for test_file in all_artifacts.get('test', []):
        if str(test_file) not in linked_paths:
            orphans['tests'].append({
                'path': str(test_file),
                'suggestion': f"Add '# Validates: REQ-*' to {test_file}"
            })

    # Check design files
    for design_file in all_artifacts.get('design', []):
        if str(design_file) not in linked_paths:
            orphans['design'].append({
                'path': str(design_file),
                'suggestion': f"Add '**Implements**: REQ-*' to {design_file}"
            })

    return orphans
```

---

### 8.3 Dangling Reference Detection

**Algorithm**: Find REQ-* tags that reference non-existent requirements

```python
def detect_dangling_references(
    link_graph: dict,
    requirements: List[dict]
) -> List[dict]:
    """
    Detect REQ-* tags referencing non-existent requirements.

    Returns:
        List of dangling references with locations
    """
    # Build set of valid requirement IDs
    valid_req_ids = {req['id'] for req in requirements}

    dangling = []

    # Check all edges in link graph
    for edge in link_graph['edges']:
        req_id = edge['target']

        if req_id not in valid_req_ids:
            dangling.append({
                'req_id': req_id,
                'source_artifact': edge['source'],
                'link_type': edge['link_type'],
                'line': edge.get('line'),
                'context': edge.get('context'),
                'suggestion': f"Create requirement {req_id} or remove reference"
            })

    return dangling
```

---

### 8.4 Circular Dependency Detection

**Algorithm**: Detect circular dependencies between requirements

```python
def detect_circular_dependencies(requirements: List[dict]) -> List[dict]:
    """
    Detect circular dependencies in requirement graph.

    Returns:
        List of circular dependency chains
    """
    # Build dependency graph
    deps = {}
    for req in requirements:
        req_id = req['id']
        deps[req_id] = req.get('depends_on', [])

    # DFS to detect cycles
    def has_cycle(node, visited, rec_stack, path):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in deps.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor, visited, rec_stack, path):
                    return True
            elif neighbor in rec_stack:
                # Cycle detected
                cycle_start = path.index(neighbor)
                return path[cycle_start:]

        rec_stack.remove(node)
        path.pop()
        return False

    cycles = []
    visited = set()

    for req_id in deps.keys():
        if req_id not in visited:
            rec_stack = set()
            path = []
            cycle = has_cycle(req_id, visited, rec_stack, path)
            if cycle:
                cycles.append({
                    'cycle': cycle,
                    'suggestion': f"Break circular dependency: {' → '.join(cycle)}"
                })

    return cycles
```

---

## 9. Report Generation

### 9.1 Coverage Report

**Template**:
```markdown
# Traceability Coverage Report

**Generated**: {generated_at}
**Total Requirements**: {total_requirements}
**Overall Coverage**: {overall_coverage}%

---

## Summary by Stage

| Stage | Requirements | Covered | Percentage | Status |
|-------|-------------|---------|------------|--------|
| Requirements → Design | {total} | {design_covered} | {design_percentage}% | {design_status} |
| Design → Code | {total} | {code_covered} | {code_percentage}% | {code_status} |
| Code → Tests | {total} | {tests_covered} | {tests_percentage}% | {tests_status} |
| Tests → Runtime | {total} | {runtime_covered} | {runtime_percentage}% | {runtime_status} |

---

## Coverage by Priority

| Priority | Requirements | Covered | Percentage |
|----------|-------------|---------|------------|
| Critical | {critical_total} | {critical_covered} | {critical_percentage}% |
| High | {high_total} | {high_covered} | {high_percentage}% |
| Medium | {medium_total} | {medium_covered} | {medium_percentage}% |
| Low | {low_total} | {low_covered} | {low_percentage}% |

---

## Coverage Gaps

### Requirements Without Design ({no_design_count})

{for req in no_design}
- **{req.id}** ({req.priority}): {req.title}
  - **Action**: Create design document referencing {req.id}
{endfor}

### Requirements Without Code ({no_code_count})

{for req in no_code}
- **{req.id}** ({req.priority}): {req.title}
  - **Action**: Implement {req.id} with '# Implements: {req.id}' tag
{endfor}

### Requirements Without Tests ({no_tests_count})

{for req in no_tests}
- **{req.id}** ({req.priority}): {req.title}
  - **Action**: Add tests with '# Validates: {req.id}' tag
{endfor}

### Requirements Without Runtime Telemetry ({no_runtime_count})

{for req in no_runtime}
- **{req.id}** ({req.priority}): {req.title}
  - **Action**: Add telemetry tags with req="{req.id}"
{endfor}

---

## Recommendations

{if overall_coverage < 0.8}
1. **Priority**: Increase overall coverage to 80% minimum
{endif}

{if critical_percentage < 1.0}
2. **Critical**: {critical_total - critical_covered} critical requirements incomplete
{endif}

{if no_code_count > 0}
3. **Implementation**: {no_code_count} requirements need code
{endif}

{if no_tests_count > 0}
4. **Testing**: {no_tests_count} requirements need tests
{endif}

{if no_runtime_count > no_code_count}
5. **Observability**: Add telemetry tags to {no_runtime_count} requirements
{endif}
```

---

### 9.2 Gap Report

**Template**:
```markdown
# Traceability Gap Report

**Generated**: {generated_at}
**Status**: {overall_status}

---

## Executive Summary

| Gap Type | Count | Severity |
|----------|-------|----------|
| Orphan Requirements | {orphan_req_count} | ERROR |
| Orphan Code | {orphan_code_count} | WARNING |
| Orphan Tests | {orphan_test_count} | WARNING |
| Dangling References | {dangling_count} | ERROR |
| Missing Tests | {missing_tests_count} | ERROR |
| Missing Runtime | {missing_runtime_count} | INFO |

**Total Gaps**: {total_gaps}

---

## Critical Gaps (Must Fix)

### Orphan Requirements ({orphan_req_count})

Requirements with no implementation:

{for req in orphan_requirements}
- **{req.id}** ({req.priority}): {req.title}
  - **Impact**: Feature not delivered
  - **Action**: Implement or remove requirement
{endfor}

### Dangling References ({dangling_count})

REQ-* tags referencing non-existent requirements:

{for ref in dangling_refs}
- **{ref.req_id}** referenced in {ref.source_artifact}:{ref.line}
  - **Context**: `{ref.context}`
  - **Action**: Create requirement or remove reference
{endfor}

### Missing Tests ({missing_tests_count})

Code without test coverage:

{for req in missing_tests}
- **{req.id}**: {req.title}
  - **Code**: {req.code_files}
  - **Action**: Add tests with '# Validates: {req.id}' tag
{endfor}

---

## Warnings (Should Fix)

### Orphan Code ({orphan_code_count})

Code files without REQ-* tags:

{for file in orphan_code}
- {file.path}
  - **Action**: {file.suggestion}
{endfor}

---

## Info (Nice to Have)

### Missing Runtime Telemetry ({missing_runtime_count})

Requirements without telemetry:

{for req in missing_runtime}
- **{req.id}**: {req.title}
  - **Action**: Add logs/metrics with req="{req.id}"
{endfor}

---

## Next Steps

1. **Fix Critical Gaps**: {critical_gap_count} items ({orphan_req_count} + {dangling_count} + {missing_tests_count})
2. **Address Warnings**: {warning_count} items ({orphan_code_count} + {orphan_test_count})
3. **Improve Observability**: {missing_runtime_count} items need telemetry
4. **Re-run Validation**: After fixes, re-validate with `python -m traceability validate`
```

---

### 9.3 Suggested Actions Report

**Template**:
```markdown
# Traceability Suggested Actions

**Generated**: {generated_at}

This report provides actionable suggestions to improve traceability.

---

## Quick Wins (< 1 hour each)

### Add REQ-* Tags to Orphan Code

{for file in orphan_code[:10]}
**File**: {file.path}
**Action**:
```python
# Add at top of file or before relevant function:
# Implements: REQ-F-XXX-001  # TODO: Replace with actual requirement
```
{endfor}

---

## High Priority (Critical Requirements)

### Implement Missing Requirements

{for req in critical_missing}
**Requirement**: {req.id} - {req.title}
**Priority**: {req.priority}
**Actions**:
1. Review requirement definition
2. Create design document
3. Implement with '# Implements: {req.id}' tag
4. Add tests with '# Validates: {req.id}' tag
5. Commit with '{req.id}' in message
{endfor}

---

## Test Coverage

### Add Tests for Untested Code

{for req in missing_tests}
**Requirement**: {req.id} - {req.title}
**Existing Code**: {req.code_files}
**Actions**:
```python
# tests/test_{module}.py

# Validates: {req.id}
def test_{function_name}():
    """Test {req.title}"""
    # Arrange
    ...

    # Act
    result = {function_name}(...)

    # Assert
    assert result == expected
```
{endfor}

---

## Observability

### Add Telemetry Tags

{for req in missing_runtime}
**Requirement**: {req.id} - {req.title}
**Actions**:
```python
# Add structured logging
logger.info(
    "{event_name}",
    extra={{
        "req": "{req.id}",
        # ... other fields
    }}
)

# Add metrics
statsd.increment(
    "{metric_name}",
    tags=["req:{req.id}", "env:production"]
)
```
{endfor}
```

---

## 10. Storage Architecture

### 10.1 File-Based Storage

**Directory Structure**:
```
docs/
└── traceability/
    ├── matrix.json                    # Full traceability matrix
    ├── TRACEABILITY_MATRIX.md         # Human-readable matrix
    ├── link_graph.json                # Link graph (nodes + edges)
    ├── coverage_report.md             # Coverage report
    ├── gap_report.md                  # Gap report
    ├── validation_report.json         # Validation results
    ├── suggested_actions.md           # Actionable suggestions
    └── index/                         # Indexes for fast queries
        ├── by_req.json                # REQ-* → artifacts
        ├── by_artifact.json           # artifact → REQ-*
        ├── by_type.json               # link_type → edges
        └── by_priority.json           # priority → requirements
```

---

### 10.2 Link Graph Schema

**File**: `docs/traceability/link_graph.json`

```json
{
  "metadata": {
    "generated_at": "2025-12-03T14:30:00Z",
    "generator_version": "1.0.0",
    "total_nodes": 258,
    "total_edges": 412
  },

  "nodes": {
    "<REQ-ID>": {
      "type": "requirement",
      "path": "docs/requirements/auth.md",
      "title": "User login with email/password",
      "priority": "critical",
      "created": "2025-12-01"
    },
    "src/auth/login.py:23": {
      "type": "code",
      "path": "src/auth/login.py",
      "line": 23,
      "function": "login",
      "language": "python"
    }
  },

  "edges": [
    {
      "source": "src/auth/login.py:23",
      "target": "<REQ-ID>",
      "link_type": "implements",
      "discovered_by": "regex",
      "discovered_at": "2025-12-03T14:30:00Z",
      "confidence": "high",
      "context": "# Implements: <REQ-ID>"
    }
  ]
}
```

---

### 10.3 Indexes for Fast Queries

#### 10.3.1 by_req.json (REQ → artifacts)

```json
{
  "<REQ-ID>": {
    "design": ["docs/design/auth-service.md"],
    "code": ["src/auth/login.py:23"],
    "tests": ["tests/auth/test_login.py:15", "features/auth.feature:5"],
    "commits": ["abc123", "def456"],
    "runtime": ["api:auth_success"]
  }
}
```

---

#### 10.3.2 by_artifact.json (artifact → REQ)

```json
{
  "src/auth/login.py": {
    "requirements": ["<REQ-ID>", "REQ-NFR-SEC-001"],
    "line_map": {
      "23": ["<REQ-ID>"],
      "45": ["REQ-NFR-SEC-001"]
    }
  }
}
```

---

#### 10.3.3 by_type.json (link_type → edges)

```json
{
  "implements": [
    {"source": "src/auth/login.py:23", "target": "<REQ-ID>"}
  ],
  "validates": [
    {"source": "tests/auth/test_login.py:15", "target": "<REQ-ID>"}
  ]
}
```

---

### 10.4 Update Strategy

**Incremental Updates** (on every commit):
1. Extract links from changed files
2. Update link graph (add/remove edges)
3. Regenerate indexes
4. Update matrix (affected requirements only)

**Full Rebuild** (on demand or weekly):
1. Scan all files
2. Rebuild link graph from scratch
3. Regenerate all indexes
4. Generate all reports

---

## 11. Implementation Guidance

### 11.1 CLI Tool

**Command**: `aisdlc-traceability`

```bash
# Scan and build link graph
aisdlc-traceability scan

# Generate traceability matrix
aisdlc-traceability matrix

# Validate traceability (exit 1 if errors)
aisdlc-traceability validate

# Generate coverage report
aisdlc-traceability coverage

# Generate gap report
aisdlc-traceability gaps

# Trace forward (REQ → artifacts)
aisdlc-traceability trace <REQ-ID>

# Trace backward (artifact → REQ)
aisdlc-traceability trace --file src/auth/login.py

# Query link graph
aisdlc-traceability query --req <REQ-ID>
aisdlc-traceability query --file src/auth/login.py
aisdlc-traceability query --type implements

# CI/CD integration
aisdlc-traceability validate --ci --min-coverage 80
```

---

### 11.2 Python API

```python
from aisdlc_traceability import (
    scan_repository,
    build_link_graph,
    generate_matrix,
    validate_traceability,
    trace_forward,
    trace_backward
)

# Scan repository
artifacts = scan_repository(root_dir='.')

# Build link graph
link_graph = build_link_graph(artifacts)

# Generate matrix
matrix = generate_matrix(link_graph, output_dir='docs/traceability')

# Validate
validation_report = validate_traceability(matrix, link_graph, artifacts)

# Check if validation passed
if validation_report['counts']['error'] > 0:
    print("Validation failed!")
    exit(1)

# Trace forward
trace_forward('<REQ-ID>')
# Output:
# <REQ-ID>: User login
# ├─ Design: docs/design/auth-service.md
# ├─ Code: src/auth/login.py:23
# ├─ Tests: tests/auth/test_login.py:15
# └─ Runtime: api:auth_success

# Trace backward
trace_backward('src/auth/login.py:23')
# Output:
# src/auth/login.py:23 implements:
# ├─ <REQ-ID> → Intent: INT-20251203-001
# └─ REQ-NFR-SEC-001 → Intent: INT-20251203-002
```

---

### 11.3 CI/CD Integration

#### 11.3.1 Pre-commit Hook

**File**: `.git/hooks/pre-commit`

```bash
#!/bin/bash
# Validate traceability before commit

echo "Validating traceability..."

# Run validation (fast mode: only changed files)
aisdlc-traceability validate --fast

if [ $? -ne 0 ]; then
    echo "❌ Traceability validation failed!"
    echo "Run 'aisdlc-traceability gaps' to see issues"
    exit 1
fi

echo "✅ Traceability validation passed"
```

---

#### 11.3.2 GitHub Actions

**File**: `.github/workflows/traceability.yml`

```yaml
name: Traceability Check

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  traceability:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Full history for git log

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install traceability tool
        run: pip install aisdlc-traceability

      - name: Scan repository
        run: aisdlc-traceability scan

      - name: Generate matrix
        run: aisdlc-traceability matrix

      - name: Validate traceability
        run: |
          aisdlc-traceability validate \
            --ci \
            --min-coverage 80 \
            --fail-on error

      - name: Upload reports
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: traceability-reports
          path: docs/traceability/

      - name: Comment on PR
        if: github.event_name == 'pull_request' && failure()
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('docs/traceability/gap_report.md', 'utf8');

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## ❌ Traceability Validation Failed\n\n${report}`
            });
```

---

### 11.4 Claude Code Skill

**File**: `claude-code/.claude-plugin/plugins/aisdlc-methodology/skills/core/validate-traceability/SKILL.md`

```markdown
---
name: validate-traceability
description: Validate full lifecycle traceability from intent to runtime. Detects gaps, orphans, and dangling references.
allowed-tools: [Read, Grep, Glob, Bash]
---

# validate-traceability

**Skill Type**: Sensor/Validator
**Purpose**: Validate traceability and detect coverage gaps
**Prerequisites**: REQ-* keys exist in requirements

---

## Agent Instructions

You validate **full lifecycle traceability** from intent to runtime.

**Your role**:
1. **Scan** - Find all artifacts with REQ-* tags
2. **Build** - Create link graph
3. **Validate** - Check for gaps, orphans, dangling refs
4. **Report** - Generate actionable gap report

---

## Workflow

1. Run traceability scan:
   ```bash
   aisdlc-traceability scan
   ```

2. Generate matrix:
   ```bash
   aisdlc-traceability matrix
   ```

3. Validate:
   ```bash
   aisdlc-traceability validate
   ```

4. If validation fails, show gaps:
   ```bash
   aisdlc-traceability gaps
   ```

5. Provide suggested actions to user.

---

## Output Format

```
[TRACEABILITY VALIDATION]

Status: ❌ FAILED

Errors (12):
  - 6 orphan requirements (no code)
  - 6 missing tests (code without tests)

Warnings (34):
  - 34 orphan code files (no REQ-* tags)

Info (56):
  - 56 requirements without runtime telemetry

See full report: docs/traceability/gap_report.md

Suggested Actions:
1. Implement 6 missing requirements
2. Add tests for 6 requirements
3. Tag 34 code files with REQ-*
```
```

---

## 12. Examples

### 12.1 Complete Traceability Example

**Intent**:
```yaml
# INT-20251203-001
title: "Add user authentication"
description: "Users need to log in with email/password"
```

**Requirement**:
```markdown
## <REQ-ID>: User Login with Email/Password

**Derived From**: INT-20251203-001

**Description**: Users must be able to log in using email and password.

**Acceptance Criteria**:
- AC-001: Login form accepts email and password
- AC-002: Valid credentials return success
- AC-003: Invalid credentials return error
```

**Design**:
```markdown
## Authentication Service

**Implements**: <REQ-ID>, REQ-NFR-SEC-001

The AuthenticationService handles user login and session management.
```

**Code**:
```python
# src/auth/login.py

# Implements: <REQ-ID>
def login(email: str, password: str) -> LoginResult:
    """User login with email and password (AC-001, AC-002, AC-003)"""
    # Implementation...
    pass
```

**Test**:
```python
# tests/auth/test_login.py

# Validates: <REQ-ID> (AC-002)
def test_user_login_with_valid_credentials():
    """Test successful login"""
    result = login("user@example.com", "SecurePass123!")
    assert result.success == True
```

**Commit**:
```
feat: Add user login functionality

Implement user authentication with email/password.

Implements: <REQ-ID>
Validates: AC-001, AC-002, AC-003
```

**Runtime**:
```python
logger.info(
    "User login successful",
    extra={"req": "<REQ-ID>", "user_id": user.id}
)
```

**Traceability Query**:
```bash
$ aisdlc-traceability trace <REQ-ID>

<REQ-ID>: User Login with Email/Password
│
├─ 📋 Intent
│   └─ INT-20251203-001: Add user authentication
│
├─ 🎨 Design
│   └─ docs/design/auth-service.md:42
│
├─ 💻 Implementation
│   └─ src/auth/login.py:23
│
├─ ✅ Tests
│   └─ tests/auth/test_login.py:15
│
├─ 📦 Commits
│   └─ abc123 "feat: Add user login"
│
└─ 🚀 Runtime
    └─ Logs: logger.info("Login", req="<REQ-ID>")

Coverage: ✅ Full traceability (100%)
```

---

### 12.2 Gap Detection Example

**Scenario**: Requirement has code but no tests

**Gap Report**:
```markdown
## Missing Tests (6)

### <REQ-ID> (User Password Reset)

- **Priority**: High
- **Code**: src/auth/reset.py:45
- **Tests**: ❌ None
- **Action**: Add tests with '# Validates: <REQ-ID>' tag

**Suggested test**:
```python
# tests/auth/test_reset.py

# Validates: <REQ-ID>
def test_password_reset_with_valid_token():
    """Test password reset flow"""
    user = create_test_user()
    token = generate_reset_token(user)

    result = reset_password(token, "NewPassword123!")

    assert result.success == True
    assert user.check_password("NewPassword123!")
```
```

---

## ADR References

- **ADR-005**: Iterative Refinement Feedback Loops (bidirectional traceability)
- **ADR-004**: Skills for Reusable Capabilities (traceability as foundation skill)

---

## Implementation Checklist

- [ ] REQ-* key pattern validation (regex)
- [ ] Link discovery engine (regex + AST)
- [ ] Link graph builder
- [ ] Traceability matrix generator
- [ ] Validation engine (10 rules)
- [ ] Gap detection algorithms
- [ ] Report generators (3 types)
- [ ] CLI tool (`aisdlc-traceability`)
- [ ] Python API
- [ ] CI/CD integration (pre-commit + GitHub Actions)
- [ ] Claude Code skill (`validate-traceability`)
- [ ] Documentation + examples

---

**Last Updated**: 2025-12-03
**Owned By**: Design Agent (Traceability System)
