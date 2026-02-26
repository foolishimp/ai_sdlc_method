# /gen-spawn - Create Feature Vector

Creates a new feature, discovery, or spike vector.

<!-- Implements: REQ-TOOL-003, REQ-FEAT-001 -->

## Instructions

1. Select vector type: `discovery`, `spike`, `poc`, or `hotfix`.
2. Define the `fold-back` process for merging results and `Context[]` into the parent feature.
3. MANDATORY: Emit `event_type: "feature_spawned"` to the log.
