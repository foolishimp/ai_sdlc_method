# Validates: REQ-F-FPC-001, REQ-F-FPC-002, REQ-F-FPC-003, REQ-F-FPC-004
# Validates: REQ-F-FPC-005, REQ-F-FPC-006
# Validates: REQ-NFR-FPC-001, REQ-NFR-FPC-002, REQ-NFR-FPC-003
# Validates: REQ-DATA-FPC-001, REQ-BR-FPC-001

Feature: Artifact Construction and Batched Evaluation
  As a developer using the methodology engine
  I want the engine to construct artifacts and evaluate them in one step
  So that I can build features faster with fewer review cycles

  Background:
    Given a project workspace with an active feature vector
    And the feature has passed all prior edges

  # ── REQ-F-FPC-001: One Construction Call Per Edge ──────────────────────

  Scenario: Engine constructs an artifact for a single edge
    # Validates: REQ-F-FPC-001
    Given I have an intent document describing user authentication
    When the engine processes the "intent to requirements" edge with construction enabled
    Then the engine produces a requirements artifact
    And the engine makes exactly one construction call for that edge

  Scenario: Construction fails gracefully when the tool is unavailable
    # Validates: REQ-F-FPC-001
    Given the construction tool is not installed on the system
    When the engine attempts to construct an artifact
    Then the engine reports a "tool unavailable" finding
    And no artifact is produced
    And the engine does not crash

  # ── REQ-F-FPC-002: Batched Evaluation ──────────────────────────────────

  Scenario: Construction response includes self-evaluation against all criteria
    # Validates: REQ-F-FPC-002
    Given an edge has five quality criteria defined
    When the engine constructs an artifact for that edge
    Then the construction response includes evaluations for all five criteria
    And each evaluation has a name, outcome, and reason

  Scenario: Batched evaluations replace individual evaluation calls
    # Validates: REQ-F-FPC-002
    Given an edge has three agent-type quality criteria
    When the engine constructs and evaluates the artifact
    Then the engine uses the batched evaluations from the construction response
    And the engine does not make separate evaluation calls for those criteria

  Scenario: Missing batched evaluation falls back to individual evaluation
    # Validates: REQ-F-FPC-002
    Given an edge has three agent criteria but construction only evaluates two
    When the engine processes the results
    Then the two matched criteria use the batched results
    And the unmatched criterion falls back to an individual evaluation call

  # ── REQ-F-FPC-003: Context Accumulation Between Edges ──────────────────

  Scenario: Prior edge artifacts are passed as context to later edges
    # Validates: REQ-F-FPC-003
    Given the "intent to requirements" edge has converged with an artifact
    When the engine processes the "requirements to design" edge
    Then the construction call receives the requirements artifact as context
    And the design artifact can reference content from the requirements

  Scenario: Context accumulates across multiple edges
    # Validates: REQ-F-FPC-003
    Given requirements and design edges have both converged
    When the engine processes the "design to code" edge
    Then the construction call receives both the requirements and design artifacts as context

  # ── REQ-F-FPC-004: Engine Integration ──────────────────────────────────

  Scenario: Construction runs before evaluation in the engine loop
    # Validates: REQ-F-FPC-004
    Given an edge is configured for construction
    When the engine iterates on that edge
    Then the engine constructs the artifact first
    And then evaluates the constructed artifact against the checklist
    And reports the combined results

  Scenario: Engine defaults to evaluation-only when construction is not requested
    # Validates: REQ-F-FPC-004
    Given an edge is not configured for construction
    When the engine iterates on that edge
    Then the engine evaluates the existing asset without constructing
    And no construction call is made

  # ── REQ-F-FPC-005: Command-Line Construction Mode ─────────────────────

  Scenario: Developer triggers construction from the command line
    # Validates: REQ-F-FPC-005
    Given a project with a configured edge
    When the developer runs the "construct" command for that edge
    Then the engine constructs and evaluates in one call
    And the output includes the artifact, evaluations, and traceability

  Scenario: Developer enables construction on the loop command
    # Validates: REQ-F-FPC-005
    Given a project with a configured edge
    When the developer runs the "run-edge" command with the construct flag
    Then the engine loops with construction enabled on each iteration
    And converges when all checks pass

  # ── REQ-F-FPC-006: Structured Output Schema ───────────────────────────

  Scenario: Construction response follows the required structure
    # Validates: REQ-F-FPC-006
    When the engine receives a construction response
    Then the response contains an artifact field with the generated content
    And the response contains an evaluations array with check results
    And the response contains a traceability array with requirement keys

  Scenario: Malformed construction response triggers a retry
    # Validates: REQ-F-FPC-006
    Given the construction tool returns an invalid response
    When the engine processes the response
    Then the engine retries the construction call
    And if the retry succeeds, the engine uses the valid response

  Scenario: All retries fail gracefully
    # Validates: REQ-F-FPC-006
    Given the construction tool returns invalid responses on every attempt
    When the engine exhausts all retry attempts
    Then the engine reports a parse error finding
    And no artifact is produced

  # ── REQ-NFR-FPC-001: Efficiency ────────────────────────────────────────

  Scenario: Full feature traversal uses minimal construction calls
    # Validates: REQ-NFR-FPC-001
    Given a feature with four edges in its profile
    When the engine traverses all four edges with construction enabled
    Then the engine makes at most four construction calls total
    And each edge uses exactly one construction call

  # ── REQ-NFR-FPC-002: Backward Compatibility ───────────────────────────

  Scenario: Existing evaluation-only workflows are unchanged
    # Validates: REQ-NFR-FPC-002
    Given a project that was built using the evaluation-only engine
    When the developer runs the engine without enabling construction
    Then all existing tests pass without modification
    And the engine behaves identically to before construction was added

  # ── REQ-NFR-FPC-003: Resilience ────────────────────────────────────────

  Scenario: Construction recovers from a timeout
    # Validates: REQ-NFR-FPC-003
    Given the construction tool takes longer than the allowed time
    When the engine detects the timeout
    Then the engine retries the construction call
    And if the retry succeeds within the time limit, the artifact is accepted

  Scenario: Construction retries are bounded
    # Validates: REQ-NFR-FPC-003
    Given the construction tool times out repeatedly
    When the engine has retried the maximum number of times
    Then the engine stops retrying
    And reports a timeout finding with the number of attempts

  # ── REQ-DATA-FPC-001: Construction Result Data Model ───────────────────

  Scenario: Construction result carries all required metadata
    # Validates: REQ-DATA-FPC-001
    When the engine completes a construction call
    Then the result includes the generated artifact content
    And the result includes the model used for construction
    And the result includes the time taken in milliseconds
    And the result includes the number of retry attempts
    And the result includes any traceability keys found

  # ── REQ-BR-FPC-001: Construction Before Evaluation Ordering ────────────

  Scenario: Artifact is written to the filesystem before evaluation begins
    # Validates: REQ-BR-FPC-001
    Given an output path is specified for the constructed artifact
    When the engine constructs an artifact
    Then the artifact is written to the specified path
    And the evaluation runs against the written artifact
    And the evaluation results reflect the constructed content

  Scenario: Construction output path creates directories as needed
    # Validates: REQ-BR-FPC-001
    Given the output path points to a directory that does not exist
    When the engine constructs an artifact
    Then the engine creates the necessary directories
    And writes the artifact to the specified location
