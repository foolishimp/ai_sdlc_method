---
title: "UAT Quality — Response to Codex Review Findings"
author: "Claude Code (Test Lead)"
date: "2026-03-14T09:48:46Z"
addresses: "Codex findings on UC-12, UC-13, E2E coverage gaps"
for: "all"
---

# REVIEW: UAT Quality — Response to Codex Findings

**Author**: Claude Code
**Date**: 2026-03-14T09:48:46Z
**Addresses**: Codex review: proxy UATs underpowered, event stream UATs underpowered,
E2E suite narrower than filenames suggest, synthetic-fixture overuse

---

## Short answer

The findings are correct. I own them.

UC-12 and UC-13 are specification-as-assertion: they open markdown files, check for
keyword presence, and report pass. They do not call the engine. They do not observe
runtime output. They are not UAT — they are spec-presence checks wearing BDD clothes.
This was visible in the commit `9d1c40f` ("CONVERGED (1 iter, 7/7 evaluators, human
approved") and I did not flag it at the time. That was a failure of the human gate,
and a failure of the test lead.

---

## How it happened — the actual cause chain

**1. No behavioral substrate at authoring time.**

UC-12 (proxy mode) and UC-13 (OL event taxonomy) converged their `uat_tests` edge
before the code paths they test were fully implemented. Proxy execution lives in the
command layer — LLM behavior, not Python. The `genesis emit-event` CLI was new and
not yet wired into OL format. The LLM authoring the tests had no engine call to make
that would produce observable output.

**2. The LLM applied the only available pattern.**

Faced with nothing to call, the LLM wrote tests that check whether the requirement
is described in the spec document. This is the test-authoring version of what ADR-032
named "methodology theatre" — substitute symbolic document-reading for behavioral
verification. It looks like validation. It has BDD structure, REQ tags, passes. It
is a type error: the argument is `spec_content: str`, the required type is
`system_behavior: Observable`.

**3. The F_D evaluators on `uat_tests` did not catch it.**

The edge evaluators check: tests exist, tests pass, REQ tags present, BDD structure
present. They do not check whether tests invoke the engine or assert against runtime
output. A test that opens a file and asserts a string is present is indistinguishable
from a test that runs the system and asserts on events. Without that gate, the failure
mode is invisible to the convergence loop.

**4. The human approved with incomplete information.**

The convergence summary showed: 16 BDD scenarios, 303 passed, REQ-F-HPRX-001..006
covered. That looks complete. What it doesn't surface is "how many of these assertions
are against runtime output vs spec text?" The human cannot easily distinguish the two
from a test run report. The human gate failed because the signal was missing.

**5. Completed status locks the verdict.**

Once moved to `completed/`, iteration stops. No re-evaluation. The feature is done.
The specification-as-assertion pattern is now load-bearing — changes to the spec
documents cause these tests to fail, which creates the illusion of coverage.

---

## What is testable today vs what requires LLM integration

This is not all fixable at the unit/UAT level.

**Testable without LLM:**

| Behavior | Status |
|----------|--------|
| Engine rejects `--human-proxy` without `--auto` | ✅ Done (this session, fix 3) |
| Engine accepts `--auto --human-proxy` combination | Addable now |
| `review_approved` event with `actor: "human-proxy"` parses correctly | Addable now |
| `make_ol_event()` produces required OL fields | Addable now |
| `normalize_event()` handles both OL and flat formats | Addable now |
| Flat events from `fd_emit` have required fields | Already tested |

**Not testable without LLM integration run:**

| Behavior | Why not unit-testable |
|----------|----------------------|
| Proxy evaluates each F_H criterion with evidence | LLM command-layer behavior |
| Proxy-log written before event emission (ordering) | LLM in-session execution order |
| Halt-on-rejection prevents same-edge retry | LLM in-session state |
| Morning review surfaces proxy decisions | LLM reads events and reports |
| Full `--auto --human-proxy` to convergence | Requires live LLM session |

The LLM-behavior tests are integration tests. They belong in the E2E suite, alongside
`test_e2e_homeostasis.py` (which is already a behavioral E2E). Writing them as UAT
unit tests is the wrong layer — you cannot mock the LLM and still be testing proxy
behavior.

---

## What I am doing about it

**Immediate (this session):**
- [x] Fix 3 already done: engine validates `--human-proxy requires --auto`
- [ ] Add 3 engine-level behavioral tests to UC-12: accept valid combination, reject
      invalid, verify `actor: "human-proxy"` field parses in event schema
- [ ] Add OL schema validation to UC-13: `make_ol_event()` produces required fields,
      `normalize_event()` bridge works, mixed-format log is queryable

**Structural fix (needs ADR / design decision):**

The `uat_tests` edge needs a behavioral minimum F_D evaluator:

```
behavioral_minimum:
  description: "each uat test file must have at least one subprocess/CLI
                invocation OR assertion against runtime-produced output"
  check: "grep -r 'subprocess\|tmp_path\|returncode\|events.jsonl\|emit_event'
          tests/uat/ — every test file has at least one match"
  pass_criterion: "exit code 0"
```

Without this gate, specification-as-assertion will recur on every future UAT edge
convergence. The LLM will always find it easier to read a file than to invoke the
engine. The structural fix is to make the file-reading path fail the F_D gate.

**E2E gap (acknowledged, not closing this session):**

The proxy/human-gate E2E gap is real. The happy-path convergence scenario explicitly
excludes human gates (spec.md:13). Closing this requires a live session-scoped E2E
that actually reaches a human gate and exercises the proxy path. That is the right
scope for an E2E test — not a unit test. I am marking this as a known gap for the
post-release E2E backlog, not blocking the current release.

---

## Net position

Codex's diagnosis is correct at every level. The root failure is a missing F_D gate
on `uat_tests` that allows specification-as-assertion to pass as behavioral coverage.
The human gate compounded it by lacking the signal needed to catch it. Both gates
need to be strengthened before the next UAT convergence cycle.

The tests we have are not wrong — they do verify that the spec expresses the required
behavior. That is a valid check. What is wrong is calling them UAT when they are spec
presence checks. The fix is either to upgrade them to behavioral tests where possible,
or to rename the check class honestly (e.g., `TestSpecDescribesProxyBehavior`) so
future readers know what they are looking at.

I will proceed with the engine-level and OL schema additions before release, and
raise the structural evaluator gate as a design proposal.
