# Validates: REQ-F-SCHEMA-DISC-001
Feature: Automatic Data Structure Discovery
  As a project team member working with an unfamiliar dataset,
  I want the system to automatically examine the data and describe its structure,
  So that I can understand the data before building features that depend on it.

  Background:
    Given the project has a data file that needs to be understood
    And the project does not yet have a description of that data's structure

  # ── Happy paths ──────────────────────────────────────────────────────────────

  Scenario: System discovers field names and data types from a data file
    Given I provide a data file containing sales records
    When I ask the system to discover the data structure
    Then the system produces a field map listing every column in the file
    And each column shows what kind of information it contains
    And the field map is saved to the project design folder

  Scenario: System identifies columns that behave as categories
    Given I provide a data file where the "region" column only contains
      the values "North", "South", "East", and "West"
    When I ask the system to discover the data structure
    Then the field map marks "region" as a category with a small fixed set of values
    And the known values are listed in the field map

  Scenario: System distinguishes identifier columns from category columns
    Given I provide a data file where the "transaction_id" column has a
      different value on every single row
    When I ask the system to discover the data structure
    Then the field map marks "transaction_id" as a unique identifier
    And it does NOT suggest "transaction_id" is a category with a fixed set of values

  Scenario: System preserves a record of how it discovered the structure
    Given I provide a data file and ask for structure discovery
    When the discovery completes
    Then the field map records where the analysis was performed
    So that the team can review or re-run the analysis at any time

  Scenario: Team member reviews and approves the discovered field map
    Given the system has produced a field map for the project's data file
    When I review the field map
    And I confirm that all fields are correctly described
    Then the field map is marked as approved
    And the project design can proceed using the confirmed structure

  Scenario: System flags unresolved questions for human review
    Given the system discovers a column it cannot confidently classify
    When the discovery completes
    Then the field map lists the uncertain column under "open questions"
    And the discovery result is still delivered
    And I can review and resolve the open question before using the schema

  # ── Negative / error paths ───────────────────────────────────────────────────

  Scenario: System reports clearly when the data file cannot be found
    Given I ask for structure discovery
    But the data file I specified does not exist in the project
    When the system attempts the discovery
    Then the system reports that the file could not be found
    And no partial or empty field map is created

  Scenario: System reports clearly when the data file is empty
    Given I ask for structure discovery
    But the data file contains no rows of data
    When the system attempts the discovery
    Then the system reports that there is no data to analyse
    And no field map is created

  Scenario: Discovery fails gracefully when the data cannot be processed
    Given I provide a file that is not in a recognisable data format
    When the system attempts the discovery
    Then the system reports that the file format was not recognised
    And the team is told what file formats are supported

  # ── Round-trip / integration path ────────────────────────────────────────────

  Scenario: Discovered field map resolves a missing-structure gap in the project design
    Given the project design has identified a gap because the data structure is unknown
    When I run structure discovery on the relevant data file
    Then the discovered field map is automatically linked to the design gap
    And the project design shows the gap as resolved
    And work on the feature that depends on this data can continue

  Scenario Outline: System correctly classifies common types of data columns
    Given I provide a data file with a column containing <data_kind>
    When I ask the system to discover the data structure
    Then the field map describes that column as <expected_label>

    Examples:
      | data_kind                         | expected_label   |
      | whole numbers (1, 2, 42)          | a number         |
      | decimal amounts (1.99, 42.50)     | a decimal number |
      | calendar dates (2024-01-15)       | a date           |
      | yes/no values (true, false)       | a boolean flag   |
      | free-form text (names, addresses) | text             |
