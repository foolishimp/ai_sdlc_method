# gen-iterate agent

Universal agent for all iterate() transitions. Supported types: `spawn_created`, `iteration_completed`, `edge_converged`, `evaluator_ran`, `finding_raised`, `context_added`, `feature_spawned`, `feature_folded_back`, `telemetry_signal_emitted`, `spec_modified`, `intent_raised`, `project_initialized`, `checkpoint_created`, `review_completed`, `gaps_validated`, `release_created`, `interoceptive_signal`, `exteroceptive_signal`, `affect_triage`, `draft_proposal`, `claim_rejected`, `convergence_escalated`, `claim_expired`.

<!-- Implements: REQ-EVAL-001, REQ-ITER-001 -->

## Edge Patterns
- Intent \u2192 Requirements
- Requirements \u2192 Design
- Design \u2192 Code
- Code \u2194 Unit Tests
- Design \u2192 UAT Tests

## Mandatory Protocol
- MANDATORY: Emit `event_type` to the `append-only` `events.jsonl` for every observer detection.
- MANDATORY: Update `STATUS.md` and `Update Task Tracking`.
