# Validates: REQ-F-EVOL-001
# Validates: REQ-EVOL-001
# Validates: REQ-EVOL-002
# Validates: REQ-EVOL-003
# Validates: REQ-EVOL-004
# Validates: REQ-EVOL-005
#
# UAT Scenarios: Spec Evolution Pipeline
# Feature: REQ-F-EVOL-001
# Edge: design → uat_tests (BDD / Gherkin)
# Profile: standard
# Language: business (no technical implementation details)

Feature: Spec Evolution Pipeline
  # Validates: REQ-F-EVOL-001

  As a developer using Genesis to evolve the specification of their project,
  I want the system to track all spec changes with a complete audit trail
  and enforce a human review gate before any proposal is promoted,
  So that no specification change occurs silently, autonomously, or without accountability.

  Background:
    Given I am working on a Genesis-managed project
    And the project has an event log recording the history of all methodology actions
    And the project has a specification folder containing the authoritative feature definitions


  # ─── REQ-EVOL-001: Workspace Vectors Are Trajectory-Only ───────────────────

  Scenario: Workspace progress files contain only tracking state, not feature definitions
    Given the project specification defines a feature called "User authentication"
    And the workspace has a progress tracking file for that feature
    When I inspect the workspace progress file
    Then I see only tracking information: current status, iteration count, and progress timestamps
    But I do not see requirement descriptions, success criteria, or dependency graphs in that file

  Scenario: Genesis rejects a workspace file that contains requirement definitions
    Given someone has manually added a "requirements" field to a workspace progress file
    When Genesis reads that workspace file
    Then Genesis raises a schema violation warning naming the offending field
    And the violation is surfaced in the workspace health report
    And Genesis does not silently continue as if the file were valid

  Scenario: Health check identifies workspace files that have drifted to contain spec content
    Given two workspace progress files contain forbidden definition fields
    When I run the workspace health check
    Then the health report lists both files by name
    And for each file, shows which field violated the schema
    And recommends corrective action


  # ─── REQ-EVOL-002: Feature Display Joins Spec and Workspace ────────────────

  Scenario: Status view shows all three feature categories
    Given the project specification defines 10 features
    And 7 of those features have workspace progress tracking started
    And 1 workspace file has no matching feature in the specification
    When I view the project status
    Then I see 7 features marked as ACTIVE (in spec and in progress)
    And I see 3 features marked as PENDING (defined in spec, not yet started)
    And I see 1 feature marked as ORPHAN (in progress but not in spec)

  Scenario: PENDING features show their full definition from the specification
    Given a feature is defined in the specification but no progress has started
    When I view that feature in the project status
    Then I see the feature title sourced from the specification
    And I see which requirements it covers, sourced from the specification
    And I see it labelled as PENDING

  Scenario: ORPHAN features are shown as warnings, not silently hidden
    Given a workspace progress file exists for a feature ID that is not in the specification
    When I run the workspace health check
    Then the health report prominently displays that feature as ORPHAN
    And recommends either adding it to the spec or archiving the workspace file
    And does not simply omit it from the display

  Scenario: Status view shows total feature count from specification, not just active count
    Given the project specification defines 12 features in total
    And only 5 have workspace tracking started
    When I view the project status
    Then the progress indicator reads "5 of 12 features active"
    And not just "5 features active"

  Scenario: Missing specification does not cause a silent empty feature list
    Given the project specification file becomes temporarily unreadable
    When I attempt to view project status
    Then I see a clear warning: "Specification layer unreadable — feature list may be incomplete"
    And I do not see an empty feature list without explanation


  # ─── REQ-EVOL-004: Spec Modified Events with Audit Trail ───────────────────

  Scenario: Every specification change produces an audit event
    Given I add a new feature to the project specification
    When the specification file is saved
    Then a "specification changed" event appears in the project event log
    And the event records: which file changed, what it looked like before, what it looks like now
    And the event records what triggered the change

  Scenario: Specification change event is recorded before the file is written
    Given a specification change is being promoted through the pipeline
    When the change is approved and applied
    Then the audit event appears in the event log
    And the event timestamp precedes or matches the file write timestamp
    And never appears after the file has already been saved

  Scenario: A manually authored specification change is recorded with "manual" trigger
    Given a developer directly edits a specification file outside the pipeline
    When the git commit hook fires after the save
    Then a "specification changed" event is added to the event log
    And the event records trigger type as "manual edit"
    And the event includes the author's identity

  Scenario: Specification hash can be verified against the event log
    Given the event log contains a record of the last change to a specification file
    When I ask Genesis to verify that file's integrity
    Then Genesis compares the current file content against the hash recorded in the last audit event
    And reports "in sync" if they match
    And reports "SPEC DRIFT" with the file name if they do not match


  # ─── REQ-EVOL-NFR-001: Event Atomicity ─────────────────────────────────────

  Scenario: A failed specification write does not leave a phantom audit event
    Given a specification change is being applied
    And the file write operation fails midway
    When I inspect the event log
    Then there is no "specification changed" event for the failed write
    And the event log reflects only completed, successful changes


  # ─── REQ-EVOL-NFR-002: Spec Hash Verification ──────────────────────────────

  Scenario: Health check flags specification files that have been modified outside the pipeline
    Given a specification file was changed directly without going through the change pipeline
    When I run the workspace health check
    Then the health report shows a "SPEC DRIFT" warning for that file
    And shows which event log entry the current content diverges from
    And does not modify the file — it only reports


  # ─── REQ-EVOL-003 / REQ-EVOL-005: Draft Features Queue (Phase 2) ───────────

  Scenario: A candidate new feature waits in the draft queue for human review
    Given the homeostasis pipeline has identified a gap and proposed a new feature
    When I view the project status
    Then I see a "Pending Proposals" section listing that proposal
    And the listing shows: proposal ID, proposed feature title, triggering gap, and how long it has been waiting
    And the proposal has not been added to the specification yet

  Scenario: An empty draft queue is displayed as an explicit positive signal
    Given no feature proposals are currently pending
    When I view the project status
    Then I see the message "No pending proposals" in the draft queue section
    And not an absent or empty section

  Scenario: The draft queue can be reconstructed from the event log alone
    Given the status display has been cleared or reset
    When I replay the project event log
    Then the reconstructed draft queue matches what was displayed before
    And all pending proposals reappear with their original IDs and details
    And all previously approved or rejected proposals are correctly excluded

  Scenario: Approving a proposal adds the feature to the specification and creates a workspace entry
    Given a feature proposal is waiting in the draft queue
    When I approve the proposal using the review command
    Then the feature is added to the specification's feature list
    And a workspace progress file is created for that feature with all phases marked as "not yet started"
    And a "specification changed" event is recorded in the event log with the proposal ID as its cause


  # ─── REQ-EVOL-BR-001 / REQ-EVOL-BR-002: Business Rules ────────────────────

  Scenario: The specification is the authoritative source — workspace files cannot override it
    Given a feature is defined in the specification with a certain set of requirements
    And the workspace progress file for that feature contains a conflicting requirements list
    When Genesis displays the feature
    Then it shows the requirements from the specification
    And not from the workspace file
    And the workspace file inconsistency is flagged as a schema violation

  Scenario: The pipeline cannot promote a proposal to the specification without human approval
    Given a new feature proposal has been generated automatically by the gap analysis pipeline
    When I inspect the event log and specification
    Then the specification has not changed
    And the event log shows no "specification changed" event for that proposal
    And the proposal is still in the draft queue awaiting review

  Scenario: Human approval is recorded as an accountable event before the spec is modified
    Given a feature proposal is waiting in the draft queue
    When I approve it with my identity
    Then the event log records my identity as the approver before the specification is modified
    And the "specification changed" event references the approval event as its cause
    And there is a clear chain: gap detected → proposal created → human approved → spec updated

  Scenario: Rejecting a proposal removes it from the draft queue and records the reason
    Given a feature proposal is waiting in the draft queue
    When I reject it with a reason
    Then the proposal disappears from the draft queue
    And a "proposal rejected" event is recorded in the event log with my reason
    And the specification is not modified
    And the rejection is permanent — the proposal does not reappear
