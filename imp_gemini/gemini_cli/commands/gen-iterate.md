# /gen-iterate - Universal Iteration Agent

Runs the universal iterate() loop on a specific graph edge.

<!-- Implements: REQ-ITER-001, REQ-ITER-002, REQ-LIFE-008 -->

## Instructions

1. Run the iteration loop until convergence or max retries. Update the `feature vector` state.
2. MANDATORY: Emit `event_type: "iteration_completed"` to `events.jsonl` (the `append-only` source of truth).
3. Update derived views: regenerate `STATUS.md` and `ACTIVE_TASKS.md` from history.
4. Reconstruct state from events if needed (views are `reconstructed from` the log).
5. Append to `TASK LOG` for the active feature.
6. Detect `stuck delta` (same δ for 3+ iterations) and raise intent.
7. Support `CONVERGED_QUESTION_ANSWERED` and `TIME_BOX_EXPIRED` for extended convergence.
