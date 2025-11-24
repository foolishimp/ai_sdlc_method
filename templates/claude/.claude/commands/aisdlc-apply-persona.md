# Apply Persona

<!-- Implements: REQ-F-CMD-003 (Persona management) -->

Apply a role-based persona to the current project context. This customizes how Claude views and interacts with the project.

## Usage

```
/aisdlc-apply-persona <persona-name>
```

## Available Personas

- `business_analyst` - Focus on requirements and business logic
- `software_engineer` - Focus on code quality and testing
- `qa_engineer` - Focus on test coverage and quality gates  
- `data_architect` - Focus on data modeling and schema
- `security_engineer` - Focus on security and compliance
- `devops_engineer` - Focus on deployment and infrastructure

## What Happens

When you apply a persona, Claude will:
1. Load role-specific focus areas
2. Apply persona overrides (highest priority)
3. Show role-specific review checklist
4. Adapt responses to role perspective

## Examples

```bash
# Apply security engineer persona
/aisdlc-apply-persona security_engineer

# Claude now focuses on:
# • Security vulnerabilities
# • Compliance requirements
# • Encryption and authentication
# • Zero-tolerance for critical issues
```

```bash
# Apply business analyst persona
/aisdlc-apply-persona business_analyst

# Claude now focuses on:
# • Business requirements
# • User stories and acceptance criteria
# • Business logic (hides technical details)
```

## Combining with Contexts

Personas work ON TOP of project contexts:

```bash
# Load project then apply persona
/load-context payment_gateway
/aisdlc-apply-persona security_engineer

# Result: Payment gateway requirements + security focus
```

## See Also

- `/aisdlc-list-personas` - See all available personas
- `/aisdlc-switch-persona` - Switch to different persona
- `/aisdlc-persona-checklist` - Get review checklist
