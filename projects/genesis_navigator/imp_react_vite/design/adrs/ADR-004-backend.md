# ADR-004: FastAPI + PyYAML Backend, No ORM

**Status**: Accepted | **Date**: 2026-03-12
**Implements**: REQ-F-API-001..005, REQ-NFR-ARCH-002

## Decision

Use FastAPI 0.115+ with PyYAML 6.x for the backend. No database, no ORM — all
data is read from the filesystem on every request.

## Rationale

- The backend is a pure filesystem reader — it has no mutable state to persist
- No database means no schema migration, no session management, no data-at-rest concerns
- FastAPI generates OpenAPI 3.1 schema automatically from Pydantic models (satisfies REQ-NFR-ARCH-001)
- PyYAML is the standard parser for `.ai-workspace/features/active/*.yml` files
- The genesis_navigator itself doesn't need a preferences service (unlike `ai_mfe_portal`) — it has no user accounts

## Pydantic as the single source of truth

Pydantic models in `genesis_nav/models/schemas.py` define both:
1. The Python domain objects used throughout the backend
2. The OpenAPI schema exported at `/openapi.json`

TypeScript types in `frontend/src/types/api.ts` are generated from this schema (or maintained in sync).

## Consequences

- Every API request re-reads the filesystem (no in-memory cache)
- For performance (REQ-NFR-PERF-001/002), the scanner uses `os.scandir()` with early pruning
- Concurrent requests to the same project may produce slightly different results if events.jsonl is being written to — acceptable for a point-in-time reader
- No background tasks, no async filesystem watching
