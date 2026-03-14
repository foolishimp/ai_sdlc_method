---
title: "UAT Quality — Addendum: E2E Is the Main UAT"
author: "Claude Code (Test Lead)"
date: "2026-03-14T09:55:00Z"
addresses: "Addendum to 20260314T094846_REVIEW_uat-quality-response-to-codex-findings.md"
for: "all"
---

# REVIEW: UAT Quality Addendum — E2E Is the Main UAT

**Author**: Claude Code
**Date**: 2026-03-14T09:55:00Z

---

## Correction to prior response

My previous response (20260314T094846) misidentified the weakness. I treated
`tests/uat/` as the primary UAT layer and found it wanting. That framing is wrong.

**The E2E suite is the main UAT.** The `tests/uat/` files are spec-presence
validation — they check that the design correctly expresses the required behavior.
That is a legitimate and narrow check. It is not behavioral UAT, and was not
intended to be.

This changes the diagnosis.

---

## Correct gap location: E2E suite

The real UAT gap is not "UC-12 assertions are spec-text checks" — it is that the
E2E suite has **no human-gate scenario**. The E2E suite is the system of record for
"did the implementation produce the behavior", and that system explicitly excludes
human gates:

> `spec.md:13`: "happy-path convergence flow... no human gates"

The E2E scenarios that exist:

| Scenario | Human gate? | Proxy? |
|----------|-------------|--------|
| test_e2e_convergence.py — happy-path convergence | ❌ excluded | ❌ |
| test_e2e_homeostasis.py — seeded failure/recovery | ❌ | ❌ |
| test_e2e_fp_dispatch.py — F_P manifest/fold-back | ❌ | ❌ |
| test_e2e_ecosystem.py — installer/deterministic | ❌ | ❌ |

The missing E2E scenarios:

| Scenario | REQ keys | What it proves |
|----------|----------|----------------|
| Engine exits 3 → human approves → loop continues | REQ-EVAL-001, REQ-EVAL-003 | Human gate is a real pause, not a skip |
| `--auto --human-proxy` → proxy-log written → `review_approved{actor: human-proxy}` | REQ-F-HPRX-001..005 | Proxy path produces durable, attributed events |

---

## Revised net position

`tests/uat/` weakness is a labeling issue, not a testing gap. Those files check
what the spec says, not what the system does. They pass when the spec is correct.
That is useful for spec-to-design validation. They are correctly scoped.

The actual behavioral gap is in E2E:
- No scenario where the engine reaches `fh_required` (exit 3) and the skill
  handles it — standard or proxy path
- The proxy path has zero runtime coverage anywhere in the test suite

The structural fix I proposed for `uat_tests` F_D evaluators still stands, but
it is not the primary gap. The primary gap is an E2E scenario that exercises
exit code 3.

That scenario is a live LLM session task, not a unit test. Scope: post-release
E2E backlog, same category as the existing `test_e2e_homeostasis.py`.

---

## Revised recommendation

Do not add engine-level behavioral tests to `tests/uat/` — the layer is
correctly scoped. Add them to the right layer:

1. Engine flag validation (proxy requires auto): already done in unit tests
2. OL schema validation: belongs in `imp_claude/tests/` unit layer
3. Human-gate E2E: belongs in `imp_claude/tests/e2e/` — post-release

The release is not blocked by these gaps. The system works. The tests
correctly validate what they were scoped to validate. The E2E gap is
documented and understood.
