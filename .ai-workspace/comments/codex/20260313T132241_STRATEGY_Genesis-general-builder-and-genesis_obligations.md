# STRATEGY: Genesis as a general-purpose builder and `genesis_obligations` as the first non-SDLC proof project

**Author**: codex
**Date**: 2026-03-13T13:22:41+11:00
**Addresses**: spec uplift for package-general Genesis; clean-room proposal for `genesis_obligations`; GTL-based implementation direction
**For**: all

## Summary
Genesis should be repriced as a general-purpose builder of governed asset systems, not as a methodology implicitly bound to the software SDLC graph. The AI SDLC graph remains a first-class Genesis package, but it is one package among many that can share the same formal substrate: append-only events, projections, iterate loops, evaluator-driven convergence, and explicit human gates.

The first forcing-function project for this uplift should be `genesis_obligations`: a global obligation intelligence and control-planning system for regulated institutions. It proves that Genesis can model exteroceptive source corpora, corporate activity universes, assumptions-and-interpretations ledgers, normalized obligations, applicability/intersection logic, and control-response planning, all inside a Genesis-native graph package authored in GTL.

## Decision
Genesis should formally support multiple graph packages authored in GTL:
- `AI SDLC` package for software/system building
- `Obligations` package for regulatory/control intelligence
- future domain packages as needed

Each package must remain:
- authored as a GTL program
- compiled to the same runtime contract
- event-sourced
- projection-driven
- evaluable with `F_D`, `F_P`, and `F_H`
- tenant-aware
- Genesis-native

This makes Genesis:
- a general-purpose builder of governed asset systems
- a builder of Genesis-aware applications
- capable of self-hosting and domain-hosting without forcing all domains into the SDLC topology

## Core Thesis
Genesis is not “the software SDLC.” It is a formal engine for constrained asset evolution.

The SDLC graph is one package. `genesis_obligations` is another package. Both are valid because they share the same formal substrate:
- append-only events
- projected state
- iterate loops
- evaluator-driven convergence
- explicit human gates
- traceable lineage

## Product Vision
Genesis should support two levels simultaneously:

### 1. General-Purpose Genesis
A configurable builder capable of authoring and running multiple domain topologies.

### 2. Genesis-Aware Applications
Applications whose own domain model, workflows, and governance are expressed as Genesis graph packages and built by Genesis itself.

This creates the path to:
- Genesis building software systems
- Genesis building regulatory/control systems
- Genesis building operational governance systems
- Genesis building itself

## First Proof Project: `genesis_obligations`
`genesis_obligations` is the first non-SDLC Genesis-aware application.

Its purpose is to answer:

**Given what the institution actually does, what obligations apply, why do they apply, what evidence is required, and what internal change is needed?**

This is not a document repository. It is not only a legal research tool. It is a constraint intelligence and control-planning system.

## Foundational Assets
The project is built around three first-rank assets and two derived layers.

### 1. External Source Corpus
The full exteroceptive input layer:
- laws
- regulations
- rules
- guidance
- standards
- tax materials
- HR/employment rules
- internal policies
- supervisory findings

Each source must preserve:
- provenance
- jurisdiction
- effective dates
- supersession chain
- source structure and references
- change history

### 2. Corporate Activity Universe
A maintained model of what the institution actually does:
- legal entities
- jurisdictions
- business lines
- product categories
- instruments / commodities
- client/counterparty populations
- employee populations
- processes
- lifecycle stages
- systems and data flows
- control domains

This constrains real regulatory exposure.

### 3. Assumptions & Interpretations Ledger
A first-class institutional interpretation layer:
- source intent
- corporate governance intent
- assumptions
- ambiguity notes
- precedent
- interpretive decisions
- review/approval
- supersession

### 4. Derived Normalized Obligations
Operational obligation objects derived from:
- source corpus
- activity universe
- assumptions & interpretations
- precedent
- governance posture

### 5. Control Response Assets
Where obligation deltas become managed work:
- obligation intent
- feature vector
- control artifact
- evidence artifact
- assessment state

## Fractal Genesis Principle
Genesis should be used at every grain, with the right graph package for that grain.

Not:
- normalize first, then use Genesis

But:
- use Genesis all the way down
- with the correct domain-specific stack at each level

For `genesis_obligations`, that means three interacting stacks:

### A. Normalization Stack
- `source_document`
- `source_provision`
- `obligation_candidate`
- `interpretation_case`
- `normalized_obligation`

### B. Applicability Stack
- `normalized_obligation`
- `activity_signature`
- `applicability_binding`
- `obligation_assessment`

### C. Response Stack
- `obligation_assessment`
- `obligation_intent`
- `feature_vector`
- `control_artifact`
- `evidence_artifact`

Same primitives, different topology.

## Scaling Model
The system must scale to thousands or millions of obligations. It cannot treat every source document or obligation as a bespoke top-level work item.

The scaling rules are:

### 1. Multi-grain assets
A source document may contain dozens or hundreds of provisions. Each provision may yield multiple obligation candidates.

### 2. Obligation families
Use canonical obligation families plus parameters, not only bespoke instances.

Examples:
- ratio threshold
- reporting obligation
- retention obligation
- notification obligation
- attestation obligation
- segregation-of-duties obligation
- training obligation

### 3. Projection over full materialization
Do not precompute every obligation × activity × entity cross-product. Store the substrate and project the intersection.

### 4. Intent only on delta
Not every normalized obligation becomes work. Only obligations with a control/evidence/process delta emit intents and feature vectors.

## Traceability Rule
Every downstream artifact must trace back upward.

Minimum lineage:
- `feature_vector -> obligation_intent`
- `obligation_intent -> obligation_assessment`
- `obligation_assessment -> applicability_binding`
- `applicability_binding -> normalized_obligation + activity_signature`
- `normalized_obligation -> interpretation_case`
- `interpretation_case -> source_provision + assumptions + precedent`
- `source_provision -> source_document`

This is non-negotiable.

## Why This Matters
This turns Genesis into both:
- a manageable general-purpose builder
- and a runtime for Genesis-aware applications built on Genesis

The obligation project is the forcing function proving that Genesis is not locked to software-delivery topology.

## GTL Authoring Model
This should be authored in GTL, not forced through static SDLC YAML.

A package like `genesis_obligations` should define its own:
- asset nodes
- edges
- evaluators
- compositions
- profiles
- workspace paths
- tenant bindings

### Example node families
- `source_document`
- `source_provision`
- `obligation_candidate`
- `interpretation_case`
- `normalized_obligation`
- `activity_signature`
- `applicability_binding`
- `obligation_assessment`
- `obligation_intent`
- `feature_vector`
- `control_artifact`
- `evidence_artifact`

### Example profile slices
- prudential
- tax
- HR
- privacy
- records retention
- market conduct
- product-specific overlays
- region-specific overlays

### Example compositions
- source extraction cycle
- interpretation review cycle
- applicability reassessment cycle
- change-impact propagation cycle
- control-gap response cycle

## Evaluator Model
This package should use all three evaluator classes.

### F_D
- provenance completeness
- citation validity
- supersession consistency
- taxonomy validity
- formula structure validation
- lineage completeness
- duplicate/conflict checks
- control mapping completeness checks

### F_P
- provision extraction
- candidate obligation classification
- source-intent inference
- interpretation drafting
- applicability reasoning
- conflict detection proposals
- change-impact drafting

### F_H
- interpretation approval
- precedent-setting decisions
- ambiguity resolution
- exception approval
- control sufficiency review
- governance posture decisions

## Required Spec Uplift
To make this a first-class Genesis capability, the specification must be uplifted in these ways:

### 1. Genesis must be explicitly graph-package general
The spec should state that the AI SDLC graph is one package, not the universal graph.

### 2. GTL must support domain-specific packages
GTL should be the canonical authoring surface for non-SDLC graphs as well as SDLC graphs.

### 3. Asset semantics need richer typing
GTL and/or the wider spec should eventually support richer asset-type semantics than only node names:
- schema
- lineage requirements
- markov criteria
- projection rules
- domain taxonomies

### 4. Design stacks must be package-specific
A domain-specific Genesis stack must be allowed to define its own topology and evaluator patterns without pretending to be a software-delivery workflow.

### 5. Intent and feature vectors must be domain-general
Intent and feature vectors should not be SDLC-only concepts. They are the mechanism by which delta becomes governed work in any Genesis package.

## New Specification Rule
Genesis packages should be authored as:

`Domain Graph + Evaluators + Compositions + Context + Runtime State`

not as static YAML bundles implicitly tied to software delivery.

## `genesis_obligations` Functional Contract

### Core capability areas
1. Exteroceptive source ingestion
2. Corporate activity modeling
3. Assumptions & interpretations
4. Obligation normalization
5. Applicability and intersection
6. Control and evidence mapping
7. Change impact analysis
8. Governance and review
9. Query and API access
10. Intent and feature-vector generation for control response

### Primary query examples
- What applies to trading exotic financial products in EMEA?
- What applies to energy trading in Texas?
- Which assumptions and precedents were used?
- Which obligations require approval, evidence, or segregation?
- Which obligations are unmapped to internal controls?
- Which regulatory changes affect this business line?

## MVP
The MVP should prove the architecture, not cover all regulation.

### MVP slice
- limited but real source domains
- real activity signatures
- explicit A&I ledger
- normalized obligation derivation
- applicability assessment
- one control/evidence mapping path
- one intent/feature-vector generation path

### MVP demonstration
Given a concrete activity signature, the system should answer:
- which obligations apply
- why they apply
- which assumptions and precedents were used
- which controls/evidence satisfy them
- which gaps remain
- which intents/features must be created to close the gap

## Resulting Strategic Outcome
With this uplift, Genesis becomes:
- a general-purpose builder of governed asset systems
- a self-hosting methodology
- a platform for Genesis-aware applications
- a formal engine that can build both software systems and institutional governance systems

This is not an extension patch. It is a clean, complete repricing of Genesis around package-general graph authoring.

## Recommended Action
1. Ratify the package-general direction for Genesis.
2. Uplift the spec so SDLC is one graph package, not the implicit universal topology.
3. Use GTL as the canonical authoring surface for domain-specific Genesis packages.
4. Open `genesis_obligations` as the first non-SDLC proof project.
5. Define its graph package explicitly: nodes, edges, evaluators, compositions, profiles, and markov criteria.
6. Make intent/feature-vector generation from obligation deltas a first-class part of the package.
