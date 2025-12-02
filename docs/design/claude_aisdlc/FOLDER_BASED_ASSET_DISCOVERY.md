# Folder-Based Asset Discovery

**Requirements Traceability**: REQ-TOOL-002 (Developer Workspace), REQ-TRACE-001 (Full Lifecycle Traceability)

**Unified folder-based approach for all SDLC assets with type tagging**

---

## Problem

Current approach assumes:
- Specific file formats and naming conventions
- Hardcoded asset locations
- Fixed requirement key formats
- Tool-specific integrations (Jira, GitHub, etc.)

This makes the system inflexible and organization-specific.

---

## Solution: Universal Folder-Based Discovery

**Any file in a typed folder = an asset of that type**

```
.ai-workspace/
  ├─ requirements/      # Type: requirement
  ├─ designs/           # Type: design
  ├─ tasks/             # Type: task
  ├─ tests/             # Type: test
  └─ runtime/           # Type: runtime
```

**Skills discover assets dynamically by folder + type**

---

## Asset Type Configuration

### Project Config

```yaml
# config/asset-discovery.yml

asset_types:
  requirement:
    folders:
      - ".ai-workspace/requirements"      # Primary: AI SDLC requirements
      - "docs/requirements"               # Optional: Project's requirements
    file_patterns:
      - "*.md"
      - "*.yml"
      - "*.yaml"
    description: "Business requirements and user stories"

  design:
    folders:
      - ".ai-workspace/designs"           # Primary: AI SDLC designs
      - "docs/design"                     # Optional: Project's design docs
    file_patterns:
      - "*.md"
      - "*.mermaid"
      - "*.plantuml"
      - "*.yml"
    description: "Technical designs and architecture"

  task:
    folders:
      - ".ai-workspace/tasks"             # Primary: AI SDLC task tracking
      - ".jira-sync"                      # Optional: Synced from Jira
    file_patterns:
      - "*.md"
      - "*.yml"
    description: "Work items and tickets"

  code:
    folders:
      - "src"                             # Project source code
      - "lib"
    file_patterns:
      - "*.py"
      - "*.js"
      - "*.ts"
      - "*.java"
    description: "Implementation code"

  test:
    folders:
      - "tests"                           # Project tests
      - ".ai-workspace/tests"             # AI SDLC test plans
    file_patterns:
      - "test_*.py"
      - "*.test.js"
      - "*.spec.ts"
      - "*.feature"                       # BDD scenarios
    description: "Test files and scenarios"

  runtime:
    folders:
      - ".ai-workspace/runtime"           # Primary: AI SDLC monitoring
      - "monitoring"                      # Optional: Project's monitoring
    file_patterns:
      - "*.yml"
      - "*.json"
    description: "Production configs, dashboards, alerts"
```

---

## Universal Folder Structure

```
project-root/                       # Your project
  │
  ├─ docs/                          # Project's documentation
  ├─ requirements/                  # Project's requirements (optional)
  ├─ src/                           # Source code
  │   └─ auth_service.py
  ├─ tests/                         # Project's tests
  │   └─ test_auth.py
  │
  └─ .ai-workspace/                 # Hidden AI SDLC folder (self-contained)
      │
      ├─ requirements/              # 📋 AI SDLC requirements
      │   ├─ functional/
      │   │   ├─ user-login.md
      │   │   └─ password-reset.md
      │   ├─ non-functional/
      │   │   ├─ performance.yml
      │   │   └─ security.yml
      │   └─ business-rules/
      │       ├─ email-validation.md
      │       └─ password-policy.md
      │
      ├─ designs/                   # 🎨 AI SDLC designs
      │   ├─ auth-architecture.md
      │   ├─ component-diagram.mermaid
      │   └─ api-spec.yml
      │
      ├─ tasks/                     # 📦 AI SDLC task tracking
      │   ├─ active/
      │   │   ├─ implement-login.md
      │   │   └─ PROJ-123.md        # Jira sync
      │   └─ completed/
      │       └─ deploy-auth.md
      │
      ├─ tests/                     # 🧪 AI SDLC test plans
      │   ├─ scenarios/
      │   │   └─ login.feature      # BDD scenarios
      │   └─ test-plans/
      │       └─ auth-test-plan.md
      │
      ├─ runtime/                   # 📈 AI SDLC runtime monitoring
      │   ├─ dashboards/
      │   │   └─ auth-metrics.json
      │   └─ alerts/
      │       └─ auth-sla.yml
      │
      └─ traceability/              # 🔗 Auto-generated mappings
          └─ asset-graph.yml
```

**Key Points**:
- `.ai-workspace/` is **hidden** (dot prefix) - won't clutter directory listings
- **Self-contained** - all AI SDLC artifacts in one place
- **Non-intrusive** - project keeps its own structure (docs/, src/, tests/, etc.)
- **Separate concerns** - project files vs AI SDLC methodology files

---

## Asset Discovery Pattern

### Discovery Script

```bash
# discover_assets.sh

ASSET_TYPE=$1  # e.g., "requirement", "design", "task"

# Read config
FOLDERS=$(yq eval ".asset_types.${ASSET_TYPE}.folders[]" config/asset-discovery.yml)
PATTERNS=$(yq eval ".asset_types.${ASSET_TYPE}.file_patterns[]" config/asset-discovery.yml)

# Discover all assets of this type
for folder in $FOLDERS; do
  if [ -d "$folder" ]; then
    for pattern in $PATTERNS; do
      find "$folder" -name "$pattern" -type f
    done
  fi
done
```

### Usage in Skills

```bash
# In design-with-traceability/SKILL.md

## Step 1: Discover Requirements

```bash
# Discover all requirement assets
requirements=$(./discover_assets.sh requirement)

echo "Found requirements:"
for req in $requirements; do
  echo "  - $req"
done
```

Output:
  Found requirements:
    - .ai-workspace/requirements/functional/user-login.md
    - .ai-workspace/requirements/non-functional/performance.yml
    - docs/requirements/auth-spec.md
```

---

## Cross-Asset Referencing

### Reference by Path (Relative to Repo Root)

```python
# src/auth_service.py

# Implements: .ai-workspace/requirements/functional/user-login.md
# Design: .ai-workspace/designs/auth-architecture.md
# Task: .ai-workspace/tasks/active/implement-login.md

def login(email: str, password: str) -> LoginResult:
    """User login with email and password."""
    ...
```

### Design References Requirements

```markdown
# .ai-workspace/designs/auth-architecture.md

# Authentication Architecture

**Implements**:
- .ai-workspace/requirements/functional/user-login.md
- .ai-workspace/requirements/functional/password-reset.md

**References**:
- .ai-workspace/requirements/non-functional/security.yml
- .ai-workspace/requirements/business-rules/password-policy.md

## Components

### AuthenticationService
Implements: .ai-workspace/requirements/functional/user-login.md
...
```

### Task References Design and Requirements

```markdown
# .ai-workspace/tasks/active/implement-login.md

# Task: Implement User Login

**Type**: Development
**Status**: In Progress
**Assignee**: @developer

**Implements**:
- .ai-workspace/requirements/functional/user-login.md

**Design**:
- .ai-workspace/designs/auth-architecture.md

**Tests**:
- tests/test_auth.py
- .ai-workspace/tests/scenarios/login.feature
```

---

## Traceability Graph

### Auto-Generated Asset Graph

```yaml
# .ai-workspace/traceability/asset-graph.yml

assets:
  .ai-workspace/requirements/functional/user-login.md:
    type: requirement
    title: "User Login Feature"
    downstream:
      - .ai-workspace/designs/auth-architecture.md
      - .ai-workspace/tasks/active/implement-login.md
      - src/auth_service.py
      - tests/test_auth.py
      - .ai-workspace/tests/scenarios/login.feature
      - .ai-workspace/runtime/dashboards/auth-metrics.json

  .ai-workspace/designs/auth-architecture.md:
    type: design
    title: "Authentication Architecture"
    upstream:
      - .ai-workspace/requirements/functional/user-login.md
      - .ai-workspace/requirements/functional/password-reset.md
    downstream:
      - .ai-workspace/tasks/active/implement-login.md
      - src/auth_service.py

  .ai-workspace/tasks/active/implement-login.md:
    type: task
    title: "Implement User Login"
    upstream:
      - .ai-workspace/requirements/functional/user-login.md
      - .ai-workspace/designs/auth-architecture.md
    downstream:
      - src/auth_service.py
      - tests/test_auth.py

  src/auth_service.py:
    type: code
    title: "AuthenticationService"
    upstream:
      - .ai-workspace/requirements/functional/user-login.md
      - .ai-workspace/designs/auth-architecture.md
      - .ai-workspace/tasks/active/implement-login.md
    downstream:
      - tests/test_auth.py

  tests/test_auth.py:
    type: test
    title: "Authentication Tests"
    upstream:
      - .ai-workspace/requirements/functional/user-login.md
      - src/auth_service.py
    validates:
      - .ai-workspace/requirements/functional/user-login.md

  .ai-workspace/runtime/dashboards/auth-metrics.json:
    type: runtime
    title: "Auth Metrics Dashboard"
    upstream:
      - .ai-workspace/requirements/functional/user-login.md
      - src/auth_service.py
    monitors:
      - .ai-workspace/requirements/non-functional/performance.yml
```

---

## Multiple Folder Support

### Why Multiple Folders?

Organizations have assets in different locations:

```yaml
asset_types:
  requirement:
    folders:
      - ".ai-workspace/requirements"    # Primary: AI SDLC requirements
      - "docs/requirements"             # Optional: Project's requirements
      - ".jira-sync/requirements"       # Optional: Synced from Jira

  design:
    folders:
      - ".ai-workspace/designs"         # Primary: AI SDLC designs
      - "docs/design"                   # Optional: Project's design docs
      - "docs/architecture"             # Optional: ADRs

  task:
    folders:
      - ".ai-workspace/tasks"           # Primary: AI SDLC task tracking
      - ".jira-sync/tasks"              # Optional: Jira tickets
      - ".github-sync/projects"         # Optional: GitHub Projects (synced)
```

Skills discover from ALL configured folders.

---

## URI Support

### Beyond Local Files

```yaml
asset_types:
  requirement:
    folders:
      - ".ai-workspace/requirements"
    uris:
      - "jira://PROJ/issues"           # Jira API
      - "github://org/repo/issues"     # GitHub API
      - "confluence://space/pages"     # Confluence

  design:
    folders:
      - ".ai-workspace/designs"
    uris:
      - "figma://file/123"             # Figma designs
      - "miro://board/456"             # Miro boards

  runtime:
    folders:
      - ".ai-workspace/runtime"
    uris:
      - "datadog://dashboard/789"      # Datadog dashboards
      - "grafana://dashboard/101"      # Grafana dashboards
```

### URI Resolution

```python
# discover_assets.py

def discover_assets(asset_type: str) -> List[Asset]:
    """Discover assets by type from folders and URIs."""
    assets = []

    # 1. Discover from local folders
    folders = config.get_folders(asset_type)
    for folder in folders:
        assets.extend(scan_folder(folder))

    # 2. Discover from URIs (optional integrations)
    uris = config.get_uris(asset_type)
    for uri in uris:
        if uri.startswith("jira://"):
            assets.extend(fetch_jira_issues(uri))
        elif uri.startswith("github://"):
            assets.extend(fetch_github_issues(uri))

    return assets
```

---

## Benefits

### 1. Format Agnostic
- Use ANY naming convention
- Use ANY file format
- No hardcoded assumptions

### 2. Tool Agnostic
- Not tied to Jira, GitHub, Azure
- Works offline (local folders)
- Optional integrations via URIs

### 3. Discovery-Based
- Skills automatically find assets
- Add new assets → automatically discovered
- No manual registration needed

### 4. Organization Flexible
- Configure folders per organization
- Support multiple locations
- Migrate between systems easily

### 5. Traceability Maintained
- Reference by path (stable)
- Auto-generate graph
- Works with git history

### 6. Extensible
- Add new asset types easily
- Support custom URIs
- Plugin architecture for integrations

---

## Migration Examples

### Example 1: Jira Shop

```yaml
# config/asset-discovery.yml

asset_types:
  requirement:
    folders:
      - ".jira-sync/requirements"     # Synced from Jira
    file_patterns:
      - "*.md"

# Sync script
./scripts/sync-jira --project PROJ --output .jira-sync/requirements/

# Result
.jira-sync/requirements/
  ├─ PROJ-123.md
  ├─ PROJ-124.md
  └─ PROJ-125.md
```

**Skills work immediately** - reference by path:
- `Implements: .jira-sync/requirements/PROJ-123.md`

### Example 2: GitHub Shop

```yaml
asset_types:
  requirement:
    folders:
      - ".github-sync/issues"

# Sync script
./scripts/sync-github --repo org/repo --output .github-sync/issues/

# Result
.github-sync/issues/
  ├─ issue-42.md
  ├─ issue-43.md
  └─ issue-44.md
```

**Skills work immediately**:
- `Implements: .github-sync/issues/issue-42.md`

### Example 3: Mixed Environment

```yaml
asset_types:
  requirement:
    folders:
      - ".ai-workspace/requirements"  # AI-generated
      - "docs/requirements"           # Human documentation
      - ".jira-sync/epics"            # Jira epics
      - ".github-sync/issues"         # GitHub issues
```

**Skills discover from ALL locations** - maximum flexibility!

---

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Folder structure | ✅ Complete | .ai-workspace/*/  |
| Config schema | ✅ Complete | asset_types config |
| Discovery script | ⏳ Planned | discover_assets.sh |
| Skill updates | 🟡 In Progress | Updating key skills |
| Traceability graph | ⏳ Planned | Auto-generate |
| URI support | ⏳ Planned | jira://, github://, etc. |
| Jira sync | ⏳ Planned | ./scripts/sync-jira |
| GitHub sync | ⏳ Planned | ./scripts/sync-github |

---

## Summary

**Old Way (Hardcoded)**:
```python
# Implements: REQ-F-DEMO-AUTH-001
```
❌ Assumes specific format
❌ Not flexible
❌ Tool-specific

**New Way (Folder-Based + Typed)**:
```python
# Implements: .ai-workspace/requirements/functional/user-login.md
```
✅ Discovered from typed folders
✅ Works with any naming convention
✅ Organization agnostic
✅ Tool agnostic
✅ Supports multiple locations
✅ Optional URI integrations

---

**"Excellence or nothing"** 🔥
