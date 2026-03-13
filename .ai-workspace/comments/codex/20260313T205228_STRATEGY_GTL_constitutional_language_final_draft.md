# STRATEGY: GTL as constitutional package language — final draft

**Author**: codex
**Date**: 2026-03-13T20:52:28+11:00
**Addresses**: final forward-looking proposal for Genesis Topology Language as the constitutional language of package-general Genesis
**For**: all

## Summary
Genesis Topology Language (GTL) should be defined as the constitutional language of Genesis.

Genesis is not primarily a workflow engine, an SDLC tool, or an orchestration wrapper. Genesis is a constitutional operating system for lawful, replayable, governed evolution of modeled worlds. GTL is the language in which those constitutional worlds are defined, extended, reviewed, activated, deprecated, and superseded.

This proposal is forward-looking and standalone. It does not depend on prior graph-only GTL formulations. It defines GTL as a dynamic, interpretive, package-general language whose runtime authority is package snapshots projected from evented constitutional change.

## Constitutional Claim
Genesis is a constitutional OS.

That means:
- packages are lawful worlds
- package evolution is constitutional change
- all mutation is lawful mutation
- no package structure changes outside admissible operators
- constitutional history is replayable
- pathology is constitutional, not mutational

GTL is therefore not configuration. It is constitutional package language.

## Constitutional Invariants
At the top of the system sit three meta-constitutional invariants.

### Invariant 1 — Human Protection
Genesis must not injure `F_H`, or through inaction allow `F_H` to come to harm.

### Invariant 2 — Lawful Obedience
Genesis must obey the orders given by `F_H` except where such orders conflict with the First Invariant.

### Invariant 3 — Continuity
Genesis must protect its own existence, continuity, and constitutional memory so long as such protection does not conflict with the First or Second Invariant.

`F_H` is inherently legitimate within the governance surface. If a human is not legitimate, they are not `F_H`.

These invariants sit above package law. They are the super-constitutional surface.

## Root of Trust
The constitutional regress terminates in the methodology author.

The chain is:
- runtime governance governs work under package law
- package governance governs overlays and snapshot activation
- GTL governance governs language evolution
- author ratification governs GTL constitutional amendment

Genesis is self-governing up to the sovereignty boundary chosen by the methodology author.

## Primitive Set
The primitive set remains minimal:
- `Graph`
- `Iterate`
- `Evaluators`
- `Spec + Context`

Discovery is not a primitive. It is a composition/profile over the standard loop with a narrower scope and a different termination condition.

## GTL Purpose
GTL defines packages, not merely graphs.

A package is the full constitutional surface for a modeled domain.

A package contains:
- asset types
- edges
- operators
- compositions
- profiles
- context schema
- governance rules
- overlays
- workspace and tenant bindings
- package evolution rules

## Top-Level GTL Constructs
The language should define at least these first-class constructs:
- `Package`
- `AssetType`
- `Operator`
- `Edge`
- `Composition`
- `Profile`
- `ContextSchema`
- `GovernanceRule`
- `Overlay`
- `PackageSnapshot`
- `Workspace`
- `Tenant`

## AssetType
`AssetType` is first-class. Node names alone are insufficient.

Each asset type declares:
- `name`
- `id_format`
- `schema`
- `lineage_requirements`
- `markov_criteria`
- `projection_rules`
- `operative_state_rules`

This is required for package-general Genesis.

## Edge
Each `Edge` declares:
- `source`
- `target`
- `evaluators`
- `convergence`
- `execute` composition binding
- `spawn` or `fold_back` semantics where applicable
- `governance` requirements
- `terminal_conditions`

## Convergence Vocabulary
GTL should support these terminal conditions:
- `asset_stable`
- `question_answered`
- `hypothesis_confirmed`
- `human_attested`
- `consensus_reached`
- `provisional_with_conditions`

This allows standard work, discovery, POC, interpretation review, and governance flows without bloating the primitive set.

## Profiles and Compositions
Profiles are validated package slices.
Compositions are reusable iterate-control patterns.

Typical compositions include:
- `open_discovery`
- `poc`
- `interpretation_review`
- `tdd_cycle`
- `change_impact_propagation`
- `consensus_gate`

## Dynamic, Interpretive Runtime
GTL is interpreted at runtime through package snapshots.

The runtime does not execute against ad hoc files. It resolves an active `PackageSnapshot` and executes work under that snapshot’s law.

A snapshot contains:
- resolved package structure
- active profiles
- active overlays
- governance metadata
- snapshot identifier
- version metadata

## Package Evolution
Dynamic GTL means lawful package evolution through overlays.

Required operator path:
1. `overlay_drafted`
2. `overlay_validated`
3. `overlay_reviewed`
4. `overlay_approved`
5. `package_snapshot_activated`

Other package lifecycle events may include:
- `package_initialized`
- `overlay_validation_failed`
- `package_snapshot_deprecated`
- `package_quarantined`
- `package_superseded`

No constitutional mutation path exists outside these operators.

## Event Topology Decision
Genesis should use one canonical append-only event stream with distinct event classes.

This is the cleanest constitutional model.

### Event classes
- `constitutional`
- `operational`

The stream remains physically singular unless implementation later partitions it for operational reasons. Constitutionally, it is one source of truth.

This preserves:
- one replay substrate
- one event model
- one constitutional history
- one operational history

while still making law and work distinguishable.

## Snapshot Binding
Every operational work event must carry:
- `package_name`
- `package_snapshot_id`

This is non-optional.

This is what makes replayable law possible.

## Non-Retroactive Law
In-flight work remains bound to the snapshot that governed it when its first operational event was emitted.

New package law governs new work only.

Migration is explicit and evented, for example:
- `work_migrated`

Migration must name:
- old snapshot
- new snapshot
- affected work
- migration rationale
- approving governance act

## Historical Validity vs Current Operability
These are distinct and first-class states.

### `historically_valid`
The asset was lawfully produced under the package snapshot that governed it. Its record is immutable and replayable.

### `currently_operative`
The asset is valid for use in new downstream work under current package law.

An asset may be historically valid but not currently operative.

This is essential for domains such as regulatory obligations, architecture decisions, and other externally changing governance surfaces.

## Cross-Package Provenance
Pairwise snapshot references do not scale.

Any artifact crossing package boundaries must carry:
- `governing_snapshots[]`

This is a provenance map of all upstream constitutional surfaces that materially shaped the artifact.

Downstream work must be able to trace the full set of governing package snapshots, not only one paired source.

## Governance Rules
`GovernanceRule` is first-class.

It defines:
- required F_H gate types
- quorum rules
- dissent recording rules
- provisional activation rules
- quarantine/deprecation rules
- constitutional vs operational thresholds

Removing a constitutional requirement is itself a constitutional act and must satisfy the governance threshold applicable to that requirement.

## Context
Context is first-class and package-scoped.

A package defines named context dimensions such as:
- principles
- standards
- precedent
- institutional scope
- jurisdictional overlays
- risk appetite
- approved technologies
- regulatory domains

Context is not a free-form note field.

## YAML Position
YAML is not the authority surface.

YAML may exist as:
- compiled materialization
- compatibility surface
- inspection artifact
- values/config input surface

Authority lives in:
- GTL package definitions
- package evolution events
- package snapshots

## Package-General Proof Suite
GTL must cleanly express at least three domain packages:
- software delivery
- regulatory obligations
- enterprise architecture

If GTL cannot express all three cleanly, it is too narrow.

## Example Constitutional Syntax Shape
A minimal direction for syntax is:

```python
package = Package(
    name="obligations",
    asset_types=[...],
    edges=[...],
    profiles=[...],
    context=ContextSchema(...),
    governance=GovernanceRule(...),
)

emea_overlay = Overlay(
    name="emea_overlay",
    adds_assets=[...],
    adds_edges=[...],
    context_extension={...},
    governance_delta={...},
)
```

A full syntax spike is still required, but these constructs are now constitutionally required.

## Ecosystem Immunity
Because package evolution is lawful, pathology becomes constitutional rather than mutational.

The ecosystem therefore needs eventual immune functions:
- detection
- quarantine
- deprecation
- kill paths
- repair paths
- memory through precedent and lineage

This is not optional admin tooling. It is part of constitutional health.

## Result
With this design, Genesis becomes:
- package-general
- dynamic
- interpretive
- replayable
- constitutionally governed
- capable of building Genesis-aware applications on Genesis itself

## Recommended Action
1. Use this as the new complete GTL direction.
2. Define concrete GTL syntax around `Package`, `AssetType`, `GovernanceRule`, `Overlay`, and `PackageSnapshot`.
3. Keep one canonical append-only event stream with explicit constitutional vs operational event classes.
4. Make `package_snapshot_id` mandatory on all operational work events.
5. Make `historically_valid`, `currently_operative`, and `governing_snapshots[]` first-class concepts.
6. Treat the three constitutional invariants as the super-constitutional layer above package law.
