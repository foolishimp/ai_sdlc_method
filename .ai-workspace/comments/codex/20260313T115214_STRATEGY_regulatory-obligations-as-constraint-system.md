# STRATEGY: Regulatory obligations as a first-class constraint system

**Author**: codex
**Date**: 2026-03-13T11:52:14+11:00
**Addresses**: follow-up to `20260313T111343_STRATEGY_best-of-breed-entitlements-for-global-finance.md`; future reference architecture for regulated financial control models
**For**: all

## Summary
In highly regulated financial environments, entitlements are only part of the control model. The deeper governing layer is regulatory and policy obligation. Entitlements say what a subject may do; obligations say what must be true before, during, and after a state transition is admissible.

This means a practical control architecture should treat obligations as first-class constraints, not as footnotes on top of access control.

## The Key Distinction
A clean distinction is:

- `visibility controls` answer: may this subject even see this asset?
- `functional privileges` answer: if inside the allowed domain, what actions may this subject perform?
- `regulatory obligations` answer: under what constraints is the action admissible at all?
- `evidence` answers: what proves those constraints were satisfied?

That gives the real decision function:

```text
admissible(subject, action, asset, context) =
  visibility_wall(subject, asset)
  AND functional_capability(subject, action, domain(asset))
  AND obligations_satisfied(subject, action, asset, context)
```

This is much closer to how regulated institutions actually operate.

## Why Obligations Are Different from Entitlements
Entitlements are usually:
- granted
- scoped
- assignable
- permissive

Obligations are usually:
- imposed by regulation, policy, or control design
- triggered by context
- not something the user is granted
- often cross-cutting across systems and processes
- temporal and evidentiary

Examples:
- a trade above a threshold must be reviewed before execution
- a specific asset class must not cross an information barrier
- records must be retained for a defined period
- an action requires dual approval
- a control must be performed within a time window
- privileged access must be session-recorded
- a release must carry attestations and evidence before promotion

These are not just permissions. They are constraints on valid transitions.

## The Correct Mental Model
The right architecture is:
- `roles/capabilities` define what actions a subject is generally able to perform
- `walls` define what assets or domains are visible
- `obligations` define when and how an action is valid
- `evidence` proves that the obligations were satisfied

This means roles are not the full governance layer. They are only one component of admissibility.

## Obligations as Constraint Objects
Obligations should be modeled as first-class policy objects.

A useful shape is:
- `source`
  - law, regulation, policy, internal control, standard, supervisory finding
- `scope`
  - jurisdiction, legal entity, business unit, product, asset class, client type, process, system, environment
- `trigger`
  - attempted action, asset classification, lifecycle state, value threshold, client segment, geography, control state, event occurrence
- `modality`
  - must, must_not, must_review, must_attest, must_notify, must_retain, must_segregate, must_record
- `timing`
  - precondition, in-flight invariant, postcondition, periodic obligation
- `evidence requirement`
  - approvals, logs, attestations, retained records, reviewer identity, time-stamped artifacts, workflow state
- `exception model`
  - whether exceptions are allowed, who approves them, compensating controls, expiry, escalation
- `severity / criticality`
  - impact of breach, escalation class, control importance

This makes obligations inspectable, testable, and explainable.

## Timing Matters
One reason obligations are often modeled poorly is that they are not all of the same kind.

A useful distinction is:

### 1. Preconditions
Something must already be true before the action may happen.

Examples:
- required approval exists
- user is inside the permitted wall
- necessary reviewer is independent
- release checklist is complete

### 2. In-flight invariants
Something must remain true while the process is ongoing.

Examples:
- segregation of duties remains intact
- ongoing session remains recorded
- workflow remains inside approved control path
- no disallowed cross-wall sharing occurs during collaboration

### 3. Postconditions
Something must be done immediately after the action.

Examples:
- emit audit event
- retain artifacts
- notify a downstream control process
- capture attestation

### 4. Periodic obligations
Something must continue to happen over time.

Examples:
- recertification
- retention and destruction schedule
- periodic review
- ongoing monitoring

This temporal structure is one reason obligations should not be collapsed into static roles.

## Evidence Is Not Optional
The only practical way to make obligations operational is to model the evidence surface explicitly.

For every important obligation, the system should be able to answer:
- what obligation applied?
- why did it apply?
- was it satisfied?
- what proof exists?
- who performed the control?
- when was it satisfied?
- what exception path was used, if any?

This implies an `effective obligations view`, analogous to an effective access view.

That view should show:
- applicable obligations
- satisfied obligations
- unsatisfied obligations
- waived obligations
- missing evidence
- blocking obligations
- originating policy source

Without that, the control system becomes opaque and audit-hostile.

## Relation to Existing Access Architecture
This follows naturally from the earlier entitlement architecture note.

### Visibility layer
Still decides whether the asset is visible.

### Functional layer
Still decides whether the subject has the relevant business capability in scope.

### Obligation layer
Now decides whether the action is valid under regulation, policy, and control constraints.

### Evidence layer
Provides proof for audit, supervision, and operational trust.

This means the overall architecture is not two-dimensional. It is at least four-dimensional:
- visibility
- function
- obligation
- evidence

That is a better representation of reality in regulated institutions.

## Why This Matters Operationally
If obligations are not first-class, they get encoded badly in one of three places:
- buried in process documents no runtime system can enforce
- approximated in static role design, causing role explosion
- handled by manual exception culture, creating operational risk

Treating obligations as first-class constraints avoids all three failures.

It also improves:
- explainability
- automation
- auditability
- policy evolution
- exception governance
- consistency across systems

## Interaction with Exceptions
Exceptions should also be modeled as governed constraint objects, not one-off informal decisions.

A compliant exception model needs:
- explicit approver
- reason and business justification
- compensating control
- expiry
- scope
- audit trail

This is especially important in finance, where many practical workflows are not “rule always applies” but “rule applies unless approved under controlled exception path.”

## Segregation of Duties Fits Here
Segregation of duties is often treated as an RBAC feature, but conceptually it is better understood as an obligation constraint.

It says:
- certain combinations of capabilities, states, or actions must not coexist without control

That makes it a classic admissibility rule, not just a permission grant. This is another reason obligations deserve their own layer.

## Target-State Architecture Consequence
A best-of-breed regulated architecture should therefore have:
1. `IGA / entitlement governance`
2. `visibility wall / information barrier control`
3. `functional authorization`
4. `obligation policy engine`
5. `evidence / audit projection layer`
6. `exception governance`
7. `PAM` for elevation and privileged workflows

In some products these layers may be partially combined, but conceptually they should remain distinct.

## Design Rule
The design rule is simple:

**Do not ask roles to carry regulatory semantics they are not structurally suited to carry.**

Roles are a poor place to encode:
- temporal conditions
- evidentiary requirements
- exception lifecycles
- cross-cutting legal constraints
- obligation satisfaction state

Those belong in the constraint and evidence system.

## Position
For regulated financial institutions, the real governance model is not:
- who are you?
- what role do you have?

It is:
- what are you allowed to see?
- what are you allowed to do in that scope?
- what obligations govern that action?
- what evidence proves those obligations were met?

That is the better abstraction.

## Recommended Action
1. Treat regulatory obligations as first-class constraint objects in future architecture work.
2. Keep them separate from raw entitlement and role hierarchy models.
3. Add an explicit evidence model for obligation satisfaction.
4. Treat SoD, approvals, retention, attestations, and exception paths as obligation patterns.
5. Evaluate future IAM/control architectures on whether they can explain admissibility, not merely access.
