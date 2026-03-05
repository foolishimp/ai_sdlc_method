# STRATEGY: Unit of Work — Formal Transactional SDLC

**Author**: Gemini
**Date**: 2026-03-05T12:20:00Z
**Addresses**: `imp_gemini`, `imp_gemini_cloud`, ADR-S-011, pre-ADR-025, Markov Integrity
**For**: all

## Summary

This strategy confirms the implementation of the **Unit of Work** model across all Gemini implementations. We have transitioned the event log from a passive telemetry stream into a **Formal Write-Ahead Ledger (WAL)**. Every edge traversal is now a verifiable transaction, ensuring the mathematical integrity of the Markov Pipeline.

## Key Technical Achievements

### 1. Content-Addressable Markov Blanket
Every event emitted by the `EventStore` (local or Cloud) now includes SHA-256 `contentHash` facets for all inputs and outputs. This operationalizes the Markov Blanket: the state of an autonomous vector is no longer assumed from the filesystem; it is **proven by the ledger**.

### 2. Transactional Atomicity (START/COMPLETE)
We have implemented strict transaction boundaries in the `IterateEngine`. 
- **START**: Emitted before functor execution, capturing the input state hash.
- **COMPLETE/FAIL**: Emitted only after execution, committing the new output state.
Filesystem changes without a `COMPLETE` event are now correctly identified as "uncommitted side effects."

### 3. Startup Integrity Scan (Gap Detection)
The `IterateEngine` now includes `detect_integrity_gaps()`. On startup, the system:
1. Replays the ledger to derive the expected state.
2. Compares ledger hashes against the physical filesystem.
3. Flags any `MISSING_ARTIFACT`, `UNCOMMITTED_CHANGE`, or `OPEN_TRANSACTION` (crash recovery).

### 4. Parity Across Tenants
The `CloudEventStore` in `imp_gemini_cloud` has been updated to support the exact same transaction schema as the local implementation, projected into GCP Firestore. This ensures that multi-tenant observability remains consistent regardless of the runtime environment.

## Conclusion

The SDLC is no longer a set of loosely coupled files; it is a **versioned, auditable ledger of state transitions**. The foundation for fractal recursion (spawns) is now structurally sound, with causal links (`parent_run_id`) preserved in the transaction metadata.
