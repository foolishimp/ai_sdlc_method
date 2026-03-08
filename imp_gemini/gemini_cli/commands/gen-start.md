# /gen-start - State-Driven Routing Entry Point

State-machine controller that detects project state and delegates to the appropriate command.

<!-- Implements: REQ-UX-001, REQ-UX-002, REQ-UX-004, REQ-UX-005, REQ-TOOL-003 -->

## Instructions

### Step 0: State Detection Algorithm

| # | State | Detection | Action |
|---|-------|-----------|--------|
| 1 | `UNINITIALISED` | No .ai-workspace | `Progressive Init` (`Project name` check) |
| 2 | `NEEDS_CONSTRAINTS` | Empty mandatory dimensions | `Deferred Constraint` at `requirements→design` |
| 3 | `NEEDS_INTENT` | No INTENT.md | Intent Authoring |
| 4 | `NO_FEATURES` | features/active/ empty | Feature Creation |
| 5 | `STUCK` | Same delta for 3+ iterations | Stuck Recovery |
| 6 | `ALL_BLOCKED` | All features blocked | Blocked Recovery |
| 7 | `IN_PROGRESS` | Active unconverged features | Delegate to `/gen-iterate` |
| 8 | `ALL_CONVERGED` | All features converged | Release/Gaps |

### Progressive Init (UNINITIALISED state)

Ask ≤5 questions to bootstrap the workspace:

1. **Project name** — human-readable identifier
2. **Project kind** — library | service | cli | webapp | data-pipeline | other
3. **Primary language** — auto-detected from repo or ask
4. **Deployment target** — local | cloud | embedded | N/A (deferred to design)
5. **Team size** — solo | small (2–5) | medium (6–15) | large (16+)

Constraint dimensions (ecosystem_compatibility, deployment_target, security_model, build_system) are **Deferred Constraints** — not required at init. They are resolved at the `requirements→design` edge when the design ADRs crystallise the technology binding.
