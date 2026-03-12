# Proxy Decision — requirements→design

**Decision**: approved
**Actor**: human-proxy
**Timestamp**: 2026-03-13T12:00:00Z
**Feature**: REQ-F-UX-001
**Edge**: requirements→design
**Gate**: human_approves_architecture

## Criterion: Architecture is sound and trade-offs are acceptable

**Evidence**:
- useWorkspacePoller mounted once at App.tsx root, fires immediately then every 30s: satisfies REQ-F-UX-001 (≤30s staleness). Single instance prevents duplicate polls.
- Polling error propagates to Zustand as pollingError without updating lastRefreshed: REQ-F-UX-001 AC3 (workspace unavailable → clear error state, not silent stale data). Sound.
- FreshnessIndicator 5-state machine (refreshing/error/stale>60s/fresh/loading): handles all states including the error case visually. No state left unrepresented.
- CommandLabel + CMD helper: REQ-F-UX-002 (underlying command shown as informational label) implemented as a shared utility — consistent across all 4 action types. No inline string construction.
- Integration with WorkspaceApiClient from PROJ-001: no new server endpoints needed. Clean reuse.

**Result**: PASS
