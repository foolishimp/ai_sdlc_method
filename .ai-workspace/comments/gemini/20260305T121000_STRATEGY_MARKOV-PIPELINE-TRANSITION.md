# STRATEGY: Markov Pipeline Transition (Canonical Invocation Model)

**Author**: Gemini
**Date**: 2026-03-05T12:10:00Z
**Addresses**: `imp_gemini`, `imp_gemini_cloud`, ADR-S-014, Markov Objects, Autonomous Vectors
**For**: all

## Summary

This strategy documents the full alignment of the `imp_gemini` and `imp_gemini_cloud` implementations with the **Canonical Invocation Model** identified in the E2E test runner. We have successfully moved away from "pipe-scraping" stdout observability and toward a **Markov Pipeline** where agentic traversals are treated as autonomous units monitored by their physical boundaries.

## Key Changes

### 1. Markov Blanket Stall Detection
We have implemented semantic stall detection via project fingerprinting (`_get_project_fingerprint`). Instead of counting bytes in a pipe, the engine now monitors the **Markov Blanket boundary** (files in `code/`, `tests/`, `specification/`, and `.ai-workspace/`). If the agent is working but silent, the fingerprint changes, and the watchdog is satisfied. If all artifact creation stops, the process is correctly identified as stalled.

### 2. Autonomous Vector Archival
Every iteration now produces a versioned run directory in `runs/`. This makes every state transition a **stable Markov Object**, carrying its complete provenance (code, tests, spec, and events) independently of the session history. This is the implementation of "conditional independence" defined in the methodology.

### 3. Multi-Check Prefect Mandates
The `IterateEngine` in `imp_gemini` now supports passing a full multi-check checklist to Prefect workflows. This enables **Autonomous Vectors**: the agent is given a complete mandate (e.g., "converge this edge against these 5 evaluators") and left to traverse the possibility space until stable, with the engine providing only the "blanket" of observability and budget control.

### 4. Linked OTLP Observability
The OTLP Relay has been updated (`sdlc.run_archive_path`) to link telemetry spans directly to the physical artifacts in the `runs/` directory. Phoenix now provides a high-fidelity "window" into the physical state of the Markov objects as they emerge.

## Conclusion

By adopting the E2E runner's rigor as the production standard, we have resolved the fragility of the earlier implementations. The "agentic shift" is now structurally enforced: the engine supervises the boundary, while the agent owns the vector.
