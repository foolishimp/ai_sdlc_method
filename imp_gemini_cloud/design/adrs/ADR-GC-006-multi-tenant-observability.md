# ADR-GC-006: Multi-tenant Observability & Telemetry

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Gemini Cloud Genesis Design Authors
**Requirements**: REQ-SENSE-001, REQ-SENSE-002, REQ-COORD-006 (Multi-tenancy)
**Extends**: ADR-GC-003 (Firestore Event Sourcing)

---

## Context

To support "consistent monitoring tools and multitenant designs," the architecture must allow multiple independent projects (tenants) to share the same execution engine while maintaining data isolation and providing a unified observability surface for platform operators.

### Requirements
1. **Isolation**: Project A cannot see Project B events.
2. **Consistency**: All projects emit events in the same schema (ADR-GC-014).
3. **Aggregability**: Platform operators can query across projects to detect systemic issues (e.g., "All projects using Python 3.12 are failing CI").

---

## Decision

**We implement a Multi-tenant Observability Layer using Firestore Sub-collections and BigQuery Sync.**

### Data Structure

Firestore root collections are namespaced by Tenant ID (Organization) and Project ID:

- `tenants/{tenant_id}/projects/{project_id}/events` (Collection)
- `tenants/{tenant_id}/projects/{project_id}/features` (Collection)
- `tenants/{tenant_id}/projects/{project_id}/claims` (Collection)

### Telemetry Collector (BigQuery)

We enable **Firestore to BigQuery Extension** (streaming) to mirror all `events` collections into a partitioned BigQuery dataset. This provides the "Consistent Monitoring Tool" backend.

**Schema**: `timestamp | tenant | project | event_type | data (JSON)`

### Real-time Cockpit

A lightweight "Cockpit" CLI or Dashboard connects to Firestore using a Group Query (filtering by user permissions) to show the `STATUS.md` equivalent for all active projects.

---

## Rationale

### Why Firestore Sub-collections?
IAM security rules cascade. Giving a user access to `tenants/acme/projects/A` automatically isolates them from Project B. It natively enforces multi-tenancy.

### Why BigQuery?
Firestore is for OLTP (state, fast lookups). BigQuery is for OLAP (telemetry, trends). The "strengthened structural requirements" for observability (gaps, convergence patterns) require analytical queries that are expensive in Firestore but trivial in BigQuery.

---

## Consequences

### Positive
- **Security**: Native IAM isolation per project.
- **Analytics**: SQL-based analysis of methodology performance across the org.
- **Standardisation**: Enforces the event schema as the integration contract.

### Negative
- **Cost**: BigQuery streaming ingestion has a small cost per GB.
- **Latency**: BigQuery sync has a few seconds of lag (not real-time).

---

## References

- [GEMINI_CLOUD_GENESIS_DESIGN.md](../GEMINI_CLOUD_GENESIS_DESIGN.md)
