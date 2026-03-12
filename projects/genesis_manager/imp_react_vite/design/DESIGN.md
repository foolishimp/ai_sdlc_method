# genesis_manager — Claude Code Implementation Design

**Version**: 0.1.0
**Date**: 2026-03-13
**Status**: Skeleton — pending specification convergence

---

## Overview

This is the Claude Code implementation tenant for genesis_manager.

The product specification lives in `../specification/`. This document covers implementation-specific decisions (HOW) that do not belong in the spec.

---

## Technology Choices (TBD)

Technology decisions will be captured as ADRs in `adrs/ADR-GM-*` once requirements and feature decomposition are converged.

Key questions to answer at the design edge:
- Frontend framework (React, Vue, Svelte?)
- Backend (FastAPI, Express, or pure static with genesis engine as subprocess?)
- Data access pattern (direct filesystem, genesis engine API, or event log projection?)
- Deployment target (local dev tool, cloud SaaS, or both?)

---

## Implementation Tenant Structure

```
imp_react_vite/
├── design/
│   ├── DESIGN.md          ← this file
│   └── adrs/              ← ADR-GM-C-001+ (implementation ADRs)
├── code/                  ← implementation (TBD after design)
└── tests/                 ← test suite (TBD after design)
```
