# UAT Stage - Design Document

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
| REQ-UAT-001 | Business Validation Tests | High | Sections 2, 3, 4 |
| REQ-UAT-002 | Sign-off Workflow | High | Sections 5, 6, 7 |

**Source**: [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) Section 8

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [UAT Test Case Design](#2-uat-test-case-design)
3. [Test Case Schema](#3-test-case-schema)
4. [Sign-off Data Structure](#4-sign-off-data-structure)
5. [Approval Workflow States](#5-approval-workflow-states)
6. [Audit Trail Format](#6-audit-trail-format)
7. [Integration with Release Gates](#7-integration-with-release-gates)
8. [Storage Design](#8-storage-design)
9. [Implementation Guidance](#9-implementation-guidance)
10. [Examples](#10-examples)

---

## 1. Executive Summary

### 1.1 Purpose

The UAT (User Acceptance Testing) Stage provides **business validation** by enabling non-technical stakeholders to verify that delivered functionality meets business needs. It includes structured test case management and formal sign-off workflow with complete audit trail.

### 1.2 Design Principles

1. **Business Language** - Test cases written in terminology stakeholders understand
2. **Requirement Traceability** - Every UAT test maps to REQ-* keys
3. **Formal Sign-off** - Explicit approval with audit trail
4. **Release Gating** - UAT approval required before production deployment
5. **Non-Technical Execution** - Tests executable by business users without coding knowledge
6. **Complete Audit Trail** - Track who approved what, when, and why

### 1.3 Key Design Decisions

| Decision | Rationale | Requirement |
|----------|-----------|-------------|
| Markdown + YAML format | Human-readable, version-controllable, parseable | REQ-UAT-001 |
| BDD Given/When/Then style | Non-technical, unambiguous, business-focused | REQ-UAT-001 |
| Multi-approver support | Different stakeholders validate different aspects | REQ-UAT-002 |
| Approval state machine | Clear workflow, prevents ambiguity | REQ-UAT-002 |
| Timestamped audit trail | Compliance, traceability, debugging | REQ-UAT-002 |
| Release gate integration | Ensures business approval before deployment | REQ-UAT-002 |

### 1.4 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    System Test Stage (Complete)                  │
│  All BDD scenarios passed, system test sign-off                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       UAT Agent Triggered                        │
│  1. Read requirements (REQ-*)                                   │
│  2. Generate UAT test cases (business language)                 │
│  3. Create UAT manifest (links tests to requirements)           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Business User Execution                       │
│  Stakeholders execute tests manually or via tool                │
│  Record results: Pass, Fail, Blocked                            │
│  Add notes and observations                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Sign-off Workflow                          │
│  State: draft → in_review → approved/rejected                   │
│  Multiple approvers (Product Owner, Business Stakeholders)      │
│  Comments and rationale recorded                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Release Gate                              │
│  Check: All UAT tests passed? Sign-off approved?                │
│  APPROVED → Allow deployment to production                      │
│  REJECTED → Block deployment, create feedback intent            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. UAT Test Case Design

### 2.1 Test Case Philosophy

**Implements**: REQ-UAT-001

UAT tests validate **business value**, not technical implementation. They must be:

- **Non-technical** - Written in business domain language
- **Scenario-based** - Describe realistic user workflows
- **Traceable** - Explicitly map to requirements
- **Executable** - Can be run by non-developers
- **Unambiguous** - Clear pass/fail criteria

### 2.2 Test Case Structure

UAT tests follow a simplified BDD (Behavior-Driven Development) structure using **Given/When/Then**, but written in pure business language without technical implementation details.

```markdown
# UAT Test Case Template

**Test ID**: UAT-{FEATURE}-{NUMBER}
**Title**: [Brief description in business terms]
**Requirement**: REQ-F-{FEATURE}-{NUMBER}
**Priority**: [Critical | High | Medium | Low]
**Test Type**: [Functional | Integration | End-to-End]

## Business Context

[Why this test matters to the business]

## Scenario

**Given** [Initial business state]
**When** [Business action is performed]
**Then** [Expected business outcome]

## Test Steps

1. [Action in business terms]
2. [Action in business terms]
3. [Action in business terms]

## Expected Results

- [ ] [Observable business outcome 1]
- [ ] [Observable business outcome 2]
- [ ] [Observable business outcome 3]

## Validation Criteria

**Pass Criteria**: [What must be true to pass]
**Fail Criteria**: [What indicates failure]

## Test Data

[Any business data needed to execute test]

## Notes

[Additional context, constraints, dependencies]
```

### 2.3 Business Language Guidelines

**DO use**:
- "Customer completes checkout"
- "Invoice is generated and sent to customer"
- "Order status changes to 'Shipped'"
- "User receives confirmation email"

**DON'T use**:
- "POST request to /api/checkout endpoint"
- "Database record inserted into orders table"
- "HTTP 201 response returned"
- "Kafka event published to order-events topic"

### 2.4 Test Case Generation from Requirements

**Process**: UAT Agent generates UAT tests from requirements

```python
# uat_generator.py

from typing import List, Dict
import re

def generate_uat_test(requirement: Dict) -> Dict:
    """
    Generate UAT test case from requirement.

    Args:
        requirement: Requirement document (REQ-F-*, REQ-NFR-*)

    Returns:
        UAT test case structure

    Example:
        Input: REQ-F-AUTH-001 "User login with email/password"
        Output: UAT-AUTH-001 test case with scenarios
    """
    req_id = requirement['id']
    req_title = requirement['title']
    acceptance_criteria = requirement.get('acceptance_criteria', [])

    # Extract feature name from REQ-F-{FEATURE}-{NUMBER}
    match = re.match(r'REQ-F-([A-Z]+)-(\d+)', req_id)
    if match:
        feature = match.group(1)
        number = match.group(2)
        test_id = f"UAT-{feature}-{number}"
    else:
        test_id = f"UAT-GENERIC-001"

    # Convert technical acceptance criteria to business scenarios
    scenarios = []
    for ac in acceptance_criteria:
        scenario = _convert_to_business_language(ac)
        scenarios.append(scenario)

    uat_test = {
        'test_id': test_id,
        'title': req_title,
        'requirement': req_id,
        'priority': requirement.get('priority', 'Medium'),
        'test_type': _infer_test_type(requirement),
        'business_context': requirement.get('description', ''),
        'scenarios': scenarios,
        'test_data': _extract_test_data(requirement),
        'validation_criteria': _generate_validation_criteria(acceptance_criteria)
    }

    return uat_test

def _convert_to_business_language(acceptance_criterion: str) -> Dict:
    """
    Convert technical acceptance criterion to business scenario.

    Example:
        Input: "Login endpoint returns 200 with JWT token"
        Output: {
            'given': 'I am a registered user with valid credentials',
            'when': 'I log in with my email and password',
            'then': 'I am successfully authenticated and can access my account'
        }
    """
    # Use LLM to translate technical → business language
    # This is a placeholder for the actual LLM prompt

    # Simple heuristic-based translation (real implementation uses LLM)
    if 'login' in acceptance_criterion.lower():
        return {
            'given': 'I am a registered user',
            'when': 'I log in with valid credentials',
            'then': 'I can access my account'
        }

    # Default fallback
    return {
        'given': 'Initial state',
        'when': 'Action is performed',
        'then': 'Expected outcome occurs'
    }

def _infer_test_type(requirement: Dict) -> str:
    """Infer test type from requirement"""
    if 'integration' in requirement.get('description', '').lower():
        return 'Integration'
    elif 'workflow' in requirement.get('description', '').lower():
        return 'End-to-End'
    else:
        return 'Functional'

def _extract_test_data(requirement: Dict) -> List[Dict]:
    """Extract test data from requirement examples"""
    # Parse examples section for test data
    examples = requirement.get('examples', [])

    test_data = []
    for example in examples:
        test_data.append({
            'description': example.get('description', ''),
            'input': example.get('input', {}),
            'expected_output': example.get('expected_output', {})
        })

    return test_data

def _generate_validation_criteria(acceptance_criteria: List[str]) -> Dict:
    """Generate pass/fail criteria from acceptance criteria"""
    return {
        'pass_criteria': [
            f"All acceptance criteria met: {', '.join(acceptance_criteria)}"
        ],
        'fail_criteria': [
            "Any acceptance criterion not met",
            "Unexpected errors or behavior observed",
            "Business outcome does not match expectation"
        ]
    }
```

---

## 3. Test Case Schema

### 3.1 UAT Test Case YAML Schema

```yaml
# File: .ai-workspace/uat/tests/UAT-{FEATURE}-{NUMBER}.yml

uat_test:
  # Identification
  test_id: "UAT-AUTH-001"
  title: "User can log in with email and password"
  requirement: "REQ-F-AUTH-001"

  # Classification
  priority: "High"
  test_type: "Functional"  # Functional | Integration | End-to-End

  # Business context
  business_context: |
    Customers need to securely access their accounts to view orders,
    update preferences, and make purchases. Login is the gateway to
    all authenticated features.

  # Scenarios (BDD style in business language)
  scenarios:
    - scenario_id: "SCENARIO-001"
      title: "Successful login with valid credentials"

      given: "I am a registered customer with email 'customer@example.com'"
      when: "I enter my email and correct password and click 'Login'"
      then: "I am logged in and see my account dashboard"

      test_steps:
        - step: 1
          action: "Navigate to login page"
          expected: "Login form is displayed"

        - step: 2
          action: "Enter email 'customer@example.com'"
          expected: "Email field accepts input"

        - step: 3
          action: "Enter password"
          expected: "Password is masked (shown as dots)"

        - step: 4
          action: "Click 'Login' button"
          expected: "System processes login"

        - step: 5
          action: "Observe result"
          expected: "Dashboard appears with personalized greeting"

      expected_results:
        - "Welcome message displays my name"
        - "Navigation shows 'My Account' option"
        - "I can access account features (orders, settings, etc.)"

      validation_criteria:
        pass: "User successfully logged in and can access account"
        fail: "Login fails, error message shown, or account inaccessible"

    - scenario_id: "SCENARIO-002"
      title: "Login fails with incorrect password"

      given: "I am a registered customer"
      when: "I enter my email with an incorrect password and click 'Login'"
      then: "I see an error message and remain on the login page"

      test_steps:
        - step: 1
          action: "Navigate to login page"
          expected: "Login form is displayed"

        - step: 2
          action: "Enter valid email"
          expected: "Email field accepts input"

        - step: 3
          action: "Enter incorrect password"
          expected: "Password field accepts input"

        - step: 4
          action: "Click 'Login' button"
          expected: "System processes login attempt"

        - step: 5
          action: "Observe result"
          expected: "Error message appears"

      expected_results:
        - "Error message: 'Invalid email or password'"
        - "I remain on the login page"
        - "Password field is cleared"
        - "Email field retains my input"

      validation_criteria:
        pass: "Login correctly rejected with appropriate error message"
        fail: "Login succeeds incorrectly, or no error message shown"

  # Test data
  test_data:
    - description: "Valid customer account"
      email: "customer@example.com"
      password: "ValidPassword123!"
      expected_outcome: "Login succeeds"

    - description: "Valid email, wrong password"
      email: "customer@example.com"
      password: "WrongPassword"
      expected_outcome: "Login fails with error"

    - description: "Non-existent email"
      email: "nonexistent@example.com"
      password: "AnyPassword"
      expected_outcome: "Login fails with error"

  # Execution tracking
  execution:
    status: "not_started"  # not_started | in_progress | passed | failed | blocked
    executed_by: null
    executed_at: null
    duration_minutes: null
    result: null
    notes: null
    screenshots: []
    issues: []

  # Metadata
  created_at: "2025-12-03T10:00:00Z"
  created_by: "uat_agent"
  last_updated: "2025-12-03T10:00:00Z"
  version: "1.0"
```

### 3.2 UAT Manifest Schema

The UAT Manifest provides an overview of all UAT tests for a release.

```yaml
# File: .ai-workspace/uat/manifests/UAT_MANIFEST_{RELEASE_ID}.yml

uat_manifest:
  # Release identification
  release_id: "v2.3.0"
  intent_id: "INT-20251203-001"
  release_date: "2025-12-15"

  # Summary
  summary:
    total_tests: 12
    critical: 3
    high: 5
    medium: 3
    low: 1

    status:
      not_started: 2
      in_progress: 3
      passed: 6
      failed: 1
      blocked: 0

  # Test cases
  tests:
    - test_id: "UAT-AUTH-001"
      title: "User can log in with email and password"
      requirement: "REQ-F-AUTH-001"
      priority: "High"
      status: "passed"
      executed_by: "jane.doe@company.com"
      executed_at: "2025-12-03T14:30:00Z"

    - test_id: "UAT-AUTH-002"
      title: "User can reset forgotten password"
      requirement: "REQ-F-AUTH-002"
      priority: "High"
      status: "passed"
      executed_by: "jane.doe@company.com"
      executed_at: "2025-12-03T14:45:00Z"

    - test_id: "UAT-CHECKOUT-001"
      title: "Customer can complete purchase"
      requirement: "REQ-F-CHECKOUT-001"
      priority: "Critical"
      status: "failed"
      executed_by: "john.smith@company.com"
      executed_at: "2025-12-03T15:00:00Z"
      failure_reason: "Payment processing fails with Visa cards"

  # Requirements coverage
  requirements_coverage:
    total_requirements: 10
    covered_by_uat: 10
    coverage_percentage: 100

    uncovered_requirements: []

    covered_requirements:
      - req_id: "REQ-F-AUTH-001"
        uat_tests: ["UAT-AUTH-001"]
      - req_id: "REQ-F-AUTH-002"
        uat_tests: ["UAT-AUTH-002"]
      - req_id: "REQ-F-CHECKOUT-001"
        uat_tests: ["UAT-CHECKOUT-001", "UAT-CHECKOUT-002"]

  # Metadata
  created_at: "2025-12-03T10:00:00Z"
  last_updated: "2025-12-03T15:30:00Z"
```

---

## 4. Sign-off Data Structure

### 4.1 Sign-off Record Schema

**Implements**: REQ-UAT-002

```yaml
# File: .ai-workspace/uat/signoffs/SIGNOFF_{RELEASE_ID}.yml

uat_signoff:
  # Release identification
  release_id: "v2.3.0"
  intent_id: "INT-20251203-001"
  uat_manifest: "UAT_MANIFEST_v2.3.0.yml"

  # Sign-off state
  status: "approved"  # draft | in_review | approved | rejected | conditionally_approved

  # Approvers (multiple stakeholders)
  approvers:
    - role: "Product Owner"
      name: "Jane Doe"
      email: "jane.doe@company.com"
      decision: "approved"
      timestamp: "2025-12-03T16:00:00Z"
      comment: |
        All critical and high priority tests passed. The failed payment
        test is tracked in JIRA-4567 and will be fixed in next patch release.
        Business impact is acceptable for launch.

      reviewed_tests:
        - "UAT-AUTH-001"
        - "UAT-AUTH-002"
        - "UAT-CHECKOUT-001"

    - role: "Business Stakeholder (Finance)"
      name: "John Smith"
      email: "john.smith@company.com"
      decision: "conditionally_approved"
      timestamp: "2025-12-03T16:15:00Z"
      comment: |
        Approved with condition that payment processing issue is fixed
        before marketing campaign launch on Dec 20th.

      conditions:
        - condition: "Fix Visa payment processing (JIRA-4567)"
          deadline: "2025-12-20"
          tracked_in: "JIRA-4567"

      reviewed_tests:
        - "UAT-CHECKOUT-001"
        - "UAT-PAYMENT-001"

    - role: "Business Stakeholder (Customer Service)"
      name: "Sarah Wilson"
      email: "sarah.wilson@company.com"
      decision: "approved"
      timestamp: "2025-12-03T16:30:00Z"
      comment: "Password reset flow works perfectly. Customer service ready."

      reviewed_tests:
        - "UAT-AUTH-002"

  # Overall decision
  final_decision:
    status: "approved"
    decided_at: "2025-12-03T16:30:00Z"
    decided_by: "jane.doe@company.com"  # Final authority (Product Owner)
    rationale: |
      All three stakeholders reviewed and approved. One conditional approval
      with acceptable risk. Payment issue tracked and will not block initial
      release. Release approved for production deployment.

  # Test summary at sign-off time
  test_summary:
    total_tests: 12
    passed: 11
    failed: 1
    blocked: 0
    pass_rate: 91.7

    critical_tests:
      total: 3
      passed: 2
      failed: 1

    acceptance_criteria_met: 95.0  # Percentage of acceptance criteria passed

  # Release gate status
  release_gate:
    status: "open"  # open | closed
    opened_at: "2025-12-03T16:30:00Z"
    opened_by: "jane.doe@company.com"
    deployment_authorized: true

  # Audit trail
  audit_trail:
    - event: "signoff_created"
      timestamp: "2025-12-03T15:00:00Z"
      actor: "uat_agent"
      details: "Sign-off workflow initiated"

    - event: "approver_assigned"
      timestamp: "2025-12-03T15:00:00Z"
      actor: "uat_agent"
      details: "Assigned 3 approvers: Product Owner, Finance, Customer Service"

    - event: "review_started"
      timestamp: "2025-12-03T15:30:00Z"
      actor: "jane.doe@company.com"
      details: "Product Owner started review"

    - event: "approval_received"
      timestamp: "2025-12-03T16:00:00Z"
      actor: "jane.doe@company.com"
      details: "Product Owner approved"

    - event: "conditional_approval_received"
      timestamp: "2025-12-03T16:15:00Z"
      actor: "john.smith@company.com"
      details: "Finance conditionally approved"

    - event: "approval_received"
      timestamp: "2025-12-03T16:30:00Z"
      actor: "sarah.wilson@company.com"
      details: "Customer Service approved"

    - event: "final_decision_made"
      timestamp: "2025-12-03T16:30:00Z"
      actor: "jane.doe@company.com"
      details: "Final approval granted, release gate opened"

  # Metadata
  created_at: "2025-12-03T15:00:00Z"
  last_updated: "2025-12-03T16:30:00Z"
  version: "1.0"
```

### 4.2 Approver Configuration

```yaml
# File: .ai-workspace/uat/config/approver_config.yml

approver_config:
  # Define who can approve UAT sign-offs

  roles:
    - role: "Product Owner"
      required: true  # Must approve
      authority: "final"  # Can make final decision
      responsibilities:
        - "Overall business value validation"
        - "Feature completeness review"
        - "Final release decision"

    - role: "Business Stakeholder (Finance)"
      required: false  # Optional
      authority: "advisory"  # Can provide input, not final decision
      responsibilities:
        - "Financial calculations validation"
        - "Payment processing review"
        - "Compliance requirements"

    - role: "Business Stakeholder (Customer Service)"
      required: false
      authority: "advisory"
      responsibilities:
        - "Customer-facing workflows"
        - "Error messaging clarity"
        - "Support readiness"

    - role: "Business Stakeholder (Legal)"
      required: true  # Must approve if legal requirements involved
      authority: "veto"  # Can block release
      responsibilities:
        - "Compliance validation"
        - "Privacy requirements"
        - "Terms of service"

      triggers:
        - "requirement_type: compliance"
        - "requirement_type: privacy"
        - "requirement_type: legal"

  # Approval thresholds
  thresholds:
    minimum_approvers: 1  # At least Product Owner

    critical_priority:
      minimum_approvers: 2
      required_roles: ["Product Owner", "Business Stakeholder"]

    compliance_related:
      minimum_approvers: 2
      required_roles: ["Product Owner", "Business Stakeholder (Legal)"]

  # Decision rules
  decision_rules:
    # All "required" approvers must approve
    all_required_approved: true

    # Any "veto" authority can block
    veto_blocks_release: true

    # Conditional approvals allowed if documented
    allow_conditional_approval: true
```

---

## 5. Approval Workflow States

### 5.1 State Machine

```
┌─────────┐
│  draft  │  (Sign-off created, awaiting review)
└────┬────┘
     │
     ▼
┌──────────┐
│in_review │  (Approvers reviewing tests)
└────┬─────┘
     │
     ├──────────┐
     │          │
     ▼          ▼
┌─────────┐  ┌──────────────────────┐
│approved │  │conditionally_approved│
└────┬────┘  └──────────┬───────────┘
     │                  │
     └───────┬──────────┘
             │
             ▼
     ┌──────────────┐
     │release_gate  │  (Deployment authorized)
     │    open      │
     └──────────────┘

     ┌─────────┐
     │rejected │  (Blocked, needs fixes)
     └─────────┘
```

### 5.2 State Definitions

```python
# uat_workflow.py

from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

class SignoffStatus(Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    REJECTED = "rejected"

class ApproverDecision(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    REJECTED = "rejected"

@dataclass
class Approver:
    """Approver for UAT sign-off"""
    role: str
    name: str
    email: str
    decision: ApproverDecision
    timestamp: Optional[datetime]
    comment: str
    conditions: List[Dict] = None
    reviewed_tests: List[str] = None

@dataclass
class SignoffRecord:
    """UAT sign-off record"""
    release_id: str
    intent_id: str
    status: SignoffStatus
    approvers: List[Approver]
    final_decision: Dict
    test_summary: Dict
    release_gate: Dict
    audit_trail: List[Dict]
    created_at: datetime
    last_updated: datetime

class UATSignoffWorkflow:
    """Manages UAT sign-off workflow"""

    def __init__(self, approver_config: dict):
        self.config = approver_config

    def create_signoff(
        self,
        release_id: str,
        intent_id: str,
        uat_manifest: Dict
    ) -> SignoffRecord:
        """
        Create new UAT sign-off record.

        Args:
            release_id: Release version (e.g., "v2.3.0")
            intent_id: Intent that triggered this release
            uat_manifest: UAT manifest with test results

        Returns:
            Sign-off record in draft state
        """
        # Determine required approvers based on test content
        required_approvers = self._determine_approvers(uat_manifest)

        approvers = []
        for approver_role in required_approvers:
            # Lookup approver details from config
            approver_info = self._get_approver_info(approver_role)

            approvers.append(Approver(
                role=approver_role,
                name=approver_info['name'],
                email=approver_info['email'],
                decision=ApproverDecision.PENDING,
                timestamp=None,
                comment="",
                conditions=[],
                reviewed_tests=[]
            ))

        signoff = SignoffRecord(
            release_id=release_id,
            intent_id=intent_id,
            status=SignoffStatus.DRAFT,
            approvers=approvers,
            final_decision={},
            test_summary=self._extract_test_summary(uat_manifest),
            release_gate={'status': 'closed'},
            audit_trail=[{
                'event': 'signoff_created',
                'timestamp': datetime.now().isoformat(),
                'actor': 'uat_agent',
                'details': 'Sign-off workflow initiated'
            }],
            created_at=datetime.now(),
            last_updated=datetime.now()
        )

        return signoff

    def submit_approval(
        self,
        signoff: SignoffRecord,
        approver_email: str,
        decision: ApproverDecision,
        comment: str,
        conditions: List[Dict] = None
    ) -> SignoffRecord:
        """
        Submit approver decision.

        Args:
            signoff: Current sign-off record
            approver_email: Email of approver
            decision: Approval decision
            comment: Rationale for decision
            conditions: Optional conditions (for conditional approval)

        Returns:
            Updated sign-off record
        """
        # Find approver
        approver = None
        for a in signoff.approvers:
            if a.email == approver_email:
                approver = a
                break

        if not approver:
            raise ValueError(f"Approver {approver_email} not found")

        # Update approver decision
        approver.decision = decision
        approver.timestamp = datetime.now()
        approver.comment = comment
        if conditions:
            approver.conditions = conditions

        # Update status
        if signoff.status == SignoffStatus.DRAFT:
            signoff.status = SignoffStatus.IN_REVIEW

        # Log audit trail
        signoff.audit_trail.append({
            'event': f'{decision.value}_received',
            'timestamp': datetime.now().isoformat(),
            'actor': approver_email,
            'details': f"{approver.role} {decision.value}"
        })

        # Check if all approvers have decided
        if self._all_approvers_decided(signoff):
            final_status = self._determine_final_status(signoff)
            signoff.status = final_status

            if final_status == SignoffStatus.APPROVED:
                signoff.release_gate = {
                    'status': 'open',
                    'opened_at': datetime.now().isoformat(),
                    'opened_by': approver_email,
                    'deployment_authorized': True
                }

        signoff.last_updated = datetime.now()

        return signoff

    def _determine_approvers(self, uat_manifest: Dict) -> List[str]:
        """Determine required approvers based on manifest"""
        required = []

        # Always require Product Owner
        required.append("Product Owner")

        # Check if any compliance/legal requirements
        for test in uat_manifest.get('tests', []):
            requirement = test.get('requirement', '')
            if 'compliance' in requirement.lower() or 'legal' in requirement.lower():
                if "Business Stakeholder (Legal)" not in required:
                    required.append("Business Stakeholder (Legal)")

        # Add other stakeholders based on config
        # (In real implementation, use more sophisticated logic)

        return required

    def _all_approvers_decided(self, signoff: SignoffRecord) -> bool:
        """Check if all approvers have made a decision"""
        return all(
            a.decision != ApproverDecision.PENDING
            for a in signoff.approvers
        )

    def _determine_final_status(self, signoff: SignoffRecord) -> SignoffStatus:
        """Determine final status based on approver decisions"""
        # Check for rejections (veto authority)
        for approver in signoff.approvers:
            if approver.decision == ApproverDecision.REJECTED:
                role_config = self._get_role_config(approver.role)
                if role_config.get('authority') == 'veto':
                    return SignoffStatus.REJECTED

        # Check if all required approvers approved
        required_approved = True
        has_conditional = False

        for approver in signoff.approvers:
            role_config = self._get_role_config(approver.role)

            if role_config.get('required', False):
                if approver.decision == ApproverDecision.REJECTED:
                    return SignoffStatus.REJECTED
                elif approver.decision == ApproverDecision.CONDITIONALLY_APPROVED:
                    has_conditional = True
                elif approver.decision != ApproverDecision.APPROVED:
                    required_approved = False

        if not required_approved:
            return SignoffStatus.REJECTED

        if has_conditional:
            return SignoffStatus.CONDITIONALLY_APPROVED

        return SignoffStatus.APPROVED

    def _get_approver_info(self, role: str) -> Dict:
        """Get approver contact info from config"""
        # Lookup from approver database/config
        # Placeholder implementation
        return {
            'name': f'{role} User',
            'email': f'{role.lower().replace(" ", ".")}@company.com'
        }

    def _get_role_config(self, role: str) -> Dict:
        """Get role configuration"""
        for role_config in self.config['roles']:
            if role_config['role'] == role:
                return role_config
        return {}

    def _extract_test_summary(self, uat_manifest: Dict) -> Dict:
        """Extract test summary from manifest"""
        return uat_manifest.get('summary', {})
```

---

## 6. Audit Trail Format

### 6.1 Audit Event Types

**All UAT events must be logged for compliance and traceability.**

```yaml
# Audit event types

audit_events:
  # Test execution events
  - event_type: "test_created"
    description: "UAT test case created"
    required_fields: ["test_id", "requirement", "created_by"]

  - event_type: "test_executed"
    description: "UAT test executed"
    required_fields: ["test_id", "executed_by", "result"]

  - event_type: "test_passed"
    description: "UAT test passed"
    required_fields: ["test_id", "executed_by"]

  - event_type: "test_failed"
    description: "UAT test failed"
    required_fields: ["test_id", "executed_by", "failure_reason"]

  # Sign-off workflow events
  - event_type: "signoff_created"
    description: "Sign-off workflow initiated"
    required_fields: ["release_id", "created_by"]

  - event_type: "approver_assigned"
    description: "Approver assigned to sign-off"
    required_fields: ["approver_email", "role"]

  - event_type: "review_started"
    description: "Approver started review"
    required_fields: ["approver_email"]

  - event_type: "approval_received"
    description: "Approver approved"
    required_fields: ["approver_email", "comment"]

  - event_type: "conditional_approval_received"
    description: "Approver conditionally approved"
    required_fields: ["approver_email", "conditions"]

  - event_type: "rejection_received"
    description: "Approver rejected"
    required_fields: ["approver_email", "reason"]

  - event_type: "final_decision_made"
    description: "Final sign-off decision made"
    required_fields: ["decision", "decided_by"]

  # Release gate events
  - event_type: "release_gate_opened"
    description: "Release gate opened, deployment authorized"
    required_fields: ["release_id", "opened_by"]

  - event_type: "release_gate_closed"
    description: "Release gate closed, deployment blocked"
    required_fields: ["release_id", "reason"]
```

### 6.2 Audit Trail Storage

```yaml
# File: .ai-workspace/uat/audit/UAT_AUDIT_{RELEASE_ID}.yml

uat_audit_trail:
  release_id: "v2.3.0"

  events:
    - event_id: "EVT-001"
      event_type: "signoff_created"
      timestamp: "2025-12-03T15:00:00Z"
      actor: "uat_agent"
      actor_type: "system"
      details:
        release_id: "v2.3.0"
        intent_id: "INT-20251203-001"
        approvers_assigned: 3

      context:
        ip_address: null  # System event
        user_agent: "uat_agent/1.0"

    - event_id: "EVT-002"
      event_type: "test_executed"
      timestamp: "2025-12-03T14:30:00Z"
      actor: "jane.doe@company.com"
      actor_type: "human"
      details:
        test_id: "UAT-AUTH-001"
        result: "passed"
        duration_minutes: 5
        notes: "All steps executed successfully"

      context:
        ip_address: "192.168.1.100"
        user_agent: "Mozilla/5.0..."

    - event_id: "EVT-003"
      event_type: "approval_received"
      timestamp: "2025-12-03T16:00:00Z"
      actor: "jane.doe@company.com"
      actor_type: "human"
      details:
        role: "Product Owner"
        decision: "approved"
        comment: "All critical tests passed"
        reviewed_tests: ["UAT-AUTH-001", "UAT-AUTH-002"]

      context:
        ip_address: "192.168.1.100"
        user_agent: "Mozilla/5.0..."

    - event_id: "EVT-004"
      event_type: "release_gate_opened"
      timestamp: "2025-12-03T16:30:00Z"
      actor: "jane.doe@company.com"
      actor_type: "human"
      details:
        release_id: "v2.3.0"
        final_decision: "approved"
        deployment_authorized: true

      context:
        ip_address: "192.168.1.100"
        user_agent: "Mozilla/5.0..."

  # Summary statistics
  summary:
    total_events: 4
    events_by_type:
      signoff_created: 1
      test_executed: 1
      approval_received: 1
      release_gate_opened: 1

    actors:
      - email: "jane.doe@company.com"
        event_count: 3
      - actor: "uat_agent"
        event_count: 1

  # Metadata
  created_at: "2025-12-03T15:00:00Z"
  last_updated: "2025-12-03T16:30:00Z"
```

---

## 7. Integration with Release Gates

### 7.1 Release Gate Check

**Implements**: REQ-UAT-002

Before production deployment, the release gate checks UAT sign-off status.

```python
# release_gate.py

from typing import Dict, Optional
from enum import Enum

class ReleaseGateStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"

class ReleaseGateDecision(Enum):
    ALLOW = "allow"
    BLOCK = "block"

class ReleaseGate:
    """Release gate that checks UAT sign-off before deployment"""

    def check_gate(self, release_id: str) -> Dict:
        """
        Check if release gate is open for deployment.

        Args:
            release_id: Release version (e.g., "v2.3.0")

        Returns:
            Gate status with details
        """
        # Load UAT sign-off record
        signoff = self._load_signoff(release_id)

        if not signoff:
            return {
                'decision': ReleaseGateDecision.BLOCK,
                'reason': 'No UAT sign-off found',
                'status': ReleaseGateStatus.CLOSED,
                'deployment_authorized': False
            }

        # Check sign-off status
        if signoff['status'] not in ['approved', 'conditionally_approved']:
            return {
                'decision': ReleaseGateDecision.BLOCK,
                'reason': f'UAT sign-off status: {signoff["status"]}',
                'status': ReleaseGateStatus.CLOSED,
                'deployment_authorized': False,
                'signoff_status': signoff['status']
            }

        # Check test pass rate
        test_summary = signoff.get('test_summary', {})
        pass_rate = test_summary.get('pass_rate', 0)

        if pass_rate < 90:  # Configurable threshold
            return {
                'decision': ReleaseGateDecision.BLOCK,
                'reason': f'Test pass rate too low: {pass_rate}% (required: 90%)',
                'status': ReleaseGateStatus.CLOSED,
                'deployment_authorized': False,
                'pass_rate': pass_rate
            }

        # Check critical tests
        critical_tests = test_summary.get('critical_tests', {})
        if critical_tests.get('failed', 0) > 0:
            return {
                'decision': ReleaseGateDecision.BLOCK,
                'reason': f'{critical_tests["failed"]} critical test(s) failed',
                'status': ReleaseGateStatus.CLOSED,
                'deployment_authorized': False,
                'critical_failures': critical_tests['failed']
            }

        # Check if release gate explicitly opened
        release_gate = signoff.get('release_gate', {})
        if release_gate.get('status') != 'open':
            return {
                'decision': ReleaseGateDecision.BLOCK,
                'reason': 'Release gate not explicitly opened',
                'status': ReleaseGateStatus.CLOSED,
                'deployment_authorized': False
            }

        # All checks passed
        return {
            'decision': ReleaseGateDecision.ALLOW,
            'reason': 'All UAT checks passed',
            'status': ReleaseGateStatus.OPEN,
            'deployment_authorized': True,
            'signoff_status': signoff['status'],
            'pass_rate': pass_rate,
            'approved_by': signoff['final_decision'].get('decided_by'),
            'approved_at': release_gate.get('opened_at')
        }

    def _load_signoff(self, release_id: str) -> Optional[Dict]:
        """Load UAT sign-off record for release"""
        # Load from .ai-workspace/uat/signoffs/SIGNOFF_{release_id}.yml
        # Placeholder implementation
        return None
```

### 7.2 CI/CD Integration

```yaml
# Example: GitHub Actions workflow

name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  check-uat-gate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Extract release version
        id: version
        run: echo "RELEASE_VERSION=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT

      - name: Check UAT Release Gate
        id: gate
        run: |
          python .ai-workspace/scripts/check_release_gate.py \
            --release-id ${{ steps.version.outputs.RELEASE_VERSION }}

      - name: Block if gate closed
        if: steps.gate.outputs.decision == 'BLOCK'
        run: |
          echo "❌ Release gate CLOSED"
          echo "Reason: ${{ steps.gate.outputs.reason }}"
          exit 1

      - name: Proceed if gate open
        if: steps.gate.outputs.decision == 'ALLOW'
        run: |
          echo "✅ Release gate OPEN"
          echo "Deployment authorized by: ${{ steps.gate.outputs.approved_by }}"

  deploy:
    needs: check-uat-gate
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: |
          # Deployment commands here
          echo "Deploying to production..."
```

---

## 8. Storage Design

### 8.1 Directory Structure

```
.ai-workspace/
└── uat/
    ├── tests/                        # Individual UAT test cases
    │   ├── UAT-AUTH-001.yml
    │   ├── UAT-AUTH-002.yml
    │   ├── UAT-CHECKOUT-001.yml
    │   └── ...
    │
    ├── manifests/                    # UAT manifests per release
    │   ├── UAT_MANIFEST_v2.3.0.yml
    │   ├── UAT_MANIFEST_v2.2.0.yml
    │   └── ...
    │
    ├── signoffs/                     # Sign-off records per release
    │   ├── SIGNOFF_v2.3.0.yml
    │   ├── SIGNOFF_v2.2.0.yml
    │   └── ...
    │
    ├── audit/                        # Audit trails per release
    │   ├── UAT_AUDIT_v2.3.0.yml
    │   ├── UAT_AUDIT_v2.2.0.yml
    │   └── ...
    │
    ├── config/                       # UAT configuration
    │   ├── approver_config.yml      # Approver roles and rules
    │   └── gate_config.yml          # Release gate thresholds
    │
    └── templates/                    # UAT test templates
        ├── functional_test_template.md
        ├── integration_test_template.md
        └── e2e_test_template.md
```

### 8.2 File Naming Conventions

```yaml
# UAT Test Cases
pattern: "UAT-{FEATURE}-{NUMBER}.yml"
examples:
  - "UAT-AUTH-001.yml"
  - "UAT-CHECKOUT-002.yml"
  - "UAT-PAYMENT-003.yml"

# UAT Manifests
pattern: "UAT_MANIFEST_{RELEASE_ID}.yml"
examples:
  - "UAT_MANIFEST_v2.3.0.yml"
  - "UAT_MANIFEST_v2.2.1.yml"

# Sign-off Records
pattern: "SIGNOFF_{RELEASE_ID}.yml"
examples:
  - "SIGNOFF_v2.3.0.yml"
  - "SIGNOFF_v2.2.1.yml"

# Audit Trails
pattern: "UAT_AUDIT_{RELEASE_ID}.yml"
examples:
  - "UAT_AUDIT_v2.3.0.yml"
  - "UAT_AUDIT_v2.2.1.yml"
```

---

## 9. Implementation Guidance

### 9.1 Phase 1: UAT Test Generation (Week 1)

**Goal**: Generate UAT tests from requirements

**Tasks**:
1. Implement UAT test generator
2. Create test case templates
3. Implement requirement → business language translation (LLM-based)
4. Generate UAT manifest
5. Review and refine generated tests

**Deliverables**:
- `uat_generator.py`
- UAT test templates
- Generated UAT tests for existing requirements
- UAT manifest

### 9.2 Phase 2: Test Execution Tracking (Week 2)

**Goal**: Enable business users to execute and record test results

**Tasks**:
1. Create test execution UI (simple web form or CLI)
2. Implement result recording (pass/fail/blocked)
3. Add screenshot/evidence attachment
4. Update test status in real-time
5. Generate test summary reports

**Deliverables**:
- Test execution interface
- Result recording system
- Test summary generator
- User documentation

### 9.3 Phase 3: Sign-off Workflow (Week 3)

**Goal**: Implement formal sign-off with multiple approvers

**Tasks**:
1. Implement sign-off workflow state machine
2. Create approver assignment logic
3. Build approval submission interface
4. Implement decision aggregation
5. Generate sign-off reports

**Deliverables**:
- `uat_workflow.py`
- Approver configuration
- Approval interface
- Sign-off reports

### 9.4 Phase 4: Release Gate Integration (Week 4)

**Goal**: Integrate UAT with CI/CD pipeline

**Tasks**:
1. Implement release gate checker
2. Integrate with CI/CD (GitHub Actions, GitLab CI, etc.)
3. Add deployment authorization logic
4. Create gate status dashboard
5. Test gate enforcement

**Deliverables**:
- `release_gate.py`
- CI/CD integration scripts
- Gate status dashboard
- Deployment documentation

### 9.5 Phase 5: Audit Trail & Compliance (Week 5)

**Goal**: Complete audit trail and compliance reporting

**Tasks**:
1. Implement audit event logging
2. Create audit trail storage
3. Build compliance reports
4. Test audit completeness
5. Create compliance documentation

**Deliverables**:
- Audit logging system
- Audit trail storage
- Compliance reports
- Audit documentation

### 9.6 Testing Strategy

**Unit Tests**:
- UAT test generation logic
- Sign-off workflow state transitions
- Approval decision aggregation
- Release gate checks

**Integration Tests**:
- Requirement → UAT test generation
- Test execution → Sign-off workflow
- Sign-off → Release gate
- Audit trail completeness

**End-to-End Tests**:
- Complete UAT workflow (generation → execution → sign-off → deployment)
- Multi-approver scenarios
- Conditional approval handling
- Release gate enforcement

**User Acceptance Tests**:
- Business users can execute UAT tests
- Approvers can review and approve
- Audit trail is complete and traceable

---

## 10. Examples

### 10.1 Complete UAT Workflow Example

#### Step 1: Generate UAT Test from Requirement

**Input**: REQ-F-AUTH-001

```yaml
requirement:
  id: "REQ-F-AUTH-001"
  title: "User login with email and password"
  description: |
    Users must be able to log in using their email address and password.
    Login should be secure, fast, and provide clear feedback on errors.

  acceptance_criteria:
    - "AC-001: User can log in with valid email and password"
    - "AC-002: Login fails with incorrect password"
    - "AC-003: Login response < 500ms (P95)"
    - "AC-004: Password is hashed securely"
    - "AC-005: Failed login attempts are logged"
```

**Output**: UAT-AUTH-001.yml (generated by UAT Agent)

```yaml
uat_test:
  test_id: "UAT-AUTH-001"
  title: "User can log in with email and password"
  requirement: "REQ-F-AUTH-001"
  priority: "High"
  test_type: "Functional"

  scenarios:
    - scenario_id: "SCENARIO-001"
      title: "Successful login with valid credentials"
      given: "I am a registered customer"
      when: "I log in with my correct email and password"
      then: "I am logged in and can access my account"

      test_steps:
        - step: 1
          action: "Go to login page"
          expected: "Login form appears"
        - step: 2
          action: "Enter email 'customer@example.com'"
          expected: "Email field accepts input"
        - step: 3
          action: "Enter correct password"
          expected: "Password is masked"
        - step: 4
          action: "Click 'Login' button"
          expected: "System processes login"
        - step: 5
          action: "Observe result"
          expected: "Dashboard appears with my name"

  execution:
    status: "not_started"
```

#### Step 2: Business User Executes Test

**Executed by**: jane.doe@company.com (Product Owner)

```yaml
execution:
  status: "passed"
  executed_by: "jane.doe@company.com"
  executed_at: "2025-12-03T14:30:00Z"
  duration_minutes: 5
  result: "All steps executed successfully. Login works perfectly."
  screenshots:
    - "login_page.png"
    - "dashboard_after_login.png"
  notes: "Password masking works well. Response was very fast."
```

#### Step 3: Generate UAT Manifest

```yaml
uat_manifest:
  release_id: "v2.3.0"

  summary:
    total_tests: 12
    passed: 11
    failed: 1
    pass_rate: 91.7

  tests:
    - test_id: "UAT-AUTH-001"
      status: "passed"
      executed_by: "jane.doe@company.com"
    # ... more tests
```

#### Step 4: Create Sign-off Workflow

```yaml
uat_signoff:
  release_id: "v2.3.0"
  status: "draft"

  approvers:
    - role: "Product Owner"
      name: "Jane Doe"
      email: "jane.doe@company.com"
      decision: "pending"

    - role: "Business Stakeholder (Finance)"
      name: "John Smith"
      email: "john.smith@company.com"
      decision: "pending"
```

#### Step 5: Approvers Review and Approve

**Product Owner Approval**:

```yaml
approvers:
  - role: "Product Owner"
    name: "Jane Doe"
    email: "jane.doe@company.com"
    decision: "approved"
    timestamp: "2025-12-03T16:00:00Z"
    comment: "All critical tests passed. Ready for production."
```

**Finance Stakeholder Approval**:

```yaml
approvers:
  - role: "Business Stakeholder (Finance)"
    name: "John Smith"
    email: "john.smith@company.com"
    decision: "approved"
    timestamp: "2025-12-03T16:15:00Z"
    comment: "Payment processing validated. Approved."
```

#### Step 6: Final Decision and Gate Opening

```yaml
uat_signoff:
  status: "approved"

  final_decision:
    status: "approved"
    decided_at: "2025-12-03T16:15:00Z"
    decided_by: "jane.doe@company.com"
    rationale: "All approvers approved. Release authorized."

  release_gate:
    status: "open"
    opened_at: "2025-12-03T16:15:00Z"
    deployment_authorized: true
```

#### Step 7: CI/CD Checks Release Gate

```bash
$ python check_release_gate.py --release-id v2.3.0

✅ Release gate OPEN
Decision: ALLOW
Reason: All UAT checks passed
Pass rate: 91.7%
Approved by: jane.doe@company.com
Approved at: 2025-12-03T16:15:00Z

Deployment authorized. Proceeding...
```

#### Step 8: Production Deployment

```bash
$ deploy.sh v2.3.0

✅ UAT sign-off verified
✅ Release gate open
🚀 Deploying v2.3.0 to production...
✅ Deployment successful
```

### 10.2 Conditional Approval Example

```yaml
approvers:
  - role: "Business Stakeholder (Finance)"
    decision: "conditionally_approved"
    timestamp: "2025-12-03T16:00:00Z"
    comment: "Approved with condition: payment fix must be deployed before marketing launch"

    conditions:
      - condition: "Fix Visa payment processing (JIRA-4567)"
        deadline: "2025-12-20"
        tracked_in: "JIRA-4567"
        criticality: "high"
```

**Result**: Sign-off status = "conditionally_approved"

Release can proceed to production, but tracking item created for condition fulfillment.

### 10.3 Rejection Example

```yaml
approvers:
  - role: "Business Stakeholder (Legal)"
    decision: "rejected"
    timestamp: "2025-12-03T16:00:00Z"
    comment: |
      REJECTED: Privacy policy update not reflected in UI.
      Cannot approve until GDPR compliance requirement addressed.

    blocking_issues:
      - issue: "Privacy policy not displayed during signup"
        requirement: "REQ-COMPLIANCE-001"
        severity: "critical"
```

**Result**:
- Sign-off status = "rejected"
- Release gate = "closed"
- Deployment blocked
- Feedback intent generated → Returns to Requirements stage

---

## ADR References

- **ADR-005**: Iterative Refinement Feedback Loops (UAT → upstream feedback)

---

## Implementation Checklist

- [ ] UAT test case template created
- [ ] UAT test generator implemented
- [ ] Business language translation (LLM integration)
- [ ] UAT manifest generator
- [ ] Test execution interface
- [ ] Result recording system
- [ ] Sign-off workflow state machine
- [ ] Multi-approver support
- [ ] Approval decision aggregation
- [ ] Conditional approval handling
- [ ] Release gate checker
- [ ] CI/CD integration (GitHub Actions, GitLab CI)
- [ ] Audit event logging
- [ ] Audit trail storage
- [ ] Compliance reporting
- [ ] Unit tests (90%+ coverage)
- [ ] Integration tests
- [ ] End-to-end tests
- [ ] User acceptance tests
- [ ] Documentation complete
- [ ] User guides for business stakeholders
- [ ] Architecture review approved
- [ ] Security review approved (sign-off authorization)

---

**Last Updated**: 2025-12-03
**Owned By**: Design Agent (UAT Stage)
