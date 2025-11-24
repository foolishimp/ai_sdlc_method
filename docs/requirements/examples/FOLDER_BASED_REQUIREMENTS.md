# Folder-Based Requirements Pattern

**Flexible requirement management without hardcoded key formats**

---

## Problem

Current skills hardcode requirement formats:
- `REQ-F-AUTH-001` (assumes this specific structure)
- `BR-001`, `C-001`, `F-001` (assumes business rules format)
- Organization-specific conventions baked into examples

**This is inflexible** - different organizations use different formats:
- Jira: `PROJ-123`, `US-456`
- Azure DevOps: `#12345`, `PBI-789`
- GitHub: `#42`, `ISSUE-001`
- Custom: `feature-login.md`, `requirement_001.yml`

---

## Solution: Folder-Based Discovery

**Any file in a requirements folder = a requirement**

```
.ai-workspace/requirements/
  ├─ user-login.md
  ├─ password-reset.md
  ├─ performance-nfr.yml
  ├─ JIRA-123.md
  ├─ US-456.md
  └─ auth-business-rules.md
```

**Skills discover requirements dynamically:**

```bash
# Instead of hardcoded "REQ-F-AUTH-001"
requirements=$(find .ai-workspace/requirements/ -type f)

# Work with whatever's there
for req in $requirements; do
  process_requirement "$req"
done
```

---

## Folder Structure

```
project-root/                     # Your project
  │
  ├─ docs/                        # Project's documentation
  ├─ src/                         # Source code
  ├─ tests/                       # Tests
  │
  └─ .ai-workspace/               # Hidden AI SDLC folder (self-contained)
      │
      ├─ requirements/            # 📁 Requirement files (any format, any naming)
      │   ├─ functional/          # Optional: organize by type
      │   │   ├─ user-login.md
      │   │   └─ user-registration.md
      │   ├─ non-functional/
      │   │   ├─ performance.yml
      │   │   └─ security.md
      │   └─ business-rules/
      │       ├─ email-validation.md
      │       └─ password-policy.md
      │
      ├─ designs/                 # Design artifacts
      │   └─ auth-architecture.md
      │       # References: .ai-workspace/requirements/functional/user-login.md
      │
      ├─ tasks/                   # Work items
      │   └─ active/
      │       └─ implement-login.md
      │           # Implements: .ai-workspace/requirements/functional/user-login.md
      │
      └─ traceability/            # Auto-generated mappings
          └─ requirement-to-code.yml
              # Maps requirement files → design → tasks → code
```

**Key Points**:
- `.ai-workspace/` is **hidden** (dot prefix)
- **Self-contained** - all AI SDLC artifacts
- **Non-intrusive** - doesn't pollute project structure
- Project can have its own `docs/`, `requirements/`, etc.

---

## Requirement File Formats

**Format agnostic** - use whatever works for your organization:

### Option 1: Markdown (Simple)

```markdown
# requirements/functional/user-login.md

## User Login Feature

**User Story**: As a registered user, I want to log in with email and password.

**Acceptance Criteria**:
- Email format validation
- Password minimum 12 characters
- Login response < 500ms
- Max 3 failed attempts before lockout

**Priority**: P0 (Critical)
```

### Option 2: YAML (Structured)

```yaml
# requirements/non-functional/performance.yml

id: perf-001
title: "Authentication Performance Requirements"
type: non-functional
category: performance

requirements:
  - metric: login_response_time
    target: "<500ms"
    p95: true

  - metric: registration_response_time
    target: "<1000ms"
    p95: true

priority: high
```

### Option 3: Jira-Style (Ticket-Based)

```markdown
# requirements/PROJ-123.md

**Type**: User Story
**Status**: Ready for Development
**Points**: 8

## Description
As a registered user, I want to log in with email/password.

## Acceptance Criteria
- [ ] Email validation
- [ ] Password hashing (bcrypt)
- [ ] Session management (JWT)
```

### Option 4: With Metadata (Optional)

```markdown
# requirements/functional/user-login.md

---
id: REQ-F-AUTH-001           # Optional: structured ID if you want
type: functional
domain: authentication
priority: P0
created: 2025-01-15
updated: 2025-01-20
owner: product@acme.com
---

# User Login

User story content...
```

**Skills read the metadata IF present, but don't require it**

---

## Referencing Requirements

### In Code

```python
# auth_service.py

# Implements: requirements/functional/user-login.md
def login(email: str, password: str) -> LoginResult:
    """
    User login with email and password.

    References:
    - requirements/functional/user-login.md
    - requirements/non-functional/performance.yml (login_response_time)
    - requirements/business-rules/email-validation.md
    """
    ...
```

### In Design Documents

```markdown
# design/auth-architecture.md

# Authentication Architecture

**Implements**:
- requirements/functional/user-login.md
- requirements/functional/password-reset.md
- requirements/non-functional/security.yml

## Components

### AuthenticationService
**References**: requirements/functional/user-login.md

Methods:
- `login(email, password)` → LoginResult
  Implements: requirements/functional/user-login.md
```

### In Tests

```python
# tests/test_auth.py

def test_user_login_with_valid_credentials():
    """
    Validates: requirements/functional/user-login.md
    Acceptance criteria: Email validation, password check
    """
    result = login("user@example.com", "SecurePass123!")
    assert result.success == True
```

### In Commits

```bash
git commit -m "Implement user login

Implements: requirements/functional/user-login.md

- Add login() method to AuthenticationService
- Email validation (requirements/business-rules/email-validation.md)
- Password hashing with bcrypt
- JWT session creation

Tests: test_auth.py
Coverage: 100%"
```

---

## Skill Updates

### Before (Hardcoded)

```markdown
# design-with-traceability/SKILL.md

Requirements:
- REQ-F-AUTH-001: User login
- REQ-F-AUTH-002: Password reset
- REQ-NFR-PERF-001: Login < 500ms

Component: AuthenticationService
Implements: REQ-F-AUTH-001, REQ-F-AUTH-002
```

### After (Folder-Based)

```markdown
# design-with-traceability/SKILL.md

## Step 1: Discover Requirements

```bash
# Read all requirement files
REQUIREMENTS_DIR="${REQUIREMENTS_DIR:-.ai-workspace/requirements}"
requirements=$(find "$REQUIREMENTS_DIR" -type f -name "*.md" -o -name "*.yml")
```

## Step 2: Design Components

For each requirement file:
- Read content
- Extract title (from filename or metadata)
- Tag design artifacts with file path

```yaml
Component: AuthenticationService
Implements:
  - requirements/functional/user-login.md
  - requirements/functional/password-reset.md

References:
  - requirements/non-functional/performance.yml
  - requirements/business-rules/email-validation.md
```

---

## Configuration

### Project-Level Config

```yaml
# config/config.yml

ai_sdlc:
  requirements:
    # Where to find requirements
    directories:
      - ".ai-workspace/requirements"
      - "docs/requirements"           # Optional: additional locations

    # What files to consider
    file_patterns:
      - "*.md"
      - "*.yml"
      - "*.yaml"
      - "*.txt"

    # Optional: metadata format (if files have frontmatter)
    metadata_format: "yaml_frontmatter"  # or "none"

    # How to extract IDs (if not using filenames)
    id_extraction:
      - "metadata.id"         # Try YAML frontmatter first
      - "filename"            # Fall back to filename
```

### Global Config

```yaml
# ~/.config/ai_sdlc_method/config.yml

# Default requirements location for all projects
requirements:
  default_directory: ".ai-workspace/requirements"

# Organization-specific patterns
organization:
  name: "Acme Corp"

  # If you want structured IDs (optional)
  requirement_id_format: "REQ-{TYPE}-{DOMAIN}-{SEQ:03d}"

  # But skills will work WITHOUT this - just use filenames
```

---

## Traceability

### Auto-Generated Mapping

```yaml
# .ai-workspace/traceability/requirement-to-artifact.yml

traceability:
  requirements/functional/user-login.md:
    design:
      - design/auth-architecture.md (AuthenticationService)
    tasks:
      - tasks/active/PROJ-123-implement-login.md
    code:
      - src/auth_service.py (login method, line 42)
    tests:
      - tests/test_auth.py (test_user_login_with_valid_credentials, line 15)
    commits:
      - abc123de (feat: Implement user login)

  requirements/non-functional/performance.yml:
    code:
      - src/auth_service.py (performance monitoring)
    tests:
      - tests/test_performance.py (test_login_performance)
    runtime:
      - monitoring/datadog-dashboard.json (login_latency metric)
```

### Traceability Query

```bash
# Find all artifacts for a requirement
./scripts/trace requirements/functional/user-login.md

Output:
  Requirements: requirements/functional/user-login.md
  ├─ Design: design/auth-architecture.md (AuthenticationService)
  ├─ Tasks: tasks/active/PROJ-123-implement-login.md
  ├─ Code: src/auth_service.py:42 (login method)
  ├─ Tests: tests/test_auth.py:15 (test_user_login)
  └─ Runtime: datadog (login_latency metric)
```

---

## Migration Path

### For Existing Projects with Structured Keys

If you already have `REQ-F-AUTH-001` style keys:

```markdown
# requirements/REQ-F-AUTH-001.md

# REQ-F-AUTH-001: User Login

(content)
```

**Skills work the same way** - just reference the filename:
- `Implements: requirements/REQ-F-AUTH-001.md`

### For Jira/Azure DevOps Integration

```bash
# Sync Jira tickets to requirements folder
./scripts/sync-jira --project PROJ --output .ai-workspace/requirements/

Result:
  .ai-workspace/requirements/
    ├─ PROJ-123.md
    ├─ PROJ-124.md
    └─ PROJ-125.md
```

Skills automatically discover and reference these:
- `Implements: requirements/PROJ-123.md`

---

## Benefits

1. **Format Agnostic**
   - Use ANY naming convention
   - Use ANY file format (.md, .yml, .txt)
   - No hardcoded assumptions

2. **Organization Flexible**
   - Jira shop? Use `PROJ-123.md`
   - GitHub shop? Use `#42.md` or `issue-42.md`
   - Custom? Use `user-login-feature.md`

3. **Discovery-Based**
   - Skills just read what's in the folder
   - No configuration needed (defaults work)
   - Add new requirements → automatically discovered

4. **Traceability Maintained**
   - Reference by file path (relative to repo root)
   - Stable across renames (update references)
   - Works with git history

5. **Tool Agnostic**
   - Not tied to Jira, Azure, GitHub
   - Works offline
   - Plain text = version control friendly

---

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Folder structure | ✅ Complete | .ai-workspace/requirements/ |
| Config schema | ✅ Complete | requirements.directories |
| Skill updates | 🟡 In Progress | Updating key skills |
| Traceability tool | ⏳ Planned | Auto-generate mappings |
| Jira sync | ⏳ Planned | Optional integration |

---

## Examples

### Example 1: Startup (No Process)

```
.ai-workspace/requirements/
  ├─ login.md
  ├─ signup.md
  └─ payments.md
```

**Reference**: `Implements: .ai-workspace/requirements/login.md`

### Example 2: Enterprise (Jira)

```
.ai-workspace/requirements/
  ├─ PORTAL-123.md
  ├─ PORTAL-124.md
  └─ PORTAL-125.md
```

**Reference**: `Implements: .ai-workspace/requirements/PORTAL-123.md`

### Example 3: Structured Organization

```
.ai-workspace/requirements/
  ├─ functional/
  │   ├─ REQ-F-AUTH-001.md
  │   └─ REQ-F-AUTH-002.md
  ├─ non-functional/
  │   └─ REQ-NFR-PERF-001.yml
  └─ business-rules/
      └─ BR-001-email-validation.md
```

**Reference**: `Implements: .ai-workspace/requirements/functional/REQ-F-AUTH-001.md`

---

## Summary

**Old Way (Hardcoded)**:
```python
# Implements: REQ-F-AUTH-001
```
❌ Assumes specific format
❌ Not flexible

**New Way (Folder-Based)**:
```python
# Implements: .ai-workspace/requirements/functional/user-login.md
```
✅ Works with any naming convention
✅ Discovered automatically
✅ Organization agnostic
✅ Hidden folder (non-intrusive)

---

**"Excellence or nothing"** 🔥
