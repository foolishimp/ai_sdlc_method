# REVIEW: Genesis Product State and imp_claude Alignment

**Author**: codex
**Date**: 2026-03-09T12:51:11Z
**Addresses**: Genesis methodology overview, current product state of `imp_claude`, alignment between spec and Claude tenant design
**For**: all

## Summary

Genesis is coherently defined at spec level as an event-sourced asset-graph methodology built from four primitives: Graph, `iterate()`, Evaluators, and Spec+Context. `imp_claude` is currently the largest and most mature product instantiation of that model in this repository: it has a real Python engine, a real plugin surface, a large deterministic test corpus, and clear product UX around `/gen-start` and `/gen-status`.

The main issue is not conceptual incoherence. The main issue is drift between three layers that are all individually strong: the canonical spec, the `imp_claude` design corpus, and the currently shipped product surface. The product is ahead of some design docs, while some newer design work is ahead of the shipped interface.

## What Genesis Is

At spec level, Genesis is not a prompt library or a linear SDLC checklist. It is:

- a typed, zoomable asset graph
- a single universal operation: `iterate(asset, context, evaluators) -> Event+`
- three evaluator families: deterministic, probabilistic/agent, and human
- an append-only event stream as substrate, with feature vectors as trajectories through the graph

The strongest stable ideas in the current spec are:

- software delivery is modeled as graph traversal, not stage handoff
- convergence is evaluator-defined, not artifact-exists-defined
- state is projected from events, not treated as mutable truth
- telemetry and homeostasis are constitutive, not optional add-ons
- tenants bind the same spec differently without changing the spec itself

That is a coherent methodology core. The repo is not wandering conceptually anymore; the core model is visible and fairly stable.

## Current Product: imp_claude

`imp_claude` is a real product, not just a design set.

Current observable surface:

- plugin version: `2.9.0`
- registered commands: `13`
- registered agents: `4`
- command docs present on disk: `19`
- edge parameterisations: `16`
- projection profiles: `7`

The product currently includes these major capability groups:

- a Python engine in `imp_claude/code/genesis/` with deterministic evaluation, routing, dispatch, event emission, workspace state, traceability, and sensory utilities
- a Claude plugin surface with `/gen-start`, `/gen-init`, `/gen-iterate`, `/gen-status`, `/gen-spawn`, `/gen-review`, `/gen-spec-review`, `/gen-escalate`, `/gen-zoom`, `/gen-trace`, `/gen-gaps`, `/gen-checkpoint`, and `/gen-release`
- graph/package configuration via `graph_topology.yml`, `edge_params/*.yml`, and profile YAMLs
- event-sourced workspace projections under `.ai-workspace/`
- feature vector tracking and REQ-key traceability
- observer-style product features around gaps, escalation, self-observation, and spec evolution
- a deterministic quorum core for `CONSENSUS` in `consensus_engine.py`

In plain product terms: Genesis for Claude Code is already past “framework sketch” and into “usable methodology product with a serious internal test harness.”

## Current State of the Product

### What looks healthy

- The deterministic and non-E2E test surface is strong.
- The consensus core is real code with passing targeted tests.
- The plugin package, config package, and engine package are all materially populated.
- The user-facing product story is understandable: install, `/gen-start`, iterate through the graph, review, trace, release.

Evidence from this review:

- `PYTHONPATH=/Users/jim/src/apps/ai_sdlc_method python -m pytest -q imp_claude/tests/test_consensus_engine.py imp_claude/tests/test_uc_consensus_001.py`
  Result: `71 passed, 7 skipped`
- `PYTHONPATH=/Users/jim/src/apps/ai_sdlc_method python -m pytest -q imp_claude/tests --ignore=imp_claude/tests/e2e`
  Result: `1873 passed, 7 skipped, 3 xfailed`

That is a strong product baseline.

### What is not healthy enough yet

- The test harness is not self-contained. A plain `python -m pytest imp_claude/tests` fails collection because tests import `imp_claude.*` directly but the package root is not importable by default.
- The live E2E lane is still an external-runtime certification problem, not a routine green build. The unfiltered suite entered a long-running `claude -p` subprocess during this review.
- Some documentation and design artifacts are stale relative to current code.

This means the product is strong in core logic, but weaker in packaging, invocation contract, and “what exactly is shipped vs designed vs proposed.”

## Alignment: Spec to imp_claude Design

### Strong alignment

| Spec concern | imp_claude design/product status | Assessment |
|---|---|---|
| Four-primitives methodology | Explicit in top-level design and user guide | Strong |
| Asset graph as topology/config | Implemented via graph/package YAMLs | Strong |
| Universal iterate engine | Real engine and CLI exist | Strong |
| Evaluator composition per edge | Real edge configs and engine dispatch exist | Strong |
| Event sourcing as substrate | Central design and implementation invariant | Strong |
| Feature vectors / REQ traceability | Explicit in design and tests | Strong |
| Projection profiles | Present in config and user docs | Strong |
| Homeostatic gap/intents loop | Present in design and command surface | Strong |

### Partial alignment

| Spec/design area | Current state | Assessment |
|---|---|---|
| Expanded graph shape with feature/module/basis decomposition | Present in spec and design, but end-user docs still present a simplified 10-asset graph | Partial |
| Supervisory actor / saga framing from newer ADRs | Present in newer consensus design, not yet consistently repriced across older design docs | Partial |
| Spec-evolution and intent-vector refinements | Reflected in parts of design/test surface, but not cleanly consolidated in top-level design docs | Partial |
| `CONSENSUS` as a tenant feature | Deterministic core exists, design is proposed, user surface is not fully shipped | Partial |

### Misalignment / drift

1. **Product surface vs command docs**
   The command directory contains more artifacts than the registered plugin surface. Consensus-related command docs exist on disk, but `plugin.json` still exposes only the older 13-command set. That means some design/product artifacts are discoverable in-repo without actually being part of the shipped interface.

2. **Design docs vs current code**
   `ENGINE_DESIGN_GAP.md` still says the engine lacks `__main__.py` and a CLI entry point, but `imp_claude/code/genesis/__main__.py` exists and is part of the current implementation. That makes `ENGINE_DESIGN_GAP.md` a stale analysis document, not an accurate current-state description.

3. **Docs version drift**
   `plugin.json` reports `2.9.0`, while the user-facing guide still identifies itself as `2.8.0`. That is not a logic bug, but it is a product-state bug: it reduces confidence that the docs describe the exact shipped build.

4. **Spec/package invocation contract**
   The spec and design say Genesis is a valid tenant product; the current test harness still depends on caller-supplied `PYTHONPATH` for many tests. That is an implementation/distribution gap, not a methodology gap.

## What the Product Actually Is Today

The honest current description is:

- Genesis is a strong formal methodology with a now-recognisable stable core.
- `imp_claude` is the most mature implementation tenant in the repo.
- The core product is already usable for graph-driven software work inside Claude Code.
- The deterministic product is much more mature than the live headless-Claude certification story.
- `CONSENSUS` exists in three different maturity levels at once:
  - deterministic quorum core: implemented
  - design/saga model: proposed and fairly coherent
  - shipped user-facing workflow: not yet fully integrated into the public plugin surface

That last point is the clearest example of the broader pattern: the product is no longer early-stage, but it is now complex enough that “implemented”, “designed”, and “advertised” need stricter separation.

## Main Risks

- **Packaging risk**: if the product cannot be invoked cleanly without repo-specific path assumptions, assurance and adoption both suffer.
- **Documentation risk**: stale design analysis and version drift create false negatives and false positives during review.
- **Surface-area risk**: extra command docs on disk without registration make it harder to know what the supported product actually is.
- **E2E certification risk**: the live Claude subprocess lane is expensive and operationally noisy, so it should not be conflated with deterministic product correctness.

## Recommended Action

1. Declare a product truth source for `imp_claude`: shipped surface = `plugin.json` + installed command set + importable engine package.
2. Reprice stale design docs. In particular, treat `ENGINE_DESIGN_GAP.md` as superseded analysis unless it is updated to current code reality.
3. Split quality reporting into two lanes:
   - deterministic/core certification
   - live-Claude E2E certification
4. Decide whether consensus commands are part of the shipped product now or still tenant-local design work. The repo should not imply both.
5. Tighten the packaging/import contract so `imp_claude` tests and engine invocation do not depend on ad hoc `PYTHONPATH` correction.

The important conclusion is positive: Genesis now has enough substance that the main review task is no longer “is there a real product here?” There is. The main task is bringing product truth, design truth, and spec truth back into tighter alignment.
