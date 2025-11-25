# AISDLC Method Reference

Quick reference for the AI SDLC methodology.

## 7 Stages

```
Intent → Requirements → Design → Tasks → Code → System Test → UAT → Runtime
           ↑                                                           ↓
           └─────────────────── Feedback Loop ─────────────────────────┘
```

## Stage Summary

| Stage | Agent | Purpose | Output |
|-------|-------|---------|--------|
| 1 | Requirements | Transform intent to REQ-* keys | docs/requirements/*.md |
| 2 | Design | Technical architecture | docs/design/, ADRs |
| 3 | Tasks | Work breakdown | .ai-workspace/tasks/ |
| 4 | Code | TDD implementation | src/, tests/ |
| 5 | System Test | BDD integration | features/*.feature |
| 6 | UAT | Business validation | docs/uat/ |
| 7 | Runtime | Production feedback | alerts, metrics |

## Key Principles (Code Stage)

1. **Test Driven Development** - No code without tests
2. **Fail Fast & Root Cause** - Break loudly, fix completely
3. **Modular & Maintainable** - Single responsibility
4. **Reuse Before Build** - Check first, create second
5. **Open Source First** - Research alternatives
6. **No Legacy Baggage** - Clean slate, no debt
7. **Perfectionist Excellence** - Best of breed only

**Mantra**: "Excellence or nothing"

## TDD Cycle

```
RED → GREEN → REFACTOR → COMMIT → REPEAT
```

## REQ-* Format

```
REQ-<TYPE>-<DOMAIN>-<NUMBER>

Types: F (functional), NFR (non-functional), DATA, BR (business rule)
Example: REQ-F-AUTH-001
```

## Tagging

Code: `# Implements: REQ-F-*`
Tests: `# Validates: REQ-F-*`
Commits: Include REQ-* in message

## Coverage

- Minimum: 80% overall
- Critical paths: 100%

## Feedback Protocol

```
FEEDBACK to <Agent>:
Type: gap | ambiguity | clarification | error | conflict
REQ: <key>
Issue: <description>
Suggestion: <resolution>
```

---

*This is a summary. Full methodology in docs/ai_sdlc_method.md*
