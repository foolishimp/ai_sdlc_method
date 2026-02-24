# Gemini CLI Core Requirements

**Feature Vector**: REQ-F-GEMINI-CLI-001
**Intent**: INT-GEMINI-001

## Functional Requirements

- **REQ-CLI-001**: Pure Python Implementation. No dependency on Markdown commands.
- **REQ-CLI-002**: Event Sourcing. Every state change must be an append to `events.jsonl`.
- **REQ-CLI-003**: Universal `iterate()` engine. Single function that takes (asset, context, evaluators).
- **REQ-CLI-004**: Projections. Support named profiles (Minimal, Standard, Full) via YAML.
- **REQ-CLI-005**: Functor Escalation. Implement $F_D$ (subprocess), $F_P$ (Gemini API), and $F_H$ (Input).
- **REQ-CLI-006**: Recursive Spawning. $F_P$ can yield a `SpawnRequest` to initiate sub-problem investigations.

## Non-Functional Requirements

- **REQ-NF-CLI-001**: Homeostatic. System should warn if `events.jsonl` or Feature Vectors are out of sync.
- **REQ-NF-CLI-002**: Stateless Engine. The engine should not store internal state; it must derive state from the event log.
