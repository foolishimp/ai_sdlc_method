# ADR-030: Spec Evolution Pipeline — Implementation Design

**Status**: Accepted — 2026-03-07
**Feature**: REQ-F-EVOL-001 (Spec Evolution Pipeline)
**Edge**: feature_decomposition→design (iteration 1)
**Satisfies**: REQ-EVOL-001, REQ-EVOL-002, REQ-EVOL-003, REQ-EVOL-004, REQ-EVOL-005
**Implements**: See also ADR-S-009, ADR-S-010

---

## Context

REQ-F-EVOL-001 implements the event-sourced pipeline for evolving the specification. The decomposition identified five build units (EVOL-U1..U5). This ADR audits current implementation state and makes the remaining design decisions.

### Implementation State Audit (2026-03-07)

| Unit | Req | Status | What Exists |
|------|-----|--------|-------------|
| EVOL-U1 | REQ-EVOL-001 | Partial | `workspace_state.py:738` checks `satisfies`+`success_criteria` in health check. No `WorkspaceSchemaViolation` exception at read time. |
| EVOL-U2 | REQ-EVOL-002 | Implemented | `compute_spec_workspace_join()` in `workspace_state.py:310` covers ACTIVE/COMPLETED/PENDING/ORPHAN. `workspace_gradient.py` has delta types. |
| EVOL-U3 | REQ-EVOL-004 | Partial | `ol_event.spec_modified()` implemented at `ol_event.py:527`. Missing: spec hash verification in health check; SPEC_DRIFT warning type. |
| EVOL-U4 | REQ-EVOL-003 | Stub | `fd_classify.py:144` has taxonomy entry. No `feature_proposal()` constructor in `ol_event.py`. Phase 2. |
| EVOL-U5 | REQ-EVOL-005 | Missing | No `compute_draft_queue()`. Phase 2. |

---

## Decisions

### Decision 1: WorkspaceSchemaViolation Exception

**EVOL-U1 gap**: The forbidden-field check in `workspace_state.py` only fires in the health check scan. REQ-EVOL-001 requires the violation to be raised at read time so callers get an immediate, named signal rather than discovering violations hours later in a batch health check.

**Decision**: Add `WorkspaceSchemaViolation(RuntimeError)` to `contracts.py`. Raise it in `load_feature_vector()` (wherever workspace YAML is loaded for use, not just health scanning). The health check scan continues to exist as a batch audit — it catches vectors that were written before enforcement was in place.

**Forbidden key set** (REQ-EVOL-DATA-001):
```python
FORBIDDEN_WORKSPACE_KEYS = frozenset({
    "satisfies",          # spec: REQ-* mapping
    "success_criteria",   # spec: product outcomes
    "dependencies",       # spec: feature dependency graph
    "what_converges",     # spec: convergence description
    "phase",              # spec: release phase assignment
})
```

The current set (`satisfies`, `success_criteria`) is a subset. The full set adds three fields that appeared in earlier workspace YAMLs before the schema was tightened.

---

### Decision 2: Spec Hash Verification

**EVOL-U3 gap**: `ol_event.spec_modified()` is implemented but nothing calls it automatically, and nothing verifies `sha256(current file) == most_recent_spec_modified.new_hash`.

**Decision**:
- Add `verify_spec_hashes(workspace, spec_dir) → list[SpecDriftWarning]` to `workspace_state.py`. Reads event log, extracts the most recent `spec_modified` event per file path, computes current hash, compares.
- Add `SPEC_DRIFT` as a named health warning type (join `PENDING`/`ORPHAN` in `workspace_gradient.py`).
- Surface in `run_health_checks()` as a new check: `spec_hash_consistency`.
- The spec_modified emission path: `gen-spec-review` command already calls spec modification; wire to `ol_event.spec_modified()` there. Manual edits: document that the author should call `gen-spec-review` after modifying spec files.

---

### Decision 3: feature_proposal() Constructor (Phase 2)

**EVOL-U4**: `fd_classify.py` already has the taxonomy entry. The constructor is missing.

**Decision**: Add `feature_proposal()` to `ol_event.py` with the schema from REQ-EVOL-003:
- `proposal_id`, `proposed_feature_id`, `proposed_title`, `proposed_description`, `proposed_satisfies`, `trigger_intent_id`, `trigger_signal_id`, `source_stage`, `rationale`, `status: "draft"`
- The function signature mirrors `spec_modified()` — same emit pattern.
- Deferred to Phase 2 (requires REQ-F-LIFE-001 convergence as emitter).

---

### Decision 4: Draft Features Queue (Phase 2)

**EVOL-U5**: The projection is missing entirely.

**Decision**: Add `compute_draft_queue(workspace) → list[DraftProposal]` to `workspace_state.py`:
```
DraftProposal = namedtuple('DraftProposal',
    ['proposal_id', 'proposed_feature_id', 'proposed_title',
     'trigger_intent_id', 'rationale', 'emitted_at'])

Algorithm:
  1. Stream events.jsonl, collect all feature_proposal events → proposals dict[proposal_id]
  2. Stream again, collect spec_modified where trigger_event_id in proposals → promoted set
  3. Stream again, collect feature_proposal_rejected where proposal_id in proposals → rejected set
  4. Queue = proposals - promoted - rejected
  5. Return sorted by emitted_at ascending (oldest first)
```

Gen-review command extensions (Phase 2):
- `gen-review approve {proposal_id}`: calls promote_proposal() which appends to FEATURE_VECTORS.md, emits spec_modified, inflates workspace trajectory
- `gen-review reject {proposal_id} --reason "{text}"`: emits feature_proposal_rejected event

The inflate operation creates a minimal workspace trajectory YAML from `graph_topology.yml` standard profile edges, all in `{status: pending}` state. This is `inflate_feature_vector()` in `workspace_state.py`.

---

### Decision 5: No New Files — Extend Existing Modules

All Phase 1 implementation fits into existing files:

| Change | File |
|--------|------|
| `WorkspaceSchemaViolation` exception | `contracts.py` |
| `FORBIDDEN_WORKSPACE_KEYS` expansion | `workspace_state.py` |
| Raise `WorkspaceSchemaViolation` on load | `workspace_state.py` |
| `verify_spec_hashes()` | `workspace_state.py` |
| `SPEC_DRIFT` delta type | `workspace_gradient.py` |
| `spec_hash_consistency` health check | `workspace_state.py` `run_health_checks()` |

Phase 2 additions:

| Change | File |
|--------|------|
| `feature_proposal()` constructor | `ol_event.py` |
| `compute_draft_queue()` | `workspace_state.py` |
| `inflate_feature_vector()` | `workspace_state.py` |
| `approve`/`reject` subcommands | `gen-review.md` command |

---

## Implementation Plan (Phase 1)

### Step 1: contracts.py — WorkspaceSchemaViolation

```python
class WorkspaceSchemaViolation(ValueError):
    """Raised when a workspace feature vector contains forbidden definition fields.

    These fields belong in specification/features/, not in .ai-workspace/.
    Implements: REQ-EVOL-001 (Workspace Vectors Are Trajectory-Only)
    """
    def __init__(self, path: str, field: str) -> None:
        super().__init__(
            f"Workspace schema violation in {path!r}: "
            f"forbidden field {field!r} belongs in specification/features/, not workspace"
        )
        self.path = path
        self.field = field
```

### Step 2: workspace_state.py — Forbidden Key Expansion + Load-Time Enforcement

Expand `_FORBIDDEN_WORKSPACE_KEYS` to the full set. Add enforcement in `load_feature_vector()`:
```python
def load_feature_vector(path: Path) -> dict:
    data = yaml.safe_load(path.read_text()) or {}
    for key in FORBIDDEN_WORKSPACE_KEYS:
        if key in data:
            raise WorkspaceSchemaViolation(str(path), key)
    return data
```

### Step 3: workspace_state.py — verify_spec_hashes()

```python
def verify_spec_hashes(workspace: Path, spec_dir: Path | None = None) -> list[dict]:
    """Compare current spec file hashes against last spec_modified event per file.
    Returns list of SPEC_DRIFT dicts: {file, expected_hash, actual_hash, event_timestamp}
    Implements: REQ-EVOL-NFR-002 (Spec Hash Verification)
    """
```

### Step 4: workspace_gradient.py — SPEC_DRIFT delta type

Add `DELTA_SPEC_DRIFT = "SPEC_DRIFT"` alongside PENDING/ORPHAN. Include in `WorkspaceGradient` fields.

### Step 5: workspace_state.py — run_health_checks() extension

Add `spec_hash_consistency` check that calls `verify_spec_hashes()` and reports SPEC_DRIFT findings.

---

## Consequences

**Positive**:
- `WorkspaceSchemaViolation` makes schema violations immediately observable — callers can't accidentally use a malformed workspace vector
- Spec hash verification closes the audit loop — spec drift is detectable without manual inspection
- All Phase 1 work fits in existing files — no new modules required

**Negative**:
- Load-time schema enforcement is a breaking change for any workspace vector that currently contains forbidden fields — mitigation: run health check first, fix violations, then deploy
- Phase 2 deferred — until REQ-F-LIFE-001 converges, the pipeline generates no proposals autonomously. Manual `feature_proposal` events can be hand-crafted for testing.

---

## Test Plan

| Test | What it validates | REQ |
|------|-----------------|-----|
| `test_workspace_schema_violation_raised_on_forbidden_field` | `WorkspaceSchemaViolation` raised when `satisfies` present | REQ-EVOL-001 |
| `test_workspace_schema_violation_lists_field_name` | Exception message contains the offending field | REQ-EVOL-001 |
| `test_workspace_schema_violation_all_forbidden_keys` | All 5 forbidden keys trigger violation | REQ-EVOL-DATA-001 |
| `test_spec_hash_verify_detects_drift` | Modified spec file not in event log → SPEC_DRIFT | REQ-EVOL-NFR-002 |
| `test_spec_hash_verify_clean` | Spec file matches event log → no drift | REQ-EVOL-NFR-002 |
| `test_health_check_includes_spec_hash_consistency` | `run_health_checks()` includes `spec_hash_consistency` | REQ-EVOL-NFR-002 |
| `test_join_shows_pending_features` | Spec-only features surface as PENDING | REQ-EVOL-002 |
| `test_join_shows_orphan_features` | Workspace-only features surface as ORPHAN | REQ-EVOL-002 |
| *(Phase 2)* `test_feature_proposal_event_schema` | All required fields present | REQ-EVOL-003 |
| *(Phase 2)* `test_draft_queue_excludes_promoted` | Promoted proposals not in queue | REQ-EVOL-005 |
