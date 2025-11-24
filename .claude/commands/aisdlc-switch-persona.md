# Switch Persona

<!-- Implements: REQ-F-CMD-003 (Persona management) -->

Switch from one persona to another and see what changed in focus areas.

## Usage

```
/aisdlc-switch-persona <new-persona-name>
```

## Example

```bash
# Switch from engineer to QA
/aisdlc-switch-persona qa_engineer

# Claude reports:
# Switched from software_engineer to qa_engineer
#
# Added Focus Areas:
#   ✚ Test planning
#   ✚ Test automation
#   ✚ Quality assurance
#
# Removed Focus Areas:
#   ✖ Code implementation
#   ✖ Technical design
```

## Use Cases

**During Code Review:**
```bash
# Start with engineer perspective
/aisdlc-apply-persona software_engineer
# Review code quality...

# Switch to security perspective
/aisdlc-switch-persona security_engineer
# Review security issues...

# Switch to DevOps perspective
/aisdlc-switch-persona devops_engineer
# Review deployability...
```

## See Also

- `/aisdlc-apply-persona` - Apply initial persona
- `/aisdlc-list-personas` - See all personas
- `/aisdlc-persona-checklist` - Get review checklist
