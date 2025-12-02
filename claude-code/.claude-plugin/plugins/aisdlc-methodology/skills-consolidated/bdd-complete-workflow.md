---
name: bdd-complete-workflow
description: Complete Behavior-Driven Development workflow - SCENARIO (Given/When/Then) → STEP DEFINITIONS → IMPLEMENT → REFACTOR. Consolidates bdd-workflow, write-scenario, implement-step-definitions, implement-feature, refactor-bdd.
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
---

# BDD Complete Workflow

**Skill Type**: Complete Workflow (System Test / UAT Stage)
**Purpose**: Create executable specifications using Given/When/Then scenarios
**Consolidates**: bdd-workflow, write-scenario, implement-step-definitions, implement-feature, refactor-bdd

---

## When to Use This Skill

Use this skill when:
- Writing integration or acceptance tests
- Stakeholders need readable test documentation
- Requirements are expressed as user stories
- Business validation is the focus
- System Test or UAT stage of SDLC

**BDD vs TDD**:
- **BDD**: High-level behavior (user/business perspective) - Given/When/Then
- **TDD**: Low-level implementation (developer perspective) - unit tests

Both can coexist: BDD for acceptance tests, TDD for unit tests.

---

## Prerequisites

Before starting, verify:
1. Requirement key exists (REQ-F-*, REQ-NFR-*)
2. Requirement details available (user story format ideal)
3. BDD framework available (Cucumber, Behave, SpecFlow)
4. Working directory is a git repository

**If prerequisites missing**:
- No REQ-* key → Use `requirements-extraction` skill first
- No BDD framework → Install one (Behave for Python, Cucumber for JS/Java)

---

## Complete Workflow

### Phase 1: SCENARIO (Write Given/When/Then)

**Goal**: Write behavior scenarios in PURE BUSINESS LANGUAGE.

**Steps**:

1. **Understand the User Story**
   ```
   As a [persona]
   I want to [capability]
   So that [benefit]
   ```

2. **Create Feature File**

   **Gherkin Format** (all BDD frameworks):
   ```gherkin
   # features/authentication.feature

   # Validates: REQ-F-AUTH-001
   # Business Rules: BR-001, BR-002, BR-003

   Feature: User Authentication
     As a customer
     I want to log in with my email and password
     So that I can access my account information

     Background:
       Given I am on the login page

     @REQ-F-AUTH-001 @happy-path
     Scenario: Successful login with valid credentials
       Given I have a registered account with email "user@example.com"
       When I enter my email "user@example.com"
       And I enter my password "SecurePass123!"
       And I click the "Login" button
       Then I should see "Welcome back"
       And I should be on the dashboard page

     @REQ-F-AUTH-001 @BR-001
     Scenario: Login fails with invalid email format
       When I enter my email "invalid-email"
       And I enter my password "SecurePass123!"
       And I click the "Login" button
       Then I should see an error "Invalid email format"

     @REQ-F-AUTH-001 @BR-002
     Scenario: Login fails with short password
       When I enter my email "user@example.com"
       And I enter my password "short"
       And I click the "Login" button
       Then I should see an error "Password must be at least 12 characters"

     @REQ-F-AUTH-001 @BR-003
     Scenario: Account locks after 3 failed attempts
       Given I have a registered account with email "user@example.com"
       When I enter wrong password 3 times
       Then I should see "Account locked. Try again in 15 minutes"
       And I should not be able to attempt login

     @REQ-F-AUTH-001 @edge-case
     Scenario Outline: Email validation edge cases
       When I enter my email "<email>"
       And I enter my password "SecurePass123!"
       And I click the "Login" button
       Then I should see an error "<error>"

       Examples:
         | email              | error                  |
         |                    | Email is required      |
         | missing@           | Invalid email format   |
         | @nodomain.com      | Invalid email format   |
   ```

**Key Rules for Scenarios**:
- PURE business language (no technical jargon)
- Each scenario tests ONE behavior
- Tag scenarios with REQ-* keys
- Use Background for common setup
- Use Scenario Outline for data-driven tests

3. **Commit SCENARIO Phase**
   ```bash
   git add features/
   git commit -m "SCENARIO: Add scenarios for REQ-F-AUTH-001

   Write Given/When/Then scenarios for user login.

   Scenarios: 5 (happy path, BR-001, BR-002, BR-003, edge cases)
   Validates: REQ-F-AUTH-001
   Business language: Pure (no technical jargon)
   "
   ```

---

### Phase 2: STEP DEFINITIONS (Implement Test Code)

**Goal**: Translate Given/When/Then into executable test code.

**Steps**:

1. **Create Step Definitions**

   **Python (Behave)**:
   ```python
   # features/steps/authentication_steps.py

   # Step definitions for: REQ-F-AUTH-001

   from behave import given, when, then
   from selenium import webdriver
   from pages.login_page import LoginPage

   @given('I am on the login page')
   def step_on_login_page(context):
       # Validates: REQ-F-AUTH-001 (setup)
       context.browser = webdriver.Chrome()
       context.login_page = LoginPage(context.browser)
       context.login_page.navigate()

   @given('I have a registered account with email "{email}"')
   def step_registered_account(context, email):
       # Validates: REQ-F-AUTH-001 (precondition)
       context.test_user = create_test_user(email=email)

   @when('I enter my email "{email}"')
   def step_enter_email(context, email):
       context.login_page.enter_email(email)

   @when('I enter my password "{password}"')
   def step_enter_password(context, password):
       context.login_page.enter_password(password)

   @when('I click the "{button}" button')
   def step_click_button(context, button):
       context.login_page.click_button(button)

   @when('I enter wrong password {count:d} times')
   def step_wrong_password_times(context, count):
       for _ in range(count):
           context.login_page.enter_password("wrong_password")
           context.login_page.click_button("Login")

   @then('I should see "{message}"')
   def step_see_message(context, message):
       assert message in context.login_page.get_page_text()

   @then('I should see an error "{error}"')
   def step_see_error(context, error):
       assert context.login_page.get_error_message() == error

   @then('I should be on the dashboard page')
   def step_on_dashboard(context):
       assert "dashboard" in context.browser.current_url

   @then('I should not be able to attempt login')
   def step_login_disabled(context):
       assert context.login_page.is_login_disabled()
   ```

   **TypeScript (Cucumber)**:
   ```typescript
   // features/step_definitions/authentication.steps.ts

   // Step definitions for: REQ-F-AUTH-001

   import { Given, When, Then } from '@cucumber/cucumber';
   import { LoginPage } from '../pages/login.page';

   let loginPage: LoginPage;

   Given('I am on the login page', async function() {
     // Validates: REQ-F-AUTH-001 (setup)
     loginPage = new LoginPage(this.browser);
     await loginPage.navigate();
   });

   Given('I have a registered account with email {string}', async function(email: string) {
     // Validates: REQ-F-AUTH-001 (precondition)
     await createTestUser({ email });
   });

   When('I enter my email {string}', async function(email: string) {
     await loginPage.enterEmail(email);
   });

   When('I enter my password {string}', async function(password: string) {
     await loginPage.enterPassword(password);
   });

   When('I click the {string} button', async function(button: string) {
     await loginPage.clickButton(button);
   });

   Then('I should see {string}', async function(message: string) {
     const text = await loginPage.getPageText();
     expect(text).toContain(message);
   });

   Then('I should see an error {string}', async function(error: string) {
     const errorMessage = await loginPage.getErrorMessage();
     expect(errorMessage).toBe(error);
   });
   ```

2. **Run Scenarios (Expect FAILURE)**
   ```bash
   # Python (Behave)
   behave features/authentication.feature

   # JavaScript (Cucumber)
   npm run cucumber features/authentication.feature
   ```

   Expected: Steps run but fail (implementation doesn't exist).

3. **Commit STEP DEFINITIONS Phase**
   ```bash
   git add features/steps/
   git commit -m "STEP DEF: Add step definitions for REQ-F-AUTH-001

   Implement step definitions for Given/When/Then steps.

   Steps: 10 step definitions
   Scenarios running: FAILED (expected - no implementation)
   Validates: REQ-F-AUTH-001
   "
   ```

---

### Phase 3: IMPLEMENT (Make Scenarios Pass)

**Goal**: Implement feature code to make scenarios pass.

**Steps**:

1. **Implement Feature Code**
   (Same as TDD GREEN phase - write code tagged with REQ-*)

2. **Implement Page Objects** (if using Selenium/Playwright)
   ```python
   # pages/login_page.py

   # Page object for: REQ-F-AUTH-001

   class LoginPage:
       def __init__(self, driver):
           self.driver = driver
           self.url = "/login"

       def navigate(self):
           self.driver.get(f"{BASE_URL}{self.url}")

       def enter_email(self, email: str):
           self.driver.find_element_by_id("email").send_keys(email)

       def enter_password(self, password: str):
           self.driver.find_element_by_id("password").send_keys(password)

       def click_button(self, button: str):
           self.driver.find_element_by_xpath(f"//button[text()='{button}']").click()

       def get_error_message(self) -> str:
           return self.driver.find_element_by_class_name("error-message").text

       def get_page_text(self) -> str:
           return self.driver.page_source
   ```

3. **Run Scenarios (Expect SUCCESS)**
   ```bash
   behave features/authentication.feature
   ```

4. **Commit IMPLEMENT Phase**
   ```bash
   git add src/ pages/
   git commit -m "IMPLEMENT: Implement REQ-F-AUTH-001

   Add authentication feature to pass BDD scenarios.

   Implements: REQ-F-AUTH-001
   Scenarios: All passing
   "
   ```

---

### Phase 4: REFACTOR (Quality + Tech Debt)

**Goal**: Improve code quality without changing behavior.

**Steps**:

1. **Refactor Feature Code** - Same as TDD REFACTOR
2. **Refactor Step Definitions**
   - Reuse common steps
   - Extract helpers
   - Improve readability

3. **Run Scenarios (Expect STILL PASSING)**

4. **Commit REFACTOR Phase**
   ```bash
   git commit -m "REFACTOR: Clean up REQ-F-AUTH-001

   Step Definitions:
   - Extracted common setup to hooks
   - Improved step reusability

   Code Quality:
   - Added type hints
   - Improved docstrings

   Scenarios: Still passing
   "
   ```

---

## Output Format

When BDD workflow completes, show:

```
[BDD Workflow: REQ-F-AUTH-001]

Phase 1: SCENARIO (Given/When/Then)
  Created: features/authentication.feature
  Scenarios: 5 (business language)
  Commit: SCENARIO: Add scenarios for REQ-F-AUTH-001

Phase 2: STEP DEFINITIONS
  Created: features/steps/authentication_steps.py
  Steps: 10 step definitions
  Scenarios: FAILED (expected)
  Commit: STEP DEF: Add step definitions for REQ-F-AUTH-001

Phase 3: IMPLEMENT
  Created: src/auth/authentication.py, pages/login_page.py
  Scenarios: PASSED
  Commit: IMPLEMENT: Implement REQ-F-AUTH-001

Phase 4: REFACTOR
  Improved: Step reusability, code quality
  Scenarios: Still passing
  Commit: REFACTOR: Clean up REQ-F-AUTH-001

BDD Workflow Complete!
  Feature File: authentication.feature (5 scenarios)
  Step Definitions: 10 steps
  Page Objects: 1 (login_page.py)
  Traceability: REQ-F-AUTH-001 → commit xyz789
```

---

## Gherkin Best Practices

### Use Business Language
```gherkin
# GOOD - Business language
Given I have $100 in my savings account
When I withdraw $30
Then I should have $70 remaining

# BAD - Technical jargon
Given the database has record id=123 with balance=100
When POST /api/withdraw {"amount": 30}
Then the response body balance equals 70
```

### One Behavior Per Scenario
```gherkin
# GOOD - Single behavior
Scenario: Successful withdrawal
  Given I have $100 in my account
  When I withdraw $30
  Then I should have $70 remaining

# BAD - Multiple behaviors
Scenario: Various account operations
  Given I have $100
  When I withdraw $30
  Then I have $70
  When I deposit $50
  Then I have $120
```

### Use Tags for Traceability
```gherkin
@REQ-F-PAYMENT-001 @happy-path @smoke
Scenario: Successful payment

@REQ-F-PAYMENT-001 @BR-001 @regression
Scenario: Payment fails with expired card
```

### Use Background for Common Setup
```gherkin
Background:
  Given I am logged in as "customer@example.com"
  And I am on the checkout page

Scenario: Successful checkout
  When I enter valid payment details
  ...

Scenario: Failed checkout - expired card
  When I enter expired card details
  ...
```

---

## BDD Framework Quick Reference

### Python (Behave)
```bash
pip install behave selenium
behave features/
behave --tags=@REQ-F-AUTH-001  # Run specific requirement
```

### JavaScript (Cucumber)
```bash
npm install @cucumber/cucumber puppeteer
npx cucumber-js features/
npx cucumber-js --tags "@REQ-F-AUTH-001"
```

### Java (Cucumber)
```xml
<dependency>
  <groupId>io.cucumber</groupId>
  <artifactId>cucumber-java</artifactId>
</dependency>
```

### .NET (SpecFlow)
```bash
dotnet add package SpecFlow.NUnit
```

---

## Configuration

```yaml
# .claude/plugins.yml
plugins:
  - name: "@aisdlc/aisdlc-methodology"
    config:
      bdd:
        gherkin_style: "cucumber"     # cucumber | behave | specflow
        require_scenarios_for_requirements: true
        scenario_language: "en"
        include_backgrounds: true
        tag_scenarios_with_req_keys: true
```

---

## Homeostasis Behavior

**If prerequisites not met**:
- Detect: Missing REQ-* key or user story
- Signal: "Need requirement extraction first"
- Action: Use `requirements-extraction` skill

**If scenarios fail in IMPLEMENT phase**:
- Detect: Scenarios still failing after implementation
- Signal: "Implementation incomplete"
- Action: Fix implementation
- Do NOT proceed to REFACTOR until scenarios pass

---

## Key Principles Applied

1. **Test Driven Development** - Scenarios written before implementation
2. **Modular & Maintainable** - Page objects, reusable steps
3. **Perfectionist Excellence** - Business-readable specifications

**"Excellence or nothing"**
