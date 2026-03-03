# Feature Decomposition: REQ-F-EVENT-001

**Implements**: REQ-EVENT-001, REQ-EVENT-002, REQ-EVENT-003, REQ-EVENT-004

## Overview
This feature implements the Event Stream substrate and projection contract as defined in ADR-S-012. The goal is to shift `imp_gemini` from a state-centric mutation model to an event-sourced architecture where assets are projections of an append-only event stream.

## Required Modifications
1. **Event Store Enhancements**: Ensure `EventStore` fully supports the OpenLineage v2 schema (already partially done) and provides query capabilities for projection generation.
2. **Iterate Engine Refactoring**: Update `IterateEngine` to return events rather than directly modifying asset files. Asset files (the working tree) should be treated as a materialized view of the stream.
3. **Projection Mechanisms**: Implement logic to derive `ProjectState` and feature vector states directly from the event log.
4. **Saga Support**: Implement `report.spawn` handling as a formal `CompensationTriggered` / `CompensationCompleted` sequence to fulfill the Saga Invariant (REQ-EVENT-004).
