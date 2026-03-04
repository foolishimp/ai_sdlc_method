Feature: Asset Graph Engine
  As a methodology architect
  I want to ensure only valid graph transitions occur
  So that the SDLC remains structured and stable

  Scenario: Reject inadmissible transitions (UC-01-04)
    Given an initialized workspace
    And a feature at the "requirements" stage
    When I attempt to iterate on the "requirements→unit_tests" edge
    Then the system rejects the traversal
    And reports that the transition is inadmissible

  Scenario: Markov Stability on Convergence (UC-01-07/08)
    Given a feature iterating on "code↔unit_tests"
    When an iteration results in delta=0
    Then the asset achieves Markov object status
    And the feature status is updated to "converged" for that edge
    When an iteration results in delta=1
    Then the asset remains a "candidate"
    And the edge status is "iterating"
