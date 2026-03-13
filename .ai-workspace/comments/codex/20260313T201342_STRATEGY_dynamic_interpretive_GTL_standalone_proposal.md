# STRATEGY: Dynamic, interpretive GTL — standalone forward proposal

**Author**: codex
**Date**: 2026-03-13T20:13:42+11:00
**Addresses**: forward-looking Genesis Topology Language proposal for package-general, dynamic, interpretive Genesis
**For**: all

## Summary
Genesis Topology Language should be the canonical language for defining, evolving, and executing Genesis packages. It is not configuration. It is the package language for lawful graph definition, governed package evolution, and replayable runtime interpretation.

GTL should be dynamic and interpretive:
- packages are loaded at runtime
- package changes are evented
- activation is governed
- historical package state is replayable
- work always binds to an explicit package snapshot

## Decision
GTL defines `packages`, not just graphs.

A package contains:
- asset types
- edges
- operators
- compositions
- profiles
- context schema
- governance rules
- workspace and tenant bindings
- package evolution rules

The runtime interprets an active package snapshot. The package snapshot is itself a projection of package-definition events.

## Primitive Model
The primitive set remains minimal:
- `Graph`
- `Iterate`
- `Evaluators`
- `Spec + Context`

Discovery is not a primitive. It is a composition/profile over the standard loop with different termination conditions.

## Core Principle
All package mutation is lawful mutation.

No package structure changes outside:
- admissible operators
- event emission
- evaluator checks
- F_H / consensus gates where required

This prevents dark mutation. Constitutional change remains explicit, attributable, and replayable.

## Top-Level GTL Constructs
- `Package`
- `AssetType`
- `Operator`
- `Edge`
- `Composition`
- `Profile`
- `ContextSchema`
- `GovernanceRule`
- `Workspace`
- `Tenant`
- `Overlay`
- `PackageSnapshot`

## AssetType
Each asset type declares:
- name
- identifier format
- schema
- lineage requirements
- markov criteria
- projection expectations

`nodes: list[str]` is not sufficient.

## Edge
Each edge declares:
- source and target asset types
- evaluator set
- convergence rule
- composition binding
- spawn/fold-back behavior where relevant
- governance requirements
- allowed terminal conditions

## Convergence Vocabulary
GTL should support multiple terminal conditions, including:
- `asset_stable`
- `question_answered`
- `hypothesis_confirmed`
- `human_attested`
- `consensus_reached`
- `provisional_with_conditions`

This allows standard work, discovery, POC, and governance flows without adding new primitives.

## Profiles and Compositions
Profiles are validated package slices.
Compositions are reusable iterate-control patterns.

Examples:
- `open_discovery`
- `poc`
- `tdd_cycle`
- `interpretation_review`
- `change_impact_propagation`
- `consensus_gate`

## Interpretive Runtime
The runtime loads an active `PackageSnapshot`, not static config files.

A snapshot contains:
- full resolved package structure
- active profiles
- active overlays
- package version or snapshot id
- governance metadata

Every runtime event binds to:
- `package_name`
- `package_snapshot_id`

This guarantees exact replay under historical package law.

## Dynamic Package Evolution
Dynamic GTL means package evolution through governed overlays, not arbitrary live mutation.

Required operator path:
1. `overlay_drafted`
2. `overlay_validated`
3. `overlay_reviewed`
4. `overlay_approved`
5. `package_snapshot_activated`

No other mutation path exists.

## Package Events
Package evolution is event-sourced through events such as:
- `package_initialized`
- `overlay_drafted`
- `overlay_validation_failed`
- `overlay_validated`
- `overlay_approved`
- `package_snapshot_activated`
- `package_snapshot_deprecated`
- `package_quarantined`

Package topology is therefore a projection of the event stream, just like all other Genesis state.

## Governance
GTL must support package-level governance rules, including:
- F_H approval requirements
- consensus quorums
- provisional activation with conditions
- dissent capture
- deprecation and quarantine rules

## Context
Context is first-class and package-scoped.

A package defines named context dimensions such as:
- principles
- standards
- precedent
- institutional scope
- regulatory domains
- approved technologies
- risk appetite
- jurisdictional overlays

Context is not a miscellaneous notes field.

## YAML Position
YAML is not the authority surface.
YAML may exist as:
- compiled materialization
- inspection format
- compatibility format
- project values format

Authority lives in GTL package snapshots and package-definition events.

## Execution Model
At runtime:
- resolve active package snapshot
- bind current work to that snapshot
- load context
- execute iterate loop under package law
- emit events
- project resulting state

Old work remains bound to old snapshots. New work uses new snapshots. Replay remains exact.

## Open-World Behavior
GTL must support domain expansion through overlays.
A package can gain:
- new asset types
- new edges
- new context dimensions
- new profiles
- new obligation families
- new governance rules

But only through lawful package evolution.

## What GTL Must Prove
A valid GTL design must cleanly express at least:
- software delivery
- regulatory obligations
- enterprise architecture

If GTL cannot express all three without feeling SDLC-specific, it is too narrow.

## Immune System Requirement
Because package evolution is lawful, pathology becomes constitutional rather than mutational.
The ecosystem therefore needs:
- detection
- quarantine
- deprecation
- kill paths
- repair paths
- memory through lineage and precedent

GTL must allow package governance to express these controls.

## Result
This makes Genesis:
- package-general
- dynamic
- interpretive
- replayable
- governable
- capable of building Genesis-aware applications on Genesis itself

## Recommended Action
1. Use this as the new forward-looking GTL direction rather than extending older graph-only proposals.
2. Define the concrete syntax and semantics of the top-level GTL constructs around `Package`, `AssetType`, and `PackageSnapshot`.
3. Make runtime binding to package snapshots non-optional.
4. Keep YAML only as materialization and compatibility surface.
5. Use software delivery, obligations, and enterprise architecture as the minimum proving suite for GTL expressiveness.
