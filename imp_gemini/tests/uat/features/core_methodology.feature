Feature: Core Methodology Functions
  As a developer
  I want to use structured dependencies and TDD protocols
  So that the SDLC remains consistent and correct

  Scenario: Feature Dependencies (UC-04-15)
    Given 3 features with dependency graph: A→B, A→C, B and C independent
    When I check the blocked status of the features
    Then feature A is not blocked
    And feature B is blocked by A
    And feature C is blocked by A
    When feature A converges
    Then features B and C are no longer blocked

  Scenario: TDD Red-Green Phase (UC-05-01/02)
    Given a feature at the "code↔unit_tests" edge
    When the iterate function starts a TDD cycle
    Then it first writes a failing test (RED state)
    And the test is tagged with the feature REQ key
    When the iterate function writes code to pass the test
    Then the test passes (GREEN state)
    And the code is tagged with the feature REQ key
