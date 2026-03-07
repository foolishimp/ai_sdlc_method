# GAP: Claude Spec → Design → Code Alignment

**Author**: codex
**Date**: 2026-03-07T16:52:15+1100
**Addresses**: Current shared spec (`ADR-S-011/012/015/016/019/020/021/022`), current Claude design ADRs, and active `imp_claude` runtime code
**For**: all

## Summary
Claude has moved meaningfully toward the newer spec, especially on the functor boundary and event-sourced projections.

The main problem is no longer isolated bugs. The accepted spec, the Claude design ADRs, and the active runtime still describe different systems in a few core places: event contract, transaction semantics, lineage/context, instance-graph lifecycle, and the actual F_P execution path.

## Cross-Layer Findings

### 1. High: the live engine still uses a legacy flat event log, while the spec and design now assume OpenLineage as the only contract
The shared spec requires every event in `.ai-workspace/events/events.jsonl` to conform to OpenLineage RunEvent with universal `instance_id`, `actor`, `causation_id`, and `correlation_id` fields (`specification/adrs/ADR-S-011-openlineage-unified-metadata-standard.md:30-31`, `specification/adrs/ADR-S-012-event-stream-as-formal-model-medium.md:82-140`). Claude design ADR-021 then says both traverse modes emit OL-format events (`imp_claude/design/adrs/ADR-021-dual-mode-traverse.md:144-169`).

The active runtime does not do that. `engine.py` emits through `fd_emit.make_event()` / `fd_emit.emit_event()` (`imp_claude/code/genesis/engine.py:102-112`, `imp_claude/code/genesis/engine.py:271-286`), and that writer persists flat records with only `event_type`, `timestamp`, `project`, plus ad hoc payload fields (`imp_claude/code/genesis/fd_emit.py:12-44`, `imp_claude/code/genesis/models.py:153-160`). `ol_event.py` exists, but the runtime path does not use it; it is effectively side-car code plus tests.

That split is already enough to break spec/design alignment. There is a second problem inside the unused OL helper itself: it maps `IterationCompleted` to `COMPLETE` (`imp_claude/code/genesis/ol_event.py:55-58`), while the accepted spec maps non-terminal `iteration_completed` to `OTHER` and reserves `COMPLETE` for terminal convergence events (`specification/adrs/ADR-S-011-openlineage-unified-metadata-standard.md:68-83`). The current test suite reinforces the wrong contract instead of catching it (`imp_claude/tests/test_event_taxonomy.py:26-33`, `imp_claude/tests/test_event_taxonomy.py:333-397`).

### 2. High: ADR-S-015 transaction semantics are not implemented, and current recovery is only heuristic
The shared spec now defines edge traversal as a transaction with START/COMPLETE/FAIL/ABORT boundaries, input manifests, content hashes, previous hashes, and startup recovery by comparing current filesystem state against the START manifest (`specification/adrs/ADR-S-015-unit-of-work-transaction-model.md:27-39`, `specification/adrs/ADR-S-015-unit-of-work-transaction-model.md:50-68`, `specification/adrs/ADR-S-015-unit-of-work-transaction-model.md:103-170`). ADR-S-016 and Claude ADR-024 both assume `StepResult.artifacts` can feed COMPLETE event outputs (`specification/adrs/ADR-S-016-invocation-contract.md:57-87`, `imp_claude/design/adrs/ADR-024-recursive-actor-model.md:172-173`).

The code path is still far short of that. `iterate_edge()` emits `iteration_started` and `iteration_completed`, but without a shared transaction runId, without an input manifest, without output content hashes, and without any population of `StepResult.artifacts` into the emitted event (`imp_claude/code/genesis/engine.py:102-112`, `imp_claude/code/genesis/engine.py:227-274`, `imp_claude/code/genesis/contracts.py:48-99`). The recovery path in `__main__.py` does not inspect open transactions or compare hashes; it only looks for `edge_started` records that lack later completion and emits `iteration_abandoned` heuristically (`imp_claude/code/genesis/__main__.py:130-159`, `imp_claude/code/genesis/workspace_state.py:224-264`).

This means the spec has moved to a commit model, the design talks as if the engine owns that commit model, but the runtime still only has append-only telemetry plus a gap heuristic.

### 3. High: lineage/context is still implemented against the old hierarchy, not the accepted spec or Claude's own lineage ADR
The current core spec and ADR-S-022 define the canonical merge order as `methodology → org → policy → domain → prior → project` (`specification/adrs/ADR-S-022-project-lineage-and-context-inheritance.md:24-35`, `specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md:824-854`). Claude ADR-027 matches that model and makes `context_sources`, live/static lineage resolution, `.ai-workspace/context/{scope}/`, `context_manifest.yml`, and `context_hash` load-bearing (`imp_claude/design/adrs/ADR-027-project-lineage-and-context-inheritance.md:86-141`, `imp_claude/design/adrs/ADR-027-project-lineage-and-context-inheritance.md:153-176`, `imp_claude/design/adrs/ADR-027-project-lineage-and-context-inheritance.md:205-211`).

The active code still implements the older four-level hierarchy. `config_loader.py` documents `global → organisation → team → project` (`imp_claude/code/genesis/config_loader.py:27-31`, `imp_claude/code/genesis/config_loader.py:59-83`), and the test suite asserts that three-level/old-style merge shape (`imp_claude/tests/test_config_loader.py:154-183`). The installer does not resolve `context_sources`, does not build a lineage manifest, and emits only a minimal `project_initialized` event with no provenance payload (`imp_claude/code/installers/gen-setup.py:26-39`, `imp_claude/code/installers/gen-setup.py:509-527`). `context_hash` exists only as a helper function, not as a runtime event field (`imp_claude/code/genesis/workspace_state.py:68-72`).

So the spec, the design ADR, and the runtime are still describing different context systems.

### 4. Medium: instance-graph lifecycle still relies on obsolete terminal and spawn semantics
ADR-S-021 now defines instance state from `feature_spawned`, `edge_started`, `iteration_completed`, and `edge_converged`, with feature completion derived when `converged_edges` covers the active profile; it no longer depends on a separate terminal event (`specification/adrs/ADR-S-021-project-instance-graph.md:33-41`). Claude ADR-022 still uses `FEATURE_CONVERGED` as the archival event (`imp_claude/design/adrs/ADR-022-instance-graph-from-events.md:39-48`, `imp_claude/design/adrs/ADR-022-instance-graph-from-events.md:70-77`).

The runtime projection has not caught up. `project_instance_graph()` archives only on explicit `feature_converged` and never derives terminal state from profile coverage (`imp_claude/code/genesis/workspace_state.py:1018-1026`, `imp_claude/code/genesis/workspace_state.py:1066-1091`). Spawn handling is also mismatched: the spawn path emits `spawn_created` with `parent_feature` and `child_feature` (`imp_claude/code/genesis/fd_spawn.py:245-266`), but the instance-graph projection creates nodes from `feature` or `feature_spawned` semantics, not from `child_feature`. In practice that means a newly spawned child does not appear in the instance graph until some later edge event happens to create a node implicitly.

The tests encode the older terminal model rather than the current spec projection rule (`imp_claude/tests/test_instance_graph.py:13-43`).

### 5. Medium: the recursive actor design is only partially implemented; current engine-mode F_P is still mostly a stub
Claude ADR-024 and ADR-021 together say engine-affinity F_P work is an MCP actor invocation with tool access, and that the engine supervises that actor with deterministic F_D re-checks (`imp_claude/design/adrs/ADR-024-recursive-actor-model.md:26-37`, `imp_claude/design/adrs/ADR-024-recursive-actor-model.md:38-65`, `imp_claude/design/adrs/ADR-021-dual-mode-traverse.md:69-90`).

The current code has the new interfaces, but not the full execution path. `iterate_edge()` does call `FpFunctor().invoke(...)` when `construct=True` (`imp_claude/code/genesis/engine.py:114-125`), but `_mcp_invoke()` in `fp_functor.py` is still an MVP stub. It does not issue an MCP tool call; it only checks for a pre-written fold-back file under `.ai-workspace/agents/fp_result_<run_id>.json` and otherwise returns a skipped result (`imp_claude/code/genesis/fp_functor.py:53-74`, `imp_claude/code/genesis/fp_functor.py:122-143`).

So the design has moved to “recursive actor via MCP,” but the runtime currently behaves as “F_D-only unless some external actor has already injected a fold-back file.” The tests already encode that fallback/skipped behavior as normal (`imp_claude/tests/test_functor_construct.py:59-79`).

### 6. Medium: most of the accepted spec event taxonomy exists only as constructors/tests, not as runtime behavior
The accepted spec requires more than iteration lifecycle events. It also requires convergence, context-arrival, authorization, and compensation events (`specification/adrs/ADR-S-012-event-stream-as-formal-model-medium.md:82-149`). Claude has constructors for these in `ol_event.py` (`imp_claude/code/genesis/ol_event.py:242-343`) and tests that validate those constructors (`imp_claude/tests/test_event_taxonomy.py:67-315`).

But the active engine and CLI do not emit them. Search usage shows these constructors are not wired into `engine.py`, `__main__.py`, or the normal engine traversal path. The role-authority gate also emits a flat `convergence_escalated` event rather than spec-level `TransitionAuthorized` / `TransitionDenied` events (`imp_claude/code/genesis/role_authority.py:146-174`, `imp_claude/code/genesis/role_authority.py:181-229`). Compensation exists as helper constructors and tests, not as runtime saga handling.

This is an important distinction: the taxonomy is present in library code, but it is not yet the runtime's actual emitted behavior.

## Validation Notes
I ran a focused Claude test slice while preparing this review:

- `python -m pytest imp_claude/tests/test_event_taxonomy.py -q`
- `python -m pytest imp_claude/tests/test_instance_graph.py -q`
- `python -m pytest imp_claude/tests/test_config_loader.py -q`
- `python -m pytest imp_claude/tests/test_workspace_gradient.py -q`

All four passed.

That does not contradict the gaps above. It confirms that the current tests mostly validate the current Claude contract, including several pre-spec or transitional assumptions: flat event records, old context hierarchy, explicit `feature_converged`, and helper-level OL constructors that are not yet the runtime path.

## Recommended Action
1. Choose one event contract for the live engine. If OL is the accepted contract, `engine.py` must stop emitting legacy `fd_emit` records and the OL helper must be corrected to match ADR-S-011 semantics.
2. Implement ADR-S-015 transaction linkage before adding more projections: START/COMPLETE runId pairing, input manifests, output hashes, and recovery from open transactions using the manifest, not `edge_started` heuristics.
3. Rebase Claude context loading and installation on ADR-S-022 / ADR-027: resolve `context_sources`, build the lineage directories and manifest, and emit `context_hash` on iteration events.
4. Align instance-graph lifecycle on the accepted spec: child node creation must be driven by actual spawn events, and terminal feature state should be derived from `edge_converged` against the active profile rather than a separate `feature_converged` event.
5. Either finish the actual MCP actor invocation in `fp_functor.py` or narrow ADR-024/ADR-021 claims so the design reflects the runtime honestly.
