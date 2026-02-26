# ADR-005: Canonical Spec Hashing

**Status**: Accepted
**Date**: 2026-02-27

## Context
To ensure auditability, we must prove that an iteration was performed against a specific, immutable version of the specification.

## Decision
Use SHA-256 to hash a canonical JSON representation of the merged intent and context surface.

## Consequences
- Every `iteration_completed` event will carry a `spec_hash`.
- Guaranteed detection of specification drift during long-running features.
