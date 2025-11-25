# BDD Workflow

Behavior-Driven Development workflow for System Test (Stage 5) and UAT (Stage 6).

## Given/When/Then Pattern

```gherkin
Given <precondition>
When <action>
Then <expected result>
```

## Feature File Structure

```gherkin
Feature: <Feature Name>
  # Validates: REQ-F-<DOMAIN>-<NUMBER>

  As a <role>
  I want <capability>
  So that <benefit>

  Background:
    Given <common setup for all scenarios>

  Scenario: <Scenario Name>
    # Validates: REQ-F-<DOMAIN>-<NUMBER>
    Given <precondition>
    And <additional precondition>
    When <action>
    And <additional action>
    Then <expected result>
    And <additional expectation>

  Scenario Outline: <Parameterized Scenario>
    # Validates: REQ-F-<DOMAIN>-<NUMBER>
    Given <precondition with <parameter>>
    When <action>
    Then <expected result>

    Examples:
      | parameter | expected |
      | value1    | result1  |
      | value2    | result2  |
```

## Example: Authentication Feature

```gherkin
Feature: User Authentication
  # Validates: REQ-F-AUTH-001

  As a registered user
  I want to log in with my credentials
  So that I can access my account

  Background:
    Given the authentication service is running
    And the database contains test users

  Scenario: Successful login with valid credentials
    # Validates: REQ-F-AUTH-001
    Given I am on the login page
    And I have a registered account with email "user@example.com"
    When I enter email "user@example.com"
    And I enter password "validPassword123"
    And I click the login button
    Then I should be redirected to the dashboard
    And I should see "Welcome back"

  Scenario: Failed login with invalid password
    # Validates: REQ-F-AUTH-001
    Given I am on the login page
    When I enter email "user@example.com"
    And I enter password "wrongPassword"
    And I click the login button
    Then I should see an error message "Invalid credentials"
    And I should remain on the login page

  Scenario Outline: Login validation
    # Validates: REQ-DATA-AUTH-001
    Given I am on the login page
    When I enter email "<email>"
    And I enter password "<password>"
    And I click the login button
    Then I should see "<message>"

    Examples:
      | email           | password | message              |
      |                 | pass123  | Email is required    |
      | invalid-email   | pass123  | Invalid email format |
      | user@test.com   |          | Password is required |
```

## Step Definitions

```python
# features/steps/auth_steps.py
# Validates: REQ-F-AUTH-001

from behave import given, when, then

@given('I am on the login page')
def step_on_login_page(context):
    context.browser.get('/login')

@when('I enter email "{email}"')
def step_enter_email(context, email):
    context.browser.find_element_by_id('email').send_keys(email)

@when('I click the login button')
def step_click_login(context):
    context.browser.find_element_by_id('login-btn').click()

@then('I should see "{text}"')
def step_should_see(context, text):
    assert text in context.browser.page_source
```

## REQ-* Tagging Rules

### Feature Level
Tag the entire feature with primary requirement:
```gherkin
Feature: User Authentication
  # Validates: REQ-F-AUTH-001
```

### Scenario Level
Tag each scenario with specific requirement:
```gherkin
Scenario: Successful login
  # Validates: REQ-F-AUTH-001
```

### Multiple Requirements
Use multiple tags for scenarios covering multiple REQs:
```gherkin
Scenario: Login with MFA
  # Validates: REQ-F-AUTH-001, REQ-NFR-SEC-001
```

## System Test vs UAT

### System Test (Stage 5)
- Technical language allowed
- Tests integration points
- Automated execution
- Focus on correctness

### UAT (Stage 6)
- Pure business language
- Tests user workflows
- May include manual steps
- Focus on business value

## Quality Gates

- [ ] All REQ-F-* have feature files
- [ ] All scenarios tagged with REQ-* keys
- [ ] Step definitions implemented
- [ ] Scenarios pass in CI/CD
- [ ] Coverage reported per requirement
