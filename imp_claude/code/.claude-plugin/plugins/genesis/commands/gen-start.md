# /gen-start - State-Driven Routing Entry Point

State-machine controller that detects project state and delegates to the appropriate command. Two verbs replace the 9-command learning curve: **Start** ("Go.") and **Status** ("Where am I?").

<!-- Implements: REQ-UX-001, REQ-UX-002, REQ-UX-004, REQ-UX-005, REQ-TOOL-003 (Workflow Commands), REQ-INTENT-001 (Intent Capture — Step 3), REQ-INTENT-002 (Intent as Spec — Step 3) -->
<!-- Reference: AI_SDLC_ASSET_GRAPH_MODEL.md v2.9.0 §7.5 Event Sourcing, ADR-012 -->

## Progressive Disclosure (First-Run Path)

<!-- Implements: REQ-UX-002 (Progressive Disclosure — show minimal options first; reveal depth on demand) -->

**When to activate this path**: First-run is detected when EITHER:
- `.ai-workspace/` does not exist (no workspace), OR
- `.ai-workspace/events/events.jsonl` is absent or empty (zero events recorded)

On first-run, **do not present the full state-machine routing** (Steps 0–10 below). Instead, show only 3 choices:

```
Welcome to Genesis! What would you like to do?

  1. Start a new project     — initialise workspace, capture intent, create first feature
  2. Continue existing work  — resume from a previous session (workspace found elsewhere)
  3. Quick spike             — explore an idea without committing to a full feature vector

Enter 1, 2, or 3 (or press Enter for option 1):
```

**Option 1 — New project**: Proceed directly to Step 1 (Progressive Init) below. Do NOT show profile options, graph topology, or context hierarchy. These are deferred until after the first iteration completes (see Step 2: Deferred Constraint Prompting).

**Option 2 — Continue existing**: Ask for the workspace path and load it. Then proceed with the standard state-detection algorithm (Step 0) as normal. This path reveals full complexity because the user has prior experience.

**Option 3 — Quick spike**: Proceed to Step 4 (Feature Creation) with `--profile spike --type spike`. Skip intent authoring — ask only "In one sentence, what are you investigating?" Write response to `specification/INTENT.md` and create a spike vector immediately.

**After first iteration completes**, the progressive disclosure path ends. Subsequent `/gen-start` invocations use the full state-detection algorithm (Step 0). Advanced options — graph topology override, profile selection, context hierarchy, functor encoding — are available via flags but never shown unprompted on first-run.

**What is deferred** (not shown until explicitly requested):
- Graph topology options (`--edge`, graph_topology.yml)
- Profile selection (`--profile full|standard|poc|spike|hotfix|minimal`)
- Context hierarchy and constraint dimensions
- Functor encoding configuration
- Zoom management (`/gen-zoom`)
- Observer dispatch configuration

## Usage

```
/gen-start [--feature "REQ-F-*"] [--edge "source→target"] [--auto] [--profile "standard"] [--asset "path/to/file"]
```

| Option | Description |
|--------|-------------|
| (none) | Detect state, select feature/edge, run one iteration |
| `--feature` | Override automatic feature selection |
| `--edge` | Override automatic edge determination |
| `--auto` | Loop: iterate → check convergence → next edge → repeat (pauses at human gates) |
| `--profile` | Override default profile for new features |
| `--asset` | Inject an existing document as the candidate asset for the current edge (skips construction from scratch) |

## Instructions

### Step 0: State Detection Algorithm

Detect the current project state from the workspace filesystem and event log. **State is derived, never stored** (§7.5 Event Sourcing).

Check in this order (first match wins):

| # | State | Detection | Action |
|---|-------|-----------|--------|
| 1 | `UNINITIALISED` | No `.ai-workspace/` directory | → Progressive Init (Step 1) |
| 2 | `NEEDS_CONSTRAINTS` | `.ai-workspace/` exists AND `project_constraints.yml` has mandatory dimensions with empty values AND at least one feature is at or past `requirements→design` edge | → Constraint Prompting (Step 2) |
| 3 | `NEEDS_INTENT` | No intent file in `specification/INTENT.md` OR intent file is empty/placeholder | → Intent Authoring (Step 3) |
| 4 | `NO_FEATURES` | Intent exists but `features/active/` is empty | → Feature Creation (Step 4) |
| 5 | `STUCK` | Any feature with same δ (failing check count) for 3+ consecutive iterations (read from `events.jsonl`) | → Stuck Recovery (Step 7) |
| 6 | `ALL_BLOCKED` | All active features blocked (spawn dependency unresolved OR human review pending with no actionable edge) | → Blocked Recovery (Step 8) |
| 7 | `IN_PROGRESS` | Active features with unconverged edges | → Feature/Edge Selection (Step 5) |
| 8 | `ALL_CONVERGED` | All active features fully converged (all edges in profile satisfied) | → Release/Gaps (Step 6) |

Display the detected state to the user:

```
State: IN_PROGRESS
  3 features active, 1 converged, 0 blocked
  Next: REQ-F-AUTH-001 on code↔unit_tests (iteration 4)
```

### Step 1: Progressive Init (UNINITIALISED)

Run a 5-question flow, then delegate to `/gen-init`:

1. **Project name**: Auto-detect from directory name, `package.json`, `pyproject.toml`, `build.sbt`, or `Cargo.toml`. Ask to confirm.
2. **Project kind**: Ask — application / library / service / data-pipeline
3. **Language**: Auto-detect from existing files (`.py` → Python, `.ts`/`.js` → TypeScript, `.scala` → Scala, `.rs` → Rust, `.go` → Go, `.java` → Java). Ask to confirm.
4. **Test runner**: Auto-detect from config files (`pytest.ini`/`pyproject.toml[tool.pytest]` → pytest, `jest.config.*` → jest, `build.sbt` → sbt test). Ask to confirm.
5. **Intent description**: Ask — "In one sentence, what are you building?"

Map project kind to default profile:
- application → `standard`
- library → `full`
- service → `standard`
- data-pipeline → `standard`

Delegate to `/gen-init` with detected values. Write intent description to `specification/INTENT.md`.

**Constraint dimensions are NOT prompted here** — they are deferred until the `requirements→design` edge (REQ-UX-002 Progressive Disclosure).

### Step 2: Deferred Constraint Prompting (NEEDS_CONSTRAINTS)

When a feature reaches the `requirements→design` edge and mandatory constraint dimensions are unresolved:

Prompt for each unresolved mandatory dimension:
- **ecosystem_compatibility**: language, version, runtime, frameworks (pre-populate from init detection)
- **deployment_target**: platform, cloud_provider, environment_tiers
- **security_model**: authentication, authorisation, data_protection
- **build_system**: tool, module_structure, ci_integration

Mention advisory dimensions but do not require them:
> "Advisory dimensions (data_governance, performance_envelope, observability, error_handling) can be filled in now or deferred. Press Enter to skip."

Write resolved values to `.ai-workspace/{impl}/context/project_constraints.yml`.

Then proceed to Step 5 (Feature/Edge Selection) to continue the iteration.

### Step 3: Intent Authoring (NEEDS_INTENT)

Prompt the user:
> "Describe what you want to build (the intent). This will become the root of your feature vectors."

Write the response to `specification/INTENT.md` using the standard intent template. Emit `project_initialized` event if not already emitted.

Then re-run state detection (will transition to NO_FEATURES).

### Step 4: Feature Creation (NO_FEATURES)

Inform the user:
> "Intent captured. Let's create your first feature vector."

Delegate to `/gen-spawn --type feature`. If user provides `--profile`, use it; otherwise use the default profile from init.

Then re-run state detection (will transition to IN_PROGRESS).

### Step 5: Feature/Edge Selection (IN_PROGRESS)

#### 5a: Feature Selection Algorithm

If `--feature` is provided, use it. Otherwise, select automatically:

**Priority tiers** (first match wins within each tier):

1. **Time-boxed spawns approaching expiry**: Features where `time_box.enabled: true` AND remaining time < 25% of budget. Sorted by urgency (least time remaining first).
2. **Closest-to-complete**: Features with the fewest unconverged edges remaining. Reduces WIP.
3. **Feature priority**: From feature vector `priority` field (critical > high > medium > low).
4. **Most recently touched**: From last event timestamp for the feature in `events.jsonl`.

Display selection reasoning:
```
Feature: REQ-F-AUTH-001 "User authentication"
  Selected: closest-to-complete (1 edge remaining)
```

#### 5b: Edge Determination Algorithm

If `--edge` is provided, use it. Otherwise, determine automatically:

1. Read the active profile's graph configuration (which edges are included/skipped)
2. Read the feature's trajectory from its `.yml` file
3. Walk edges in topological order (from `graph_topology.yml` transitions)
4. Skip edges already converged
5. Skip edges not included in the active profile
6. Return the first unconverged, non-skipped edge

For co-evolution edges (`code↔unit_tests`), present both sides as a single unit.

Display determination:
```
Edge: code↔unit_tests (TDD co-evolution)
  Skipped: intent→requirements (converged), requirements→design (converged)
  Profile: standard (includes this edge)
```

#### 5b.5: Candidate Asset Detection (Asset Injection)

Before delegating to iterate, scan for an existing document that could serve as the candidate for the **target** asset type of the current edge. If found, inject it — do not construct from scratch.

This step is **agent-executed, not user-prompted**. The agent reads the filesystem, finds the document, and passes it as `--asset` to the engine call. Only surface to the user if genuinely ambiguous (multiple candidates, or conflicting signals).

**Scan paths by target asset type** (check in order, first match wins):

| Target asset | Conventional paths to scan |
|---|---|
| `requirements` | `REQUIREMENTS.md`, `requirements.md`, `docs/requirements.md`, `specification/requirements/*.md` |
| `design` | `DESIGN.md`, `ARCHITECTURE.md`, `docs/design.md`, `docs/architecture.md` |
| `feature_decomposition` | `FEATURES.md`, `specification/features/FEATURE_VECTORS.md` |
| `uat_tests` | `UAT.md`, `tests/uat/*.feature`, `spec/*.feature` |
| `intent` | `INTENT.md`, `specification/INTENT.md`, `docs/intent.md` |
| `code`, `unit_tests` | (skip — directory assets, not single-file candidates) |

**Auto-inject behaviour** (no dialog):

1. Read the candidate file.
2. Run the engine in deterministic-only mode to establish the starting delta:
   ```bash
   PYTHONPATH=.genesis python -m genesis evaluate \
     --edge "{edge}" \
     --asset "{file}" \
     --feature "{feature_id}" \
     --deterministic-only
   ```
3. Report result:
   ```
   Found: REQUIREMENTS.md → evaluating against {edge} checklist
   F_D result: delta={n}, {passed}/{total} checks pass
   ```
4. If **converged** (delta=0):
   - Mark edge as converged in feature vector (`produced_asset_ref: {file}`).
   - Emit `edge_converged` event to `events.jsonl`.
   - Display: `✓ {file} satisfies all F_D checks — {edge} converged. Proceeding to next edge.`
   - Re-run Step 5b for the next edge.
5. If **not converged** (delta>0):
   - Show the failing checks briefly.
   - Proceed to Step 5c with `--asset {file}` — the document becomes the iteration 1 candidate.
   - The full iterate loop (F_D gate → F_P construction via MCP if needed → F_D re-evaluate) runs from there.

**Ambiguity — ask the user only when**:
- Multiple candidates found for the same asset type (e.g., both `REQUIREMENTS.md` and `docs/requirements.md` exist)
- The candidate file is very large (>2000 lines) or appears to be a different format than expected
- `--asset` was explicitly passed AND a different candidate was auto-detected (conflict)

**If no candidate found**: Skip this step, proceed to Step 5c. The iterate agent constructs the asset from scratch.

#### 5c: Delegate to Iterate

Delegate to `/gen-iterate --edge "{source}→{target}" --feature "{feature_id}"`.

Pass `--asset {file}` if an existing document was selected in Step 5b.5.

### Step 6: Release/Gaps (ALL_CONVERGED)

All features are converged. Suggest next actions:

```
All features converged! 🎉

Recommended actions:
  1. /gen-gaps           — Check for traceability gaps before release
  2. /gen-release        — Create a versioned release
  3. /gen-spawn --type feature  — Start a new feature
```

If `--auto` is set, delegate to `/gen-gaps` first, then `/gen-release`.

### Step 7: Stuck Recovery (STUCK)

Surface stuck features:

```
Stuck features detected:
  REQ-F-AUTH-001 on code↔unit_tests — δ=3 unchanged for 4 iterations
    Failing checks: test_coverage_minimum, all_req_keys_have_tests

Recommended actions:
  1. Spawn a discovery vector to investigate the root cause
  2. Request human review (/gen-review)
  3. Override and force-iterate (/gen-iterate --force)
```

If `--auto` is set, pause and ask the user to choose.

### Step 8: Blocked Recovery (ALL_BLOCKED)

Surface blocked features with reasons:

```
All features blocked:
  REQ-F-AUTH-001 — blocked by spawn dependency (REQ-F-DB-001 not converged)
  REQ-F-API-001  — human review pending on requirements edge

Recommended actions:
  1. Work on the blocking feature: /gen-start --feature "REQ-F-DB-001"
  2. Complete pending reviews: /gen-review --feature "REQ-F-API-001"
```

### Step 9: Auto-Mode Loop

When `--auto` is provided, loop:

```
while state == IN_PROGRESS:

    # ── dispatch_monitor pass (inline homeostatic loop) ────────────────
    # Before every feature/edge selection, scan events.jsonl for unhandled
    # intent_raised events. Any intent with no matching edge_started is
    # dispatched via IntentObserver → EDGE_RUNNER before manual work resumes.
    # This is the dispatch_monitor: a scan on every auto-loop iteration.
    unhandled = get_pending_dispatches(workspace_root)
    if unhandled:
        print(f"dispatch_monitor: {len(unhandled)} unhandled intent(s) — dispatching")
        for target in unhandled:
            run_edge(target)                    # EDGE_RUNNER: F_D → F_P → F_H
            if target.requires_fh:
                # F_H gate: emit intent_raised{signal_source=human_gate_required}
                # Pause auto-mode — human must resolve before loop continues
                print(f"F_H gate reached for {target.feature_id}:{target.edge}")
                print("dispatch_monitor: pausing auto-mode — human gate pending")
                break
        re-detect state
        continue

    feature = select_feature()
    edge = determine_edge(feature)

    # Pause at human gates
    if edge.human_required:
        print("Human gate: {edge} requires human review. Pausing auto-mode.")
        delegate to /gen-review
        break

    # Pause at spawn decisions
    if iterate_result.recommends_spawn:
        print("Spawn recommended: {reason}. Pausing auto-mode.")
        break

    # Pause if stuck
    if iterate_result.delta_unchanged and iteration_count >= 3:
        print("Stuck: δ unchanged for {n} iterations. Pausing auto-mode.")
        break

    # Pause if time-box expired
    if feature.time_box_expired:
        print("Time-box expired for {feature}. Pausing auto-mode.")
        break

    delegate to /gen-iterate --edge "{edge}" --feature "{feature}"
    re-detect state
```

**dispatch_monitor contract** (for Step 9 implementors):

```python
# Inline dispatch_monitor — the homeostatic heartbeat inside --auto
from genesis.intent_observer import get_pending_dispatches
from genesis.edge_runner import run_edge

workspace_root = Path(".ai-workspace")
pending = get_pending_dispatches(workspace_root)
for target in pending:
    result = run_edge(target, workspace_root, events_path)
    if result.status == "fh_required":
        # F_H gate fires — pause, surface to human
        break
```

**F_H gate as intent_raised** (ADR-S-032 §Graduated Autonomy):
When EDGE_RUNNER reaches an F_H gate, it emits `intent_raised` with
`signal_source: human_gate_required` and `affected_features: [feature_id]`.
Auto-mode pauses. The human resolves (approve/reject via `/gen-review` or
`/gen-consensus-open`). On next `/gen-start --auto`, the dispatch_monitor
detects the resolved state and continues traversal from the next edge.

This mechanism makes F_H gates from CONSENSUS documents autonomous triggers:
a CONSENSUS that reaches quorum emits an event → dispatch_monitor sees it →
routes next edge automatically. F_H is still human-controlled; the routing
after F_H resolution is automatic.

### Step 10: Recovery and Self-Healing (REQ-UX-005)

On every invocation, before state detection, run a quick health check:

| Issue | Detection | Recovery |
|-------|-----------|----------|
| Corrupted event log | Malformed JSON lines in `events.jsonl` | Offer: "Event log has N corrupted lines. Truncate at last valid line?" |
| Missing feature vectors | Event log references feature IDs with no `.yml` file | Offer: "Feature {id} referenced in events but no vector file. Regenerate from events?" |
| Orphaned spawns | Child vectors with `parent.feature` pointing to non-existent parent | Offer: "Spawn {id} has no parent. Link to feature or archive?" |
| Stuck features | δ unchanged 3+ iterations | Detected in state machine (Step 7) |
| Unresolved constraints | Mandatory dimensions empty when feature is at design edge | Detected in state machine (Step 2) |

Recovery is always non-destructive — never silently delete user data. Always ask before modifying.

## Output Format

Per-state output examples:

**UNINITIALISED**:
```
Project not initialized. Starting progressive setup...
  Project: my-app (detected from directory)
  Language: Python 3.12 (detected from .py files)
  Test runner: pytest (detected from pyproject.toml)
  Profile: standard (default for application)
```

**IN_PROGRESS**:
```
State: IN_PROGRESS (3 active, 1 converged)
Feature: REQ-F-AUTH-001 "User authentication" (closest-to-complete)
Edge: code↔unit_tests (iteration 4, δ=2)
Delegating to /gen-iterate...
```

**ALL_CONVERGED**:
```
State: ALL_CONVERGED
All 4 features converged across 20 edges.
Run /gen-gaps to check traceability, then /gen-release.
```

## Event Emission

Start does **not** emit its own events. It delegates to underlying commands which emit their own events. This avoids double-counting in the event log.

The state detection algorithm is a **pure read** — it observes workspace state without modifying it.
