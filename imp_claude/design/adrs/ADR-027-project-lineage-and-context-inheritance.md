# ADR-027: Project Lineage and Context Inheritance

**Status**: Accepted
**Date**: 2026-03-07
**Deciders**: Methodology Author
**Requirements**: REQ-CTX-001 (Context as Constraint Surface), REQ-CTX-002 (Context Hierarchy), REQ-TOOL-011 (Installability), REQ-LIFE-001 (CI/CD as Graph Edge)
**Extends**: ADR-026 (Minimal Installer Footprint), ADR-010 (Spec Reproducibility)
**Supersedes**: ADR-026 §1 (installer footprint — extended, not replaced)

---

## Context

ADR-026 defined the minimal installer footprint: three operations (settings.json, events.jsonl touch, bootloader injection). This was correct as far as it went.

But it left open a deeper question: **what does a project inherit at the moment of its inception?**

### The Abiogenesis Problem

A project created with genesis is not a blank slate that acquires methodology over time. It is born into a context — a lineage of prior decisions, constraints, and knowledge that existed before the project did. That lineage shapes what the project can do, what it must comply with, and what it already knows.

Currently, this lineage is implicit:
- The developer knows their organisation uses Python and Kubernetes
- They know their company has a security policy
- They know there was a prior system they are replacing
- They know the genesis methodology itself has a version

None of this is wired. The project starts with an empty `project_constraints.yml` and the developer fills it in from memory. The nervous system — the monitors, the feedback loops, the observability infrastructure — is added later, project by project, as an afterthought.

This is wrong. **Observability is constitutive, not optional** (bootloader §XV). The nervous system must be present at the moment of abiogenesis. And the context that shapes the project's constraints must be traceable to its source — not reconstructed from memory.

### CI/CD and Running System are Contextual

ADR-026's backlog item "CI/CD integration" was a misclassification. CI/CD and Running System are not things the methodology builds for itself — they are graph nodes whose content is entirely parameterised by the target project's technology stack. A Python service's CI/CD is GitHub Actions + pytest. A Rust library's CI/CD is `cargo test` + `cargo publish`. The methodology defines the shape of those nodes and their convergence criteria; the implementation is always domain-specific.

The corollary: **the CI/CD and telemetry nodes, and the feedback loop from Running System back to Intent, should be wired into the graph topology from day one** — not as implemented functionality, but as declared edges that the project knows it must eventually converge.

### Context[] is a Lineage DAG, Not a Flat File

The `iterate()` function takes `Context[]` as its constraint surface:

```
iterate(Asset<Tn>, Context[], Evaluators) → Asset<Tn.k+1>
```

Currently `Context[]` is effectively `[project_constraints.yml, edge_params/{edge}.yml]` — a flat list of two files. But the real constraint surface of any project is a directed acyclic graph of prior context, each node contributing constraints that are inherited, composed, and overridden as the DAG is traversed.

```
Genesis Methodology          (live — axiom set, bootloader version)
    ↓
Org Architectural ADRs       (live — technology standards, platform choices)
    ↓
Corporate Policy             (live — security, compliance, data governance)
    ↓
Domain Knowledge             (static — prior system docs, domain ontology, historical decisions)
    ↓
Prior State                  (static — prior project version, related projects)
    ↓
THIS PROJECT                 (owned — project_constraints.yml, design/adrs/, spec/)
```

---

## Decision

### 1. Two Lineage Types

Every context source in the lineage DAG is typed as **live** or **static**:

| Type | Definition | Behaviour at Install | Behaviour at Update |
|------|-----------|---------------------|-------------------|
| **Live** | Source that evolves independently and whose updates are relevant to this project | Referenced by URI + version pin. Content not copied. | `gen-update` fetches new version, diffs context, presents changes for human review before adoption |
| **Static** | Source that is snapshotted at inception — its content is sealed | Content copied into `.ai-workspace/context/{scope}/`. SHA-256 hash recorded in `context_manifest.yml`. | Immutable. Re-snapshot only on explicit `gen-init --re-snapshot` |

Live sources include:
- The genesis methodology itself (bootloader version, graph topology)
- Organisation-level architectural ADRs (language, platform, deployment target)
- Corporate compliance/security policy

Static sources include:
- Prior system documentation (the system this project replaces or extends)
- Domain ontology and terminology glossaries
- Historical decisions and post-mortems
- Snapshots of related projects at the moment of inception

### 2. The Lineage Declaration

Every project declares its lineage in `project_constraints.yml` under `context_sources`. This field — currently present but empty — becomes load-bearing:

```yaml
context_sources:
  # Live sources — referenced, not copied
  - uri: "https://github.com/org/genesis-methodology"
    scope: methodology
    type: live
    version: "3.0.0"
    description: "Genesis methodology axiom set and graph topology"

  - uri: "/org/standards/architectural-adrs/"
    scope: adrs
    type: live
    version: "2026-Q1"
    description: "Org-wide technology choices: Python 3.12, Kubernetes, PostgreSQL"

  - uri: "/corp/policy/security-compliance/"
    scope: policy
    type: live
    version: "2026-01-15"
    description: "Corporate security and data governance requirements"

  # Static sources — snapshotted at inception
  - uri: "/projects/legacy-system/docs/"
    scope: domain
    type: static
    snapshotted_at: "2026-03-07T00:00:00Z"
    content_hash: "sha256:a1b2c3..."
    description: "Prior system documentation — read-only domain knowledge"

  - uri: "/projects/related-service/specification/"
    scope: prior_state
    type: static
    snapshotted_at: "2026-03-07T00:00:00Z"
    content_hash: "sha256:d4e5f6..."
    description: "Related service spec at moment of this project's inception"
```

### 3. Lineage Scope → Context Directory Mapping

Each source maps to a subdirectory of `.ai-workspace/context/`:

| Scope | Directory | Content |
|-------|-----------|---------|
| `methodology` | `.ai-workspace/context/methodology/` | Bootloader, graph topology, profiles |
| `adrs` | `.ai-workspace/context/adrs/` | Org-level architectural decisions |
| `policy` | `.ai-workspace/context/policy/` | Compliance, security, governance |
| `domain` | `.ai-workspace/context/domain/` | Domain knowledge, prior system docs |
| `prior_state` | `.ai-workspace/context/prior_state/` | Related project specs and state |
| `project` | `.ai-workspace/context/project/` | Owned — project_constraints.yml, project ADRs |

The `load_context_hierarchy()` function (REQ-CTX-002, config_loader.py) resolves these in order: methodology → adrs → policy → domain → prior_state → project. Later overrides earlier.

### 4. The Nervous System is Inherited, Not Configured

The observability infrastructure — interoceptive monitors, event log, feedback loop — is not configured project-by-project. It cascades down the lineage:

- **Methodology lineage** provides: base interoceptive monitors (test health, coverage, event freshness, feature staleness), the standard graph topology with Telemetry → Intent edge wired
- **Org ADR lineage** provides: platform-specific monitors (build health for the org's CI system, deployment health checks for the org's platform)
- **Policy lineage** provides: compliance monitors (security scanner thresholds, data governance checks)
- **Project** adds: project-specific thresholds and overrides

At install, the inherited monitors are active immediately. The project does not need to configure observability — it inherits a nervous system calibrated to its stack.

### 5. Extended Installer Contract

ADR-026's three operations are preserved. The installer is extended with two additional operations that occur during `gen-start` UNINITIALISED handling (not the installer itself — consistent with ADR-026's lazy scaffolding principle):

```
ADR-026 (installer, immediate):
  1. Write .claude/settings.json
  2. Touch .ai-workspace/events/events.jsonl
  3. Append GENESIS_BOOTLOADER to CLAUDE.md

ADR-027 (gen-start UNINITIALISED, lazy):
  4. Resolve context_sources declared in project_constraints.yml
     - Live sources: record URI + version, do not copy
     - Static sources: copy content to .ai-workspace/context/{scope}/, hash, record in context_manifest.yml
  5. Instantiate design tenant:
     - Create design/adrs/ with Tier 1 governance ADRs (methodology-standard, language-agnostic)
     - Generate Tier 2 ecosystem ADRs from constraint prompting answers (technology-bound)
     - Wire project_constraints.yml $variable references to the generated ADRs
  6. Activate inherited monitors from lineage
     - Write .ai-workspace/monitors/ configs inherited from methodology + org + policy scopes
     - Override thresholds from project-level constraints
  7. Emit project_initialized event with lineage provenance:
     { live_sources: [...], static_sources: [...], context_hash: "sha256:..." }
```

### 6. Tier 1 and Tier 2 Design ADRs

Every project's design tenant begins with two tiers of ADRs:

**Tier 1 — Governance ADRs (language-agnostic, shipped with methodology)**

| ADR | Title | Content |
|-----|-------|---------|
| ADR-G-001 | Spec/Design Boundary | The project's spec is tech-agnostic; design ADRs are technology-bound |
| ADR-G-002 | Feature Vector Format | REQ key convention, trajectory structure, vector types |
| ADR-G-003 | Convergence Contract | What "done" means per edge; evaluator passing criteria |
| ADR-G-004 | Event Log Contract | events.jsonl schema, append-only invariant, projection semantics |
| ADR-G-005 | Observability Contract | The project monitors itself; monitors are constitutive, not optional |

**Tier 2 — Ecosystem ADRs (generated from constraint prompting)**

| ADR | Title | Populated From |
|-----|-------|---------------|
| ADR-E-001 | Language & Runtime | ecosystem_compatibility dimension |
| ADR-E-002 | Test Framework | tools.test_runner in project_constraints.yml |
| ADR-E-003 | Linter & Formatter | tools.linter, tools.formatter |
| ADR-E-004 | Deployment Target | deployment_target dimension |
| ADR-E-005 | Security Model | security_model dimension |
| ADR-E-006 | Build System | build_system dimension |

Tier 2 ADRs are generated at `gen-start` Step 2 (Deferred Constraint Prompting, REQ-UX-002) when the first feature reaches the `requirements→design` edge. The same information that populates `project_constraints.yml` simultaneously materialises as ADRs — the human-readable durable record of the decision.

### 7. Provenance in Every Event

The `project_initialized` event carries the full lineage declaration. Every subsequent `iteration_completed` event carries the `context_hash` (from `context_manifest.yml`) that captures which version of the lineage was active during that iteration. This means:

- Any iteration can be reproduced: given the event's `context_hash`, recover the exact context state
- Lineage changes are visible in the event log: a context update produces a new `context_hash`
- Compliance audits can trace any design decision back through the lineage to its source policy

### 8. The Telemetry → Intent Edge is Wired from Day One

The full graph topology — including `Running System → Telemetry → Intent` — is present in `graph_topology.yml` from installation. The CI/CD and Running System nodes are parameterised by the project's technology stack (their evaluator configs reference `$tools.*` variables), but the edges exist.

This means the project knows, from day one, that:
- It will eventually deploy to a running system
- That system will emit telemetry
- Telemetry will be observed and delta-computed against the spec
- Non-zero deltas become new intents — closing the homeostatic loop

The project does not add observability when it "gets to production." Observability is the final edge of the graph the project was born knowing it must traverse.

---

## Consequences

### Positive

- **Projects are born alive**: the nervous system is present at inception, not retrofitted later
- **Lineage is explicit and traceable**: every constraint knows where it came from
- **Observability cascades from the methodology**: project teams don't configure monitoring — they inherit it, override thresholds, add project-specific sensors
- **Static lineage enables spec reproducibility**: content-addressed snapshots mean any prior project state can be recovered exactly
- **Live lineage enables policy propagation**: a security policy update propagates to all child projects through their live lineage subscription
- **CI/CD and Running System are never forgotten**: they're in the topology from day one, pending traversal

### Negative

- **Lineage declaration adds install-time complexity**: the developer must know their context sources at project inception. Unknown sources can be added later but the initial lineage may be incomplete.
- **Live source resolution requires network access** at context update time (not at install — URIs are recorded, not fetched)
- **Static snapshot size**: domain knowledge can be large. The context directory may grow significantly for knowledge-heavy projects.

### Neutral

- `load_context_hierarchy()` (config_loader.py, REQ-CTX-002) already implements the merge semantics. This ADR defines what sources feed into that function, not how the merge works.
- ADR-026's three-operation installer is unchanged. The lineage resolution is lazy (gen-start UNINITIALISED), consistent with ADR-026's philosophy.

---

## Relationship to the Formal System

This ADR is a direct expression of two principles in the bootloader:

**Context is a constraint surface (§III)**:
> "Spec + Context: Constraint surface — what bounds construction"

The lineage DAG is the full constraint surface of the project. `project_constraints.yml` alone is only the owned layer — the bottom of the DAG. The effective constraint surface is the DAG collapsed.

**Observability is constitutive (§XV)**:
> "A product that does not monitor itself is incomplete. The event log, sensory monitors, and feedback loop are methodology constraints, not tooling features. This applies recursively — the methodology tooling is itself a product."

The inherited nervous system is the consequence of this invariant applied at install time. If the system is constitutively observable, it must be observable from the first moment it exists — not from the moment the team decides to add monitoring.

**Abiogenesis (§VIII)**:
> "Human intent is the abiogenesis — the initial spark that creates the spec and bootstraps the constraint surface. Once the system has a specification and sensory monitors, it becomes self-sustaining."

The lineage declaration at project inception is the abiogenesis act. The human provides the initial intent and declares the lineage. Everything else — monitors, feedback loops, constraint resolution, homeostasis — emerges from those constraints.

---

## References

- ADR-026: Minimal Installer Footprint (extended by this ADR)
- ADR-010: Spec Reproducibility (content-addressable context manifest)
- ADR-012: Two-Command UX (gen-start UNINITIALISED state, constraint prompting Step 2)
- REQ-CTX-001: Context as Constraint Surface
- REQ-CTX-002: Context Hierarchy (load_context_hierarchy() — the merge function)
- REQ-LIFE-001: CI/CD as Graph Edge (topology wired from day one)
- REQ-TOOL-011: Installability
- REQ-UX-002: Progressive Disclosure (Tier 2 ADRs generated at design edge, not at install)
- `imp_claude/code/genesis/config_loader.py`: deep_merge(), load_context_hierarchy()
- `imp_claude/code/.claude-plugin/plugins/genesis/config/project_constraints_template.yml`: context_sources field
- Genesis Bootloader §III, §VIII, §XV
