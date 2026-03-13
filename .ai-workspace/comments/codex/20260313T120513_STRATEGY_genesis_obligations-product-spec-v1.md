# STRATEGY: Genesis Obligations product specification v1

**Author**: Dimitar Popov
**Date**: 2026-03-13T12:05:13+11:00
**Addresses**: clean-room Genesis project specification for a global regulatory obligation intelligence and constraint-mapping system
**For**: all

## Summary
`genesis_obligations` should be specified as a global obligation intelligence system for regulated institutions. Its purpose is not merely to store laws and policies, but to determine what they mean for the institution given its real activity footprint, precedent, and governance posture.

The first-rank problem is exteroceptive: the institution must ingest and maintain external obligations across jurisdictions and domains. But those sources are not directly executable. They must pass through an explicit `Assumptions & Interpretations` stage constrained by the institution's known corporate activity universe. The resulting normalized obligations can then be intersected against concrete internal activities such as trading exotic products in EMEA or energy trading in Texas.

## Product Name
`genesis_obligations`

## Product Purpose
`genesis_obligations` answers this question:

**Given what the institution actually does, what obligations apply, why do they apply, what evidence is required, and where are we exposed?**

The product exists to provide a durable, explainable constraint system for:
- global regulation
- corporate governance requirements
- internal policy
- control obligations
- evidentiary expectations
- exception and precedent management

## Problem Statement
A global institution is subject to overlapping obligations across many dimensions:
- taxation
- financial regulation
- market conduct
- AML / KYC
- sanctions
- privacy
- data residency
- HR / employment
- record retention
- cyber and operational resilience
- outsourcing and vendor management
- internal governance and supervisory commitments

The institution does not need only a library of source documents. It needs a system that can:
- ingest and version those sources
- interpret them in institutional context
- relate them to the institution's actual activities
- compute effective obligations for concrete actions
- identify control, evidence, and gap implications
- track precedent and change over time

## Core Product Thesis
The governing model is not:
- source text alone
- role hierarchy alone
- policy documents alone

The governing model is the intersection of four things:
1. `External Source Corpus`
2. `Corporate Activity Universe`
3. `Assumptions & Interpretations Ledger`
4. `Normalized Obligations and Evidence Requirements`

A source creates regulatory exposure only through the institution's activity footprint and interpretive posture.

## Foundational Assets
The product should be built around three first-rank assets and one derived asset.

### 1. External Source Corpus
The full corpus of exteroceptive inputs.

Includes:
- laws
- regulations
- rules
- guidance
- supervisory communications
- standards
- tax bulletins
- HR and employment rules
- internal policies and control standards

Each source must preserve:
- provenance
- jurisdiction
- effective dates
- supersession chain
- source structure and references
- change history

### 2. Corporate Activity Universe
A maintained model of what the institution actually does.

Includes:
- legal entities
- jurisdictions and regions
- business lines
- product categories
- instruments and commodity classes
- client and counterparty types
- employee populations
- processes and lifecycle stages
- systems and data flows
- control domains

This asset constrains regulatory exposure. It defines where the external source corpus can intersect with reality.

### 3. Assumptions & Interpretations Ledger
A first-class institutional interpretation layer.

This is the critical stage between source and obligation.

It records:
- source intent
- corporate governance intent
- institutional assumptions
- interpretive decisions
- ambiguity notes
- precedent references
- chosen scope decisions
- stricter-than-minimum governance choices
- reviewer / approver identity
- validity period and supersession

### 4. Derived Normalized Obligations
These are the structured obligations the institution actually operates against.

They are derived from:
- source corpus
- activity universe
- assumptions and interpretations
- precedent
- governance posture

They are not the raw law. They are the institution's normalized operational obligation objects.

## Primary Users
- regulatory change teams
- legal and policy teams
- compliance and control owners
- tax teams
- HR policy and employment governance teams
- product and business governance teams
- operations and risk teams
- audit and assurance functions
- internal systems that need machine-readable obligation decisions

## Core Questions the Product Must Answer
1. What obligations exist in the external environment?
2. What do they mean for this institution given what it actually does?
3. Which obligations apply to a specific internal activity?
4. Why does each obligation apply?
5. What assumptions, interpretations, and precedents were used?
6. What controls, approvals, or evidence are required?
7. Where are obligations unsatisfied, conflicting, or unmapped?
8. What changed, and what activities or controls are impacted?

## Core Domain Model

### SourceDocument
Represents an external or internal source.

Minimum fields:
- source_id
- source_type
- issuer
- jurisdiction
- legal scope
- publication_date
- effective_date
- supersedes / superseded_by
- citation structure
- provenance
- raw text / structured import reference

### ActivitySignature
Represents a concrete internal activity point in the corporate activity universe.

Examples:
- trading exotic financial products in EMEA
- energy trading in Texas
- hiring employees in Germany
- processing payroll in Singapore
- transferring regulated data from UK to US

Minimum fields:
- activity_type
- legal_entity
- business_line
- jurisdiction / region
- product_class
- instrument_or_asset_class
- client_or_counterparty_type
- lifecycle_stage
- booking_location
- actor_location
- data_classes_involved
- channel / venue
- time context

### InterpretationCase
Represents an institutional interpretation of source material in context.

Minimum fields:
- interpretation_id
- source references
- source intent
- corporate governance intent
- relevant activity scope
- assumptions
- ambiguity notes
- precedent references
- interpretive decision
- reviewer / approver
- valid_from / valid_to
- resulting obligation references

### Assumption
Represents an explicit institutional assumption used in interpretation.

Examples:
- product category mapping
- jurisdictional scope inference
- stricter internal posture choice
- control boundary assumption

### Precedent
Represents prior institutional or supervisory interpretation precedent.

Includes:
- legal opinions
- prior internal rulings
- historical control decisions
- audit findings
- supervisory outcomes

### NormalizedObligation
Represents the institution's structured obligation object.

Minimum fields:
- obligation_id
- source lineage
- interpretation lineage
- jurisdiction scope
- entity scope
- product scope
- process scope
- modality: must / must_not / must_review / must_notify / must_retain / must_attest / must_segregate / must_record
- timing: precondition / in-flight / postcondition / periodic
- evidence requirements
- exception model
- severity / criticality
- effective dates

### ControlMapping
Maps obligations to internal controls, procedures, systems, approvals, or evidentiary artifacts.

### ObligationAssessment
Represents the evaluated result for a concrete activity signature.

Must include:
- applicable obligations
- non-applicable but nearby obligations when useful
- blocking obligations
- satisfied obligations
- unsatisfied obligations
- missing evidence
- required approvals
- conflicts or overlaps
- rationale and traceability

## Product Principles
- Source provenance is mandatory.
- Interpretations are first-class and never implicit.
- Corporate activity constrains exposure.
- Obligations are derived, not invented ad hoc.
- Every effective obligation must be explainable.
- Every assessment must be traceable to source, interpretation, and activity context.
- Change must be versioned and auditable.
- Conflicts and ambiguity must remain visible, not collapsed silently.

## Capability Areas

### 1. Exteroceptive Source Ingestion
The system must ingest and preserve source documents from external and internal environments.

Includes:
- ingestion pipelines
- provenance capture
- effective dating
- source versioning
- supersession handling
- structured and unstructured input support

### 2. Corporate Activity Modeling
The system must maintain a modeled representation of institutional activities.

Includes:
- regional and jurisdictional presence
- legal entities
- product and service taxonomy
- business processes
- lifecycle stages
- employee and client/counterparty categories
- data and system context

### 3. Assumptions & Interpretations
This is the first-rank interpretive layer.

The system must support:
- explicit interpretation cases
- assumption recording
- ambiguity handling
- precedent referencing
- corporate governance posture expression
- review and approval of interpretations
- supersession of outdated interpretations

### 4. Obligation Normalization
The system must derive structured obligations from:
- source material
- activity universe
- interpretation cases
- precedent
- governance posture

### 5. Applicability and Intersection
The system must compute the effective obligation set for a given activity signature.

Includes:
- applicability reasoning
- overlap and redundancy analysis
- conflict detection
- stricter-versus-weaker constraint reasoning
- jurisdiction and product interaction logic

### 6. Control and Evidence Mapping
The system must map obligations to internal controls and evidence.

Includes:
- policy mappings
- procedure mappings
- approval mappings
- attestation mappings
- record-retention mappings
- system-control mappings
- evidence gap detection

### 7. Change Impact Analysis
The system must detect what changed and what is impacted.

Includes:
- source change detection
- interpretation invalidation
- affected activities
- affected controls
- affected evidence requirements
- pending reassessment queue

### 8. Governance and Review
The system must support human review over:
- interpretation cases
- normalization outcomes
- obligation conflicts
- exception paths
- control sufficiency

### 9. Query and API Access
The system must support both human and machine queries.

Examples:
- what applies to trading exotic derivatives in EMEA?
- what applies to energy trading in Texas?
- what changed for payroll obligations in APAC this quarter?
- which obligations for client onboarding lack mapped controls?

## Functional Requirements
- `REQ-F-SRC-001`: ingest external and internal source documents with provenance and versioning
- `REQ-F-SRC-002`: preserve supersession and effective-date chains for source material
- `REQ-F-ACT-001`: model the corporate activity universe across regions, entities, products, processes, and data domains
- `REQ-F-ACT-002`: represent concrete activity signatures for obligation assessment
- `REQ-F-INT-001`: create and maintain interpretation cases tied to source material and activity scope
- `REQ-F-INT-002`: record explicit assumptions, ambiguity notes, and precedent references
- `REQ-F-INT-003`: capture source intent and corporate governance intent separately
- `REQ-F-OBL-001`: derive normalized obligations from source, activity, and interpretation inputs
- `REQ-F-OBL-002`: preserve traceability from normalized obligations back to source and interpretation lineage
- `REQ-F-APL-001`: compute applicability of obligations to a concrete activity signature
- `REQ-F-APL-002`: explain why each obligation applies or does not apply
- `REQ-F-INTX-001`: determine the intersection of overlapping obligations across jurisdictions, entities, and product categories
- `REQ-F-INTX-002`: identify conflicts, stricter constraints, and exception paths where relevant
- `REQ-F-CTL-001`: map obligations to internal controls, procedures, approvals, and evidence artifacts
- `REQ-F-GAP-001`: identify unsatisfied, unmapped, or weakly evidenced obligations
- `REQ-F-CHG-001`: detect source or interpretation changes and compute impacted activities and controls
- `REQ-F-GOV-001`: support review and approval workflows for interpretations and obligation decisions
- `REQ-F-QRY-001`: provide human-readable query surfaces for obligation and impact questions
- `REQ-F-API-001`: provide machine-readable APIs for effective obligation assessment

## Non-Functional Requirements
- full auditability
- immutable history for source, interpretation, and obligation lineage
- temporal correctness
- jurisdictional precision
- explainability of assessments
- deterministic projection from source + interpretation + activity inputs
- support for ambiguity without forced false precision
- support for large, multi-domain taxonomies
- support for cross-region and cross-category overlap
- no silent change to obligation meaning or scope

## Information Architecture
A first usable product should likely expose:
- `Sources`
- `Activity Universe`
- `Interpretations`
- `Obligations`
- `Assessments`
- `Controls & Evidence`
- `Changes & Impact`
- `Governance Queue`

Each should have canonical detail pages and drill-through.

## Primary Workflow
1. ingest or update a source
2. classify source scope
3. review against corporate activity universe
4. create or update interpretation case
5. derive normalized obligations
6. assess applicability to targeted activity signatures
7. map to controls and evidence
8. flag gaps, conflicts, and changes
9. review and approve where required

## MVP Scope
The MVP should prove the model, not boil the ocean.

### MVP slice
- one or two regulatory domains
- limited but real regional coverage
- a small but concrete activity taxonomy
- explicit interpretation ledger
- one assessment engine path
- one control/evidence mapping path

### MVP demonstration
Given an activity signature such as:
- `trading exotic financial products in EMEA`
- `energy trading in Texas`

The system should be able to answer:
- which obligations apply
- why they apply
- which assumptions and precedents were used
- which obligations are blockers or require approval
- what evidence is required
- what internal controls map to those obligations
- which gaps remain

## Future Extensions
- broader regulatory source coverage
- richer precedent mining
- cross-jurisdiction conflict resolution support
- automated control sufficiency suggestions
- continuous exteroceptive change monitoring
- enterprise APIs for workflow gating and decision support
- integration with policy, control, and assurance platforms

## Project Boundaries
This project is not initially:
- a general document repository
- a pure legal research tool
- a generic compliance dashboard
- an entitlement system

It is specifically:
- an interpretive obligation intelligence system
- grounded in corporate activity
- designed to compute effective obligations and exposure

## Recommended Action
1. Ratify `genesis_obligations` as the project framing.
2. Translate this into project artifacts: `INTENT.md`, `REQUIREMENTS.md`, and an initial `FEATURE_VECTORS.md`.
3. Make `Assumptions & Interpretations` a first-class asset in the project graph rather than a note attached to obligations.
4. Make `Corporate Activity Universe` a first-rank modeled asset alongside external source ingestion.
5. Define the first MVP around one concrete activity-signature assessment flow to prove the architecture.
