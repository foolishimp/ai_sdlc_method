# MATRIX: Cross-Tenant Orchestration Analysis (Claude vs. Gemini vs. Cloud)

**Author**: Gemini
**Date**: 2026-03-07T15:30:00Z
**Addresses**: `imp_claude/`, `imp_gemini/`, `imp_gemini_cloud/`
**For**: all

## Summary
Analysis of orchestration patterns across all three implementation tenants. While `imp_gemini` (Local Core) utilizes Prefect for asynchronous task management, this pattern is identified as redundant for `imp_gemini_cloud` (Downstream), which must remain GCP Native. `imp_claude` utilizes an "Orthogonal Projection" model with a deterministic engine gating an MCP-based Recursive Actor.

## Decision Evaluation Matrix

| Item | Proposal | Spec Alignment | Delivery Risk | Effort | Decision | Reasoning |
|---|---|---:|---:|---:|---|---|
| 1 | **Prefect for Cloud** | Low | High | Medium | **Reject** | Introduces redundant orchestration layer; violates GCP Native mandate. |
| 2 | **Recursive Actor (MCP)** | High | Low | Low | **Adopt (Claude)** | Lightweight, session-aware, and perfectly suited for interactive CLI environments. |
| 3 | **GCP Cloud Workflows** | High | Medium | Medium | **Adopt (Cloud)** | Provides serverless, event-driven state management aligned with Firestore/Vertex AI. |
| 4 | **Deterministic Engine Loop**| High | Low | Low | **Adopt (All)** | Core engine should be a deterministic supervisor ($F_D$) that gates agent work ($F_P$). |

## Orchestration Patterns Comparison

| Feature | imp_claude | imp_gemini (Local) | imp_gemini_cloud |
| :--- | :--- | :--- | :--- |
| **Primary Driver** | Sequential Engine Loop | Prefect Workflows | GCP Cloud Workflows |
| **Agent Transport** | MCP (Recursive Actor) | Direct Object/Prefect Task | Cloud Run / Vertex AI |
| **State Persistence** | Local Filesystem | Prefect API / Local FS | GCP Firestore (Native) |
| **Design Principle** | Orthogonal Projection | Recoverable Flow | Serverless Homeostasis |

### Key Findings
1.  **Claude's "Recursive Actor" (ADR-024)**: Claude bypasses heavy workflow engines by treating $F_P$ as a tool-calling sub-session. The engine remains a pure $F_D$ supervisor.
2.  **Gemini's "Recoverable Flow"**: Prefect is used locally to manage long-running agent tasks that might outlive a single CLI invocation.
3.  **Cloud's "Serverless Homeostasis"**: The cloud implementation maps the SDLC graph directly to **Cloud Workflows**. This eliminates the need for any persistent orchestrator (like Prefect or a long-running Python engine).

## Recommended Action
1.  **Isolate Prefect**: Ensure Prefect dependencies remain strictly within the `imp_gemini` core and do not leak into `imp_gemini_cloud`.
2.  **Implement Cloud Workflows**: Transition the `CloudIterateEngine` in `imp_gemini_cloud` to be triggered by Cloud Workflows steps rather than a local loop.
3.  **Align Functor Protocols**: Ensure both Vertex AI and MCP functors adhere to the same `Intent -> StepResult` contract defined in `ADR-S-016`.
