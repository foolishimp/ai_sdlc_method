# gen spec-review
**Implements**: REQ-LIFE-009, REQ-UX-003, ADR-011

## Usage
`gen spec-review`

## Description
Performs a stateless review of the workspace against the specification. It calculates the "gradient" (the difference between what the spec asserts and what the workspace contains).

## Checks
- **Orphaned Requirements**: Finds REQ keys in the spec that have no active feature vector.
- **Stalled Features**: Identifies features with no recent activity (default > 7 days).
- **Traceability Gaps**: Scans for requirements lacking implementation or tests (delegates to `gen gaps`).

## Effects
- For every non-zero delta detected, emits an `intent_raised` event.
- Signals appear in `gen status` and `gen start`.
