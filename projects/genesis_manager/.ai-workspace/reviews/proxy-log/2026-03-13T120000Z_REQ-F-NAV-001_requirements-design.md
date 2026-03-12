# Proxy Decision — requirements→design

**Decision**: approved
**Actor**: human-proxy
**Timestamp**: 2026-03-13T12:00:00Z
**Feature**: REQ-F-NAV-001
**Edge**: requirements→design
**Gate**: human_approves_architecture

## Criterion: Architecture is sound and trade-offs are acceptable

**Evidence**:
- ROUTES constant pattern: single source of truth for all canonical URLs — prevents link drift across all 7 features. Sound.
- NavHandle with typed variants (req/feature/run/event) and exhaustive ts-pattern match: type system enforces no missed cases. REQ-NFR-ACC-001 (no dead links) served by PlaceholderPage for all 404 cases. Sound.
- Server-side routes added for /api/features, /api/runs, /api/req, /api/events: extends PROJ-001 Express server cleanly. No new architecture needed.
- FeatureDetailPage, RunDetailPage, ReqKeyDetailPage, EventDetailPage: canonical pages with stable paths matching REQ-F-NAV-005. Bookmarkable. Sound.
- Dead-link protocol: every canonical page catches API 404 → PlaceholderPage (never rethrows). REQ-NFR-ACC-001 satisfied by design constraint, not runtime luck.

**Result**: PASS
