# ADR-020: Human Proxy Evaluation Lives in the Command Layer

**Status**: Accepted
**Date**: 2026-03-13
**Implements**: REQ-F-PROXY-001 (REQ-F-HPRX-001..006, REQ-NFR-HPRX-001..002, REQ-BR-HPRX-001..002)
**Traces To**: INT-AISDLC-001

---

## Context

Human Proxy Mode (REQ-F-PROXY-001) requires that, when `--auto --human-proxy` is active,
the LLM evaluates artifacts against F_H criteria rather than pausing for terminal input.

There are two candidate locations for this logic:

1. **Python engine** (`genesis/__main__.py`, `edge_runner.py`) — the deterministic
   evaluation layer (F_D)
2. **Command layer** (`gen-iterate.md`, `gen-start.md`) — the LLM orchestration layer
   that already owns F_H gate prompting

---

## Decision

**Proxy evaluation logic lives entirely in the command layer (option 2).**

The Python engine is not modified.

---

## Rationale

### The engine does not do F_H evaluation today

The engine's responsibility is F_D evaluation: deterministic checks, schema validation,
delta computation, fold-back manifest writing. F_H evaluation is entirely the command
layer's domain — it is the LLM reading criteria and prompting the human (or, in proxy
mode, evaluating autonomously).

Adding F_H proxy logic to the engine would:
- Require the engine to invoke MCP or LLM tooling (which it explicitly cannot — ADR-023)
- Blur the engine/LLM boundary that ADR-023 establishes
- Make the engine aware of `--human-proxy`, a UX concern

### The command layer already owns F_H

`gen-iterate.md` Step 4 already reads "If human evaluator required: present the candidate
for review." Proxy mode replaces "present and wait" with "evaluate and log." This is a
small, local change to the LLM orchestration path — no new architectural boundary required.

### The escalation chain is: F_D → F_P → F_H

Proxy mode substitutes the F_H actor (human → LLM-acting-as-proxy). The substitution
is at the F_H level. The F_D engine and F_P actor dispatch path are unaffected.

### Auditability is preserved in the log + event stream

The risk of command-layer proxy evaluation (no machine enforcement) is mitigated by:
- One proxy-log file per decision with evidence citations (REQ-F-HPRX-003)
- `actor: "human-proxy"` on every proxy `review_approved` event (REQ-F-HPRX-004)
- Morning review via `/gen-status` surfacing all proxy decisions (REQ-F-HPRX-006)
- Human override available at any time (REQ-F-HPRX-006)

These controls make proxy decisions fully auditable without embedding enforcement in
the engine.

---

## Consequences

### Positive
- Zero engine changes — proxy mode is a pure command-layer overlay
- Clean separation: engine = F_D, command layer = F_P + F_H (including proxy F_H)
- Proxy mode ships without a Python release

### Negative
- Machine enforcement of proxy evaluation quality is impossible — the LLM may produce
  low-quality evaluations. Mitigation: proxy-log + morning review + human override.
- Session-tracking (`rejected_in_session`) is in-memory only — if the session is killed,
  the prohibition on self-correction is not enforced on resume. Mitigation: proxy-log
  records the rejection; morning review catches any inconsistency.

### Neutral
- Command source files (`gen-iterate.md`, `gen-start.md`, `gen-status.md`) are modified.
  Installer redeploys to target projects. Existing installed copies are replaced on next
  install run.

---

## Alternatives Rejected

**Option A: Engine-side proxy mode**
Would require the engine to call MCP tools or spawn LLM subprocesses — violates ADR-023.
Rejected.

**Option B: Separate proxy agent**
A new MCP-dispatched agent for proxy evaluation. Adds a new actor type and fold-back
path for a feature that is entirely within the existing F_H responsibility boundary.
Over-engineered for the scope. Rejected.
