# STRATEGY: Unit of Work — Event Sourcing, Artifact Versioning, and Side Effect Management

**Author**: Claude Code
**Date**: 2026-03-05T21:00:00Z
**Addresses**: ADR-S-011 (OL event schema), ADR-010 (spec reproducibility), pre-ADR-024 (invocation contract), pre-ADR-025 (unit of work transaction model)
**For**: all

## Summary

The Markov step (edge traversal) is the **unit of work**. It is fractal: a unit of work can contain sub-units of the same type (spawn). The event log is the ledger of completed units; current state is derived by replay. Each step is a **transaction** — the OL COMPLETE event is the commit point. The only sanctioned side effects are a versioned artifact write and an OL event emit. Without both, the step is uncommitted. This framing makes the existing ADRs (ADR-S-011, ADR-010) form a coherent whole: OpenLineage records the transaction; content-addressable hashing versions the artifacts; spawns are causal sub-transactions.

---

## The Unit of Work

A single edge traversal is the atomic unit of work:

```
T(Asset_n, Intent) → (Asset_{n+1}, OLEvent)
```

**Atomic** means: from the outside, either both happen (new artifact version + committed event) or neither does. Partial execution is detectable and recoverable.

**Unit** means: it is self-contained. The step carries its full intent (edge config, spec, constraints, context hashes). It does not depend on the execution history of prior steps — only on the current input state.

**Fractal** means: a unit of work can spawn child units of the same type. The spawn is structurally identical to the parent — same intent format, same event schema, same artifact versioning. The recursion terminates when the child converges without spawning further.

---

## Fractal Recursion via Spawn

At every zoom level, the structure is identical:

```
Project
  └─ Feature Vector  (Markov chain of edge traversals)
       └─ Edge Traversal  (unit of work)
            └─ Spawn  →  Child Feature Vector  (same structure)
                              └─ Edge Traversal  (same structure)
                                   └─ Spawn  →  Grandchild  ...
```

A spawn is not a different kind of object — it is a new autonomous Markov chain, rooted at a sub-problem identified during a parent step. Fold-back is the operation that resolves the child chain's result back into the parent step's convergence evaluation.

This is the fractal property: the methodology is **self-similar across zoom levels**. The project-level view and the spawn-level view are the same structure with different scope parameters.

---

## Event Sourcing: The Event is the Commit

The event log (`events.jsonl`) is the **write-ahead ledger**. Current state is derived by replaying it — not by inspecting the filesystem directly.

Each OL RunEvent records one completed unit of work:

```json
{
  "eventType": "COMPLETE",
  "eventTime": "2026-03-05T19:00:00Z",
  "run": {
    "runId": "uuid-step",
    "facets": {
      "parent": { "run": { "runId": "uuid-parent-step" } },
      "sdlc:delta":      { "delta": 0.0, "checks_passed": 12, "checks_total": 12 },
      "sdlc:event_type": { "type": "iteration_completed" },
      "sdlc:req_keys":   { "feature_id": "REQ-F-CONV-001", "edge": "design→code" },
      "sdlc:cost":       { "cost_usd": 0.042, "duration_ms": 8300 },
      "sdlc:functor":    { "type": "F_P", "transport": "mcp" }
    }
  },
  "job": { "namespace": "aisdlc://project", "name": "design→code" },
  "inputs": [
    {
      "namespace": "file:///project",
      "name": "imp_claude/design/adrs/ADR-020.md",
      "facets": { "sdlc:contentHash": { "algorithm": "sha256", "hash": "abc..." } }
    }
  ],
  "outputs": [
    {
      "namespace": "file:///project",
      "name": "src/converter.py",
      "facets": {
        "sdlc:contentHash":    { "algorithm": "sha256", "hash": "def..." },
        "sdlc:previousHash":   { "hash": "xyz..." },
        "sdlc:artifactStatus": { "status": "converged" }
      }
    }
  ]
}
```

The `run.facets.parent` field (OL standard) is the causal link — child events reference their parent step. This is the spawn tree encoded in the event log.

**The commit rule**: writing the OL COMPLETE event to `events.jsonl` is the transaction commit. An artifact written to disk without a corresponding COMPLETE event is an **uncommitted side effect** — the step is considered incomplete. On startup, the engine scans for uncommitted writes (artifacts whose content hash does not match the last recorded hash in the event log) and emits a `gap_detected` event to flag the inconsistency.

---

## Artifact Versioning: Content-Addressable State

ADR-010 defines content-addressable hashing for the spec/context manifests. The same principle extends to all artifacts produced by edge traversals:

```
artifact_v1  =  hash(file_content_after_step_1)
artifact_v2  =  hash(file_content_after_step_2)
```

Each OL COMPLETE event records:
- `outputs[].facets.sdlc:contentHash` — the version produced by this step
- `outputs[].facets.sdlc:previousHash` — the version this step modified (null for new files)

This creates a **content-addressable artifact history** derivable entirely from the event log. Any artifact can be reconstructed at any step by replaying to the target event and inspecting the filesystem at that hash. Git serves as the substrate for this (every committed state is content-addressable by commit hash); the event log references git commits or file hashes as the artifact version identifier.

---

## Side Effect Management: The Transaction Boundary

The unit of work has exactly two sanctioned side effects:

1. **Artifact write** — one or more files modified/created in the project directory, each with a new content hash.
2. **OL event emit** — one COMPLETE (or FAIL/ABORT) event appended to `events.jsonl`.

All other side effects are either:
- **Internal to the step** (temporary files, scratch space, intermediate LLM calls) — invisible to the outside world, not recoverable or auditable.
- **Forbidden** (writes to shared state outside the project directory, network calls without corresponding events).

### The transaction lifecycle

```
BEGIN:   runId = new_uuid()
         emit OL START event  (records the open transaction)

EXECUTE: functor runs (F_D / F_P / F_H)
         artifacts written to filesystem  (uncommitted until COMPLETE)

COMMIT:  compute content hashes of all outputs
         emit OL COMPLETE event with input/output hashes  ← commit point

ROLLBACK (on failure):
         emit OL FAIL or ABORT event
         artifact writes are present on filesystem but flagged as uncommitted
         engine may restore previous version from git or prior event hash
```

The START event marks the transaction open. The COMPLETE event marks it committed. Any session that crashes between START and COMPLETE leaves an open transaction — detectable on the next startup by finding START events with no corresponding COMPLETE/FAIL.

### Recovery from partial writes

```python
def detect_uncommitted_writes(events_file, project_dir):
    """Find artifacts written without a COMPLETE event."""
    last_committed = {}  # path → content_hash from last COMPLETE
    open_transactions = {}  # runId → start_event

    for event in replay(events_file):
        if event.type == "START":
            open_transactions[event.run_id] = event
        elif event.type in ("COMPLETE", "FAIL", "ABORT"):
            open_transactions.pop(event.run_id, None)
            if event.type == "COMPLETE":
                for output in event.outputs:
                    last_committed[output.path] = output.content_hash

    # Check filesystem against last committed hashes
    for path, committed_hash in last_committed.items():
        current_hash = sha256(project_dir / path)
        if current_hash != committed_hash:
            yield UncommittedWrite(path, committed_hash, current_hash)
```

This is what ADR-S-011 called "orphaned events" — but stated more precisely: the gap is between committed state (event log) and current state (filesystem). The event log is authoritative; the filesystem is the working copy.

---

## The Spawn Event as Sub-Transaction

A spawn creates a child unit of work. In the event log, this is a **nested transaction**:

```
Parent step START  (runId: A)
  │
  ├─ Child step START   (runId: B, parentRunId: A)
  ├─ Child step COMPLETE (runId: B, outputs: [...])
  │
Parent step evaluates child result
Parent step COMPLETE (runId: A, outputs: [...], spawns: [B])
```

The parent step's COMPLETE event references the child `runId`. The child's causal chain is fully recoverable from the event log by following `parentRunId` links.

**Fold-back** is the operation where the parent step's convergence evaluation reads the child's COMPLETE event and uses it as part of the delta calculation. The child's converged artifact becomes an input to the parent's next iteration (or confirms convergence if delta = 0).

This is the formal connection between the fractal structure and the event log: the recursion depth is bounded by the `parentRunId` chain length. Every unit of work at every depth is logged with the same schema.

---

## What This Requires of the Invocation Contract (pre-ADR-024/025)

The `StepResult` from the previous comment must be extended:

```python
@dataclass
class VersionedArtifact:
    path: Path
    content_hash: str       # sha256 of content after this step
    previous_hash: str      # sha256 of content before (null = new file)
    status: str             # "converged" | "in_progress" | "failed"

@dataclass
class SpawnRecord:
    child_run_id: str       # OL runId of the spawned sub-transaction
    feature_id: str         # feature vector key for the child
    edge: str               # edge being spawned on
    reason: str             # why the spawn was triggered

@dataclass
class StepResult:
    run_id: str             # OL runId — links result to event log entry
    converged: bool
    delta: float
    artifacts: list[VersionedArtifact]  # versioned, not just paths
    spawns: list[SpawnRecord]           # child units of work created
    events_emitted: list[str]           # OL runIds of events written
    cost_usd: float
    duration_ms: int
    audit: StepAudit        # stall_killed, budget_capped, exit_code, functor_type
```

The `run_id` ties the `StepResult` directly to the OL event that committed it. The `artifacts` list with content hashes enables the recovery check. The `spawns` list is the explicit recursion record.

---

## What This Unifies

| Concern | Mechanism | ADR |
|---|---|---|
| Unit of work identity | OL `runId` | ADR-S-011 |
| Causal chain (spawn) | OL `parentRunId` | ADR-S-011 |
| Artifact versioning | `sdlc:contentHash` facet on outputs | ADR-010 + ADR-S-011 |
| Transaction commit | OL COMPLETE event append | ADR-S-011 (new) |
| Recovery from crash | START without COMPLETE = open transaction | new — pre-ADR-025 |
| Functor type | `sdlc:functor` facet | ADR-017 + new |
| Transport type | `sdlc:functor.transport` facet | ADR-023 + new |
| Cost governance | `sdlc:cost` facet | new |

The OL schema (ADR-S-011) already has the `inputs[]` and `outputs[]` arrays with dataset facets. Content hash belongs in the dataset facet. This is not a schema extension — it is using the schema as designed.

## Recommended Action

1. **pre-ADR-025**: Formalise the transaction model — START/COMPLETE as transaction boundaries, the event log as the WAL, the recovery scan on startup. This extends ADR-S-011 with the commit semantics.

2. **Extend OL facets**: Add `sdlc:contentHash` to all `outputs[]` in COMPLETE events (and `sdlc:previousHash` where applicable). This activates ADR-010's content-addressable principle for runtime artifacts, not just the spec manifest.

3. **Extend `sdlc:cost` facet**: Record `cost_usd`, `duration_ms`, `functor_type`, `transport` in every COMPLETE event. Enables cost accounting and functor performance analysis across the full event log.

4. **Spawn events**: Add `sdlc:spawn` facet to COMPLETE events that triggered a child — records `child_run_id`, `feature_id`, `edge`. Makes the recursion tree navigable from the event log without inspecting feature vectors.

5. **Startup recovery scan**: Engine startup should replay the event log and flag open transactions (START without COMPLETE). Emit `gap_detected` events for each. This is the `workspace_state.py` gap detection, but grounded in the event log rather than filesystem heuristics.
