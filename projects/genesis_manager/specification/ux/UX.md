# UX Specification — genesis_manager

**Version**: 0.1.0
**Date**: 2026-03-13
**Status**: Draft

---

## Primary UX Outcome

On every screen, the user must be able to answer three questions quickly:

1. **What is happening?**
2. **Why does the system believe that?**
3. **What can I do next?**

If any view cannot answer those three questions, it is not complete.

---

## UX Principles

### 1. Context before substrate

The UI must present project meaning before internal representation.

- Project purpose before topology
- Feature meaning before REQ keys
- State before event logs
- Evidence summary before raw traces

Raw events, graph internals, and technical encodings remain valuable, but they must sit behind context — not replace it.

### 2. Plain language leads, technical identifiers anchor

Human-readable language is the primary semantic surface.

- Titles, labels, and summaries must be written for a customer or supervisor first
- Technical identifiers remain visible as secondary stable anchors
- Identifiers are never the only label shown

A row that shows only `REQ-F-*`, `run_id`, or edge names has failed the product goal.

### 3. Every claim needs an adjacent evidence path

Any meaningful status claim must have a visible route to explanation.

| Claim | Required evidence path |
|-------|----------------------|
| `Blocked` | Link to the blocker and impacted scope |
| `Ready for release` | Link to release criteria and supporting evidence |
| `Feature converged` | Link to history, evidence, and backing artifacts |
| `Needs your decision` | Link to the decision object and its context |

This is the primary trust principle of the product.

### 4. Summary first, drill-through always available

Each page begins with a usable summary and then offers progressive disclosure.

Required ordering on every page:
1. Summary
2. Important actions and exceptions
3. Current status details
4. Relationships and dependencies
5. Evidence
6. Raw internals

### 5. Navigability is a product invariant

All meaningful technical references must be navigable.

- Every visible feature ID is clickable
- Every requirement key is clickable
- Every run, decision, and artifact reference is clickable when shown
- Every detail page offers backlinks to its parent context

The user must be able to traverse the project through the UI rather than mentally reconstructing it.

### 6. Actionability beats exhaustiveness

Primary pages privilege decisions and next actions over total data density.

The default question is not "what can we show?" It is "what does the user need to understand or do next?"

This is the primary guardrail against Monitor-style widget overgrowth.

### 7. Safe control must be explicit

Every mutating action must show:
- what it will do
- what scope it will affect
- what prerequisites matter
- whether human review is involved
- what evidence or artifacts are expected to result

The user must never feel that Genesis is performing opaque mutations from a vague button press.

### 8. Exceptions outrank completeness

The UI biases attention toward:
- blockers
- contradictions
- confidence caveats
- pending human gates
- stalled or risky work

A healthy project can be summarized briefly. An unhealthy project must surface the reasons prominently.

### 9. One project is primary, many projects are supported

The default operating mode is single-project supervision. The architecture must always preserve:
- project switching
- cross-project orientation
- future portfolio analytics

Multi-project support belongs in the architecture now, even if rich analytics remain future work.

### 10. Consistency of meaning over visual novelty

Status labels, evidence language, and action semantics must be consistent across all pages. If `blocked`, `needs decision`, `healthy`, or `ready` mean different things in different places, the product becomes untrustworthy regardless of visual quality.

---

## UX Anti-Patterns to Reject

The following failure modes are explicitly rejected:

- Graph-first navigation as the default entry experience
- Raw event feed as a primary home-screen widget
- Code/key-only tables without plain-language meaning
- Dashboards that answer no action question
- Visually dense widget walls with no prioritisation
- Hidden mutating actions behind generic controls
- Summary cards that cannot be explained through linked evidence
- Disconnected advanced views with no path back to project meaning

---

## Progressive Disclosure Layers

The product is structured as five layers of progressive disclosure:

### Layer 1: Orientation
The user immediately understands:
- what project they are in
- what Genesis is doing
- whether attention is needed
- what the top next action is

### Layer 2: Supervision
The user can monitor:
- active work
- blockers
- decisions needed
- recent changes
- release pressure

### Layer 3: Evidence
The user can inspect:
- why a state exists
- what supports it
- what contradicts it
- what changed over time

### Layer 4: Control
The user can:
- start or continue work
- refresh or rescan
- approve or review
- initiate repair or release checks
- inspect action results

### Layer 5: Advanced internals
The user can still reach:
- graph views
- edge timelines
- raw events
- lineage tables
- deeper workspace artifacts

Advanced internals are reachable, but they are not the main product identity.

---

## Page Experience Contracts

### Projects page
Behaves like a switchboard, not a report archive.

Each project item must answer:
- What is this project?
- What state is it in?
- Does it need attention?
- Is something waiting on the user?
- When did it last change meaningfully?

### Overview page (default project landing)
Answers in one screen:
- What is Genesis building?
- What is the current state?
- What are the top blockers?
- What is the next action?
- What human decisions are pending?
- What is the current readiness/confidence?

This is the page a customer should be comfortable glancing at daily.

### Supervision page
Feels like supervising an autonomous worker. Shows:
- What is actively moving
- What is stalled
- What Genesis recommends next
- Where human intervention is required
- What changed since the last visit

### Evidence page
Resolves trust questions without drowning the user in substrate.

Required ordering:
1. Evidence summary
2. Notable gaps and caveats
3. Traceability links
4. History and run context
5. Raw artifacts and raw events

### Control page
Feels deliberate and safe. Distinguishes clearly between:
- Read-only actions
- Mutating project actions
- Review / approval actions
- Repair actions

The user must always understand the expected consequence before execution.

### Release page
Answers one business question: **can I accept or ship this yet?**

Every element on the page serves that question directly.

---

## Entity Experience Contracts

### Feature experience
A feature detail page must answer:
- What is this feature for?
- Where does it stand now?
- What depends on it, and what does it depend on?
- What happened to it?
- What evidence supports its state?
- What should happen next?

### Run experience
A run detail page must answer:
- What happened?
- What did it touch?
- What changed because of it?
- Did it succeed, stall, fail, or escalate?
- Where to go next?

### Decision experience
A decision detail page must answer:
- What is the decision?
- Why does it exist?
- What scope does it affect?
- What evidence informs it?
- What remains unresolved?
- What action closes it?

### Requirement / artifact experience
Privilege meaning and relationship context over raw structure.
Show which features this requirement belongs to, which code/tests satisfy it, and which decisions affect it.

---

## Content and Status Language Rules

### Labels
- Prefer plain nouns and verbs over methodology jargon
- Use technical terms only where they add precision
- Avoid internal-only labels as primary headings

### Status vocabulary
Use a small, stable vocabulary. Each status word has exactly one product meaning.

| Status word | Product meaning |
|-------------|----------------|
| `Active` | Genesis is currently working on this |
| `Blocked` | Progress is halted; reason is always linked |
| `Needs decision` | Human judgment is required before progress continues |
| `Converged` | This item has met all its evaluators |
| `Ready` | Release or acceptance criteria are satisfied |
| `Stalled` | Work has not progressed past expected threshold |
| `Healthy` | No anomalies or blockers detected |

### Empty states
Empty states teach the next step.

| Empty state | Message |
|-------------|---------|
| No active work | Show recommended bootstrap or start action |
| No blockers | "Nothing currently blocks progress" |
| No decisions pending | "Genesis does not currently need your judgment" |

### Error and caveat states
Errors and caveats are explanatory, not merely alarming. Must state:
- What is wrong
- Why it matters
- What Genesis recommends
- What the user can do now

---

## Widget Selection and Placement Rules

A widget belongs on a primary page only if it satisfies at least one of:
- Improves orientation
- Improves supervision
- Improves trust
- Improves decision-making
- Improves actionability

If a widget is primarily diagnostic substrate, it belongs in the Evidence page or advanced views, not on primary pages.

### Primary page widgets (allowed)
- Overview summary card
- Progress summary cards
- Blocker list with evidence links
- Next actions queue
- Decisions needed list
- Recent changes summary
- Release snapshot

### Secondary page widgets (Evidence / Control)
- Feature trajectory view
- Gap analysis panels
- History / run list
- Traceability panel
- Evidence inspector

### Advanced view widgets (Layer 5 only)
- Graph / topology view
- Edge convergence table
- Edge traversal timeline
- Raw event feed
- Feature-to-module map
- Consensus / reviews table
- Status document panel
- Workspace hierarchy

---

## Harvest Rules from Prior Products

### Preserve from genesis_monitor
- Deep drill-through and lineage navigation
- Richer entity context and feature history
- Run / event detail with clear consequence tracing

### Preserve from genesis_navigator
- Cleaner top-level information architecture
- More approachable entry points
- Better separation of summary and detail

### Reject from genesis_monitor
- Dense, under-prioritised widget walls
- Raw substrate as primary home-screen content

### Reject from genesis_navigator
- Code-heavy meaning surfaces without sufficient explanatory context
- Navigation structures that require methodology knowledge to traverse

---

## Source

Synthesised from Codex strategy post:
- `20260313T023438_STRATEGY_genesis_manager-ux-principles-and-enrichment.md`

Cross-references:
- `20260313T022013_STRATEGY_genesis_manager-navigability-amendment.md`
- `20260313T021252_STRATEGY_genesis_manager-customer-supervision-amendment.md`
- `20260313T020625_STRATEGY_genesis_manager-product-spec-v1.md`
