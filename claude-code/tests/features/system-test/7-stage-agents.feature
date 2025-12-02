# Feature: 7-Stage AISDLC Agents
# Validates: REQ-F-CMD-002 (Persona Management via Agents)
# Stage: System Test (Stage 5)

@system-test @agents @REQ-F-CMD-002
Feature: 7-Stage AISDLC Agents
  As a developer following the AI SDLC methodology
  I want specialized agents for each SDLC stage
  So that I receive expert guidance throughout the development lifecycle

  Background:
    Given the AISDLC methodology plugin is installed
    And a valid project workspace exists

  # ===========================================================================
  # Stage 1: Requirements Agent
  # ===========================================================================

  @requirements @stage-1 @AG-REQ-001
  Scenario: Requirements Agent extracts requirements from intent
    Given I have a business intent:
      """
      Build a customer self-service portal where users can:
      - Register and log in
      - View their account details
      - Submit support tickets
      """
    When I invoke the Requirements Agent with this intent
    Then the agent should generate functional requirements:
      | Key            | Description                           |
      | REQ-F-AUTH-001 | User registration with email/password |
      | REQ-F-AUTH-002 | User login with credentials           |
      | REQ-F-ACCT-001 | View account details                  |
      | REQ-F-SUPP-001 | Submit support tickets                |
    And each requirement should have acceptance criteria
    And requirements should have unique, immutable keys

  @requirements @stage-1 @AG-REQ-002
  Scenario: Requirements Agent generates non-functional requirements
    Given a business intent for a payment system
    When I invoke the Requirements Agent
    Then the agent should generate NFR requirements:
      | Key              | Category    | Description                    |
      | REQ-NFR-SEC-001  | Security    | Encrypt sensitive data at rest |
      | REQ-NFR-PERF-001 | Performance | Response time < 500ms          |
      | REQ-NFR-AV-001   | Availability| 99.9% uptime SLA               |

  @requirements @stage-1 @AG-REQ-003
  Scenario: Requirements Agent uses correct key format
    When I invoke the Requirements Agent for any intent
    Then all generated requirement keys should match patterns:
      | Pattern         | Type                    |
      | REQ-F-*-NNN     | Functional requirement  |
      | REQ-NFR-*-NNN   | Non-functional requirement |
      | REQ-DATA-*-NNN  | Data quality requirement   |
      | REQ-BR-*-NNN    | Business rule              |

  # ===========================================================================
  # Stage 2: Design Agent
  # ===========================================================================

  @design @stage-2 @AG-DES-001
  Scenario: Design Agent creates solution architecture
    Given requirements exist:
      | Key            | Description                |
      | REQ-F-AUTH-001 | User authentication        |
      | REQ-F-ACCT-001 | Account management         |
    When I invoke the Design Agent for these requirements
    Then the agent should produce:
      | Artifact         | Description                    |
      | Components       | AuthService, AccountService    |
      | API Specs        | REST endpoints for auth/acct   |
      | Data Model       | User, Account tables           |
      | Traceability     | Design elements → REQ keys     |

  @design @stage-2 @AG-DES-002
  Scenario: Design Agent creates ADRs for decisions
    Given a design decision is needed for authentication approach
    When I invoke the Design Agent
    Then an ADR should be created with:
      | Section      | Content                          |
      | Context      | Why decision is needed           |
      | Decision     | Chosen approach (e.g., JWT)      |
      | Rationale    | Why this approach was chosen     |
      | Requirements | Linked REQ-* keys                |
      | Status       | Proposed / Accepted              |

  @design @stage-2 @AG-DES-003
  Scenario: Design Agent validates requirement coverage
    Given requirements REQ-F-001 through REQ-F-005 exist
    When I ask the Design Agent to validate coverage
    Then the agent should report:
      | Requirement | Covered By              | Status |
      | REQ-F-001   | AuthService             | Yes    |
      | REQ-F-002   | AccountService          | Yes    |
      | REQ-F-003   | (none)                  | MISSING|

  # ===========================================================================
  # Stage 3: Tasks Agent
  # ===========================================================================

  @tasks @stage-3 @AG-TSK-001
  Scenario: Tasks Agent breaks design into work units
    Given a design document for AuthService exists
    When I invoke the Tasks Agent
    Then work units should be created:
      | Task ID | Title                      | Requirement    | Estimate |
      | TASK-001| Implement login endpoint   | REQ-F-AUTH-001 | 4h       |
      | TASK-002| Add password validation    | REQ-F-AUTH-001 | 2h       |
      | TASK-003| Create JWT token service   | REQ-F-AUTH-002 | 3h       |

  @tasks @stage-3 @AG-TSK-002
  Scenario: Tasks Agent identifies dependencies
    Given multiple design components with interdependencies
    When I invoke the Tasks Agent
    Then the agent should identify:
      | Task     | Depends On    | Reason                    |
      | TASK-003 | TASK-001      | Login must exist first    |
      | TASK-004 | TASK-002,003  | Requires auth components  |
    And a dependency graph should be generated

  @tasks @stage-3 @AG-TSK-003
  Scenario: Tasks Agent maintains requirement traceability
    When the Tasks Agent creates work units
    Then every task should have at least one REQ-* reference
    And tasks should be traceable back to design elements
    And design elements should trace to original requirements

  # ===========================================================================
  # Stage 4: Code Agent
  # ===========================================================================

  @code @stage-4 @AG-COD-001
  Scenario: Code Agent follows TDD workflow
    Given a task to implement login endpoint (REQ-F-AUTH-001)
    When I invoke the Code Agent
    Then the agent should follow TDD phases:
      | Phase    | Action                              |
      | RED      | Write failing test first            |
      | GREEN    | Write minimal code to pass test     |
      | REFACTOR | Improve code quality                |
      | COMMIT   | Commit with "Implements: REQ-F-AUTH-001" |

  @code @stage-4 @AG-COD-002
  Scenario: Code Agent enforces Key Principles
    When I invoke the Code Agent for any implementation
    Then the agent should check:
      | Principle | Check                           |
      | #1 TDD    | Tests written before code       |
      | #2 Fail Fast | Error handling is explicit   |
      | #3 Modular | Single responsibility per unit  |
      | #4 Reuse  | Existing code checked first     |
      | #5 OSS    | Open source alternatives noted  |
      | #6 Clean  | No technical debt introduced    |
      | #7 Excellence | Best practices followed     |

  @code @stage-4 @AG-COD-003
  Scenario: Code Agent tags code with requirements
    Given a code implementation for REQ-F-AUTH-001
    When the Code Agent generates code
    Then the code should contain requirement tags:
      """
      # Implements: REQ-F-AUTH-001
      def login(email: str, password: str) -> LoginResult:
          ...
      """
    And test code should contain validation tags:
      """
      # Validates: REQ-F-AUTH-001
      def test_login_with_valid_credentials():
          ...
      """

  # ===========================================================================
  # Stage 5: System Test Agent
  # ===========================================================================

  @system-test @stage-5 @AG-SYS-001
  Scenario: System Test Agent creates BDD scenarios
    Given a requirement REQ-F-AUTH-001 for user login
    When I invoke the System Test Agent
    Then BDD scenarios should be generated:
      """
      Feature: User Authentication
        # Validates: REQ-F-AUTH-001

        Scenario: Successful login
          Given I am on the login page
          When I enter valid email "user@example.com"
          And I enter valid password "password123"
          And I click "Login"
          Then I should see "Welcome back"
      """

  @system-test @stage-5 @AG-SYS-002
  Scenario: System Test Agent validates requirement coverage
    Given requirements REQ-F-001 through REQ-F-010 exist
    And BDD scenarios exist for some requirements
    When I invoke the System Test Agent to check coverage
    Then the agent should report:
      | Requirement | BDD Scenarios | Coverage Status |
      | REQ-F-001   | 3             | Covered         |
      | REQ-F-002   | 2             | Covered         |
      | REQ-F-003   | 0             | NOT COVERED     |

  @system-test @stage-5 @AG-SYS-003
  Scenario: System Test Agent creates step definitions
    Given BDD scenarios for authentication exist
    When I invoke the System Test Agent to generate steps
    Then step definition stubs should be created:
      """
      @given('I am on the login page')
      def step_impl(context):
          context.browser.get('/login')

      @when('I enter valid email "{email}"')
      def step_impl(context, email):
          context.browser.find_element_by_id('email').send_keys(email)
      """

  # ===========================================================================
  # Stage 6: UAT Agent
  # ===========================================================================

  @uat @stage-6 @AG-UAT-001
  Scenario: UAT Agent creates business-language test cases
    Given a requirement REQ-F-AUTH-001 "User login"
    When I invoke the UAT Agent
    Then UAT test cases should be in business language:
      | ID       | Title                    | Steps                            |
      | UAT-001  | Verify user can log in   | 1. Go to login page              |
      |          |                          | 2. Enter valid credentials       |
      |          |                          | 3. Click login                   |
      |          |                          | 4. Verify dashboard appears      |
    And test cases should NOT contain technical jargon

  @uat @stage-6 @AG-UAT-002
  Scenario: UAT Agent links to requirements
    When the UAT Agent creates test cases
    Then every UAT test should reference at least one REQ-* key
    And the traceability should be bidirectional:
      | Direction      | Example                       |
      | UAT → REQ      | UAT-001 validates REQ-F-AUTH-001 |
      | REQ → UAT      | REQ-F-AUTH-001 validated by UAT-001 |

  @uat @stage-6 @AG-UAT-003
  Scenario: UAT Agent supports sign-off workflow
    Given UAT test cases exist for a feature
    When I invoke the UAT Agent for sign-off
    Then the agent should track:
      | Field        | Value                       |
      | Test ID      | UAT-001                     |
      | Requirement  | REQ-F-AUTH-001              |
      | Tester       | Business Analyst name       |
      | Status       | PASSED / FAILED / BLOCKED   |
      | Sign-off     | Approved / Rejected         |
      | Date         | 2025-11-27                  |

  # ===========================================================================
  # Stage 7: Runtime Feedback Agent
  # ===========================================================================

  @runtime @stage-7 @AG-RUN-001
  Scenario: Runtime Agent sets up observability
    Given a deployed service for REQ-F-AUTH-001
    When I invoke the Runtime Feedback Agent
    Then the agent should configure:
      | Component   | Configuration                           |
      | Logging     | Structured logs with REQ tags           |
      | Metrics     | Latency, error rate by REQ key          |
      | Tracing     | Distributed traces tagged with REQ      |
      | Alerts      | Thresholds linked to NFR requirements   |

  @runtime @stage-7 @AG-RUN-002
  Scenario: Runtime Agent traces issues to requirements
    Given a production error occurs:
      | Field        | Value                              |
      | Error        | Authentication timeout             |
      | Service      | AuthService                        |
      | Timestamp    | 2025-11-27 14:30:00               |
    When I invoke the Runtime Feedback Agent
    Then the agent should trace to:
      | Requirement    | Description                    |
      | REQ-F-AUTH-001 | User login functionality       |
      | REQ-NFR-PERF-001 | Response time < 500ms (violated) |

  @runtime @stage-7 @AG-RUN-003
  Scenario: Runtime Agent generates new intents from issues
    Given a recurring production issue traced to REQ-F-AUTH-001
    When I invoke the Runtime Feedback Agent
    Then the agent should generate a new intent:
      | Field       | Value                                    |
      | Intent ID   | INT-042                                  |
      | Type        | Maintenance                              |
      | Priority    | High                                     |
      | Description | Fix auth timeout causing REQ-F-AUTH-001 failures |
      | Source      | Runtime Feedback                         |
    And the intent should feed back to Requirements stage

  # ===========================================================================
  # Cross-Stage Agent Integration
  # ===========================================================================

  @integration @cross-stage @AG-INT-001
  Scenario: Requirement traceability flows through all stages
    Given an intent "Add user authentication"
    When I execute the full 7-stage pipeline:
      | Stage | Agent                      | Output                      |
      | 1     | Requirements Agent         | REQ-F-AUTH-001              |
      | 2     | Design Agent               | AuthService design          |
      | 3     | Tasks Agent                | TASK-001, TASK-002          |
      | 4     | Code Agent                 | auth_service.py             |
      | 5     | System Test Agent          | auth.feature                |
      | 6     | UAT Agent                  | UAT-001                     |
      | 7     | Runtime Feedback Agent     | Telemetry dashboard         |
    Then REQ-F-AUTH-001 should be traceable through all artifacts
    And the traceability matrix should be complete

  @integration @cross-stage @AG-INT-002
  Scenario: Agent handoff includes context
    When transitioning from Requirements to Design stage
    Then the Design Agent should receive:
      | Context Item         | Description                    |
      | All REQ-* keys       | Generated requirements         |
      | Acceptance criteria  | Per requirement                |
      | Business context     | Original intent                |
      | Constraints          | NFRs and business rules        |

  @integration @feedback @AG-INT-003
  Scenario: Feedback loop from runtime to requirements
    Given a production issue identified by Runtime Agent
    When a new intent is generated
    Then the Requirements Agent should receive:
      | Context Item     | Value                          |
      | Source           | Runtime Feedback               |
      | Original REQ     | REQ-F-AUTH-001                 |
      | Issue details    | Auth timeout, 2% error rate    |
      | Suggested action | Performance optimization       |
    And the lifecycle should continue from Stage 1
