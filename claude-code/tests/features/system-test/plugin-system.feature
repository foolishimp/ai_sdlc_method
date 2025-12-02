# Feature: AISDLC Plugin System
# Validates: REQ-F-PLUGIN-001, REQ-F-PLUGIN-002, REQ-F-PLUGIN-003, REQ-F-PLUGIN-004
# Stage: System Test (Stage 5)

@system-test @plugins @REQ-F-PLUGIN-001
Feature: AISDLC Plugin System
  As a developer or organization
  I want to use the plugin system to load methodology configurations
  So that I can customize and extend the AI SDLC methodology

  Background:
    Given Claude Code is installed and running
    And the plugin marketplace is accessible

  # ===========================================================================
  # Plugin Installation (REQ-F-PLUGIN-001)
  # ===========================================================================

  @install @PL-001
  Scenario: Install aisdlc-methodology plugin from marketplace
    Given the plugin "aisdlc-methodology" exists in the marketplace
    And the plugin is not currently installed
    When I execute the plugin install command for "aisdlc-methodology"
    Then the plugin should be installed successfully
    And the plugin should appear in the installed plugins list
    And all 7 stage agents should be available
    And all 8 slash commands should be registered

  @install @PL-002
  Scenario: Plugin includes all required components
    Given the "aisdlc-methodology" plugin is installed
    When I inspect the plugin contents
    Then the plugin should contain:
      | Component Type | Count | Description                |
      | Agents         | 7     | One per SDLC stage         |
      | Commands       | 8     | Workflow commands          |
      | Skills         | 42    | Code, Design, Testing, etc |
      | Hooks          | 4     | Lifecycle hooks            |
      | Templates      | 5     | Workspace templates        |
    And the plugin.json should have valid metadata

  @install @PL-003
  Scenario: Plugin version displayed correctly
    Given the "aisdlc-methodology" plugin is installed
    When I check the plugin version
    Then the version should match marketplace.json
    And the version should follow semantic versioning (x.y.z)

  # ===========================================================================
  # Plugin Marketplace (REQ-F-PLUGIN-001)
  # ===========================================================================

  @marketplace @MK-001
  Scenario: Marketplace lists available plugins
    When I access the plugin marketplace
    Then I should see "aisdlc-methodology" listed
    And the listing should include:
      | Field       | Expected Value                              |
      | name        | aisdlc-methodology                          |
      | version     | 4.x.x (current)                             |
      | provider    | anthropic                                   |
      | description | Intent-Driven AI SDLC Methodology           |

  @marketplace @MK-002
  Scenario: Marketplace shows plugin details
    When I view details for "aisdlc-methodology" plugin
    Then I should see the full description
    And I should see the list of included components
    And I should see installation instructions

  # ===========================================================================
  # Federated Plugin Loading (REQ-F-PLUGIN-002)
  # ===========================================================================

  @federated @FD-001
  Scenario: Load plugins from multiple sources
    Given the following plugin sources exist:
      | Source     | Path                                  |
      | global     | ~/.claude/plugins/                    |
      | project    | ./claude-code/plugins/                |
    When Claude Code starts
    Then plugins from both sources should be loaded
    And project plugins should override global plugins

  @federated @FD-002
  Scenario: Plugin configuration inheritance
    Given a corporate-level plugin sets:
      | Setting              | Value |
      | tdd.enabled          | true  |
      | coverage.minimum     | 80    |
    And a project-level plugin sets:
      | Setting              | Value |
      | coverage.minimum     | 90    |
    When the merged configuration is computed
    Then tdd.enabled should be "true" (from corporate)
    And coverage.minimum should be "90" (from project override)

  @federated @FD-003
  Scenario: Plugin loading order is deterministic
    Given multiple plugins with different priorities exist
    When plugins are loaded
    Then loading order should be:
      | Order | Level      |
      | 1     | Corporate  |
      | 2     | Division   |
      | 3     | Team       |
      | 4     | Project    |
    And later plugins override earlier ones

  # ===========================================================================
  # Plugin Versioning (REQ-F-PLUGIN-004)
  # ===========================================================================

  @versioning @VS-001
  Scenario: Plugin version compatibility check
    Given the methodology requires Claude Code version "1.0.0+"
    And the current Claude Code version is "1.2.0"
    When I install the "aisdlc-methodology" plugin
    Then installation should succeed
    And no version compatibility warnings should appear

  @versioning @VS-002 @error-handling
  Scenario: Plugin version incompatibility detected
    Given the plugin requires Claude Code version "2.0.0+"
    And the current Claude Code version is "1.5.0"
    When I attempt to install the plugin
    Then I should see a version incompatibility warning
    And installation should be blocked or require confirmation

  @versioning @VS-003
  Scenario: Plugin update available notification
    Given the installed plugin version is "4.0.0"
    And the marketplace has version "4.1.0" available
    When I check for plugin updates
    Then I should see "aisdlc-methodology" has an update available
    And I should see the changelog for v4.1.0

  # ===========================================================================
  # Plugin Components (Skills, Agents, Commands)
  # ===========================================================================

  @components @CP-001
  Scenario: All 7 stage agents are registered
    Given the "aisdlc-methodology" plugin is installed
    When I list available agents
    Then I should see the following agents:
      | Agent Name                          | Stage              |
      | aisdlc-requirements-agent          | 1 - Requirements   |
      | aisdlc-design-agent                | 2 - Design         |
      | aisdlc-tasks-agent                 | 3 - Tasks          |
      | aisdlc-code-agent                  | 4 - Code           |
      | aisdlc-system-test-agent           | 5 - System Test    |
      | aisdlc-uat-agent                   | 6 - UAT            |
      | aisdlc-runtime-feedback-agent      | 7 - Runtime        |

  @components @CP-002
  Scenario: All slash commands are registered
    Given the "aisdlc-methodology" plugin is installed
    When I list available commands
    Then I should see the following commands:
      | Command                    | Purpose                       |
      | /aisdlc-status             | Display task status           |
      | /aisdlc-checkpoint-tasks   | Save task progress            |
      | /aisdlc-commit-task        | Create traceable commit       |
      | /aisdlc-finish-task        | Complete a task               |
      | /aisdlc-refresh-context    | Reload workspace context      |
      | /aisdlc-release            | Create a release              |
      | /aisdlc-update             | Update framework              |
      | /aisdlc-help               | Display help guide            |

  @components @CP-003
  Scenario: Skills are loaded and accessible
    Given the "aisdlc-methodology" plugin is installed
    When I list available skills
    Then I should see skills in categories:
      | Category     | Count | Examples                           |
      | code         | 18    | tdd-red, tdd-green, tdd-refactor   |
      | design       | 3     | create-adr, design-traceability    |
      | requirements | 8     | extract-req, validate-req          |
      | testing      | 5     | coverage-check, test-generation    |
      | runtime      | 3     | observability, telemetry           |
      | core         | 3     | req-coverage, key-propagation      |
      | principles   | 2     | key-principles, checklist          |

  # ===========================================================================
  # Hooks System (REQ-F-HOOKS-001)
  # ===========================================================================

  @hooks @HK-001
  Scenario: SessionStart hook loads context
    Given the "aisdlc-methodology" plugin is installed
    And a .ai-workspace directory exists
    When a new Claude Code session starts
    Then the SessionStart hook should execute
    And ACTIVE_TASKS.md should be loaded into context
    And the method reference should be available

  @hooks @HK-002
  Scenario: Stop hook checkpoints work
    Given an active Claude Code session with unsaved work
    When the session ends
    Then the Stop hook should execute
    And task progress should be checkpointed

  @hooks @HK-003
  Scenario: PreToolUse hook validates operations
    Given the methodology requires TDD for code changes
    When a Write tool is invoked
    Then the PreToolUse hook should check for tests
    And the hook should warn if no tests exist

  # ===========================================================================
  # Plugin Uninstallation
  # ===========================================================================

  @uninstall @UN-001
  Scenario: Clean plugin uninstallation
    Given the "aisdlc-methodology" plugin is installed
    When I uninstall the plugin
    Then the plugin should be removed from installed list
    And all plugin commands should be unregistered
    And all plugin agents should be unregistered
    And workspace data should be preserved

  @uninstall @UN-002
  Scenario: Uninstall preserves user work
    Given the "aisdlc-methodology" plugin is installed
    And .ai-workspace contains active tasks
    When I uninstall the plugin
    Then .ai-workspace directory should remain
    And ACTIVE_TASKS.md should be unchanged
    And finished task documents should be unchanged

  # ===========================================================================
  # Plugin Configuration
  # ===========================================================================

  @config @CF-001
  Scenario: Plugin respects stages_config.yml
    Given the plugin's stages_config.yml contains:
      | Stage        | Agent                | Enabled |
      | requirements | aisdlc-requirements-agent | true    |
      | code         | aisdlc-code-agent        | true    |
    When the plugin is loaded
    Then agent configurations should match stages_config.yml
    And agent responsibilities should be as specified

  @config @CF-002
  Scenario: Plugin loads Key Principles configuration
    Given the plugin's config.yml contains Key Principles:
      | Principle | Name                    | Enabled |
      | 1         | Test Driven Development | true    |
      | 2         | Fail Fast & Root Cause  | true    |
      | 7         | Perfectionist Excellence| true    |
    When the Code Agent is invoked
    Then all 7 Key Principles should be enforced
    And TDD workflow should be required
