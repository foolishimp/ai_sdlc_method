# STRATEGY: Genesis Manager product specification v1

**Author**: codex
**Date**: 2026-03-13T02:06:25+11:00
**Addresses**: clean-room replacement specification for a new `genesis_manager` project, superseding the current split mental model between `genesis_monitor` and `genesis_navigator`
**For**: all

## Summary
`genesis_manager` should be specified as the operating console for Genesis projects. It is not a methodology browser, not a graph demo, and not a raw event monitor. Its job is to help a PM, manager, builder, or customer understand project state, trust the evidence behind that state, and take the next meaningful action.

This specification is intentionally written from scratch around user questions and product capabilities. Existing Monitor and Navigator implementations should be treated as input sources only.

## Product Purpose
Genesis Manager answers three categories of questions:
- `Status`: what is happening now?
- `Analytics`: why does the system believe that?
- `Management`: what should happen next, and what action can be taken?

The product exists to turn Genesis methodology state into a usable project operating surface.

## Primary User Questions
1. What is this project trying to achieve?
2. Where is it up to right now?
3. What is blocked or risky?
4. What should happen next?
5. What decisions or approvals are waiting on people?
6. Why should I trust this status?
7. What changed recently?
8. Is the project ready to release?

## User Roles
- `PM / manager`: wants progress, risks, decisions, readiness, and next actions.
- `Builder / operator`: wants work queues, commands, technical evidence, and drill-down.
- `Customer / stakeholder`: wants goals, status, recent change, confidence, and release readiness.

## Product Scope
Genesis Manager is a project control plane with three top-level work areas:
1. `Project Status`
2. `Project Analytics`
3. `Project Management`

It also provides supporting drill-down surfaces:
- `Feature Detail`
- `Decision Detail`
- `Run Detail`
- `Release Detail`
- `Advanced Views`

## Information Design Principles
- Plain language leads; methodology codes are secondary.
- Every status claim must have an evidence path.
- Raw events are substrate, not default UI.
- Graphs and deep projections are advanced views, not primary navigation.
- Progress, risk, and next action must be visible within one screen of entry.
- If a user asks “what am I looking at?”, the page has failed its purpose.

## Primary Navigation Model
Top-level navigation:
1. `Projects`
2. `Project Overview`
3. `Project Status`
4. `Project Analytics`
5. `Project Management`
6. `Release`
7. `Advanced`

Supporting routes:
- `Feature Detail`
- `Decision Detail`
- `Run Detail`

## Projects Page
**Purpose**: select and compare Genesis projects.

**Required widgets**:
- product header
- refresh action
- project list or cards
- portfolio summary strip

**Information each project item must present**:
- project name
- project purpose or one-line summary
- current project state
- active feature count
- blocker count
- pending decision count
- last significant update timestamp
- release readiness summary

**Portfolio summary must present**:
- total projects
- projects needing attention
- projects blocked
- projects release-ready
- projects with pending decisions

## Project Overview
**Purpose**: give the single-screen executive answer.

**Required widgets**:
- project identity and purpose
- current state summary
- top milestones / outcomes
- top risks
- top next actions
- decision summary
- confidence / evidence summary

**Information required**:
- project title
- project objective in plain language
- current state label
- key outcome areas
- top three risks
- top three next actions
- pending decisions count
- readiness headline

This page should be understandable to a non-technical stakeholder without explaining REQ keys, edges, or vectors.

## Project Status
**Purpose**: answer “where is the project up to right now?”

**Required widgets**:
- progress summary cards
- workstream / feature board
- blocker summary
- recent significant change summary
- release readiness snapshot

**Progress summary cards must include**:
- project state
- active work count
- completed work count
- blocked work count
- percent complete or equivalent convergence indicator

**Workstream / feature board must include**:
- plain-language title
- technical ID as secondary label
- status
- current stage or current edge
- delta / problem count when relevant
- owner or responsibility when available
- direct link to feature detail

**Blocker summary must include**:
- blocker title
- impacted work
- severity
- why it is blocked
- required decision or action

**Recent significant change summary must include**:
- new milestones reached
- new blockers
- recent decisions
- recent feature completions

## Project Analytics
**Purpose**: answer “why does the system believe this?”

**Required widgets**:
- progress trend view
- gap analysis
- evidence / traceability view
- health and integrity view
- run / session history
- optional advanced projections

### Progress Trend View
Must show:
- trend of completed work over time
- trend of active/blocking work
- momentum / throughput signal
- stagnation or drift indicators

### Gap Analysis
Must show:
- required gaps
- advisory gaps
- layer or category of each gap
- impacted features or outcomes
- files or evidence where relevant
- severity and actionability

### Evidence / Traceability
Must answer, for any claim:
- what feature / requirement does this map to?
- what artifacts support it?
- what tests support it?
- what events or decisions support it?

### Health and Integrity
Must include:
- workspace health findings
- projection / evidence integrity findings
- observability debt findings
- stale or contradictory state findings
- confidence caveats

### Run / Session History
Must include:
- major runs or sessions
- final state of each run
- event count or work intensity
- important transitions in the run
- ability to inspect one run in detail

## Project Management
**Purpose**: answer “what should happen next, and what can I do?”

**Required widgets**:
- next actions queue
- decision queue
- command center
- action preview
- execution result stream

### Next Actions Queue
Must present ordered work items with:
- title
- type
- priority / severity
- impacted feature or scope
- reason
- recommended command or action
- expected value of doing it

### Decision Queue
Must present:
- pending reviews
- pending approvals
- consensus sessions
- unresolved human gates
- disposition required
- urgency and affected scope

### Command Center
Must allow controlled project actions such as:
- `start`
- `refresh`
- `iterate`
- `review`
- `open consensus`
- `close consensus`
- `release check`
- `rescan`
- `repair evidence`

The exact command set may evolve, but the product must make project actions explicit and reviewable.

### Action Preview
Before executing a command, the user must be shown:
- what will happen
- what scope will be affected
- what preconditions are required
- whether the action is read-only or mutating
- what evidence or events are expected to be produced

### Execution Result Stream
After an action, the product must show:
- whether it succeeded
- what changed
- what evidence was emitted
- what next state is expected
- what follow-up actions are now available

## Release Area
**Purpose**: answer “is the project ready?”

**Required widgets**:
- readiness headline
- unmet release criteria
- open risks
- required approvals
- recent regressions or concerns
- evidence backing release claims

**Release readiness must explicitly distinguish**:
- ready
- not ready
- ready with risks
- blocked pending decision

## Feature Detail
**Purpose**: answer “what is this feature, and where does it stand?”

**Required widgets**:
- feature identity card
- status summary
- trajectory / stage summary
- blockers and risks
- evidence and traceability
- acceptance criteria
- next recommended action

**Feature detail must present**:
- feature title
- feature ID
- current status
- current stage or edge
- delta / health metrics if relevant
- linked requirements
- linked code/tests/artifacts
- acceptance criteria
- next action and why

## Decision Detail
**Purpose**: answer “what decision is pending, and what evidence supports it?”

**Required widgets**:
- decision summary
- scope impacted
- comments / review input
- votes / dispositions if applicable
- recommended options
- outcome / closure state

## Run Detail
**Purpose**: answer “what happened during this run?”

**Required widgets**:
- run identity
- run outcome
- major transitions timeline
- related features / edges
- emitted evidence
- failures, if any

## Advanced Views
Advanced views are allowed, but must be explicitly secondary.

Candidate advanced views harvested from Monitor:
- asset graph / topology view
- edge convergence table
- edge traversal timeline
- traceability matrix
- feature-to-module map
- rendered STATUS.md panel
- workspace hierarchy
- raw event inspection
- consensus / review session table

These are not primary navigation surfaces. They exist to deepen evidence, not to define the product.

## Trust and Integrity Invariants
Genesis Manager must enforce the following trust model:
- project status must be evidence-backed
- projections must not assert stronger state than the substrate supports
- status claims and analytics must expose their evidence path
- mutating actions must be explicit
- read-only views and mutating views must be distinguishable in the UI
- review / approval state must be visible before actions that depend on it

## Command and Safety Model
Genesis Manager is not purely read-only.

The specification must therefore distinguish three action classes:
- `Read`: inspect state only
- `Recommend`: compute or propose next work
- `Mutate`: issue a real project action

Every command/action surface must declare which class it belongs to.

## Progressive Disclosure Model
Default experience:
- simple language
- summary first
- actionability first

Second-level disclosure:
- technical IDs
- stages / edges
- history detail
- traceability detail

Advanced disclosure:
- raw events
- graphs
- dense operational tables
- debugging projections

## What This Specification Rejects
This specification explicitly rejects the following as primary UX:
- raw event feed as homepage content
- graph-first navigation
- methodology jargon as top-level labels
- large walls of low-context widgets
- separate competing product identities for Monitor and Navigator

## Harvest Rules from Existing Projects
From `genesis_navigator`, keep:
- primary page architecture
- read-oriented clarity
- project, status, gaps, queue, history, feature-detail surfaces

From `genesis_monitor`, harvest selectively:
- traceability
- timeline and run detail richness
- edge convergence / edge status projections
- feature-module map
- status panel
- workspace hierarchy when relevant
- consensus / reviews as secondary management surfaces

Do not carry over Monitor’s widget sprawl as the product skeleton.

## Suggested Initial Build Phases
### Phase 1: Core Operating Surface
- Projects
- Project Overview
- Project Status
- Project Management basic queue
- Feature Detail

### Phase 2: Evidence and History
- Project Analytics
- Gap analysis
- Run/session history
- Evidence / traceability
- Release area

### Phase 3: Advanced Control Plane
- Decision detail
- Consensus / review management
- advanced projections
- workspace hierarchy
- graph and timeline expert modes

## Review Enrichment Questions
The review phase should pressure-test:
1. Are the top-level tabs correct?
2. Is `Project Overview` distinct enough from `Project Status`?
3. Which management actions belong in-product versus link out to command execution?
4. Which Monitor widgets add real decision value versus visual noise?
5. What is the minimum evidence path required for a status claim?
6. What is the right boundary between default and advanced views?

## Recommended Action
Treat this as the clean-room baseline specification for `genesis_manager`.

Next, run review enrichment against it in this order:
1. validate the user questions
2. validate the top-level navigation model
3. validate the widget contracts
4. validate the command/action safety model
5. only then derive concrete requirement IDs and implementation slices

This keeps the new product anchored to user value instead of inheriting the accidental complexity of the current Monitor/Navigator split.
