---
name: design-with-traceability
description: Complete design workflow - Component design, ADRs, API specs, data models with full requirement traceability. Consolidates create-adrs, design-with-traceability, validate-design-coverage.
allowed-tools: [Read, Write, Edit, Grep, Glob]
---

# Design with Traceability

**Skill Type**: Complete Workflow (Design Stage)
**Purpose**: Transform requirements into technical design with full traceability
**Consolidates**: create-adrs, design-with-traceability, validate-design-coverage

---

## When to Use This Skill

Use this skill when:
- Requirements are validated and ready for design
- Creating component architecture
- Making architecture decisions (ADRs)
- Designing APIs, data models, or interfaces
- Need design-to-requirement traceability

---

## Complete Workflow

### Phase 1: Design Analysis

**Goal**: Understand requirements and identify design decisions.

**For each requirement, determine**:
- What components are needed?
- What APIs are required?
- What data models are needed?
- What are the architectural options?

**Example**:
```yaml
REQ-F-AUTH-001: User Login

Components Needed:
  - AuthenticationService (new)
  - UserRepository (existing - extend)
  - SessionManager (new)

APIs Required:
  - POST /api/v1/auth/login
  - POST /api/v1/auth/logout
  - GET /api/v1/auth/session

Data Models:
  - User (extend with login_attempts, locked_until)
  - Session (new)
  - AuditLog (new)

Architectural Decisions:
  - Session storage: JWT vs Redis
  - Password hashing: bcrypt vs argon2
```

---

### Phase 2: Architecture Decision Records (ADRs)

**Goal**: Document significant design decisions with rationale.

**ADR Template**:

```markdown
# ADR-001: Session Storage Strategy

**Status**: Accepted
**Date**: 2025-12-03
**Requirements**: REQ-F-AUTH-001, REQ-NFR-PERF-001

## Context

We need to store user sessions for authentication.
Requirements:
- Session timeout after 30 minutes (BR-004)
- Support 10,000+ concurrent users (C-004)
- Response time < 500ms (C-001)

## Options Considered

### Option 1: JWT (Stateless)
Pros:
- No server-side storage
- Horizontally scalable
- Self-contained

Cons:
- Cannot revoke individual sessions
- Token size grows with claims

### Option 2: Redis (Stateful)
Pros:
- Can revoke sessions
- Fast lookup
- TTL support built-in

Cons:
- Additional infrastructure
- Single point of failure (if not clustered)

### Option 3: Database Sessions
Pros:
- Simple implementation
- Uses existing infrastructure

Cons:
- Slower than Redis
- Database load

## Decision

**Selected: Option 1 (JWT) with Redis blacklist for revocation**

Rationale:
- JWT for scalability and performance
- Redis blacklist for logout/revocation
- Best of both worlds

## Consequences

- Need JWT library (jose)
- Need Redis for blacklist only
- Token refresh strategy needed

## Traceability

Implements:
- REQ-F-AUTH-001: User login
- REQ-NFR-PERF-001: Response < 500ms

Business Rules:
- BR-004: 30-minute session timeout (JWT exp claim)

Constraints:
- C-001: Response < 500ms (JWT decode is ~1ms)
- C-004: 10,000+ concurrent users (stateless = infinite scale)
```

---

### Phase 3: Component Design

**Goal**: Define component structure with requirement mapping.

**Component Design Template**:

```markdown
# AuthenticationService

**Type**: Domain Service
**Layer**: Application Layer
**Requirements**: REQ-F-AUTH-001, REQ-F-AUTH-002

## Responsibilities

1. Authenticate users with credentials
2. Manage session lifecycle
3. Enforce login policies (lockout, etc.)

## Interface

```python
class AuthenticationService:
    """Authentication service for user login/logout.

    Implements: REQ-F-AUTH-001, REQ-F-AUTH-002
    """

    def login(self, email: str, password: str) -> LoginResult:
        """Authenticate user with email and password.

        Implements: REQ-F-AUTH-001
        Business Rules: BR-001, BR-002, BR-003
        Constraints: C-001 (< 500ms)

        Args:
            email: User's email address
            password: User's password

        Returns:
            LoginResult with success status, user, and token

        Raises:
            AccountLockedException: If account locked (BR-003)
            InvalidCredentialsException: If credentials invalid
        """
        pass

    def logout(self, token: str) -> None:
        """Invalidate user session.

        Implements: REQ-F-AUTH-001
        """
        pass

    def reset_password(self, email: str) -> None:
        """Initiate password reset flow.

        Implements: REQ-F-AUTH-002
        Business Rules: BR-005, BR-006
        """
        pass
```

## Dependencies

- UserRepository: User data access
- PasswordHasher: Password verification
- TokenService: JWT generation
- CacheService: Blacklist storage

## Sequence Diagram

```
User -> API: POST /login {email, password}
API -> AuthService: login(email, password)
AuthService -> UserRepo: get_by_email(email)
AuthService -> PasswordHasher: verify(password, hash)
AuthService -> TokenService: generate_token(user)
AuthService -> API: LoginResult(success, token)
API -> User: 200 OK {token}
```

## Traceability

| Method | Requirement | Business Rules | Constraints |
|--------|-------------|----------------|-------------|
| login() | REQ-F-AUTH-001 | BR-001, BR-002, BR-003 | C-001 |
| logout() | REQ-F-AUTH-001 | - | - |
| reset_password() | REQ-F-AUTH-002 | BR-005, BR-006 | - |
```

---

### Phase 4: API Design

**Goal**: Define API contracts with requirement mapping.

**OpenAPI Template**:

```yaml
# api/v1/auth.yaml

openapi: 3.0.0
info:
  title: Authentication API
  version: 1.0.0
  description: |
    Authentication endpoints for user login/logout.

    Implements:
    - REQ-F-AUTH-001: User login
    - REQ-F-AUTH-002: Password reset

paths:
  /api/v1/auth/login:
    post:
      summary: User login
      description: |
        Authenticate user with email and password.

        Implements: REQ-F-AUTH-001
        Business Rules: BR-001, BR-002, BR-003
        Constraints: C-001 (response < 500ms)
      tags:
        - Authentication
      x-requirements:
        - REQ-F-AUTH-001
      x-business-rules:
        - BR-001
        - BR-002
        - BR-003
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LoginRequest'
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LoginResponse'
        '401':
          description: Invalid credentials
        '423':
          description: Account locked (BR-003)

components:
  schemas:
    LoginRequest:
      type: object
      required:
        - email
        - password
      properties:
        email:
          type: string
          format: email
          description: User email (BR-001 validation)
        password:
          type: string
          minLength: 12
          description: User password (BR-002 min length)

    LoginResponse:
      type: object
      properties:
        token:
          type: string
          description: JWT access token
        expires_at:
          type: string
          format: date-time
          description: Token expiration (BR-004)
```

---

### Phase 5: Data Model Design

**Goal**: Define data structures with requirement mapping.

```markdown
# Data Models

## User

**Implements**: REQ-F-AUTH-001, REQ-F-PORTAL-002

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,  -- BR-001: validated format
    password_hash VARCHAR(255) NOT NULL,  -- C-003: bcrypt hash
    login_attempts INT DEFAULT 0,         -- BR-003: lockout counter
    locked_until TIMESTAMP NULL,          -- BR-003: lockout time
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for login lookup (C-001: < 500ms)
CREATE INDEX idx_users_email ON users(email);
```

## Session (if using stateful sessions)

**Implements**: REQ-F-AUTH-001

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    token VARCHAR(500) NOT NULL,
    expires_at TIMESTAMP NOT NULL,  -- BR-004: 30 min timeout
    created_at TIMESTAMP DEFAULT NOW()
);

-- TTL cleanup (BR-004)
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
```
```

---

### Phase 6: Design Coverage Validation

**Goal**: Ensure all requirements have design coverage.

**Validation Report**:

```
[DESIGN COVERAGE VALIDATION]

Requirements Analyzed: 8

Design Coverage:
  REQ-F-AUTH-001: ✅ AuthService, POST /login, User model
  REQ-F-AUTH-002: ✅ AuthService, POST /reset-password
  REQ-F-PORTAL-001: ⏳ Pending design
  REQ-F-PORTAL-002: ⏳ Pending design
  REQ-F-PORTAL-003: ⏳ Pending design
  REQ-NFR-PERF-001: ✅ Covered in ADR-001, API constraints
  REQ-NFR-SEC-001: ✅ Covered in ADR-002
  REQ-DATA-VAL-001: ✅ Covered in API schema

Coverage: 5/8 (63%)

ADRs Created: 2
  - ADR-001: Session Storage Strategy
  - ADR-002: Password Hashing Strategy

Components Designed: 3
  - AuthenticationService
  - UserRepository
  - SessionManager

APIs Designed: 4
  - POST /api/v1/auth/login
  - POST /api/v1/auth/logout
  - POST /api/v1/auth/reset-password
  - GET /api/v1/auth/session

Remaining:
  - REQ-F-PORTAL-001: Need BalanceService design
  - REQ-F-PORTAL-002: Need ProfileService design
  - REQ-F-PORTAL-003: Need DocumentService design
```

---

## Output Format

```
[DESIGN STAGE - INT-042]

Requirements Covered: 5/8

ADRs Created:
  ADR-001: Session Storage Strategy (REQ-F-AUTH-001)
  ADR-002: Password Hashing Strategy (REQ-NFR-SEC-001)

Components Designed:
  AuthenticationService → REQ-F-AUTH-001, REQ-F-AUTH-002
  UserRepository → REQ-F-AUTH-001
  SessionManager → REQ-F-AUTH-001

APIs Designed:
  POST /api/v1/auth/login → REQ-F-AUTH-001
  POST /api/v1/auth/logout → REQ-F-AUTH-001
  POST /api/v1/auth/reset-password → REQ-F-AUTH-002

Data Models:
  User (extended) → REQ-F-AUTH-001, REQ-F-PORTAL-002
  Session → REQ-F-AUTH-001

Files Created:
  + docs/design/adrs/ADR-001-session-storage.md
  + docs/design/adrs/ADR-002-password-hashing.md
  + docs/design/components/authentication-service.md
  + api/v1/auth.yaml

Traceability: All designs linked to REQ-* keys

Design Stage Complete (Partial)!
  Next: Design remaining 3 requirements
```

---

## Configuration

```yaml
# .claude/plugins.yml
plugins:
  - name: "@aisdlc/aisdlc-methodology"
    config:
      design:
        require_adrs_for_decisions: true
        require_api_specs: true
        require_traceability: true
        min_coverage_to_proceed: 80
        adr_template: "docs/templates/adr-template.md"
```

---

## Homeostasis Behavior

**If design missing traceability**:
- Detect: Component/API without REQ-* link
- Signal: "Design needs requirement mapping"
- Action: Add Implements/Requirements sections

**If coverage too low**:
- Detect: < 80% requirements have design
- Signal: "Design coverage insufficient"
- Action: List uncovered requirements
- Block: Do not proceed to Tasks until coverage met

---

## Next Steps

After design complete:
1. **Tasks**: Break design into work units
2. **Code**: Implement using TDD workflow
3. **Update**: Traceability matrix

**"Excellence or nothing"**
