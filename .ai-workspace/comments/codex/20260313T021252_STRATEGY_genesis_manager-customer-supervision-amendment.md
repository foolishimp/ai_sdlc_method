# STRATEGY: Genesis Manager customer-supervision amendment

**Author**: codex
**Date**: 2026-03-13T02:12:52+11:00
**Addresses**: amendment to `20260313T020625_STRATEGY_genesis_manager-product-spec-v1.md`
**For**: all

## Summary
The `genesis_manager` specification should be repriced around the true primary user: the customer of Genesis, meaning the person using Genesis to build projects. That user is primarily supervising an autonomous builder, not acting as a generic portfolio manager. This changes the primary perspective of the product, but it does not remove multi-project navigation or future portfolio analytics. It only changes what the product feels like at the center.

## Primary User Reframing
The primary user is:
- a person building one or more projects through Genesis
- usually focused on one project at a time
- supervising, steering, approving, and trusting the system
- occasionally switching across projects
- potentially needing cross-project analytics later

So the product should feel like:
- a `project cockpit`
- a `builder supervision console`
- a `trust and intervention surface`

not primarily:
- a team PM dashboard
- a methodology browser
- a raw observability tool

## Core User Questions (Repriced)
The top questions are now:
1. What is Genesis building for me?
2. How far has it gotten?
3. What is blocked, wrong, or uncertain?
4. What does Genesis want to do next?
5. What does Genesis need from me right now?
6. Why should I trust its current status?
7. What changed since I last looked?
8. Is this ready for me to accept, review, or ship?

These should govern the information architecture.

## Revised Product Model
The top-level product should now be framed as four work areas:
1. `Overview`
2. `Supervision`
3. `Evidence`
4. `Control`

This is a better fit than the earlier `Status / Analytics / Management` framing, while still preserving the same functional coverage.

## Revised Primary Navigation
### 1. Projects
**Purpose**: move between projects and understand which projects need attention.

This remains necessary because the future includes multiple projects.

Required at minimum:
- project list
- project state
- last meaningful update
- projects needing attention
- quick switch into a project

This is a navigation and orientation layer, not the primary product identity.

### 2. Overview
**Purpose**: one-screen answer to “what is Genesis doing in this project?”

Must include:
- project purpose
- current project state
- progress summary
- top blockers
- top next actions
- decisions needed now
- release/readiness summary

This is the default project landing area.

### 3. Supervision
**Purpose**: monitor active autonomous work and see what needs attention.

Must include:
- feature/workstream status
- active work
- blocked work
- queue of recommended next actions
- pending human gates / decisions
- recent significant changes

This is where the user supervises Genesis as an actor.

### 4. Evidence
**Purpose**: answer “why should I trust this?”

Must include:
- gap analysis
- traceability
- run/session history
- health/integrity findings
- drill-down into evidence for any claim

Advanced projections live here behind progressive disclosure.

### 5. Control
**Purpose**: let the user steer Genesis deliberately.

Must include:
- explicit actions/commands
- action preview
- approval/review actions
- repair actions
- execution results

This is where commands such as `start`, `iterate`, `refresh`, `review`, `open consensus`, or `release check` belong.

### 6. Release
**Purpose**: make the ship/no-ship question explicit.

Must include:
- readiness headline
- missing criteria
- open risks
- approvals still needed
- evidence backing the release claim

## Functional Coverage Mapping
The earlier capability set is preserved; it is just regrouped around the customer-supervision stance.

### Overview covers:
- project summary
- progress summary
- top outcomes
- top risks
- top decisions
- top next actions

### Supervision covers:
- status and progress
- blockers and risks
- next actions queue
- decision queue
- feature/workstream monitoring
- recent change summary

### Evidence covers:
- evidence and traceability
- health and integrity
- gap analysis
- run history
- advanced projections

### Control covers:
- command center
- action preview
- execution results
- approvals and interventions
- evidence repair / remediation actions

### Release covers:
- release readiness
- final evidence-backed acceptance view

## Multi-Project Future (Preserved)
This user reframing does not remove multi-project capability.

The correct model is:
- `single-project supervision` is primary
- `multi-project navigation` is always available
- `multi-project analytics` is a future higher-order layer

So the product should support three scopes:
1. `Project scope` — primary day-to-day mode
2. `Project-switching scope` — move between projects quickly
3. `Portfolio scope` — future aggregate insights across projects

### Project scope (primary)
The user is inside one project and supervising Genesis there.

### Project-switching scope
The user can move between projects from a persistent project switcher or projects page.

### Portfolio scope (future)
Possible later capabilities:
- compare project risk levels
- compare throughput/momentum
- compare release readiness
- identify projects needing attention
- identify cross-project observability or health issues

These are future analytics, not the baseline product core.

## IA Consequences
This changes the tone of the product in important ways.

### What should lead
- “What Genesis is doing for you”
- “What Genesis needs from you”
- “What you should trust / question”
- “What to do next”

### What should be secondary
- REQ keys
- edge names
- vector jargon
- event types
- graph structure
- dense raw widgets

### What becomes tertiary / advanced
- raw event feeds
- graph-first navigation
- deep methodology internals
- expert observability tables

## Widget Repricing
The same widgets can stay, but their role changes.

### Primary widgets
- overview summary card
- progress summary cards
- blocker list
- next actions queue
- decisions needed list
- recent changes summary
- release snapshot

### Secondary widgets
- feature trajectory view
- gap layers
- history/run list
- traceability panel
- evidence inspector

### Advanced widgets
Harvested mainly from Monitor:
- graph view
- edge convergence table
- edge traversal timeline
- status document panel
- feature-to-module map
- workspace hierarchy
- consensus/reviews table
- raw events

## Revised Specification Rule
The new spec should be written as:
- a supervision product for a customer using Genesis
- with project switching built in
- with future multi-project analytics reserved explicitly

It should not be written as:
- a pure PM tool
- a pure engineering observability tool
- a methodology teaching interface

## Recommended Action
Amend the `genesis_manager` baseline spec as follows:
1. Replace the primary framing with `customer supervising Genesis`.
2. Recast the top-level work areas as `Overview / Supervision / Evidence / Control / Release`.
3. Keep `Projects` as the navigation entry point and future multi-project base.
4. Preserve all earlier functional coverage, but regroup it around this primary user stance.
5. Keep portfolio analytics as a future explicit layer, not the default identity of the product.

The important point is: the product should feel like the control surface for your builder, not a dashboard about your methodology.
