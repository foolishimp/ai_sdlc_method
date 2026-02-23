# ADR-GC-009: OpenAPI as Browser-to-Cloud Interface

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Gemini Cloud Genesis Design Authors
**Requirements**: REQ-TOOL-001, REQ-UX-003

---

## Context

To enable browser-based Gemini sessions (Vertex AI, custom UIs) to interact with the methodology without a local CLI, we need a standard, machine-readable interface that Gemini can consume as a "tool".

---

## Decision

**We adopt OpenAPI 3.0 as the formal contract between Gemini (Client) and GCP (Runtime).**

The API surface maps the four core verbs of the Asset Graph Model to RESTful endpoints:
1. **GET /status**: Corresponds to `/gen-status`. Returns the Cockpit view derived from Firestore.
2. **POST /start**: Corresponds to `/gen-start`. Executes state detection logic and suggests the next edge.
3. **POST /iterate**: Triggers the Cloud Workflow for a specific edge/feature.
4. **POST /review**: Submits a human decision to a pending callback (ADR-GC-002).

### Browser-Only Mode
In this mode, Gemini uses the **Genesis Bootloader** to understand the SDLC constraints and then uses the OpenAPI spec to "see" the GCP backend as its hands and eyes.

---

## Rationale

### Tool-Calling Native
Modern LLMs (Gemini Pro, Claude Sonnet) are natively trained to consume OpenAPI definitions. Providing this spec allows Gemini to accurately generate the JSON payloads required to trigger Cloud Workflows without human intervention.

### Multi-Tenancy
The API paths include `{tenantId}` and `{projectId}`, ensuring that Gemini sessions remain isolated and secure using GCP API Gateway authentication.

---

## Consequences

### Positive
- **Zero Installation**: Users only need a browser and the Bootloader prompt.
- **Consistency**: The same API powers the local CLI (via `requests`) and the browser.
- **Discoverability**: The spec documents the available transitions and state types.

### Negative
- **API Management**: Requires maintaining the API Gateway and OAuth/API Key scopes.

---

## References

- [openapi.yaml](../api/openapi.yaml)
- [ADR-GC-006: Multi-tenant Observability](./ADR-GC-006-multi-tenant-observability.md)
