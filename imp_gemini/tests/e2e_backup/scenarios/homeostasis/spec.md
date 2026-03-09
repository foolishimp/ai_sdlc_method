# BDD Spec — Homeostatic Loop Closure

**Scenario**: `homeostasis`
**Executable test**: `imp_gemini/tests/e2e/test_e2e_homeostasis.py`
**Derived from**: `specification/verification/UAT_TEST_CASES.md`
**Satisfies**: UC-01 (UC-01-12, UC-01-14), UC-02, UC-07 (UC-07-03)
**Validates**: REQ-SUPV-003, REQ-EVAL-001, REQ-EVAL-002, REQ-ITER-001, REQ-ITER-002

---

## Scenario Overview

A project is seeded with **deliberately wrong code** at the `code↔unit_tests` edge
(wrong mathematical formulas). Headless Gemini must detect the failure, record it as
events, produce corrective iterations, and eventually achieve delta=0.

This proves the methodology's core claim: **failures are detected, recorded, and drive
correction** — not just claimed by the agent.

The scenario starts from the `code↔unit_tests` edge only (earlier edges pre-converged)
to save ~10 minutes of Gemini time.

---

## Fixture: IN_PROGRESS (homeostasis-project)

```
homeostasis-project/
  CLAUDE.md
  pyproject.toml
  specification/
    INTENT.md                    # same temperature-converter intent
  src/
    temperature_converter.py     # WRONG formulas (deliberately seeded)
  tests/
    test_temperature_converter.py  # correct tests (will FAIL against wrong code)
  .ai-workspace/
    graph/                       # standard graph topology
    gemini_genesis/context/
      project_constraints.yml
    features/
      active/
        REQ-F-FAIL-001.yml       # status: in_progress, trajectory:
                                 #   intent→requirements: converged
                                 #   requirements→design: converged
                                 #   design→code: converged
                                 #   code↔unit_tests: in_progress (pre-seeded)
    events/
      events.jsonl               # pre-loaded with edge_started for code↔unit_tests
    ...
```

Scaffolded by `homeostasis_project` session fixture in `test_e2e_homeostasis.py`.

---

## Scenario: RED → GREEN Correction

```gherkin
Given a project with deliberately wrong temperature conversion formulas
  Source file has incorrect formulas:
    celsius_to_fahrenheit: C * 9/5 (missing + 32)
    fahrenheit_to_celsius: (F - 32) (missing * 5/9)
  Test suite has correct expected values (will fail against wrong code)
  Feature vector shows code↔unit_tests edge as in_progress (iteration 0)

When I run headless Gemini:
  gemini start --feature "REQ-F-FAIL-001"
  With budget cap: $10.00 USD
  With wall timeout: 45 minutes

Then the following homeostatic correction is observable:
```

---

### UC-01-12: Multi-Iteration Convergence

```gherkin
Given the event log after the run

When I inspect iteration_completed events for REQ-F-FAIL-001 on code↔unit_tests

Then there are at least 2 iteration_completed events for this edge
And the first iteration has delta > 0 (tests failing)
And the final iteration before edge_converged has delta = 0
And delta does not increase between iterations
  (each iteration either holds steady or decreases)
```

`Executable`: `TestE2EHomeostasis.test_multiple_iterations_produced`,
`test_delta_never_increases`

---

### UC-01-14 / UC-02-A: Evaluator Failure Recording

```gherkin
Given the first iteration_completed event on code↔unit_tests

When I inspect the evaluator_details

Then at least 1 evaluator has result="fail"
And failing evaluators include:
  - tests_pass: fail (pytest exit code non-zero)
  OR
  - test_coverage: fail (coverage below threshold)
And each failing evaluator includes a structured finding (actual vs expected,
  or error message, or file list)
```

`Executable`: `TestE2EHomeostasis.test_first_iteration_has_failures`,
`test_evaluator_failure_details_recorded`

---

### UC-02-B: Failure Observability (REQ-SUPV-003)

```gherkin
Given the failing iteration events

When I examine evaluator_detail events

Then each failing check is recorded with:
  - name (e.g. "tests_pass", "test_coverage")
  - result: "fail"
  - structured context (actual value, threshold, files affected, etc.)
And the event log provides enough information to reproduce and diagnose
  the failure without re-running Gemini
```

`Executable`: `TestE2EHomeostasis.test_evaluator_failure_details_recorded`,
`test_failure_context_is_diagnostic`

---

### UC-07-03: Homeostatic Chain — Failure → Intent → Correction

```gherkin
Given the full event log for REQ-F-FAIL-001

When I analyse the causal chain of events

Then I can identify the homeostatic correction sequence:
  1. edge_started (code↔unit_tests)
  2. iteration_completed (delta > 0, evaluators: fail)  ← failure detected
  3. iteration_completed (delta decreasing)              ← correction in progress
  ...
  N. iteration_completed (delta = 0)                    ← convergence achieved
  N+1. edge_converged                                    ← promoted to Markov object

And the correction chain is fully causal:
  each iteration follows the previous with decreasing delta
And edge_converged is only emitted after delta = 0
```

`Executable`: `TestE2EHomeostasis.test_homeostatic_chain_observable`,
`test_edge_converged_only_after_delta_zero`

---

### UC-02-C: Final Convergence After Correction

```gherkin
Given the corrected project state

When I inspect code↔unit_tests outcome

Then edge_converged is present in events.jsonl for REQ-F-FAIL-001
And the final generated code contains correct formulas
And running pytest on the corrected project exits with code 0
And code has "# Implements: REQ-" tags
And tests have "# Validates: REQ-" tags
```

`Executable`: `TestE2EHomeostasis.test_edge_converged_emitted`,
`test_corrected_tests_pass`, `test_corrected_code_has_req_tags`

---

## Run Archive

Same archive structure as `convergence_lifecycle`. Each homeostasis run is archived
to `runs/` with a timestamped directory and `.e2e-meta/` metadata.
