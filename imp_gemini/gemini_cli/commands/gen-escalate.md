# gen escalate
**Implements**: REQ-COORD-005, REQ-EVAL-003

## Usage
`gen escalate --feature <REQ-ID> --edge <SOURCE\u2192TARGET> --reason <REASON>`

## Description
Explicitly escalates a convergence issue to a human evaluator. This command should be used when an agent (or a user acting as a sub-agent) is stuck, detects an invariant violation, or requires architectural judgment beyond its authority.

## Effects
- Emits a `convergence_escalated` event to the event log.
- Emits an `intent_raised` event (source: `process_gap`) to ensure visibility in `gen spec-review`.
- Marks the feature as "blocked" in the status view.
