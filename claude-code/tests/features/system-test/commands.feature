# Feature: AISDLC Slash Commands
# Validates: REQ-F-CMD-001 (Slash Commands for Workflow)
# TCS Reference: TCS-001 through TCS-007
# Stage: System Test (Stage 5)

@system-test @commands @REQ-F-CMD-001
Feature: AISDLC Slash Commands
  As a developer using the AI SDLC methodology
  I want to use slash commands to manage my workflow
  So that I can track tasks, checkpoint progress, and create releases

  Background:
    Given the AISDLC methodology plugin is installed
    And a valid .ai-workspace directory exists
    And ACTIVE_TASKS.md contains task definitions

  # ===========================================================================
  # /aisdlc-status Command Tests
  # TCS-001: Status Command
  # ===========================================================================

  @status @ST-001
  Scenario: Display status with empty workspace
    Given ACTIVE_TASKS.md has no tasks defined
    When I execute the /aisdlc-status command
    Then I should see the "AI SDLC Task Status" header
    And the active task count should be "0"
    And I should see "(No tasks in progress)"
    And I should see a suggestion to "Use /start-session to begin new work"

  @status @ST-002
  Scenario: Display status with single active task
    Given ACTIVE_TASKS.md has 1 task with title "Implement Authentication"
    And the task has status "In Progress"
    And the task has priority "High"
    When I execute the /aisdlc-status command
    Then the active task count should be "1"
    And I should see task title "Implement Authentication" in the list
    And the task should show status "In Progress"

  @status @ST-003
  Scenario: Display status with multiple active tasks
    Given ACTIVE_TASKS.md has the following tasks:
      | ID | Title                    | Status      | Priority |
      | 1  | Implement Authentication | In Progress | High     |
      | 2  | Add Database Schema      | Not Started | Medium   |
      | 3  | Create API Endpoints     | Not Started | Low      |
    When I execute the /aisdlc-status command
    Then the active task count should be "3"
    And I should see all 3 task titles listed
    And tasks should be grouped by priority

  @status @ST-004
  Scenario: Display recently finished tasks
    Given the finished/ directory contains task documents:
      | Filename                              | Date       |
      | 20251127_1400_user_registration.md   | 2025-11-27 |
      | 20251126_1000_database_setup.md      | 2025-11-26 |
    When I execute the /aisdlc-status command
    Then I should see "Recently Finished: 2"
    And finished tasks should be listed most recent first

  @status @ST-005 @error-handling
  Scenario: Status command with missing workspace
    Given no .ai-workspace directory exists
    When I execute the /aisdlc-status command
    Then I should see an error message about missing workspace
    And I should see instructions to run the installer

  # ===========================================================================
  # /aisdlc-checkpoint-tasks Command Tests
  # TCS-002: Checkpoint Command
  # ===========================================================================

  @checkpoint @CP-001
  Scenario: Checkpoint updates ACTIVE_TASKS.md timestamp
    Given ACTIVE_TASKS.md was last updated "2025-11-27 10:00"
    When I execute the /aisdlc-checkpoint-tasks command at "2025-11-27 14:30"
    Then ACTIVE_TASKS.md should have timestamp "2025-11-27 14:30"

  @checkpoint @CP-002
  Scenario: Checkpoint creates finished task document for completed tasks
    Given ACTIVE_TASKS.md has a task with status "Completed":
      | ID | Title                    | Requirements   |
      | 1  | Implement Authentication | REQ-F-AUTH-001 |
    When I execute the /aisdlc-checkpoint-tasks command
    Then a finished task document should be created in finished/
    And the document filename should match pattern "YYYYMMDD_HHMM_*.md"
    And the document should contain "REQ-F-AUTH-001"
    And the task should be removed from ACTIVE_TASKS.md

  @checkpoint @CP-003
  Scenario: Checkpoint preserves in-progress tasks
    Given ACTIVE_TASKS.md has tasks with various statuses:
      | ID | Title        | Status      |
      | 1  | Task One     | In Progress |
      | 2  | Task Two     | Completed   |
      | 3  | Task Three   | Not Started |
    When I execute the /aisdlc-checkpoint-tasks command
    Then Task 1 should remain in ACTIVE_TASKS.md with status "In Progress"
    And Task 3 should remain in ACTIVE_TASKS.md with status "Not Started"
    And Task 2 should be moved to finished/

  # ===========================================================================
  # /aisdlc-commit-task Command Tests
  # TCS-003: Commit Command
  # ===========================================================================

  @commit @CM-001
  Scenario: Commit task with proper traceability
    Given a finished task document exists for Task #1:
      | Field        | Value                    |
      | Title        | Implement Authentication |
      | Requirements | REQ-F-AUTH-001           |
      | Solution     | Added JWT authentication |
    And there are staged git changes
    When I execute the /aisdlc-commit-task command for Task #1
    Then a git commit should be created
    And the commit message should contain "Task #1"
    And the commit message should contain "Implements: REQ-F-AUTH-001"
    And the commit message should contain "Co-Authored-By: Claude"

  @commit @CM-002
  Scenario: Commit task requires finished document
    Given no finished task document exists for Task #99
    When I attempt to execute /aisdlc-commit-task for Task #99
    Then I should see an error about missing finished document
    And no git commit should be created

  @commit @CM-003
  Scenario: Commit task includes TDD workflow confirmation
    Given a finished task document exists with TDD evidence:
      | Field       | Value                    |
      | Title       | Add Login Endpoint       |
      | TDD Phase   | REFACTOR complete        |
      | Tests       | 5 passing, 0 failing     |
    When I execute the /aisdlc-commit-task command
    Then the commit message should contain "TDD: RED -> GREEN -> REFACTOR"
    And the commit message should contain "Tests: 5 passing"

  # ===========================================================================
  # /aisdlc-finish-task Command Tests
  # TCS-004: Finish Task Command
  # ===========================================================================

  @finish @FT-001
  Scenario: Finish task creates properly formatted document
    Given Task #1 "Implement Authentication" is marked for completion
    And the task has requirements "REQ-F-AUTH-001, REQ-NFR-SEC-001"
    When I execute the /aisdlc-finish-task command for Task #1
    And I provide the following details:
      | Field    | Value                        |
      | Problem  | Users cannot log in          |
      | Solution | Implemented JWT auth flow    |
      | Result   | All tests passing            |
    Then a finished document should be created matching the template
    And the document should contain all requirement keys
    And the document should have status "Completed"

  @finish @FT-002
  Scenario: Finish task uses correct filename format
    Given the current datetime is "2025-11-27 15:30"
    When I execute the /aisdlc-finish-task for "User Registration"
    Then the filename should be "20251127_1530_user_registration.md"

  # ===========================================================================
  # /aisdlc-release Command Tests
  # TCS-006: Release Command
  # ===========================================================================

  @release @RL-001
  Scenario: Release creates annotated git tag
    Given no uncommitted changes exist
    And the latest tag is "v0.4.1"
    When I execute the /aisdlc-release command with version "v0.4.2"
    Then an annotated git tag "v0.4.2" should be created
    And the tag message should contain release notes

  @release @RL-002 @error-handling
  Scenario: Release fails with uncommitted changes
    Given there are uncommitted changes in the repository
    When I attempt to execute the /aisdlc-release command
    Then I should see an error about uncommitted changes
    And no tag should be created

  @release @RL-003
  Scenario: Release generates changelog from commits
    Given the following commits exist since last tag:
      | Message                                    |
      | feat: Add user authentication (REQ-F-001) |
      | fix: Correct validation logic (REQ-F-002) |
      | docs: Update README                       |
    When I execute the /aisdlc-release command
    Then the release notes should include all commit messages
    And commits should be grouped by type (feat, fix, docs)

  @release @RL-004
  Scenario: Release supports dry-run mode
    Given the latest tag is "v0.4.1"
    When I execute the /aisdlc-release command with --dry-run
    Then I should see what the release would contain
    And no actual tag should be created

  # ===========================================================================
  # /aisdlc-update Command Tests
  # TCS-007: Update Command
  # ===========================================================================

  @update @UP-001
  Scenario: Update preserves active work
    Given ACTIVE_TASKS.md contains important work in progress
    And the finished/ directory contains task history
    When I execute the /aisdlc-update command
    Then ACTIVE_TASKS.md should be unchanged
    And finished/ contents should be unchanged
    And only framework files should be updated

  @update @UP-002
  Scenario: Update creates backup before changes
    Given the .ai-workspace/ directory exists with content
    When I execute the /aisdlc-update command
    Then a backup should be created with timestamp
    And I should see confirmation of backup location

  # ===========================================================================
  # /aisdlc-help Command Tests
  # ===========================================================================

  @help @HP-001
  Scenario: Help displays all available commands
    When I execute the /aisdlc-help command
    Then I should see documentation for all 7 commands
    And I should see the 7-stage lifecycle diagram
    And I should see the Key Principles summary
    And I should see quick start workflows

  # ===========================================================================
  # Command Integration Tests
  # ===========================================================================

  @integration @INT-001
  Scenario: Full workflow from task creation to release
    Given a fresh workspace with no tasks
    When I add Task #1 "Implement Feature X" with requirements "REQ-F-FEAT-001"
    And I execute /aisdlc-status
    Then I should see 1 active task

    When I complete work on Task #1
    And I execute /aisdlc-finish-task for Task #1
    Then a finished document should exist

    When I execute /aisdlc-checkpoint-tasks
    Then Task #1 should be moved to finished/

    When I stage and execute /aisdlc-commit-task for Task #1
    Then a git commit should exist with "REQ-F-FEAT-001"

    When I execute /aisdlc-release with version "v0.1.0"
    Then a git tag "v0.1.0" should exist
