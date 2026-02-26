# /gen-start - State-Driven Routing Entry Point

State-machine controller that detects project state and delegates to the appropriate command.

<!-- Implements: REQ-UX-001, REQ-UX-002, REQ-UX-004, REQ-UX-005, REQ-TOOL-003 -->

## Instructions

### Step 0: State Detection Algorithm

| # | State | Detection | Action |
|---|-------|-----------|--------|
| 1 | `UNINITIALISED` | No .ai-workspace | `Progressive Init` (`Project name` check) |
| 2 | `NEEDS_CONSTRAINTS` | Empty mandatory dimensions | `Deferred Constraint` at `requirements\u2192design` |
| 3 | `NEEDS_INTENT` | No INTENT.md | Intent Authoring |
| 4 | `NO_FEATURES` | features/active/ empty | Feature Creation |
| 5 | `STUCK` | Same delta for 3+ iterations | Stuck Recovery |
| 6 | `ALL_BLOCKED` | All features blocked | Blocked Recovery |
| 7 | `IN_PROGRESS` | Active unconverged features | Feature/Edge Selection |
| 8 | `ALL_CONVERGED` | All features converged | Release/Gaps |
