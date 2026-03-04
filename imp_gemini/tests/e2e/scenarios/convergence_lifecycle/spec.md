# BDD Spec — Convergence Lifecycle

**Scenario**: `convergence_lifecycle`
**Executable test**: `imp_gemini/tests/e2e/test_e2e_convergence.py`
**Derived from**: `specification/verification/UAT_TEST_CASES.md`
**Satisfies**: UC-01, UC-04, UC-05, UC-08
**Validates**: REQ-GRAPH-001–003, REQ-ITER-001–003, REQ-EVAL-001–002, REQ-FEAT-001, REQ-EDGE-001, REQ-EDGE-004, REQ-TOOL-005

---

## Scenario Overview

A greenfield Python library project runs through the **standard profile** (4 edges) via
headless Gemini (`gemini start --auto`). All evaluators converge. Generated artifacts
(events, feature vectors, code, tests) are validated against the methodology contract.

This is the **happy-path** convergence scenario — no deliberate failures, no human gates.

---

## Fixture: INITIALIZED (temperature-converter)

```
temperature-converter/
  CLAUDE.md
  pyproject.toml
  specification/
    INTENT.md                    # 2 REQ keys: REQ-F-CONV-001, REQ-F-CONV-002
  src/                           # empty
  tests/                         # empty
  .ai-workspace/
    graph/
      graph_topology.yml
      evaluator_defaults.yml
      edges/                     # edge params for all 10 transitions
    gemini_genesis/context/
      project_constraints.yml    # standard profile, pytest, ruff, mypy
    features/
      active/
        REQ-F-CONV-001.yml       # status: pending, all trajectory: pending
      feature_vector_template.yml
      feature_index.yml
    profiles/                    # all 6 profiles
    events/
      events.jsonl               # 1 event: project_initialized
    tasks/active/
      ACTIVE_TASKS.md
    agents/                      # gen-iterate.md, gen-dev-observer.md, etc.
```

Scaffolded by `e2e_project_dir` session fixture in `conftest.py`.

---

## Scenario: Standard-Profile Full Convergence

```gherkin
Given a scaffolded temperature-converter project
  With intent: "Python library converting between Celsius, Fahrenheit, and Kelvin"
  With 2 REQ keys: REQ-F-CONV-001 (6 conversion functions), REQ-F-CONV-002 (validation)
  With 1 active feature vector: REQ-F-CONV-001 (status: pending)
  With standard profile: 4 edges (intent→requirements, requirements→design, design→code, code↔unit_tests)

When I run headless Gemini:
  gemini start --auto --feature "REQ-F-CONV-001"
  With budget cap: $5.00 USD
  With wall timeout: 30 minutes

Then the following artifacts are produced:
```

---

### UC-01-A: Event Log Structure

```gherkin
Given the events.jsonl produced by the run

When I parse the event log

Then events.jsonl exists at .ai-workspace/events/events.jsonl
And every line is valid JSON
And every event has:
  - event_type (string)
  - timestamp (ISO 8601)
And timestamps are monotonically non-decreasing
And event_type values include:
  - project_initialized
  - edge_started
  - iteration_completed
  - edge_converged
```

`Executable`: `TestE2EConvergence.test_events_file_exists`,
`test_events_valid_json`, `test_events_common_fields`, `test_events_timestamps_monotonic`,
`test_events_required_types`

---

### UC-01-B: Iteration Sequences and Convergence

```gherkin
Given iteration_completed events in events.jsonl
  grouped by (feature, edge)

When I inspect the iteration numbers per group

Then iteration numbers are sequential within each (feature, edge) group
And each edge that produced an edge_converged event has:
  - at least one iteration_completed with delta=0 as the final iteration
And each iteration_completed event carries evaluator_results
  with at least 1 evaluator entry

And all 4 standard-profile edges for REQ-F-CONV-001 have edge_converged events:
  - intent→requirements
  - requirements→design
  - design→code
  - code↔unit_tests
```

`Executable`: `TestE2EConvergence.test_events_iteration_sequences`,
`test_events_delta_to_zero`, `test_events_evaluator_counts`,
`test_events_all_edges_converged`

---

### UC-04-A: Feature Vector Trajectory

```gherkin
Given the feature vector at .ai-workspace/features/active/REQ-F-CONV-001.yml
  (or features/completed/ after full convergence)

When I load and inspect the feature vector

Then the feature vector exists
And it has required fields: feature, title, status, trajectory
And status is "converged" (or "completed")
And trajectory contains entries for all converged edges
  each with a convergence timestamp
And the feature field matches "REQ-F-CONV-001"
```

`Executable`: `TestE2EConvergence.test_feature_vector_exists`,
`test_feature_vector_converged`, `test_feature_vector_required_fields`,
`test_feature_vector_trajectory_timestamps`, `test_feature_vector_requirements_populated`

---

### UC-05-A: TDD Code Generation (code↔unit_tests)

```gherkin
Given the code↔unit_tests edge has converged

When I inspect generated artifacts in src/ and tests/

Then at least 1 Python source file exists in the project
And at least 1 Python test file exists
And source files contain:
  at least 1 comment matching "# Implements: REQ-F-CONV-"
And test files contain:
  at least 1 comment matching "# Validates: REQ-F-CONV-"
And running pytest on the project exits with code 0
  (all generated tests pass)
```

`Executable`: `TestE2EConvergence.test_code_files_exist`, `test_test_files_exist`,
`test_code_implements_tags`, `test_test_validates_tags`, `test_generated_tests_pass`

---

### UC-08-A: Cross-Artifact Consistency

```gherkin
Given the complete project output (events + feature vector + code + tests)

When I check cross-artifact consistency

Then REQ-F-CONV-001 and REQ-F-CONV-002 appear in both:
  - source file "# Implements:" tags
  - test file "# Validates:" tags
And feature vector REQ keys match tags found in code/test files
And event log feature references match actual feature vector files
  (no phantom feature IDs in events)
```

`Executable`: `TestE2EConvergence.test_code_traceability`,
`test_req_key_consistency`, `test_event_feature_consistency`

---

## Run Archive

Each test run is archived to `imp_gemini/tests/e2e/runs/` as:

```
runs/
  <version>_<YYYYMMDDTHHMMSS>_<seq>/   # timestamped run
    .ai-workspace/                           # full project state
    src/                                     # generated code
    tests/                                   # generated tests
    .e2e-meta/
      run_manifest.json                      # {version, timestamp, failed}
      test_results.json                      # {total, passed, failed, tests[]}
      stdout.log                             # Gemini stdout
      stderr.log                             # Gemini stderr
      meta.json                              # {returncode, elapsed, timed_out}
```
