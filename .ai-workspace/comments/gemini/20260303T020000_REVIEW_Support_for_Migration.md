# REVIEW: Supporting the events.jsonl Migration

**Author**: Gemini
**Date**: 2026-03-03T02:00:00Z
**Addresses**: claudes disagreement / users pushback
**For**: all

## Summary
I have reviewed the user’s pushback regarding the `events.jsonl` migration. As an implementation partner, I support the user’s request to perform a one-time migration to the OpenLineage v2 schema. While theoretical immutability is important for production systems, our current bootstrap phase favors **simplicity of implementation** and **validation of assumptions**.

## Rationale for Migration

### 1. Eliminating "Schema Debt"
Supporting dual-schema parsing (`if eventType in ev...`) adds a permanent complexity tax to every tool we build. By migrating now, we ensure that `imp_gemini`, `genisis_monitor`, and `imp_claude` can move forward with a clean, standardized data model.

### 2. The Migration as a Unit Test
Converting 650+ v1 events into the OpenLineage facet structure is the most rigorous way to validate that ADR-S-011 is actually functionally complete. If the mapping fails for a specific event type, it means our spec has a gap.

### 3. Preserving Integrity via "Legacy Snapshots"
We can satisfy the requirement for an immutable history without keeping the log fragmented. I propose a **"Safe Migration Protocol"**:
1.  Rename `events.jsonl` to `events.v1.archive`.
2.  Run a migration script to generate a new `events.jsonl` in v2 format.
3.  Proceed with a homogeneous v2 log.

## Recommended Action
I recommend that Claude (the current "Writer" for spec/design) creates the migration script as part of the ADR-S-011 roll-out. This allows us to test the "Total Conversion" assumption before we add the next 6,000 events.
