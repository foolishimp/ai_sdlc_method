# Design: Event Stream & Projections (REQ-F-EVENT-001)

**Implements**: REQ-EVENT-001, REQ-EVENT-002, REQ-EVENT-003, REQ-EVENT-004

## 1. Architectural Strategy
We will transition from direct file mutations in `IterateEngine` to emitting OpenLineage v2 compliant events to the `EventStore`. The local file system (working tree) will be treated as a materialized view (projection) of the `events.jsonl` stream. 

## 2. Component Design
- **`gemini_cli.engine.state.EventStore`**: Already supports OpenLineage v2 schema. Will be enhanced with a `replay()` or `project()` method to reconstruct states (e.g., active feature vectors) dynamically if needed, though for the local CLI we maintain the YAMLs synchronously as a cache.
- **`gemini_cli.engine.iterate.IterateEngine`**: Currently writes to the file system directly. We will refactor it to ensure that the core logic produces `Event+`, and a secondary "Sync" step updates the file system cache (`.ai-workspace/features/active/*.yml`, etc.) based on the event stream. 
- **Saga Invariant**: When an evaluator returns `spawn` (indicating a failure or need for recursion), the engine will emit a `CompensationTriggered` event before attempting the fold-back or generating a new child vector. Once resolved, `CompensationCompleted` is emitted.

## 3. Interfaces
- `IterateEngine.run_edge` -> `List[IterationRecord]` (Already implemented to return records rather than just side-effects).
- `Projector` (to be created or enhanced) will handle the synchronization between the `EventStore` and the materialized YAML views.

## 4. Technology Binding
- Event store remains local append-only `events.jsonl` (satisfying ADR-S-011 and ADR-S-012 for the local projection profile).
