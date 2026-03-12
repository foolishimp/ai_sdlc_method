# STRATEGY: Genesis Manager UX principles and experience enrichment

**Author**: codex
**Date**: 2026-03-13T02:34:38+11:00
**Addresses**: enrichment of the `genesis_manager` clean-room specification, especially `20260313T020625_STRATEGY_genesis_manager-product-spec-v1.md`, `20260313T021252_STRATEGY_genesis_manager-customer-supervision-amendment.md`, and `20260313T022013_STRATEGY_genesis_manager-navigability-amendment.md`
**For**: all

## Summary
The next specification step for `genesis_manager` should be a UX enrichment pass that reduces ambiguity in the product experience itself. The product shape is now directionally correct, but it still needs explicit UX principles so future requirements, widgets, and flows do not regress into Monitor-style widget sprawl or Navigator-style code-heavy opacity.

The purpose of this post is to define those principles at the product level. This is not visual design yet. It is the interaction, information, and trust contract that the eventual UX must satisfy.

## UX Goal
`genesis_manager` should feel like a clear supervision console for a customer using Genesis to build software.

The user should feel:
- oriented
- informed
- able to trust but verify
- able to intervene deliberately
- able to move from summary to evidence without getting lost

The user should not feel:
- buried in methodology jargon
- forced to decode opaque keys
- surrounded by disconnected raw widgets
- uncertain about what action matters next
- uncertain whether a status claim is real or inferred

## Primary UX Outcome
On every screen, the user should be able to answer three questions quickly:
1. What is happening?
2. Why does the system believe that?
3. What can I do next?

If any view cannot answer those questions, it is not complete.

## UX Principles

### 1. Context before substrate
The UI must present project meaning before internal representation.

That means:
- project purpose before topology
- feature meaning before REQ keys
- state before event logs
- evidence summary before raw traces

Raw events, graph internals, and technical encodings remain valuable, but they must sit behind context, not replace it.

### 2. Plain language leads, technical identifiers anchor
Human-readable language is the primary semantic surface.

That means:
- titles, labels, and summaries should be written for a customer or supervisor first
- technical identifiers remain visible, but as secondary stable anchors
- identifiers are never the only label shown

A row that shows only `REQ-F-*`, `run_id`, or edge names has failed the product goal.

### 3. Every claim needs an adjacent evidence path
Any meaningful status claim must have a visible route to explanation.

Examples:
- `Blocked` should link to the blocker and impacted scope
- `Ready for release` should link to release criteria and supporting evidence
- `Feature converged` should link to history, evidence, and backing artifacts
- `Needs your decision` should link to the decision object and its context

This is the main trust principle of the product.

### 4. Summary first, drill-through always available
Each page should begin with a usable summary and then offer progressive disclosure.

Good ordering:
- summary
- important actions and exceptions
- current status details
- relationships and dependencies
- evidence
- raw internals

This preserves power without forcing expertise.

### 5. Navigability is a product invariant
All meaningful technical references must be navigable.

That means:
- every visible feature ID is clickable
- every requirement key is clickable
- every run, decision, and artifact reference is clickable when shown
- every detail page offers backlinks to its parent context

The user should be able to traverse the project through the UI rather than mentally reconstructing it.

### 6. Actionability beats exhaustiveness
Primary pages should privilege decisions and next actions over total data density.

The default question is not “what can we show?”
It is “what does the user need to understand or do next?”

This is the main guardrail against Monitor-style overgrowth.

### 7. Safe control must be explicit
If the product can issue commands, command UX must be explicit and trustworthy.

Every mutating action should show:
- what it will do
- what scope it will affect
- what prerequisites matter
- whether human review is involved
- what evidence or artifacts are expected to result

The user should never feel that Genesis is performing opaque mutations from a vague button press.

### 8. Exceptions outrank completeness
The UI should bias attention toward:
- blockers
- contradictions
- confidence caveats
- pending human gates
- stalled or risky work

A healthy project can be summarized briefly. An unhealthy project must surface the reasons prominently.

### 9. One project is primary, many projects are supported
The default operating mode is one-project supervision.

But the system must always preserve:
- project switching
- cross-project orientation
- future portfolio analytics

This means multi-project support belongs in the architecture now, even if the richest analytics remain future work.

### 10. Consistency of meaning matters more than visual novelty
Status labels, evidence language, and action semantics must be consistent across all pages.

If `blocked`, `needs decision`, `healthy`, or `ready` mean different things in different places, the product becomes untrustworthy regardless of visual quality.

## UX Anti-Patterns to Reject
The specification should explicitly reject these failure modes:
- graph-first navigation as the default entry experience
- raw event feed as a primary home-screen widget
- code/key-only tables without plain-language meaning
- dashboards that answer no action question
- visually dense widget walls with no prioritization
- hidden mutating actions behind generic controls
- summary cards that cannot be explained through linked evidence
- disconnected advanced views with no path back to project meaning

## Required UX Layers
The spec should describe the product as a layered experience.

### Layer 1. Orientation
The user immediately understands:
- what project they are in
- what Genesis is doing
- whether attention is needed
- what the top next action is

### Layer 2. Supervision
The user can monitor:
- active work
- blockers
- decisions needed
- recent changes
- release pressure

### Layer 3. Evidence
The user can inspect:
- why a state exists
- what supports it
- what contradicts it
- what changed over time

### Layer 4. Control
The user can:
- start or continue work
- refresh or rescan
- approve or review
- initiate repair or release checks
- inspect action results

### Layer 5. Advanced internals
The user can still reach:
- graph views
- edge timelines
- raw events
- lineage tables
- deeper workspace artifacts

But these are advanced tools, not the main product identity.

## Page-Level UX Rules

### Projects
The projects surface should behave like a switchboard, not a report archive.

Each project item should quickly answer:
- what it is
- what state it is in
- whether it needs attention
- whether something is waiting on the user
- when it last changed meaningfully

### Overview
This is the project's default landing page.

It should answer, in one screen:
- what Genesis is building
- current state
- top blockers
- next action
- pending human decisions
- current readiness/confidence

This is the page a customer should be comfortable glancing at daily.

### Supervision
This page should feel like supervising an autonomous worker.

It should show:
- what is actively moving
- what is stalled
- what Genesis recommends next
- where human intervention is required
- what changed since the last visit

### Evidence
This page should resolve trust questions, not drown the user in substrate.

Evidence UX should follow this order:
- evidence summary
- notable gaps and caveats
- traceability links
- history and run context
- raw artifacts and raw events only after that

### Control
This page should feel deliberate and safe.

The command surface should distinguish clearly between:
- read-only actions
- mutating project actions
- review/approval actions
- repair actions

The user should always be able to understand the expected consequence before execution.

### Release
This page should answer a single business question:
- can I accept or ship this yet?

Everything on the page should serve that question directly.

## Entity Experience Rules
The eventual UX should give each important entity a canonical experience contract.

### Feature experience
A feature page should answer:
- what this feature is for
- where it stands now
- what depends on it and what it depends on
- what happened to it
- what evidence supports its state
- what should happen next

### Run experience
A run page should answer:
- what happened
- what it touched
- what changed because of it
- whether it succeeded, stalled, failed, or escalated
- where to go next

### Decision experience
A decision page should answer:
- what the decision is
- why it exists
- what scope it affects
- what evidence informs it
- what remains unresolved
- what action closes it

### Requirement / artifact experience
These pages should privilege meaning and relationship context over raw structure.

## Content Design Principles
The specification should also define content behavior.

### Labels
- Prefer plain nouns and verbs over methodology jargon.
- Use technical terms only where they add precision.
- Avoid internal-only labels as primary headings.

### Status language
- Use a small, stable vocabulary.
- Each status word should have one product meaning.
- Status words should map to clear evidence or workflow implications.

### Empty states
Empty states should teach the next step.

Examples:
- no active work -> show the recommended bootstrap or start action
- no blockers -> say explicitly that nothing currently blocks progress
- no decisions pending -> say that Genesis does not currently need user judgment

### Error and caveat states
Errors and caveats should be explanatory, not merely alarming.

The UX should tell the user:
- what is wrong
- why it matters
- what Genesis recommends
- what the user can do now

## Widget Selection Principles
The specification should guide widget choice explicitly.

A widget belongs on a primary page only if it does at least one of these:
- improves orientation
- improves supervision
- improves trust
- improves decision-making
- improves actionability

If a widget is mainly diagnostic substrate, it belongs in evidence or advanced views.

## Harvest Rules from Prior Products
The specification should explicitly preserve these strengths from prior work:
- Monitor's deep drill-through and lineage navigation
- Monitor's richer entity context and feature history
- Navigator's cleaner top-level IA and more approachable entry points

And reject these weaknesses:
- Monitor's dense, under-prioritized widget walls
- Navigator's tendency toward code-heavy meaning surfaces without enough explanatory context

## Recommended UX Section Additions to the Spec
The `genesis_manager` specification should gain explicit sections for:
1. `UX Principles`
2. `Page Experience Contracts`
3. `Entity Experience Contracts`
4. `Content and Status Language Rules`
5. `Progressive Disclosure and Advanced Views`
6. `Command Safety and Action Preview Rules`
7. `Widget Selection and Placement Rules`

These should sit above visual design and below raw product intent.

## Recommended Action
1. Add a dedicated UX principles section to `genesis_manager/specification/ux/UX.md`.
2. Specify each top-level page by user question, primary actions, required widgets, and evidence paths.
3. Specify canonical detail-page experience contracts for project, feature, decision, run, requirement, and artifact.
4. Define a stable product vocabulary for statuses, blockers, readiness, and attention states.
5. Use these UX rules as the filter for harvesting Monitor and Navigator functionality into the new product.

The key point is simple: `genesis_manager` should not just be better structured than its predecessors. It should feel legible, trustworthy, and actionable from the first screen onward.
