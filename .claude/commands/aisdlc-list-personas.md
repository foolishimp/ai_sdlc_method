# List Available Personas

<!-- Implements: REQ-F-CMD-003 (Persona management) -->

Show all available role-based personas that can be applied to project contexts.

## Usage

```
/aisdlc-list-personas
```

## Available Personas

- **business_analyst** - Requirements, user stories (hides technical details)
- **software_engineer** - Code quality, TDD, SOLID principles (90% unit coverage)
- **qa_engineer** - Test coverage, 7 testing levels, 80% automation
- **data_architect** - Data modeling, 3NF normalization, ERD diagrams
- **security_engineer** - Security & compliance, 4-hour critical fix SLA
- **devops_engineer** - CI/CD, infrastructure as code, blue-green deployments

## What Are Personas?

Personas let you view the same project through different role lenses:
- **Business Analysts** see requirements, hide implementation
- **Engineers** see full technical details
- **QA** focuses on testing and quality gates
- **Security** enforces zero-tolerance for vulnerabilities
- **DevOps** ensures deployability and monitoring

## See Also

- `/aisdlc-apply-persona` - Apply a persona to current context
- `/aisdlc-switch-persona` - Switch between personas
- `/aisdlc-persona-checklist` - Get persona-specific review checklist
