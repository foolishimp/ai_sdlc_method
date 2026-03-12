# STRATEGY: Genesis Manager navigability and drill-through amendment

**Author**: codex
**Date**: 2026-03-13T02:20:13+11:00
**Addresses**: amendment to `20260313T020625_STRATEGY_genesis_manager-product-spec-v1.md` and `20260313T021252_STRATEGY_genesis_manager-customer-supervision-amendment.md`
**For**: all

## Summary
One of the strongest lessons from the earlier Monitor work should become an explicit invariant in `genesis_manager`: the product must support navigability through the system, not just presentation of status. Keys, IDs, and technical references are necessary, but they must function as clickable addresses into full context. The user should be able to traverse from any meaningful reference to the underlying feature, module, run, decision, artifact, or requirement and see its full history, dependencies, evidence, and evolution.

This is not a minor UX refinement. It is a core product capability.

## The Lesson from Prior Projects
`genesis_navigator` improved the top-level information architecture, but `genesis_monitor` did a better job exposing deep entity context and click-through lineage. The feature route and template in Monitor show the shape worth preserving:
- feature definition
- status and trajectory
- parent/child relationships
- decision trail
- edge traversal history
- backing documents
- raw vector / source context

The new product should preserve that strength without inheriting Monitor’s widget sprawl.

## New Product Invariant: Navigability
Genesis Manager must satisfy this invariant:

**Every visible technical identifier is a navigation handle into deeper context.**

That means:
- REQ keys are clickable
- feature IDs are clickable
- run IDs are clickable
- decision/review IDs are clickable
- modules/artifacts are clickable where appropriate
- requirement references are clickable

If a user sees a code, key, or identifier, they should be able to click it and understand what it means in project terms.

## Keys Are Addresses, Not Labels
The product should follow this rule:
- human-readable language is the primary label
- technical keys are secondary labels
- technical keys provide stable addressing and drill-down

So the UI should not force the user to read `REQ-F-*` as the primary semantic content. Instead:
- title or plain-language description leads
- key appears as a secondary stable identifier
- clicking the key opens the canonical detail page

## Canonical Detail Pages
Genesis Manager should define canonical detail pages for the entities that actually matter.

### 1. Project Detail
Must provide:
- purpose
- current state
- top next actions
- top blockers
- recent important changes
- release readiness
- linked features, decisions, runs, and evidence

### 2. Feature Detail
Must provide:
- feature title and ID
- current status
- current stage / trajectory
- linked requirements
- parent/child feature relationships
- blockers and dependencies
- decision trail
- run history
- backing docs / linked evidence
- linked artifacts and modules
- next recommended action

### 3. Decision Detail
Must provide:
- decision summary
- scope affected
- current review/consensus state
- comments / dispositions / votes
- evidence that informs the decision
- resulting action or closure

### 4. Run Detail
Must provide:
- run identity
- final outcome
- features and edges touched
- significant events
- artifacts or outputs produced
- failures / anomalies
- links back to affected features and decisions

### 5. Requirement / Spec Detail
Must provide:
- plain-language requirement meaning
- linked features
- linked code/tests/artifacts
- linked gaps
- linked decisions or reviews

### 6. Artifact / Module Detail
Must provide:
- what feature(s) it supports
- what requirements it traces to
- related tests / telemetry
- change history where available

## Dependency Navigator
A dependency navigator is a core capability, not an optional advanced widget.

From any feature, the user must be able to navigate to:
- its requirements
- its parent / child features
- its dependent or blocking features
- its artifacts / modules
- its tests and evidence
- its runs and execution history
- its decisions and reviews
- its release impact

From any other entity, the user must also be able to navigate back to the feature or project it belongs to.

This makes the product traversable as a project graph in human terms.

## Bidirectional Navigation Rule
Navigation must be bidirectional wherever meaningful.

Minimum required traversals:
- project -> feature
- feature -> project
- feature -> requirement
- requirement -> feature
- feature -> decision
- decision -> feature
- feature -> run
- run -> feature
- feature -> artifact/module
- artifact/module -> feature
- feature -> linked evidence
- evidence -> source entity

If a relationship is shown, it should usually be traversable.

## Context Before Raw Data
Drill-through pages must prioritize context before low-level representation.

For example, a feature page should show in this order:
1. what the feature is
2. current state and next step
3. what it depends on and what depends on it
4. what happened to it over time
5. what evidence supports its state
6. only then raw YAML, raw events, or internal details

This preserves the power of Monitor’s feature lineage without forcing every user into methodology internals first.

## Advanced Views Still Matter
This amendment does not remove advanced views. It reprices them.

The following remain valuable:
- traceability matrix
- edge traversal timeline
- feature-module map
- raw event inspection
- graph view
- review / consensus detail
- backing document inspection

But these should be reachable from canonical detail pages and evidence panels, not dropped as disconnected raw widgets into the main overview.

## Widget Consequences
This amendment implies several widget-level rules.

### Primary views must include:
- clickable titles and keys
- direct drill-down links
- visible relationship summaries
- visible “why / evidence” links

### Feature cards and rows must include:
- human title
- key/ID
- click target to feature detail
- state
- next-step hint

### Queue items and gap items must include:
- linked feature or requirement references
- click-through to relevant detail pages
- linked evidence where available

### History views must include:
- links from runs/events back to affected features and decisions

## Specification Consequence
The `genesis_manager` specification should gain a dedicated section:

`Navigability and Entity Drill-Through`

That section should define:
- canonical entity pages
- clickable identifier rule
- dependency navigator capability
- bidirectional navigation rule
- context-before-raw-data ordering

This should be treated as a first-class capability, not a UI nice-to-have.

## Recommended Action
Amend the `genesis_manager` baseline as follows:
1. Add navigability as a product invariant.
2. Add canonical detail pages for project, feature, decision, run, requirement, and artifact/module.
3. Add dependency navigation as a core capability.
4. Require all meaningful technical identifiers to be clickable.
5. Preserve Monitor’s strong lineage/dependency drill-through, but integrate it into the cleaner Manager architecture.

The most important lesson is simple: users should not have to decode the system from static labels. They should be able to navigate through it.
