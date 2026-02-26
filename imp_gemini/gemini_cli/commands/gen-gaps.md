# /gen-gaps - Traceability Gap Analysis

Scans for implementation or test gaps against feature vectors.

<!-- Implements: REQ-TOOL-005, REQ-TOOL-009, REQ-LIFE-006 -->

## Instructions

1. Analyze traceability across 3 layers (Layer 1, Layer 2, Layer 3) using the `--layer` flag.
2. MANDATORY: Emit `event_type: "intent_raised"` with `signal_source: "gap"` for detected gaps.
