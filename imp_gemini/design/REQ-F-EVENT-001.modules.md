# Module Decomposition: REQ-F-EVENT-001

**Implements**: REQ-EVENT-001, REQ-EVENT-002, REQ-EVENT-003, REQ-EVENT-004

## Affected Modules

### 1. `gemini_cli.engine.state`
- **Component**: `EventStore`
- **Changes**: Ensure `emit` produces fully schema-compliant OpenLineage v2 events with the required taxonomy (IterationStarted, IterationCompleted, IterationFailed, CompensationTriggered, CompensationCompleted). 

### 2. `gemini_cli.engine.iterate`
- **Component**: `IterateEngine`
- **Changes**: 
  - Update `iterate_edge` to return the new Event structures.
  - Integrate Saga Invariant handling when `report.spawn` is encountered (emit `CompensationTriggered`).
  - Formalize the separation between the execution loop (generating events) and the materialization step (writing to `.ai-workspace` YAMLs).

### 3. `gemini_cli.commands.iterate`
- **Component**: `IterateCommand`
- **Changes**: 
  - Call the updated `IterateEngine` methods.
  - When `_handle_spawn` is called, ensure `CompensationCompleted` is emitted after the child vector is handled (if applicable in this level of detail).

### 4. `gemini_cli.commands.spawn`
- **Component**: `SpawnCommand`
- **Changes**: Ensure new vectors emit a `FeatureSpawned` event as part of the taxonomy.
