# Feature: Context Snapshot and Recovery
# Validates: REQ-TOOL-012.0.1.0 (Context Snapshot and Recovery)
# TCS Reference: TCS-012
# Stage: System Test (Stage 5)

@system-test @context-snapshot @REQ-TOOL-012
Feature: Context Snapshot and Recovery
  As a developer using the AI SDLC methodology
  I want to capture immutable snapshots of my work session context
  So that I can recover my work state and share context with team members

  Background:
    Given the AISDLC methodology plugin is installed
    And a valid .ai-workspace directory exists

  # ===========================================================================
  # Basic Snapshot Creation Tests
  # TCS-012: SS-001 through SS-004
  # ===========================================================================

  @snapshot-creation @SS-001
  Scenario: Create basic snapshot with active tasks
    Given ACTIVE_TASKS.md contains the following tasks:
    When I execute the /aisdlc-snapshot-context command
    Then a snapshot file should be created in .ai-workspace/context_history/
    And the snapshot should show "**Total Active**: 2"
    And I should see the success message with snapshot ID

  @snapshot-creation @SS-002
  Scenario: Create snapshot with empty workspace
    Given ACTIVE_TASKS.md has no tasks defined
    When I execute the /aisdlc-snapshot-context command
    Then a snapshot file should be created
    And the snapshot should show "**Total Active**: 0"
    And the snapshot should contain "(None)" for in-progress tasks
    And the snapshot should contain "(None)" for pending tasks
    And the snapshot should contain "(None)" for blocked tasks

  @snapshot-naming @SS-003
  Scenario: Snapshot filename follows correct format
    Given the current datetime is "2025-12-16 14:30:45"
    When I execute the /aisdlc-snapshot-context command
    Then the snapshot filename should match pattern "{YYYYMMDD}_{HHMM}_{label}.md"
    And the snapshot filename should be "20251216_1430_context_snapshot.md"

  @snapshot-directory @SS-004
  Scenario: Snapshot directory is auto-created
    Given no context_history directory exists
    When I execute the /aisdlc-snapshot-context command
    Then the directory .ai-workspace/context_history/ should be created
    And a snapshot file should be created in the context_history directory

  # ===========================================================================
  # Recovery Guidance Tests
  # TCS-012: SS-013
  # ===========================================================================

  @recovery @SS-013
  Scenario: Snapshot includes recovery guidance
    Given ACTIVE_TASKS.md contains the following tasks:
    When I execute the /aisdlc-snapshot-context command
    Then a snapshot file should be created
    And the snapshot should contain recovery guidance section
    And the snapshot should contain git status commands
    And the snapshot should contain ACTIVE_TASKS.md reference

  # ===========================================================================
  # Multiple Snapshot Tracking Tests
  # TCS-012: SS-014
  # ===========================================================================

  @snapshot-tracking @SS-014
  Scenario: Multiple snapshots are tracked
    Given ACTIVE_TASKS.md contains the following tasks:
    And multiple snapshots already exist
    When I execute the /aisdlc-snapshot-context command
    Then a snapshot file should be created
    And the new snapshot should have a unique ID
    And the success message should show the total snapshot count
