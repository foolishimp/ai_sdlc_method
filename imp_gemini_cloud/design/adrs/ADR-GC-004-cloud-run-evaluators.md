# ADR-GC-004: Cloud Run Jobs for Deterministic Evaluators

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Gemini Cloud Genesis Design Authors
**Requirements**: REQ-EVAL-001, REQ-TOOL-005
**Extends**: ADR-GC-001 (Vertex AI Platform)

---

## Context

Deterministic evaluators (F_D) require executing arbitrary code (tests, linters, static analysis). These tasks can be long-running (minutes) and require specific language toolchains (Python, Node, Go). Standard Cloud Functions have execution limits and environment constraints that make them unsuitable for diverse test suites.

### Options Considered

1. **Cloud Functions**: Too limited in timeout and environment customization.
2. **GKE**: Too much infrastructure to manage for an on-demand task.
3. **Cloud Run Jobs (The Decision)**: Executes containerized tasks on demand with no idle cost and high timeout limits (up to 24h).

---

## Decision

**We use Cloud Run Jobs to execute all deterministic (F_D) evaluators.**

Each language/toolchain (e.g., `python-pytest`, `node-jest`) will have a pre-built container image in Artifact Registry. The iterate workflow will launch a Cloud Run Job, passing the artifact location (GCS URI) and the REQ keys to verify as environment variables.

---

## Rationale

### Isolation and Flexibility
Cloud Run Jobs provide true container isolation. Each test run happens in a clean room. Developers can update test runners by pushing a new image to Artifact Registry without modifying the core methodology engine.

---

## Consequences

### Positive
- **Infinite Scale**: Hundreds of test suites can run in parallel.
- **Custom Environments**: Any toolchain can be supported via Docker.
- **Pay-per-use**: No cost when no tests are running.

### Negative
- **Startup Latency**: Container pull/startup adds 5-15 seconds to the evaluation turn.

---

## References

- [GEMINI_CLOUD_GENESIS_DESIGN.md](../GEMINI_CLOUD_GENESIS_DESIGN.md)
- [ADR-AB-002](../adrs/ADR-AB-002-iterate-engine-step-functions.md) — AWS Lambda containers equivalent
