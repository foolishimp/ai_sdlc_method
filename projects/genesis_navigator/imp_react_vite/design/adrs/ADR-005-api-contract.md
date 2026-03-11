# ADR-005: OpenAPI 3.1 as the Binding Contract

**Status**: Accepted | **Date**: 2026-03-12
**Implements**: REQ-NFR-ARCH-001

## Decision

The REST API contract is the single coupling point between frontend and backend.
FastAPI publishes it at `GET /openapi.json`. The frontend depends only on this contract.

## Endpoint inventory

| Method | Path | Feature vector | Response time |
|--------|------|----------------|--------------|
| GET | /api/projects | REQ-F-SCANNER-001 | < 2000ms |
| GET | /api/projects/{id} | REQ-F-PROJDATA-001 | < 1000ms |
| GET | /api/projects/{id}/gaps | REQ-F-GAPENGINE-001 | < 3000ms |
| GET | /api/projects/{id}/queue | REQ-F-QUEUEENGINE-001 | < 1000ms |
| GET | /api/projects/{id}/runs | REQ-F-HISTENGINE-001 | < 2000ms |
| GET | /api/projects/{id}/runs/{run_id} | REQ-F-HISTENGINE-001 | < 2000ms |
| GET | /openapi.json | — | < 100ms |

## CORS configuration

In development, CORS allows `http://localhost:5173` (Vite dev server).
In production (static files served by FastAPI), CORS is not needed — same origin.

## Error responses

All errors follow RFC 9457 Problem Details:
```json
{"type": "...", "title": "...", "status": 404, "detail": "Project not found: foo"}
```

## Consequences

- Frontend can be tested with a mock server that satisfies the OpenAPI schema
- Future adapters (VS Code extension, Electron) need only implement this contract
- Schema breaking changes require version bump and migration
