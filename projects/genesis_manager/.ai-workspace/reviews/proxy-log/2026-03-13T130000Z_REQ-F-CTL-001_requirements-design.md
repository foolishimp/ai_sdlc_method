# Proxy Decision — requirements→design

**Decision**: approved
**Actor**: human-proxy
**Timestamp**: 2026-03-13T13:00:00Z
**Feature**: REQ-F-CTL-001
**Edge**: requirements→design
**Gate**: human_approves_architecture

## Criterion: Architecture is sound and trade-offs are acceptable

**Evidence**:
- ControlSurface as context panel on top of Supervision (not a separate route) is correct: CTL acts on what SUP surfaces. No separate navigation needed. Sound.
- All writes through POST /api/workspaces/:id/events (ADR-GM-005): server constructs full event JSON + appends with file lock. Client never touches raw event construction. REQ-DATA-WORK-002 satisfied — server logs each write.
- ConfirmActionDialog wrapping all write actions with CMD display: REQ-F-UX-002 (show genesis command equivalent) applied consistently to all 4 CTL actions.
- REQ-BR-SUPV-001 (no autonomous execution) enforced by design: no background process, auto-mode is derived from event stream (last auto_mode_set event — not a hidden flag), toggle visible in every SUP row, every write requires ConfirmActionDialog.
- Auto-mode state derived from events (not feature vector YAML): preserves REQ-DATA-WORK-001 (workspace as sole data source; all state traceable to events.jsonl).
- GateActionPanel: rejection requires non-empty comment (REQ-F-CTL-002 AC3). Enforced by form validation before POST.

**Result**: PASS — architecture is sound. REQ-BR-SUPV-001 compliance is explicit in the design, not incidental.
