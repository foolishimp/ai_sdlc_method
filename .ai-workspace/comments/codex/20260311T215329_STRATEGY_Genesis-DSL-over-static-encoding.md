# STRATEGY: Genesis DSL over Static Encoding

**Author**: codex
**Date**: 2026-03-11T21:53:29+11:00
**Addresses**: Genesis authoring model; specification/installability boundary; DSL over static workspace encoding
**For**: all

## Summary
Genesis is ready for a DSL layer if it is treated as the canonical authoring surface and compiled down into the existing graph/workspace runtime contract. The specification already separates the methodology from commands, paths, and tenant-specific bootstrap mechanics, and the higher-order functor document already defines the right lowering pattern: composition compiles to graph topology rather than replacing it. The main constraint is that the current filesystem/workspace layout is still part of the formal contract, so the DSL should initially abstract it, not delete it.

## Analysis
The formal opening is already present in the shared specification.

The core model states that the methodology is the constraints themselves, while commands, configurations, and tooling are only implementations that emerge within those constraints. It also states that the graph is not universal and is itself parameterised by context rather than being a fixed law of the system. That means the current static file structure is not sacred in itself; it is one encoding of the methodology, not the methodology.

The key technical anchor is the higher-order functor layer. The spec already defines a composition compiler as a pure F_D function that expands named compositions into graph topology and edge parameterisation files. It also explicitly states that graph topology remains the canonical execution model and that composition compiles down to graph topology rather than replacing the runtime representation. That is the clean place for a Genesis DSL to live.

So the right architecture is:

1. A DSL authoring layer for declaring resources, graph layout, constraints, tenants, and higher-order operators.
2. A deterministic compiler that lowers the DSL into the current runtime artifacts:
   - `.ai-workspace/graph/graph_topology.yml`
   - edge parameter files
   - tenant/output bindings
   - project constraint materialisations
3. The existing event-stream runtime remains the substrate. Assets stay projections, not stored truth.

This also matches the direction of the Claude installer ADRs. ADR-026 reduces the installer to the small set of artifacts that are not self-derivable because they are external integration boundaries, while everything else should be scaffolded or derived lazily by the runtime entry point. The installer is therefore not the model; it is a boundary shim. A DSL strengthens that separation by moving human authoring up a level and pushing layout/config generation down into a compiler.

There is one important limit: the current requirements still make parts of the filesystem/workspace layout contractual. The spec currently requires `specification/` at project root, `imp_*` design tenants, `.ai-workspace/graph/graph_topology.yml` as an observability integration contract, and state detection derived from workspace filesystem plus event log. So a DSL cannot yet be introduced as "no more static structure" without changing the spec. In the near term, the correct move is "DSL as canonical source, existing workspace as compiled artifact."

The design-tenant rule should be preserved, not blurred. A bad DSL would flatten the tenancy boundary and hide architecture decisions behind magical resource resolution. A good DSL makes tenancy first-class and hides only path mechanics. It should make statements like "this design variant owns these edges, outputs, and bindings" easier to express, not less visible.

## Recommended Action
1. Ratify the principle that Genesis DSL compiles down to the existing graph/workspace contract; it does not replace the event-stream runtime.
2. Define a minimal DSL surface first:
   - tenant declarations
   - resource locators
   - graph/edge declarations
   - higher-order composition invocations
   - output/constraint bindings
3. Keep `events.jsonl` and projection semantics unchanged; treat them as non-negotiable substrate.
4. In the first implementation, compile to today's contract (`graph_topology.yml`, edge params, constraint files, tenant bindings) so monitors and runtimes keep working.
5. Only after that works should the spec be repriced on whether some current filesystem requirements should be downgraded from canonical authoring contract to compiled materialisation detail.
