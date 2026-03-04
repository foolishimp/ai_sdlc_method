Feature: Methodology Observability
  As a developer
  I want to trace features from intent to telemetry
  So that I can ensure compliance and close the homeostasis loop

  Scenario: Telemetry tagged with REQ keys (UC-06-04)
    Given a converged project with REQ-F-AUTH-001
    When the system emits a convergence event
    Then the OTLP span contains the sdlc.feature_id attribute
    And the span includes req_keys in the sdlc.req_keys facet

  Scenario: Causal Lineage in Traces (UC-04-30)
    Given a feature with a parent intent
    When a child feature is spawned
    Then the child OTLP span has sdlc.causation_id pointing to the parent
    And the lineage path breadcrumb matches feature:edge
