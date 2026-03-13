# STRATEGY: Best-of-breed entitlement architecture for a global financial institution

**Author**: codex
**Date**: 2026-03-13T11:13:43+11:00
**Addresses**: future reference architecture for entitlement systems in highly regulated, wall-constrained financial institutions
**For**: all

## Summary
In a global financial institution, a practical entitlement architecture is usually not a single hierarchy of users, groups, roles, and entitlements. The scalable shape is a layered control model:
- strict visibility walls for protected assets
- scoped functional privileges within allowed domains
- entitlement/provisioning automation underneath
- separate governance, runtime policy, PAM, and data-governance layers

This is the main reason large entitlement estates become unmanageable when modeled as one inheritance graph. At scale, raw entitlements are machine-layer atoms. Humans should govern walls, capability bundles, policy, and exceptions.

## The Core Split
The institution described has two different control problems:

1. **Visibility control**
   - who may even know an asset exists
   - who may view books, deals, clients, projects, datasets, investigations, or regions
   - where legal or regulatory walls must be absolute

2. **Functional control**
   - what actions a subject may perform once inside an allowed domain
   - approve, reconcile, operate, review, release, administer, investigate, or modify

These should not be modeled as one unified role graph.

The practical decision function is:

```text
allow(subject, action, asset) =
  visibility_wall(subject, asset)
  AND functional_capability(subject, action, domain(asset))
  AND policy(subject, action, asset, context)
```

That is the right mental model for a bank.

## Why Role Hierarchies Break Down
A single inheritance tree usually becomes unworkable because it mixes:
- group membership
- information barriers
- business function
- application-native entitlements
- exception handling
- segregation of duties
- privileged access

That creates a graph where:
- walls leak through convenience inheritance
- roles become too coarse or too numerous
- recertification becomes unreadable
- exceptions become permanent structure
- engineers cannot explain effective access cleanly

At large scale, manual maintenance fails unless the system is mostly automated.

## Best-of-Breed Layering
The best practical architectures usually separate concerns into distinct systems.

### 1. IGA / lifecycle governance
Purpose:
- access requests
- approvals
- joiner/mover/leaver
- certification / recertification
- provisioning orchestration
- entitlement catalog and role bundles

Representative products:
- SailPoint
- Saviynt

This is where entitlement sprawl gets cataloged and governed. It should not be the only runtime decision engine.

### 2. Visibility wall / information barrier control
Purpose:
- enforce hard walls around protected assets and collaboration boundaries
- prevent visibility across incompatible segments
- preserve regulatory separation

Representative patterns/products:
- Microsoft Purview Information Barriers for Microsoft-heavy estates
- policy engines using ABAC / PBAC over asset classification and subject attributes

This layer should decide whether the subject may see the asset at all.

### 3. Runtime authorization / policy decision layer
Purpose:
- evaluate dynamic access at request time
- combine domain role, asset class, context, location, business unit, jurisdiction, SoD, and exception state
- keep application runtime authorization out of static entitlement explosion

Representative products/patterns:
- PlainID
- Axiomatics
- OPA / Cerbos / AWS Verified Permissions as policy-engine patterns

This layer is what usually saves institutions from encoding every runtime rule as a static role.

### 4. PAM layer
Purpose:
- privileged access
- admin elevation
- session control
- break-glass and audited elevation

Representative products:
- CyberArk

This should remain separate from ordinary business functional roles.

### 5. Data access governance layer
Purpose:
- fine-grained governance over analytics platforms, data estates, and data products
- policy-driven access by data classification, purpose, region, and control domain

Representative products:
- Immuta

In many institutions, this is where the most difficult access problems really live.

## The Practical Modeling Rule
The sane model is:
- `groups` define visibility domains or assignment sets
- `roles` define functional capability bundles inside scope
- `entitlements` are leaf grants generated underneath
- `policy` resolves dynamic context and exception cases
- `PAM` handles elevated privilege separately

That means humans review and request:
- wall membership
- business capability bundles
- scoped role assignments
- exceptions with expiry

while automation handles:
- entitlement expansion
- provisioning
- revocation
- certification support
- drift detection
- SoD checks

## What Should Be Human-Managed
Humans are good at:
- deciding who belongs behind a wall
- deciding which business function a person should perform in a domain
- approving exceptions
- reviewing risk
- attesting access at a business level

Humans are bad at:
- manually reviewing thousands of raw entitlement atoms
- reasoning about deep inheritance graphs
- understanding app-native leaf grants across many systems

So the human review surface should be bundles, policies, and exceptions, not the raw entitlement universe.

## What Automation Must Do
A practical architecture needs automation for:
- entitlement normalization
- bundle expansion
- scoped-template instantiation
- joiner/mover/leaver changes
- certification preparation
- drift detection
- role mining / clustering assistance
- exception expiry and cleanup

Without this, the model becomes an ever-growing manual maintenance burden.

## The Key Design Move: Scoped Bundles
Instead of static role explosion, the more scalable pattern is parameterized access.

Examples:
- `ProjectContributor(project=X)`
- `ResearchReviewer(domain=Rates, region=EU)`
- `ReleaseApprover(platform=Payments, env=Prod)`

Those expand into the underlying entitlements and policies.

This is much cleaner than trying to predefine every possible composite role in a global hierarchy.

## Recommended Reference Architecture
For an institution already deep in SailPoint, the most pragmatic target state usually looks like:

1. `SailPoint` remains the IGA / governance and provisioning plane
2. `Visibility walls` are enforced by a dedicated policy / information-barrier layer
3. `Functional runtime authorization` moves into a policy decision engine instead of static role explosion
4. `CyberArk`-style PAM handles privileged/elevated workflows separately
5. `Immuta`-style data governance handles fine-grained data access where needed
6. The full system is evented, automated, and explainable through effective-access projections

That is much more realistic than trying to make one hierarchy solve everything.

## What “Best of Breed” Means Here
It does not mean “buy the most features from one vendor.”

It means:
- best system for governance
- best system for walls
- best system for runtime policy
- best system for PAM
- best system for data controls
- clear integration boundaries between them

That layered model is what usually survives scale, regulation, and audit.

## Evaluation Criteria
A serious future evaluation should compare solutions on:
- ability to enforce absolute visibility walls
- ability to model scoped functional privileges cleanly
- explainability of effective access
- automation of entitlement expansion and certification support
- SoD support
- exception governance with expiry
- runtime policy expressiveness
- integration burden with existing SailPoint estates
- auditability and operational maintainability

## Position
For a global financial institution, the correct architecture is not a giant inherited role tree.

It is:
- a visibility lattice
- plus scoped functional RBAC
- plus dynamic policy
- plus PAM
- plus automated entitlement expansion underneath

That is the closest practical shape to the real control problem.

## Recommended Action
1. Treat visibility walls and functional privileges as separate first-class concerns.
2. Keep raw entitlements as machine-layer artifacts, not human review units.
3. Preserve or use SailPoint as the governance plane rather than forcing it to become the entire runtime authorization model.
4. Introduce a dedicated runtime policy layer for walling and contextual authorization.
5. Design the target state around automation, explainability, and exception governance rather than deeper inheritance.
