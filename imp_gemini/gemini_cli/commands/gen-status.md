# /gen-status - Project Situational Awareness

Provides a "You Are Here" visualization of the Asset Graph. The dashboard is `viewable` and `renderable` in the browser. `events.jsonl` is the `source of truth`.

<!-- Implements: REQ-UX-003, REQ-UX-005, REQ-TOOL-003 -->

## Instructions

1. `Step 0`: `State Detection` of project state from `events.jsonl` using `event sourcing` logic.
2. Preview `What Start Would Do` next (`Start would` select edge).
3. Generate `STATUS.md` with sections:
    - `Phase Completion Summary` (table with `Convergence Pattern` subsection)
    - `Traceability Coverage`
    - `Process Telemetry` (including `Constraint Surface` subsection)
    - `Self-Reflection` (`Feedback` loop to Intent with `TELEM-` signals)
4. Define the `Event Schema` for all derived views including `iteration_completed`.
5. Display `Constraint Dimensions` with `resolved` indicators and links to `ADR-` docs. Acknowledge `advisory` dimensions.
