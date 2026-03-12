# Proxy Decision — design→module_decomposition (all 7 MVP features)

**Decision**: approved
**Actor**: human-proxy
**Timestamp**: 2026-03-13T14:00:00Z
**Features**: REQ-F-PROJ-001, REQ-F-NAV-001, REQ-F-UX-001, REQ-F-OVR-001, REQ-F-SUP-001, REQ-F-EVI-001, REQ-F-CTL-001
**Edge**: design→module_decomposition
**Gate**: human_approves_module_structure
**Artifact**: imp_react_vite/design/module_decomp/MODULE_DECOMPOSITION.md

## Criterion 1: Module boundaries make sense

**Evidence**:
- 14 modules total: 4 infra leaves (api-client, routing, server-workspace-reader, server-write-handler), 3 infra composed (ux-shared, store, server-routes), 1 app-shell, 5 feature pages (project-nav, overview, supervision, evidence, control), 1 server-core
- Each module has a single, articulable purpose. api-client = HTTP; routing = URL schema; ux-shared = shared UI primitives; store = state; feature-* = one page area each
- feature-control as a panel within feature-supervision (not a separate route) is correct — consistent with REQ-BR-SUPV-001 design decision
**Result**: PASS

## Criterion 2: No God modules

**Evidence**:
- Largest module by responsibility is api-client — but all methods are HTTP wrappers on a single base URL. This is appropriate cohesion (all-read from one server).
- server-routes delegates reads to server-workspace-reader and writes to server-write-handler — not conflating read/write concerns
- No single module implements both UI and business logic. Business logic (isStuck, computeAutoMode) lives in server-workspace-reader (server-side, deterministic)
**Result**: PASS

## Criterion 3: Dependency direction matches intended architecture

**Evidence**:
- Infrastructure modules (api-client, routing, ux-shared, store) are never imported by infrastructure from feature modules — correct inversion
- feature-control → feature-supervision (single-direction component import for shared GateActionPanel + AutoModeToggle). Justified: CTL is a context panel on SUP — sharing these components avoids duplication and reflects the design decision in ADR-GM-005 / REQ-BR-SUPV-001
- Server layering: server-core → server-routes → server-workspace-reader / server-write-handler — each layer adds one concern
- Topological order is well-defined with no cycles
**Result**: PASS

## Criterion 4: Interface contracts reasonable — no leaky abstractions

**Evidence**:
- All cross-module calls have named TypeScript types (WorkspaceSummary, GateItem, FeatureVector, TraceabilityEntry, WorkspaceEvent, ApiError, WriteError)
- Error types are named, not generic `throws Error`
- React component contracts via prop interfaces (GateActionPanelProps, AutoModeToggleProps) — appropriate for React module boundaries; prop types ARE the contract
- Server-write-handler emitEvent() signature is minimal (payload: EventPayload) — server adds timestamp + project, satisfying ADR-GM-005 (client never constructs raw event)
- No "any" types in contracts
**Result**: PASS

## Summary

All 4 criteria PASS. Module structure is clean, acyclic, and traceable to design decisions. The 4-wave parallelism analysis enables concurrent construction of 6 modules in Wave 3. Architecture is sound.

**Result**: APPROVED — all 7 features advance to module_decomposition→basis_projections
