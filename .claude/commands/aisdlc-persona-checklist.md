# Get Persona Review Checklist

<!-- Implements: REQ-F-CMD-003 (Persona management) -->

Get the code review checklist for the current or specified persona.

## Usage

```
/aisdlc-persona-checklist [persona-name]
```

If no persona name is provided, shows checklist for currently active persona.

## Example Output

**Security Engineer Checklist:**
```
Security Review Checklist:

□ Are there security vulnerabilities?
□ Is authentication proper?
□ Is data encrypted?
□ Are inputs validated?
□ Are secrets properly managed?
```

**QA Engineer Checklist:**
```
QA Review Checklist:

□ Are there adequate tests?
□ Are edge cases covered?
□ Is test data representative?
□ Are tests maintainable?
□ Is test coverage sufficient?
```

**DevOps Engineer Checklist:**
```
DevOps Review Checklist:

□ Is this deployable?
□ Are there deployment scripts?
□ Is rollback possible?
□ Are there monitoring hooks?
□ Is infrastructure code present?
```

## Examples

```bash
# Get checklist for current persona
/aisdlc-persona-checklist

# Get checklist for specific persona
/aisdlc-persona-checklist security_engineer
```

## See Also

- `/aisdlc-apply-persona` - Apply a persona
- `/aisdlc-list-personas` - See all personas
