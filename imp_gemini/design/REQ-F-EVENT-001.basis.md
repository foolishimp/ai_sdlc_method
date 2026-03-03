# Basis Projection: REQ-F-EVENT-001

**Implements**: REQ-EVENT-001, REQ-EVENT-002, REQ-EVENT-003, REQ-EVENT-004

## 1. Event Store Implementation (`gemini_cli/engine/state.py`)
- Enhance the `emit` method to support specific `event_type` classifications mapping to the required taxonomy: `IterationStarted`, `IterationCompleted`, `IterationFailed`, `CompensationTriggered`, `CompensationCompleted`.
- Add a stub `project` method to `EventStore` or create a standalone `Projector` class if one does not exist to rebuild state from the event stream.

## 2. Iteration Engine Implementation (`gemini_cli/engine/iterate.py`)
- Modify `run_edge` to capture `report.spawn` and immediately `emit("CompensationTriggered", ...)` before returning.
- Formalize the synchronization block at the end of `run_edge` so that the file system is updated based on the event generated.

## 3. Iterate Command Integration (`gemini_cli/commands/iterate.py`)
- Ensure that `_handle_spawn` or the caller handles the completion of a spawn and emits `CompensationCompleted`.

## 4. Test Coverage (`tests/test_state_machine.py` / `tests/test_iterate_engine.py`)
- Write tests to verify that the required taxonomy events are correctly formatted and logged.
- Verify the Saga Invariant (that a failure/spawn correctly emits `CompensationTriggered`).
