# GAP: Human Proxy Should Be a Distinct MCP Actor

**Date**: 2026-03-13T10:35:00Z
**Type**: GAP
**Severity**: Medium
**Traces To**: REQ-F-PROXY-001, REQ-F-HPRX-002
**Parent Feature**: REQ-F-PROXY-001

---

## Observed Gap

REQ-F-PROXY-001 implements `--human-proxy` as an in-session behaviour: the **same LLM
context** that runs `/gen-start --auto` also fulfils the F_H gate. The builder and the
evaluator share identity and context within a single session.

This creates a structural weakness:

| Problem | Effect |
|---------|--------|
| Builder and evaluator are the same entity in the same context | Evaluator has implicit bias toward approving what it just constructed |
| No independent observer | Proxy evaluation is uncheckable from outside the session |
| Session continuity required | Overnight run must remain active in one Claude session — no handoff |

The correct architecture separates roles:

```
Outer controller (cron or event-driven watcher):
  /gen-start --auto → pauses at F_H gate → emits intent_raised{signal_source: human_gate_required}
    ↓
  gen-proxy-review actor (separate MCP invocation):
    reads artifact + F_H criteria from edge config
    evaluates each criterion independently (no builder context)
    writes proxy-log
    emits review_approved{actor: human-proxy}
    ↓
  dispatch_monitor sees review_approved → auto-loop continues
```

This is exactly the F_P actor pattern (ADR-023/024) applied to F_H evaluation:

```
F_H gate → intent manifest written → gen-proxy-review actor invoked via MCP
         → fold-back result → loop continues
```

---

## What REQ-F-PROXY-001 Gets Right

- Proxy-log for auditability (REQ-F-HPRX-003) ✓
- `actor: "human-proxy"` on events (REQ-F-HPRX-004) ✓
- Morning review and override (REQ-F-HPRX-006) ✓
- No self-correction prohibition (REQ-BR-HPRX-001) ✓

The gap is architectural, not functional. The behaviour spec is correct; the execution
topology is suboptimal.

---

## Proposed Fix

**New actor**: `gen-proxy-review` — an MCP-dispatchable agent that:

1. Receives an F_H gate manifest (same structure as F_P actor manifests — ADR-024)
2. Reads the artifact at the path specified
3. Loads the F_H criteria from the edge config
4. Evaluates each criterion with no builder context (cold read)
5. Writes proxy-log + emits `review_approved{actor: human-proxy}`

**Integration point**: In `gen-iterate.md` Step 4, at the F_H gate, when `--human-proxy`:

```
Instead of: evaluate inline in current context
Do:         write fh_proxy_intent_{run_id}.json
            invoke: mcp__claude-code-runner__claude_code(proxy_manifest["prompt"])
            actor writes fh_proxy_result_{run_id}.json (proxy-log path + decision)
            read result; continue or halt
```

**Key benefit**: The proxy evaluator has no memory of constructing the artifact. Its
evaluation is a fresh cold read against the stated criteria only — closer to genuine
human review than in-session self-evaluation.

---

## Option A (current — REQ-F-PROXY-001)

Same-session proxy. Fast to implement; audit log compensates for evaluator bias.
Adequate for overnight runs where morning review is the safety net.

## Option B (this gap — follow-on feature)

Separate MCP actor for proxy evaluation. Stronger independence; no session continuity
requirement; evaluator context is cleanly isolated from builder context.

**Recommended**: Implement Option B as a child vector of REQ-F-PROXY-001.
Option A remains valid for use cases where the MCP actor overhead is not warranted.

---

## Suggested Feature ID

`REQ-F-PROXY-002 — Human Proxy as Independent MCP Actor`

Parent: REQ-F-PROXY-001
Profile: standard
Dependencies: REQ-F-PROXY-001 (proxy-log format, event schema), ADR-023/024 (fold-back protocol)
