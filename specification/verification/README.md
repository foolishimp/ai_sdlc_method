# Verification — Shared Acceptance Contracts

This directory contains **platform-agnostic verification artifacts** — the shared contracts that any implementation must satisfy.

## Why not in `specification/`?

The `specification/` directory defines WHAT the system *is* (requirements, formal model). Verification documents define HOW to confirm any implementation *satisfies* those requirements. These are different things — in the asset graph, Spec and UAT Tests are separate nodes:

```
Spec → Design → Code ↔ Unit Tests → UAT Tests → CI/CD → Telemetry→Intent
 ▲                                       ▲
 │                                       │
specification/                      verification/
```

## Why not in `imp_*/tests/`?

Because the scenarios here are **platform-agnostic**. A Gemini implementation and a Claude implementation must both pass these same acceptance criteria. The executable test code lives in each `imp_*/tests/uat/` — this document is the shared contract they both implement.

## Contents

| Document | What it covers |
|----------|---------------|
| [UAT_TEST_CASES.md](UAT_TEST_CASES.md) | 9 use cases, BDD-style (Given/When/Then), traced to REQ keys. One use case per major domain: Asset Graph Engine, Evaluators, Context, Traceability, Edges, Lifecycle, Sensory, Tooling, UX. |
