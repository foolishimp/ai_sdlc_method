# AI SDLC: User Experience Design

**Complete System Design: Agents, Skills, Marketplace**

**Status**: Design Exploration (Pre-Implementation)
**Date**: 2025-11-20
**Version**: 3.0.0
**Purpose**: Explore user experience before implementation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [User Personas](#user-personas)
3. [User Journeys](#user-journeys)
4. [Marketplace Experience](#marketplace-experience)
5. [Skills Experience](#skills-experience)
6. [Agent Experience](#agent-experience)
7. [Homeostasis Experience](#homeostasis-experience)
8. [Requirements Refinement Loop](#requirements-refinement-loop)
9. [Team Onboarding](#team-onboarding)
10. [Configuration & Customization](#configuration--customization)
11. [Observability & Debugging](#observability--debugging)
12. [Complete Workflow Examples](#complete-workflow-examples)

---

## Executive Summary

### The Vision

**AI SDLC transforms software development through homeostatic, skills-based orchestration where Claude autonomously manages the complete lifecycle from intent to production feedback.**

### Core Concepts

1. **Skills**: Modular capabilities (TDD workflow, requirement extraction, code generation)
2. **Agents**: AI personas specialized for SDLC stages (Requirements Agent, Code Agent)
3. **Marketplace**: Plugin ecosystem for teams to compose their methodology
4. **Homeostasis**: Self-correcting system (sensors detect deviations, actuators fix them)
5. **Traceability**: REQ-* keys flow from intent → code → runtime → feedback

### Key Innovation

**Requirements Refinement Loop**: Disambiguated requirements (business rules, constraints, formulas) enable code autogeneration, while discovered requirements during TDD/BDD flow back to update the requirement set.

---

## User Personas

### 1. Sarah - Startup Developer

**Context**:
- Solo developer building MVP
- Wants speed + quality
- Limited time for process

**Needs**:
- Quick setup (< 5 minutes)
- Minimal overhead
- TDD workflow enforcement
- No formal stages

**Pain Points**:
- Forgets to write tests
- Requirements drift
- Tech debt accumulates

**Goal**: Ship fast without sacrificing quality

---

### 2. David - Enterprise Tech Lead

**Context**:
- Leading 20-person team
- SOC2 compliance required
- Multiple stakeholders
- Complex approval workflows

**Needs**:
- Full 7-stage SDLC
- Requirement traceability
- ADRs for decisions
- UAT sign-off gates
- Audit trail

**Pain Points**:
- Requirements change constantly
- Lost traceability (issue → requirement)
- Manual compliance checks
- Inconsistent code quality

**Goal**: Governance + velocity without bureaucracy

---

### 3. Maria - QA Lead

**Context**:
- Testing team of 5
- BDD advocate
- Coverage obsessed
- Automated testing champion

**Needs**:
- BDD workflow
- Coverage validation
- Requirement → test mapping
- Auto-generate missing tests

**Pain Points**:
- Requirements incomplete (missing edge cases)
- Tests written after code
- Coverage gaps undetected
- Manual test maintenance

**Goal**: 100% coverage with minimal manual work

---

### 4. James - Data Scientist

**Context**:
- ML model development
- Jupyter notebooks
- Exploratory workflow
- Production deployment gap

**Needs**:
- REPL-driven workflow
- Notebook → module extraction
- Property-based testing
- Model versioning

**Pain Points**:
- Notebooks hard to test
- Requirements unclear
- Production handoff messy
- No traceability

**Goal**: Bridge research → production gap

---

## User Journeys

### Journey 1: Sarah (Startup Developer) - Day 1

**Morning: Setup**

```bash
# 9:00 AM - Install Claude Code
brew install claude-code

# 9:02 AM - Create new project
mkdir my-saas-app
cd my-saas-app
git init

# 9:03 AM - Initialize Claude Code
claude init

# 9:04 AM - Browse marketplace
claude marketplace search ai-sdlc
```

**Claude shows**:
```
🔍 AI SDLC Plugins:

Recommended for startups:
  📦 @aisdlc/aisdlc-core          - Requirement traceability foundation
  📦 @aisdlc/code-skills      - Test-Driven Development workflow
  📦 @aisdlc/principles-key       - Key Principles (TDD, Fail Fast, etc.)

Full governance:
  📦 @aisdlc/requirements-skills  - Formal requirement extraction
  📦 @aisdlc/design-skills        - Architecture & ADRs
  📦 @aisdlc/testing-skills       - Coverage validation
  📦 @aisdlc/runtime-skills       - Production telemetry

💡 Quick start: claude install @aisdlc/startup-bundle
```

```bash
# 9:05 AM - Install startup bundle (core + TDD + principles)
claude install @aisdlc/startup-bundle

Installing:
  ✓ @aisdlc/aisdlc-core v3.0.0
  ✓ @aisdlc/code-skills v1.0.0
  ✓ @aisdlc/principles-key v1.0.0

Skills available:
  ✓ requirement-traceability
  ✓ tdd-workflow
  ✓ red-phase
  ✓ green-phase
  ✓ refactor-phase
  ✓ seven-questions-checklist

Ready! Try: "Implement user authentication"
```

**9:06 AM - First feature**

```
Sarah: "Implement user authentication with email and password"

Claude: I'll help implement user authentication using TDD. Let me start by
creating requirements and following the RED → GREEN → REFACTOR workflow.

First, I'll check the Seven Questions:
  1. Tests first? ✓ (Will use TDD)
  2. Fail loud? ✓ (Will add assertions)
  3. Module focused? ✓ (Separate auth module)
  4. Check if exists? Searching... no existing auth found
  5. Researched alternatives? Should we use PassportJS or build custom?

Sarah: "Build custom, keep it simple"

Claude: Got it. Creating requirement:

REQ-F-DEMO-AUTH-001: User authentication with email/password

Business Rules:
- BR-001: Email validation (standard regex)
- BR-002: Password minimum 12 characters
- BR-003: Max 3 login attempts, 15min lockout

Starting TDD workflow...

[RED Phase]
Creating test_auth.py:

# Validates: REQ-F-DEMO-AUTH-001
def test_user_login_with_valid_credentials():
    user = create_test_user(email="sarah@startup.com", password="SecurePass123!")
    result = auth.login("sarah@startup.com", "SecurePass123!")
    assert result.success == True
    assert result.user.email == "sarah@startup.com"

Test created. Running... FAILED ✓ (expected - RED phase)

Commit: RED: Add test for REQ-F-DEMO-AUTH-001

[GREEN Phase]
Creating auth.py:

# Implements: REQ-F-DEMO-AUTH-001
def login(email: str, password: str) -> LoginResult:
    user = User.get_by_email(email)
    if user and user.check_password(password):
        return LoginResult(success=True, user=user)
    return LoginResult(success=False)

Test running... PASSED ✓

Commit: GREEN: Implement REQ-F-DEMO-AUTH-001

[REFACTOR Phase]
Improving code quality...
- Added type hints
- Added logging (tagged with REQ-F-DEMO-AUTH-001)
- Extracted validation to separate function
- Added docstrings

Tests still passing ✓

Commit: REFACTOR: Clean up REQ-F-DEMO-AUTH-001

Final commit: feat: Add user authentication (REQ-F-DEMO-AUTH-001)

✅ Complete! Coverage: 100%
```

**Sarah's reaction**: "Wow, it wrote tests first, generated code, and kept me honest about quality. This is exactly what I need!"

---

### Journey 2: David (Enterprise Tech Lead) - Onboarding Team

**Monday 9:00 AM - Team Meeting**

```
David: "We're adopting AI SDLC. Everyone install these plugins:"

# .claude/plugins.yml (team config, committed to git)
plugins:
  # Core
  - "@aisdlc/aisdlc-core"
  - "@aisdlc/intent-manager"

  # All 7 stages (compliance requirement)
  - "@aisdlc/requirements-skills"
  - "@aisdlc/design-skills"
  - "@aisdlc/code-skills"
  - "@aisdlc/testing-skills"
  - "@aisdlc/stage-uat"
  - "@aisdlc/runtime-skills"

  # Principles (company standards)
  - "@aisdlc/principles-key"
  - "@aisdlc/principles-clean-arch"

  # Custom company plugin
  - "@acme/security-standards"
```

**Team installs**:
```bash
cd acme-payment-service
git pull  # Gets .claude/plugins.yml
claude install  # Installs all plugins from config

Installing 10 plugins...
✓ All plugins installed

Skills available: 47 skills
Agents available: 7 agents (Requirements, Design, Tasks, Code, Test, UAT, Runtime)

Ready for enterprise development!
```

**Monday 10:00 AM - First Feature**

```
Developer: "Add credit card payment processing"

Claude: I'll guide you through the full AI SDLC workflow.

[STAGE 1: Requirements]
Invoking: Requirements Agent

I need more details to extract requirements:
1. What credit card types? (Visa, MC, Amex?)
2. Payment gateway? (Stripe, Braintree?)
3. Compliance requirements? (PCI-DSS?)
4. Currency support?

Developer: "Visa and Mastercard only, use Stripe, PCI-DSS Level 1, USD only"

Requirements Agent: Creating disambiguated requirements...

REQ-F-DEMO-PAY-001: Credit card payment processing via Stripe

Business Rules:
- BR-001: Card types: Visa, Mastercard only
- BR-002: Card number validation: Luhn algorithm
- BR-003: CVV validation: 3 digits
- BR-004: Expiry validation: MM/YY format, not expired
- BR-005: Amount validation: > $0.01, < $10,000 per transaction

Constraints:
- C-001: PCI-DSS Level 1 compliance (no card storage)
- C-002: Stripe API timeout: 10 seconds
- C-003: Transaction idempotency: Use Stripe idempotency keys
- C-004: 3D Secure required for amounts > $1,000

Formulas:
- F-001: Stripe fee = (amount * 0.029) + 0.30
- F-002: Idempotency key = SHA256(merchant_id + timestamp + amount + card_last4)

REQ-NFR-DEMO-SEC-001: Card data security
- BR-006: Never log full card numbers
- BR-007: Tokenize cards via Stripe API
- BR-008: HTTPS only for payment endpoints

REQ-DATA-001: Payment audit trail
- BR-009: Log all payment attempts (success + failure)
- BR-010: Retain logs for 7 years (PCI-DSS)

Traceability matrix created: INT-042 → REQ-F-DEMO-PAY-001, REQ-NFR-DEMO-SEC-001, REQ-DATA-001

Ready for Design stage. Proceed?

Developer: "Yes"

[STAGE 2: Design]
Invoking: Design Agent

Creating architecture for payment processing...

Components:
- PaymentService (implements REQ-F-DEMO-PAY-001)
- StripeGateway (adapter pattern)
- CardValidator (implements BR-001 through BR-004)
- AuditLogger (implements REQ-DATA-001)

API Design:
  POST /api/v1/payments
  Request:
    {
      "amount": 100.00,
      "currency": "USD",
      "card_token": "tok_visa",  # Stripe token (C-001: no raw card data)
      "idempotency_key": "..."    # C-003
    }

Data Model:
  Payment:
    - id: UUID
    - amount: Decimal
    - status: enum(pending, completed, failed)
    - stripe_charge_id: String
    - created_at: Timestamp
    - requirement: "REQ-F-DEMO-PAY-001"  # Traceability

ADR Created:
  ADR-012: Use Stripe for payment processing
  Context: Need PCI-DSS Level 1 compliance (C-001)
  Decision: Use Stripe to avoid storing card data
  Consequences: +Compliance, +Security, -Vendor lock-in
  Acknowledges: E(t) = PCI-DSS regulations

Design complete. Ready for Tasks stage.

[STAGE 3: Tasks]
Invoking: Tasks Agent

Creating Jira tickets...

ACME-123: Implement CardValidator (REQ-F-DEMO-PAY-001, BR-001-004)
  Estimate: 3 points
  Assigned: Auto-generated

ACME-124: Implement PaymentService (REQ-F-DEMO-PAY-001)
  Estimate: 5 points
  Dependencies: ACME-123

ACME-125: Implement AuditLogger (REQ-DATA-001)
  Estimate: 2 points

ACME-126: Integration tests (REQ-F-DEMO-PAY-001)
  Estimate: 3 points

Ready for Code stage. Pick a ticket to implement.

Developer: "Start with ACME-123 - CardValidator"

[STAGE 4: Code (TDD)]
Invoking: Code Agent (TDD workflow)

[RED Phase]
Creating test_card_validator.py:

# Validates: REQ-F-DEMO-PAY-001, BR-001 (Visa/MC only)
def test_validate_visa_card():
    result = CardValidator.validate("4532015112830366", "Visa")
    assert result.valid == True

# Validates: BR-002 (Luhn algorithm)
def test_invalid_card_fails_luhn():
    result = CardValidator.validate("4532015112830367", "Visa")  # Invalid checksum
    assert result.valid == False
    assert result.error == "Invalid card number"

# Validates: BR-001 (Reject Amex)
def test_amex_card_rejected():
    result = CardValidator.validate("378282246310005", "Amex")
    assert result.valid == False
    assert result.error == "Card type not supported"

Tests created. Running... 0/3 FAILED ✓ (RED phase)

[GREEN Phase]
Creating card_validator.py:

# Implements: REQ-F-DEMO-PAY-001, BR-001, BR-002
class CardValidator:
    ALLOWED_TYPES = ["Visa", "Mastercard"]  # BR-001

    @staticmethod
    def validate(card_number: str, card_type: str) -> ValidationResult:
        # BR-001: Check card type
        if card_type not in CardValidator.ALLOWED_TYPES:
            return ValidationResult(valid=False, error="Card type not supported")

        # BR-002: Luhn algorithm
        if not CardValidator._luhn_check(card_number):
            return ValidationResult(valid=False, error="Invalid card number")

        return ValidationResult(valid=True)

    @staticmethod
    def _luhn_check(card_number: str) -> bool:
        # Luhn algorithm implementation (autogenerated from BR-002)
        ...

Tests running... 3/3 PASSED ✓

[REFACTOR Phase]
Seven Questions Checklist:
  1. Tests first? ✓
  2. Fail loud? ✓ (Clear error messages)
  3. Module focused? ✓ (Single responsibility)
  4. Check if exists? ✓ (No existing validator)
  5. Researched alternatives? ✓ (Could use Stripe SDK, but custom is simpler)
  6. Avoiding tech debt? ✓ (Clean code)
  7. Is this excellent? ✓

Code quality check passed ✓

Commit: feat: Add CardValidator (REQ-F-DEMO-PAY-001, BR-001, BR-002)

✅ ACME-123 Complete!
   Coverage: 100%
   Traceability: REQ-F-DEMO-PAY-001 → ACME-123 → commit abc123

Continue with next ticket?
```

**David's reaction**: "Perfect! Every commit is tagged with requirements, we have full traceability for audits, and the team follows the same process."

---

### Journey 3: Maria (QA Lead) - BDD Workflow

**Setup**:
```bash
# Maria's team uses BDD, not TDD
claude install @aisdlc/code-skills
```

**Feature Request**:
```
Maria: "Add password reset functionality"

Claude: I'll use BDD workflow since you have code-bdd-skills installed.

[Requirements Phase]
REQ-F-DEMO-AUTH-002: Password reset via email

Business Rules:
- BR-010: Email must be registered user
- BR-011: Reset token expires after 1 hour
- BR-012: Token usable only once
- BR-013: Email sent within 5 seconds

Formulas:
- F-004: token_expiry = issue_time + (60 * 60) seconds

[BDD Workflow - SCENARIO Phase]
Creating auth.feature:

# Validates: REQ-F-DEMO-AUTH-002
Feature: Password Reset

  As a user
  I want to reset my password via email
  So that I can regain access if I forget my password

  Scenario: Successful password reset
    Given I am a registered user with email "maria@example.com"
    And I have forgotten my password
    When I click "Forgot Password"
    And I enter email "maria@example.com"
    And I click "Send Reset Link"
    Then I should see "Check your email for reset link"
    And I should receive an email at "maria@example.com"
    And the email should contain a reset link

  Scenario: Reset link expires after 1 hour (BR-011)
    Given I received a password reset link 61 minutes ago
    When I click the reset link
    Then I should see "Reset link expired"
    And I should be prompted to request a new link

  Scenario: Reset token can only be used once (BR-012)
    Given I received a password reset link
    And I have already used the link to reset my password
    When I try to use the same link again
    Then I should see "Reset link already used"

[STEP DEFINITIONS Phase]
Creating step definitions...

@given("I am a registered user with email {email}")
def step_impl(context, email):
    context.user = create_test_user(email=email)

@when("I click {button}")
def step_impl(context, button):
    context.response = context.client.post(f"/click/{button}")

... (more step definitions)

[IMPLEMENT Phase]
Implementing password reset service...

# Implements: REQ-F-DEMO-AUTH-002
class PasswordResetService:
    def send_reset_email(self, email: str) -> ResetResult:
        # BR-010: Check user exists
        user = User.get_by_email(email)
        if not user:
            # Security: Don't reveal if email exists
            return ResetResult(success=True, message="Check your email")

        # Generate token
        token = self._generate_token()  # BR-012: One-time use
        expiry = datetime.now() + timedelta(hours=1)  # F-004, BR-011

        # Store token
        ResetToken.create(user=user, token=token, expiry=expiry)

        # Send email (BR-013: within 5 seconds)
        self._send_email(user.email, token)

        return ResetResult(success=True)

Scenarios running... 3/3 PASSED ✓

✅ Complete! Coverage: 100%
```

**Maria's reaction**: "Scenarios are in business language, stakeholders can read them, and they're executable tests. Perfect!"

---

### Journey 4: Requirements Refinement Loop (Discovery)

**Context**: Developer implementing REQ-F-DEMO-PAY-001 (payment processing)

```
Developer: "Implement payment processing for REQ-F-DEMO-PAY-001"

Claude: Starting TDD workflow for REQ-F-DEMO-PAY-001...

[RED Phase]
Creating test_payment_service.py:

# Validates: REQ-F-DEMO-PAY-001
def test_process_payment_success():
    result = PaymentService.process(amount=100.00, card_token="tok_visa")
    assert result.success == True
    assert result.charge_id is not None

# Validates: BR-005 (amount > $0.01)
def test_payment_fails_below_minimum():
    result = PaymentService.process(amount=0.005, card_token="tok_visa")
    assert result.success == False
    assert result.error == "Amount below minimum"

Tests created. Running... FAILED ✓

[GREEN Phase]
Implementing PaymentService.process()...

def process(amount: float, card_token: str) -> PaymentResult:
    # BR-005: Validate amount
    if amount < 0.01:
        return PaymentResult(success=False, error="Amount below minimum")

    # Call Stripe API (C-002: 10 second timeout)
    try:
        charge = stripe.Charge.create(
            amount=int(amount * 100),  # Convert to cents
            currency="usd",
            source=card_token,
            timeout=10  # C-002
        )
    except stripe.error.CardError as e:
        # 🚨 DISCOVERY: What about concurrent duplicate payments?
        # Missing requirement!

Developer: "Wait, what if user clicks 'Pay' button twice?"

Claude: Great catch! That's a missing requirement. Let me invoke the
refine-requirements skill.

[Refine Requirements Skill]
Discovered requirement during GREEN phase:

Missing: Idempotency handling for duplicate payments

Adding to REQ-F-DEMO-PAY-001:

REQ-F-DEMO-PAY-001: Credit card payment processing via Stripe

Business Rules (UPDATED):
- BR-001: Card types: Visa, Mastercard only
- BR-002: Card number validation: Luhn algorithm
- BR-003: CVV validation: 3 digits
- BR-004: Expiry validation: MM/YY format, not expired
- BR-005: Amount validation: > $0.01, < $10,000 per transaction
- BR-015: Duplicate payment prevention (ADDED 2025-11-20) ⭐ NEW
  - Use idempotency keys for all payment requests
  - Same idempotency key = same charge (no duplicate)
  - Idempotency key format: SHA256(user_id + timestamp + amount)
  - Discovered during: TDD GREEN phase
  - Source: Developer question about duplicate payments

Updating code with BR-015...

def process(amount: float, card_token: str, user_id: str) -> PaymentResult:
    # BR-015: Generate idempotency key
    idempotency_key = self._generate_idempotency_key(user_id, amount)

    # BR-005: Validate amount
    if amount < 0.01:
        return PaymentResult(success=False, error="Amount below minimum")

    # Call Stripe API with idempotency key (BR-015)
    try:
        charge = stripe.Charge.create(
            amount=int(amount * 100),
            currency="usd",
            source=card_token,
            timeout=10,  # C-002
            idempotency_key=idempotency_key  # BR-015
        )
        return PaymentResult(success=True, charge_id=charge.id)
    except stripe.error.CardError as e:
        return PaymentResult(success=False, error=str(e))

Now adding test for BR-015:

# Validates: BR-015 (duplicate prevention)
def test_duplicate_payment_prevented():
    # First payment
    result1 = PaymentService.process(
        amount=100.00,
        card_token="tok_visa",
        user_id="user_123"
    )
    assert result1.success == True

    # Duplicate payment (same user, amount, timestamp)
    result2 = PaymentService.process(
        amount=100.00,
        card_token="tok_visa",
        user_id="user_123"
    )
    # Should return same charge, not create new one
    assert result2.success == True
    assert result2.charge_id == result1.charge_id  # Same charge!

Tests running... 3/3 PASSED ✓

✅ Requirement refined during implementation!
   REQ-F-DEMO-PAY-001 updated with BR-015
   Code regenerated with idempotency handling
   New test added for BR-015
   Coverage: 100%

Traceability updated:
  BR-015:
    discovered_during: TDD GREEN phase
    discovered_by: Developer (manual question)
    date: 2025-11-20
    commit: def456
```

**Developer's reaction**: "The system captured my discovery and updated the requirements automatically. Now the next developer won't have this same question!"

---

## Marketplace Experience

### Browsing Plugins

```bash
claude marketplace search
```

**Claude shows**:
```
📦 AI SDLC Marketplace

Categories:
  🏗️  Foundations
  📋 Requirements
  🎨 Design
  💻 Code Workflows
  🧪 Testing
  🚀 Runtime
  📖 Principles
  🎯 Bundles

Popular:
  ⭐ @aisdlc/aisdlc-core (10k downloads)
  ⭐ @aisdlc/code-skills (8k downloads)
  ⭐ @aisdlc/code-skills (5k downloads)

Featured:
  🆕 @aisdlc/code-generation-skills (NEW - Autogenerate from business rules)
  🔥 @aisdlc/runtime-skills (HOT - Production feedback loop)

Search: claude marketplace search <query>
Install: claude install @aisdlc/<plugin-name>
```

### Plugin Details

```bash
claude marketplace show @aisdlc/code-skills
```

**Claude shows**:
```
📦 @aisdlc/code-skills v1.0.0

Description:
  Test-Driven Development workflow with RED → GREEN → REFACTOR → COMMIT cycle.
  Maintains requirement traceability throughout development.

Skills Provided:
  ✓ tdd-workflow          - Complete TDD orchestration
  ✓ red-phase             - Write failing tests
  ✓ green-phase           - Implement minimal code
  ✓ refactor-phase        - Improve code quality
  ✓ commit-with-req-tag   - Git commits tagged with REQ-*

Prerequisites:
  - @aisdlc/aisdlc-core (required for requirement traceability)

Works Well With:
  - @aisdlc/testing-skills (coverage validation)
  - @aisdlc/principles-key (enforce Key Principles)

Used By:
  - 8,342 teams
  - 94% satisfaction

Reviews:
  ⭐⭐⭐⭐⭐ "Keeps me honest about TDD!" - Sarah, Startup Dev
  ⭐⭐⭐⭐⭐ "Our team's code quality went up 40%" - David, Tech Lead
  ⭐⭐⭐⭐☆ "Love it, but wish it had BDD support" - Maria, QA Lead
    → Try @aisdlc/code-skills instead!

Install: claude install @aisdlc/code-skills
```

### Bundle Recommendations

```bash
claude marketplace bundles
```

**Claude shows**:
```
🎯 Recommended Plugin Bundles

@aisdlc/startup-bundle ($0 - Free)
  Perfect for: Solo developers, MVPs, prototypes
  Includes:
    ✓ @aisdlc/aisdlc-core
    ✓ @aisdlc/code-skills
    ✓ @aisdlc/principles-key
  What you get:
    - TDD workflow enforcement
    - Requirement traceability
    - Key Principles validation
    - Minimal overhead

@aisdlc/enterprise-bundle ($0 - Free)
  Perfect for: Large teams, compliance, governance
  Includes:
    ✓ @aisdlc/aisdlc-core
    ✓ @aisdlc/requirements-skills
    ✓ @aisdlc/design-skills
    ✓ @aisdlc/code-skills
    ✓ @aisdlc/testing-skills
    ✓ @aisdlc/stage-uat
    ✓ @aisdlc/runtime-skills
    ✓ @aisdlc/principles-key
    ✓ @aisdlc/principles-clean-arch
  What you get:
    - Full 7-stage SDLC
    - Complete traceability
    - ADRs and design docs
    - UAT sign-off gates
    - Production feedback loop

@aisdlc/qa-bundle ($0 - Free)
  Perfect for: QA teams, test-first development
  Includes:
    ✓ @aisdlc/aisdlc-core
    ✓ @aisdlc/code-skills
    ✓ @aisdlc/testing-skills
    ✓ @aisdlc/requirements-skills
  What you get:
    - BDD workflow (Gherkin scenarios)
    - Coverage validation
    - Auto-generate missing tests
    - Requirement completeness checking

@aisdlc/datascience-bundle ($0 - Free)
  Perfect for: ML/Data Science teams, notebooks
  Includes:
    ✓ @aisdlc/aisdlc-core
    ✓ @aisdlc/code-repl-driven-skills
    ✓ @aisdlc/testing-property-skills
  What you get:
    - REPL-driven workflow
    - Notebook → module extraction
    - Property-based testing
    - Model versioning

Install: claude install @aisdlc/<bundle-name>
```

---

## Skills Experience

### Discovering Skills

```bash
claude skills list
```

**Claude shows**:
```
🎯 Available Skills (12 skills from 3 plugins)

From @aisdlc/aisdlc-core:
  📌 requirement-traceability      - REQ-* key patterns and rules
  📊 check-requirement-coverage    - Detect requirements without tests (Sensor)
  🏷️  propagate-req-keys            - Tag artifacts with REQ-* (Actuator)

From @aisdlc/code-skills:
  🔄 tdd-workflow                  - Complete TDD orchestration
  🔴 red-phase                     - Write failing tests
  🟢 green-phase                   - Implement minimal code
  🔧 refactor-phase                - Improve code quality
  📝 commit-with-req-tag           - Git commits with REQ-*

From @aisdlc/principles-key:
  ✅ apply-key-principles          - Enforce 7 Key Principles
  ❓ seven-questions-checklist     - Validate before coding (Sensor)

Sensors (detect deviations):
  - check-requirement-coverage
  - seven-questions-checklist

Actuators (fix deviations):
  - propagate-req-keys
  - tdd-workflow
  - red-phase, green-phase, refactor-phase

View details: claude skills show <skill-name>
```

### Skill Details

```bash
claude skills show tdd-workflow
```

**Claude shows**:
```
🔄 tdd-workflow

Description:
  Test-Driven Development workflow maintaining requirement traceability.
  Follows RED → GREEN → REFACTOR → COMMIT cycle.

Type: Orchestrator Skill

Prerequisites:
  - Work unit with REQ-* tag
  - Requirement details available

Uses Skills:
  - requirement-traceability (for REQ-* patterns)
  - red-phase (write failing test)
  - green-phase (make test pass)
  - refactor-phase (improve code)
  - commit-with-req-tag (commit with REQ-*)
  - propagate-req-keys (tag code/tests)

Workflow:
  1. RED Phase: Write failing test for REQ-*
  2. GREEN Phase: Write minimal code to pass
  3. REFACTOR Phase: Improve quality, add logging
  4. COMMIT Phase: Tag commit with REQ-*

Homeostasis Behavior:
  If prerequisites missing:
    → Detect: No REQ-* key
    → Signal: "Need requirement extraction first"
    → Claude invokes: requirement-extraction skill
    → Retry: tdd-workflow with new REQ-*

Allowed Tools:
  - Read, Write, Edit, Bash

Example:
  User: "Implement user login for REQ-F-DEMO-AUTH-001"
  Claude: (invokes tdd-workflow skill)
    → RED: test_user_login()
    → GREEN: login() implementation
    → REFACTOR: Add logging, improve code
    → COMMIT: feat: Add login (REQ-F-DEMO-AUTH-001)

Success Rate: 94% (8,234 invocations)
Avg Duration: 4.2 minutes
```

### Skill Invocation (Autonomous)

**User doesn't explicitly call skills - Claude decides when to use them**

```
User: "I need to implement a payment feature"

Claude (internal reasoning):
  1. Observe: User wants payment feature
  2. Check context: No REQ-* keys exist
  3. Prerequisite missing: requirement-extraction needs intent first
  4. Action: Ask user for details

Claude: To create requirements, I need more details:
  - What payment methods? (credit card, PayPal, crypto?)
  - Payment provider? (Stripe, Braintree?)
  - Compliance needs? (PCI-DSS level?)

User: "Credit card via Stripe, PCI-DSS Level 1"

Claude (internal reasoning):
  1. Now have intent details
  2. Invoke: requirement-extraction skill
  3. Invoke: disambiguate-requirements skill (add business rules)
  4. Output: REQ-F-DEMO-PAY-001 with BR-*, C-*, F-*

Claude: I've created detailed requirements:

REQ-F-DEMO-PAY-001: Credit card payment via Stripe
  Business Rules: 5 rules (card validation, amount limits)
  Constraints: 4 constraints (PCI-DSS, timeouts, idempotency)
  Formulas: 2 formulas (Stripe fee calculation, idempotency key)

Ready to implement using TDD workflow?

User: "Yes"

Claude (internal reasoning):
  1. Prerequisites met: REQ-F-DEMO-PAY-001 exists ✓
  2. Invoke: tdd-workflow skill
  3. Invoke: red-phase skill (write tests)
  4. Invoke: green-phase skill (implement)
  5. Invoke: refactor-phase skill (improve)
  6. Invoke: commit-with-req-tag skill

Claude: [Shows TDD workflow progress...]

✅ Complete! REQ-F-DEMO-PAY-001 implemented with 100% coverage.
```

**Key point**: User never said "use tdd-workflow skill" - Claude autonomously decided based on context and prerequisites.

---

## Agent Experience

### What Are Agents?

**Agents = Specialized AI personas for SDLC stages**

- Requirements Agent: Extract and disambiguate requirements
- Design Agent: Create architecture and ADRs
- Code Agent: Implement using TDD/BDD
- Test Agent: Validate coverage
- UAT Agent: Business validation
- Runtime Agent: Production feedback

### Agent Invocation

**Claude becomes the agent based on stage context**

```
User: "Create requirements for customer portal"

Claude: (Switches to Requirements Agent persona)

I'm the Requirements Agent. Let me extract structured requirements from your intent.

[Requirements Agent behavior]:
- Asks clarifying questions
- Creates REQ-F-*, REQ-NFR-*, REQ-DATA-*
- Generates business rules, constraints, formulas
- Builds traceability matrix

Output:
  REQ-F-DEMO-PORTAL-001: Customer login
  REQ-F-DEMO-PORTAL-002: View account balance
  REQ-F-DEMO-PORTAL-003: Update profile
  ...

Traceability: INT-055 → [REQ-F-DEMO-PORTAL-001, ...]

Ready for Design Agent?

User: "Yes"

Claude: (Switches to Design Agent persona)

I'm the Design Agent. Let me create the architecture for these requirements.

[Design Agent behavior]:
- Creates component diagrams
- Designs APIs
- Writes ADRs acknowledging E(t)
- Tags everything with REQ-*

Output:
  Components:
    - AuthenticationService (REQ-F-DEMO-PORTAL-001)
    - AccountService (REQ-F-DEMO-PORTAL-002)
    - ProfileService (REQ-F-DEMO-PORTAL-003)

  ADR-023: Use OAuth2 for authentication
    Context: E(t) = Existing OAuth2 infrastructure
    Decision: Integrate with company OAuth2 server
    Consequences: +Consistency, +SSO, -Custom flows

Ready for Code Agent?
```

**Key point**: User experiences different "personas" (agents) as they progress through SDLC stages, but it's still Claude orchestrating.

---

## Homeostasis Experience

### User Sees Self-Correction

**Example: Missing Tests Detected**

```
User: "I'm done implementing payment processing"

Claude: Let me validate test coverage...

[Invoking: validate-test-coverage skill (Sensor)]

Coverage Report:
  REQ-F-DEMO-PAY-001: 85% coverage ⚠️
    ✓ test_process_payment_success
    ✓ test_payment_fails_below_minimum
    ✗ Missing: Test for BR-003 (CVV validation)
    ✗ Missing: Test for BR-015 (idempotency)

  REQ-NFR-DEMO-SEC-001: 0% coverage ❌
    ✗ Missing: All security tests

Homeostasis deviation detected! Coverage below 100%.

Should I generate missing tests?

User: "Yes"

Claude: [Invoking: generate-missing-tests skill (Actuator)]

Generating tests for missing coverage...

[RED Phase]
Created test_cvv_validation():
  # Validates: BR-003
  def test_invalid_cvv_rejected():
      result = PaymentService.process(
          amount=100.00,
          card_token="tok_visa_invalid_cvv"
      )
      assert result.success == False
      assert result.error == "Invalid CVV"

[GREEN Phase]
Updated PaymentService to validate CVV...

[REFACTOR Phase]
Code quality check passed ✓

Coverage re-checked:
  REQ-F-DEMO-PAY-001: 95% coverage ✓
  REQ-NFR-DEMO-SEC-001: 100% coverage ✓

Homeostasis achieved! All requirements have >= 80% coverage.
```

**User's reaction**: "It detected gaps and fixed them automatically. I didn't have to think about what tests I missed!"

---

### Example: Tech Debt Detected (Principle #6 Enforcement)

```
User: "I'm done with the authentication refactor"

Claude: Let me check for technical debt...

[Invoking: detect-unused-code skill (Sensor)]

Tech Debt Report:
  auth_service.py:
    ⚠️ Unused imports (5):
      - import hashlib      # Line 3 (never used)
      - import re           # Line 4 (never used)
      - from typing import Dict  # Line 7 (never used)

    ⚠️ Dead code (2 functions):
      - legacy_hash_password()  # Line 45-52 (no callers)
      - validate_old_token()    # Line 89-97 (no callers)

    ⚠️ Commented code (15 lines):
      - Lines 120-135 (old implementation)

[Invoking: detect-complexity skill (Sensor)]

Complexity Report:
  auth_service.py:
    ❌ login() - Cyclomatic complexity: 18 (threshold: 10)
      - 6 nested if statements
      - 4 try/except blocks
      - Recommend extracting validation logic

Homeostasis deviation detected! Tech debt > 0 (Principle #6 violated).

Should I automatically prune this tech debt?

User: "Yes"

Claude: [Invoking: prune-unused-code skill (Actuator)]

Removing unused imports...
  ✓ Deleted: import hashlib (line 3)
  ✓ Deleted: import re (line 4)
  ✓ Deleted: from typing import Dict (line 7)

Removing dead code...
  ✓ Deleted: legacy_hash_password() (8 lines)
  ✓ Deleted: validate_old_token() (9 lines)

Removing commented code...
  ✓ Deleted: Lines 120-135 (16 lines)

[Invoking: simplify-complex-code skill (Actuator)]

Refactoring login() to reduce complexity...

Before (Complexity: 18):
def login(email: str, password: str) -> LoginResult:
    if email is None:
        if not is_valid_email(email):
            if User.exists(email):
                user = User.get(email)
                if user.is_locked:
                    if user.lockout_expired():
                        # ... 50 more lines of nested logic

After (Complexity: 6):
def login(email: str, password: str) -> LoginResult:
    validation_error = validate_login_input(email, password)
    if validation_error:
        return LoginResult(success=False, error=validation_error)

    user = get_user_or_fail(email)

    if user.is_locked and not user.lockout_expired():
        return LoginResult(success=False, error="Account locked")

    return authenticate_user(user, password)

# Extracted functions (each < 10 lines, complexity < 5)
def validate_login_input(email, password): ...
def get_user_or_fail(email): ...
def authenticate_user(user, password): ...

Running tests to verify refactor...
  ✓ All 47 tests passing

Tech debt re-checked:
  ✓ Unused imports: 0
  ✓ Dead code: 0 functions
  ✓ Commented code: 0 lines
  ✓ Complexity: Max 6 (threshold: 10)

Homeostasis achieved! Tech debt = 0 (Principle #6: "No Legacy Baggage" ✓)

File size reduced: 487 lines → 312 lines (-36%)
```

**User's reaction**: "It automatically deleted all the cruft I accumulated and simplified my overly complex function. Principle #6 actually has teeth now!"

---

## Requirements Refinement Loop

### User Experience of Discovery → Feedback

**Scenario: Developer discovers edge case**

```
User: "Implement user registration with REQ-F-DEMO-AUTH-003"

Claude: Starting TDD for REQ-F-DEMO-AUTH-003...

REQ-F-DEMO-AUTH-003: User registration with email

Business Rules:
- BR-020: Email must be unique
- BR-021: Email validation (standard regex)
- BR-022: Password minimum 12 characters

[RED Phase]
test_user_registration():
  # Validates: REQ-F-DEMO-AUTH-003
  def test_register_new_user():
      result = auth.register("newuser@example.com", "SecurePass123!")
      assert result.success == True

[GREEN Phase]
Implementing register()...

def register(email: str, password: str) -> RegisterResult:
    # BR-021: Validate email
    if not validate_email(email):
        return RegisterResult(success=False, error="Invalid email")

    # BR-020: Check uniqueness
    if User.exists(email):
        return RegisterResult(success=False, error="Email already registered")

    # BR-022: Validate password
    if not validate_password(password):
        return RegisterResult(success=False, error="Weak password")

    # Create user
    user = User.create(email=email, password=hash_password(password))
    return RegisterResult(success=True, user=user)

Tests passing ✓

User: "Wait, what if two users register with the same email at the exact same time?"

Claude: Excellent catch! That's a race condition. Let me refine the requirements.

[Invoking: refine-requirements skill]

Discovered requirement:
  "Concurrent registration with same email should be prevented"

Adding to REQ-F-DEMO-AUTH-003:

REQ-F-DEMO-AUTH-003: User registration with email (UPDATED)

Business Rules:
- BR-020: Email must be unique
- BR-021: Email validation (standard regex)
- BR-022: Password minimum 12 characters
- BR-023: Prevent concurrent duplicate registrations (ADDED 2025-11-20) ⭐ NEW
  - Use database unique constraint on email column
  - Catch unique constraint violation
  - Return clear error message
  - Discovered during: TDD GREEN phase
  - Source: Developer question about race condition

Updating code for BR-023...

def register(email: str, password: str) -> RegisterResult:
    try:
        # BR-021: Validate email
        if not validate_email(email):
            return RegisterResult(success=False, error="Invalid email")

        # BR-022: Validate password
        if not validate_password(password):
            return RegisterResult(success=False, error="Weak password")

        # Create user (BR-020 + BR-023: unique constraint handles race condition)
        user = User.create(email=email, password=hash_password(password))
        return RegisterResult(success=True, user=user)

    except IntegrityError as e:
        # BR-023: Concurrent registration caught by database
        if "unique constraint" in str(e).lower():
            return RegisterResult(success=False, error="Email already registered")
        raise

Adding test for BR-023:

def test_concurrent_registration_prevented():
    # Validates: BR-023 (race condition)
    # Simulate concurrent registrations using threads
    ...

✅ Requirements refined!
   REQ-F-DEMO-AUTH-003 updated with BR-023
   Code updated with race condition handling
   New test added
   Coverage: 100%

requirements.md automatically updated ✓
Traceability matrix updated ✓
```

**User's reaction**: "My question became a permanent part of the requirements. The next developer won't have to discover this edge case again!"

---

## Team Onboarding

### Day 1: New Developer Joins Enterprise Team

**9:00 AM - Laptop Setup**

```bash
# Clone team repo
git clone git@github.com:acme/payment-service.git
cd payment-service

# Install Claude Code
brew install claude-code

# Team plugins auto-install from .claude/plugins.yml
claude install

Installing plugins for Acme Payment Service...
✓ @aisdlc/aisdlc-core
✓ @aisdlc/requirements-skills
✓ @aisdlc/design-skills
✓ @aisdlc/code-skills
✓ @aisdlc/testing-skills
✓ @aisdlc/runtime-skills
✓ @aisdlc/principles-key
✓ @acme/security-standards

Skills available: 42 skills
Agents available: 7 agents

Team standards loaded:
  ✓ TDD workflow enforced
  ✓ Requirement traceability required
  ✓ 90% coverage minimum
  ✓ Security scans on every commit
  ✓ ADRs required for architecture decisions

Welcome to Acme Payment Service! 🎉

Quick start:
  1. Read: cat docs/GETTING_STARTED.md
  2. Ask Claude: "Show me an example workflow"
  3. Pick a ticket: "Implement ACME-XXX"
```

**9:15 AM - First Ticket**

```
New Dev: "Show me an example workflow"

Claude: I'll walk you through our complete workflow using a real ticket.

Pick a ticket from Jira, or try:
  ACME-234: Add support for EUR currency (REQ-F-DEMO-PAY-005)

New Dev: "Let's do ACME-234"

Claude: Great choice! Let me pull the requirement details...

REQ-F-DEMO-PAY-005: Multi-currency support (EUR)

Business Rules:
- BR-030: Support USD and EUR only (initially)
- BR-031: Exchange rates updated hourly from ECB API
- BR-032: Display currency with proper formatting (€ for EUR, $ for USD)

Constraints:
- C-010: Exchange rate API timeout: 5 seconds
- C-011: Cache exchange rates for 1 hour

Formulas:
- F-010: converted_amount = amount * exchange_rate

This was designed in ADR-025 (already exists).

Starting TDD workflow...

[RED Phase]
test_payment_in_euros():
  # Validates: REQ-F-DEMO-PAY-005
  def test_process_payment_in_euros():
      result = PaymentService.process(
          amount=100.00,
          currency="EUR",  # New parameter
          card_token="tok_visa"
      )
      assert result.success == True
      assert result.currency == "EUR"

Running tests... FAILED ✓ (RED phase - expected)

[GREEN Phase]
Updating PaymentService.process() to support currency parameter...

(Continues TDD workflow...)

✅ ACME-234 Complete!
   Coverage: 100%
   Traceability: REQ-F-DEMO-PAY-005 → ACME-234 → commit xyz789
   Security scan: PASSED
   Ready to push!

Push to remote?

New Dev: "Yes"

Claude: git push origin feature/ACME-234

Pushed! Create PR with:
  gh pr create --title "Add EUR support (REQ-F-DEMO-PAY-005, ACME-234)"
```

**New Dev's reaction**: "I didn't have to learn your process - Claude guided me through your exact workflow, and I shipped a feature on Day 1!"

---

## Configuration & Customization

### Team Config (.claude/plugins.yml)

```yaml
# Committed to git - shared across team
plugins:
  - name: "@aisdlc/aisdlc-core"
    version: "^3.0.0"

  - name: "@aisdlc/code-skills"
    version: "^1.0.0"
    config:
      minimum_coverage: 90        # Company standard
      enforce_red_green_refactor: true
      allow_skip_tests: false

  - name: "@aisdlc/principles-key"
    version: "^1.0.0"
    config:
      seven_questions_required: true
      block_on_no_answers: true   # Don't allow code if questions fail

  - name: "@acme/security-standards"
    version: "^2.1.0"
    config:
      run_security_scan: true
      block_on_vulnerabilities: high  # Block on high severity
      allowed_licenses:
        - MIT
        - Apache-2.0
        - BSD-3-Clause
```

### Personal Overrides (~/.claude/config.yml)

```yaml
# Personal preferences - NOT committed to git
personal:
  verbose_mode: true              # I like detailed output
  auto_commit: false              # I prefer manual commits
  preferred_test_framework: pytest

  # Override team setting (if allowed)
  minimum_coverage: 95            # Higher than team's 90%
```

### Runtime Overrides (Per Session)

```bash
# Override coverage for this session only
claude config set minimum_coverage 80

# Check current config
claude config show

Current Configuration:
  minimum_coverage: 80 (overridden from 90)
  enforce_red_green_refactor: true
  seven_questions_required: true

# Reset to team defaults
claude config reset
```

---

## Observability & Debugging

### Homeostasis Visualization

```bash
claude homeostasis status
```

**Claude shows**:
```
🔄 Homeostasis Status

Current State:
  Requirements: 15 REQ-* keys
  Code: 12 files
  Tests: 87 tests
  Coverage: 94%

Sensors (Monitoring):
  ✓ check-requirement-coverage    - Last run: 2 min ago
    Status: 2 requirements below 80% coverage
    Deviation: REQ-F-DEMO-PAY-005 (75%), REQ-NFR-DEMO-SEC-002 (60%)

  ✓ validate-test-coverage         - Last run: 2 min ago
    Status: 2 tests failing
    Deviation: test_payment_in_euros, test_security_headers

  ⚠️ detect-unused-code            - Last run: 1 min ago
    Status: Tech debt detected
    Deviation: 5 unused imports, 2 dead functions, 15 lines of commented code

  ⚠️ detect-complexity             - Last run: 1 min ago
    Status: Complexity violations
    Deviation: login() complexity 18 (threshold: 10)

  ✓ seven-questions-checklist      - Last run: 5 min ago
    Status: All questions answered ✓

Actuators (Correcting):
  🔄 generate-missing-tests        - Running now...
    Target: REQ-F-DEMO-PAY-005, REQ-NFR-DEMO-SEC-002
    Progress: 1/2 tests generated

  🔄 prune-unused-code             - Queued
    Target: 5 unused imports, 2 dead functions, 15 lines commented code
    Waiting for: generate-missing-tests to complete

  🔄 simplify-complex-code         - Queued
    Target: login() (complexity 18 → 6)
    Waiting for: prune-unused-code to complete

  ⏸️ tdd-workflow                  - Idle
    Last used: 10 min ago

Homeostasis Goal:
  ✗ 100% coverage (currently 94%)
  ✗ All tests passing (2 failing)
  ✗ Tech debt = 0 (currently 22 violations)
  ✗ Complexity ≤ 10 (max: 18)
  ✓ All questions answered

Estimated time to homeostasis: 5 minutes

Watch live: claude homeostasis watch
```

### Skill Execution Trace

```bash
claude trace last
```

**Claude shows**:
```
📊 Last Execution Trace

Command: "Implement payment processing"

Execution Flow:
  1. User intent received
     ↓
  2. check-requirement-coverage (Sensor)
     Detected: No REQ-* for payment processing
     ↓
  3. requirement-extraction (Actuator)
     Output: REQ-F-DEMO-PAY-001
     Duration: 15s
     ↓
  4. disambiguate-requirements (Actuator)
     Added: 5 business rules, 4 constraints, 2 formulas
     Duration: 22s
     ↓
  5. seven-questions-checklist (Sensor)
     All questions answered ✓
     ↓
  6. tdd-workflow (Orchestrator)
     ├─ red-phase (Actuator)
     │  Output: test_payment_processing.py (3 tests)
     │  Duration: 18s
     ├─ green-phase (Actuator)
     │  Output: payment_service.py
     │  Duration: 34s
     ├─ refactor-phase (Actuator)
     │  Output: Improved code quality
     │  Duration: 12s
     └─ commit-with-req-tag (Actuator)
        Output: commit abc123 "feat: Add payment (REQ-F-DEMO-PAY-001)"
        Duration: 3s
     ↓
  7. validate-test-coverage (Sensor)
     Coverage: 100% ✓
     ↓
  8. Homeostasis achieved ✓

Total Duration: 1m 44s
Skills Invoked: 8 skills
Homeostasis Iterations: 1 (converged immediately)
```

### Debugging Failed Skills

```bash
claude debug skill tdd-workflow
```

**Claude shows**:
```
🐛 Debug: tdd-workflow Skill

Last Execution: 5 min ago
Status: ✓ Success

Execution Details:
  Prerequisites Check:
    ✓ Work unit with REQ-* tag: REQ-F-DEMO-PAY-001
    ✓ Requirement details available
    ✓ git repository initialized

  Skills Invoked:
    1. red-phase
       Status: ✓ Success
       Output: 3 tests created
       Duration: 18s

    2. green-phase
       Status: ✓ Success
       Output: payment_service.py (142 lines)
       Duration: 34s

    3. refactor-phase
       Status: ✓ Success
       Code quality: 9.2/10
       Duration: 12s

    4. commit-with-req-tag
       Status: ✓ Success
       Commit: abc123
       Duration: 3s

  Output:
    Files created: 2 (payment_service.py, test_payment_service.py)
    Tests: 3 tests, 100% passing
    Coverage: 100%
    Commits: 4 commits (RED, GREEN, REFACTOR, final)

Previous Executions (last 5):
  1. 5 min ago: ✓ Success (REQ-F-DEMO-PAY-001)
  2. 2 hours ago: ✓ Success (REQ-F-DEMO-AUTH-002)
  3. 1 day ago: ✓ Success (REQ-F-DEMO-PORTAL-003)
  4. 2 days ago: ✗ Failed (Missing REQ-* tag) ← Click to debug
  5. 3 days ago: ✓ Success (REQ-NFR-DEMO-PERF-001)

Success Rate: 80% (4/5 succeeded)

Common Failures:
  - 15%: Missing REQ-* tag (prerequisite not met)
  - 3%: Tests didn't pass in GREEN phase
  - 2%: Git commit failed

Debug specific execution: claude debug skill tdd-workflow --execution <id>
```

---

## Complete Workflow Examples

### Example 1: Feature from Scratch (Startup)

**User**: Sarah (solo developer)
**Plugins**: `@aisdlc/startup-bundle`

```
9:00 AM - Sarah: "Build a todo app"

Claude: I'll help build a todo app using TDD. Let me start with requirements.

[Creating requirements on-the-fly]
REQ-F-DEMO-TASK-001: Create task item
REQ-F-DEMO-TASK-002: Mark task as complete
REQ-F-DEMO-TASK-003: List all tasks

Starting with REQ-F-DEMO-TASK-001...

[RED Phase]
test_create_task.py:
  def test_create_task():
      task = Task.create(title="Buy milk")
      assert task.title == "Buy milk"
      assert task.completed == False

[GREEN Phase]
task.py:
  class Task:
      def create(title):
          return Task(title=title, completed=False)

[REFACTOR Phase]
(Improved with validation, logging)

✅ REQ-F-DEMO-TASK-001 complete!

Continue with REQ-F-DEMO-TASK-002?

Sarah: "Yes, all of them"

(Claude completes remaining features...)

3 hours later:

✅ Todo app complete!
   - 3 features (REQ-F-DEMO-TASK-001, 002, 003)
   - 15 tests, 100% coverage
   - Clean code (7/7 principles met)
   - Production ready

Deploy to Vercel?

Sarah: "Yes!"

(Claude deploys...)

Live: https://sarah-todo-app.vercel.app

Sarah ships an MVP in 3 hours ✅
```

---

### Example 2: Enterprise Feature (Complete 7-Stage)

**User**: David's team (enterprise)
**Plugins**: `@aisdlc/enterprise-bundle`

```
Monday 9:00 AM - Product Owner: "We need GDPR data export feature"

Claude: I'll guide you through the full AI SDLC workflow.

[STAGE 1: Requirements]
Requirements Agent: I need more details...
  - What data should be exported? (all user data, specific tables?)
  - Format? (JSON, CSV, PDF?)
  - Timeline? (immediate download, async email?)
  - Access control? (user only, admins?)

PO: "All user data, JSON format, async email, user-initiated only"

Requirements Agent: Creating requirements...

REQ-F-DEMO-GDPR-001: User data export

Business Rules:
- BR-100: User can only export their own data
- BR-101: Export includes: profile, orders, payments, activity logs
- BR-102: Export format: JSON
- BR-103: Delivery: Email with download link (expires 24 hours)
- BR-104: Rate limit: 1 export per user per 24 hours

Constraints:
- C-100: GDPR Article 20 compliance (data portability)
- C-101: Export generation timeout: 5 minutes max
- C-102: Files encrypted at rest (AES-256)

Formulas:
- F-100: download_link_expiry = generation_time + (24 * 3600) seconds

REQ-NFR-DEMO-SEC-003: Data export security
- BR-105: Authenticate user before export
- BR-106: Audit log every export request
- BR-107: Delete export file after 24 hours

Traceability: INT-100 → REQ-F-DEMO-GDPR-001, REQ-NFR-DEMO-SEC-003

[STAGE 2: Design]
Design Agent: Creating architecture...

Components:
- DataExportService (REQ-F-DEMO-GDPR-001)
- ExportJobQueue (async processing)
- StorageService (encrypted storage, REQ-NFR-DEMO-SEC-003)
- NotificationService (email delivery)

API Design:
  POST /api/v1/exports
  Response: { "job_id": "...", "status": "pending" }

ADR-045: Use S3 for export file storage
  Context: E(t) = AWS infrastructure, GDPR encryption requirements
  Decision: Use AWS S3 with server-side encryption
  Consequences: +Scalability, +Encryption, +Compliance, -AWS dependency

[STAGE 3: Tasks]
Tasks Agent: Creating Jira tickets...

ACME-500: Implement DataExportService (REQ-F-DEMO-GDPR-001) [8 points]
ACME-501: Setup export job queue (REQ-F-DEMO-GDPR-001) [5 points]
ACME-502: Integrate S3 storage (REQ-NFR-DEMO-SEC-003) [3 points]
ACME-503: Add audit logging (REQ-NFR-DEMO-SEC-003) [2 points]
ACME-504: Integration tests (REQ-F-DEMO-GDPR-001) [5 points]

Capacity: 23 points total, 2 week sprint

[STAGE 4: Code]
Developer picks ACME-500...

Code Agent (TDD workflow):
  (Complete TDD implementation as shown earlier...)

✅ ACME-500 complete (5 days later, all tickets done)

[STAGE 5: System Test]
Test Agent: Running integration tests...

BDD scenarios:
  Feature: GDPR Data Export
    Scenario: User exports data successfully
      Given I am logged in as "user@acme.com"
      When I request a data export
      Then I should receive email with download link
      And the export should contain my profile data
      And the export should contain my order history

  18 scenarios, all passing ✓

Coverage:
  REQ-F-DEMO-GDPR-001: 100% ✓
  REQ-NFR-DEMO-SEC-003: 100% ✓

[STAGE 6: UAT]
UAT Agent: Creating UAT test cases...

UAT-050: Business validation
  Tester: Product Owner
  Test: Export user data and verify completeness
  Status: ⏳ Pending

PO tests in staging... approves ✓

UAT-050: APPROVED ✅

[STAGE 7: Runtime Feedback]
Deploy to production...

Runtime Agent: Setting up telemetry...

Datadog metrics:
  - export_requests (tagged: REQ-F-DEMO-GDPR-001)
  - export_duration (tagged: REQ-F-DEMO-GDPR-001)
  - export_failures (tagged: REQ-F-DEMO-GDPR-001)

Alerts:
  - export_duration > 5 minutes → "ERROR: REQ-F-DEMO-GDPR-001 - Export timeout"

Production (1 week later):
  Alert fired: "ERROR: REQ-F-DEMO-GDPR-001 - Export timeout for large accounts"

Runtime Agent: Tracing back...
  REQ-F-DEMO-GDPR-001 → INT-100 → Create new intent

New Intent Created:
  INT-150: Optimize GDPR export for large accounts
  Related: REQ-F-DEMO-GDPR-001
  Impact: 5% of exports timing out
  Priority: P1

Homeostasis loop begins again... ♻️

David's team ships enterprise-grade feature with complete governance ✅
```

---

## Summary: User Experience Highlights

### For Sarah (Startup Developer)
- ✅ 5-minute setup
- ✅ Ships MVP in hours
- ✅ TDD enforced automatically
- ✅ No formal process overhead
- ✅ Quality without bureaucracy

### For David (Enterprise Tech Lead)
- ✅ Full governance + traceability
- ✅ Team consistency (everyone uses same workflow)
- ✅ Audit trail for compliance
- ✅ Production feedback loop
- ✅ Velocity without sacrificing quality

### For Maria (QA Lead)
- ✅ BDD scenarios in business language
- ✅ Auto-detect coverage gaps
- ✅ Auto-generate missing tests
- ✅ 100% coverage without manual work

### For James (Data Scientist)
- ✅ REPL-driven workflow (Jupyter notebooks)
- ✅ Notebook → production bridge
- ✅ Property-based testing for ML models
- ✅ Traceability even in exploratory work

---

## Key UX Innovations

1. **Homeostasis is Visible**: Users see system self-correct (sensors → actuators)
2. **Requirements Refine During Development**: Discoveries flow back to requirements
3. **Autonomous Orchestration**: Claude decides which skills to use, when
4. **No Prescriptive Workflow**: Emergent behavior from prerequisites
5. **Marketplace Flexibility**: Teams compose exactly what they need
6. **Traceability Everywhere**: REQ-* keys from intent → production → feedback

---

## Next Steps

This UX design document explores:
- ✅ How users interact with skills
- ✅ How agents guide workflows
- ✅ How marketplace enables composition
- ✅ How homeostasis creates self-correction
- ✅ How requirements refinement loop works

**Ready to implement?**

1. Validate this UX with stakeholders
2. Create first plugin: `@aisdlc/aisdlc-core`
3. Build proof-of-concept: Core + TDD skills
4. Test with real users (Sarah, David, Maria, James)
5. Iterate based on feedback

---

**"Excellence or nothing"** 🔥
