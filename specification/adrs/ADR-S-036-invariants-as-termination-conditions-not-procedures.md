# ADR-S-036: Invariants as Termination Conditions, Not Procedures

**Status**: Ratified
**Date**: 2026-03-12
**Revised**: 2026-03-14 (adds invariant primes and terminal manifestations — proposed by Codex, ratified by human principal)
**Deciders**: Jim (human principal)
**Tags**: methodology-core, invariants, path-independence, agent-capability, conformance, ontology

---

## Context

The Genesis methodology defines a set of invariants that must hold for a workspace to be considered
valid: REQ key traceability from spec to code to tests, feature vectors in correct format, events
emitted, gaps validated, convergence documented. As the methodology has been applied across projects,
a question has emerged:

**Does the methodology prescribe the path to satisfying these invariants, or only the invariants
themselves?**

This question has practical consequences. During genesis_navigator construction (March 2026), all 13
features were built in two passes:

- **Pass 1**: F_P construction — code, tests, and features converged (iter=1 on every edge).
- **Pass 2**: F_D assurance — workspace artifacts brought into compliance: feature YAML restructured,
  STATUS.md written, gaps validated, proposals drafted.

The system was correct after Pass 1. The invariants were satisfied after Pass 2. Pass 2 was not
re-work — it was the assurance path closing. The question is whether this two-pass pattern is
a methodology violation, a methodology concession, or a methodology-correct outcome.

---

## Decision

**The Genesis methodology prescribes invariants as termination conditions, not procedures.**

The path to satisfying the invariants is unconstrained. Any path that arrives at a state where all
required invariants hold is a valid execution. The F_D evaluation layer checks whether invariants
hold — it does not check how they came to hold.

This is a direct consequence of the Constraint-Emergence principle (Bootloader §II): constraints
restrict which final states are admissible, not which transformations must occur. The methodology
fills its possibility space — it does not mandate a single path through it.

---

## Rationale

### 1. Path-independence is already an invariant

Bootloader §XI states: *"A stable asset must be reconstructable from the event stream alone,
independent of the execution path that produced it."* This applies to the methodology itself. Two
conformant executions that produce equivalent artifacts are equivalent — regardless of how many
passes, sub-steps, or orderings they used.

### 2. Procedure-prescription is the wrong layer

Procedures are implementation details of an agent's capability at a given point in time. A less
capable agent may need 5 passes to satisfy the invariants. A more capable agent may satisfy them
in 1. The methodology must not encode agent-capability limitations as structural requirements —
doing so would make the methodology regress as agents improve.

The correct layer for procedure is the **profile** (standard, hotfix, spike, etc.) — which
configures how many edges to traverse and in what order. Profiles are projections of the graph,
not prescriptions of the path within an edge.

### 3. The two-pass pattern is methodology-correct

The genesis_navigator two-pass build is a valid execution:
- Pass 1 satisfied the construction invariants (code exists, tests pass, features converged).
- Pass 2 satisfied the traceability invariants (REQ keys threaded, workspace formatted, gaps
  validated).

Both invariant sets are required. Neither pass alone is sufficient. Together they produce a
valid workspace. The order — construction before traceability — was the optimal path for the
agent at hand. A different agent might interleave construction and traceability at each feature.
Both are valid.

### 4. Assurance is not remediation

The second pass was not fixing errors from the first pass. The code was correct. The tests passed.
The assurance pass was closing the evidence trail — the artifact layer that makes correctness
visible and machine-readable. This distinction matters: assurance creates the sensor; it does not
repair the system.

The methodology's traceability invariants exist so that future agents (and humans) can verify
correctness without re-running the construction. The artifacts are the proof of work, not the
work itself.

### 5. Framework evolution trajectory

As agent capability increases, the two-pass pattern should collapse:

| Agent capability | Expected path |
|-----------------|---------------|
| Current (2026) | 2 passes — construct, then assure |
| Near-term | Interleaved — assure each feature as it converges |
| Mature | 1 pass — invariants satisfied inline during construction |

The methodology does not change as agents improve. Only the path changes. The F_D gate remains
the same check regardless of which pass produced the artifacts.

---

## Consequences

### Positive

- **Agent freedom**: Agents may use the most efficient path available to them. The methodology
  does not impose unnecessary ordering constraints.
- **Scalable to capability**: As agents improve, the framework naturally accommodates more
  efficient execution without requiring spec changes.
- **Correct incentive**: Agents are incentivised to satisfy invariants, not to perform theatre.
  A two-pass execution that produces correct artifacts is preferred over a one-pass execution
  that produces incomplete artifacts.
- **Assurance clarity**: The purpose of the assurance pass is explicit — it closes the evidence
  trail, it does not fix construction errors.

### Negative / Constraints

- **All invariants remain mandatory**: Path freedom does not mean invariant freedom. Every
  required invariant must be satisfied before the workspace is considered valid. Partial
  compliance is not valid compliance.
- **Evidence must be accurate**: The assurance artifacts must accurately reflect the construction
  that occurred. Fabricated traceability (tagging code with REQ keys that don't match what was
  built) violates the traceability invariant even if the format is correct.
- **F_H gate timing**: Invariants that require human approval (F_H evaluators) must be satisfied
  before downstream edges that depend on them proceed. The ordering constraint comes from the
  graph topology, not from procedure prescription.

---

## The Invariant Set (non-negotiable termination conditions)

Regardless of path, a valid Genesis workspace at convergence must satisfy:

| Invariant | What must hold |
|-----------|---------------|
| **Code exists** | All features have production code implementing their REQ keys |
| **Tests pass** | All unit and integration tests green |
| **REQ threading** | `# Implements: REQ-*` in code, `# Validates: REQ-*` in tests |
| **Feature vectors** | All active features have correctly formatted YAML in workspace |
| **Events emitted** | edge_started, iteration_completed, edge_converged events in events.jsonl |
| **Gaps validated** | /gen-gaps run; test and telemetry gaps documented |
| **Proposals drafted** | Gap clusters have corresponding PROP-* entries in reviews/pending/ |
| **STATUS.md current** | Workspace status reflects actual convergence state |

These are the termination conditions. The path to reaching them is the agent's choice.

---

## Relationship to Other ADRs

- **Bootloader §II** — Constraint-Emergence: constraints determine admissible states, not
  transformations. This ADR applies that principle to the methodology itself.
- **Bootloader §XI** — Path-independence invariant: stable assets are path-independent. Extended
  here to the workspace as a whole.
- **ADR-S-016** (Invocation Contract): defines what `invoke()` must produce, not how to produce
  it. Consistent with this ADR.
- **ADR-S-030** (Gap-Driven Vector Lineage): gaps drive new vectors, not re-execution of the
  same path. Assurance gaps are handled by the assurance pass, not by re-doing construction.

---

## Invariant Primes and Terminal Manifestations

The invariant checklist above mixes foundational conditions with derived evidence artifacts. This section sharpens the ontology by introducing two layers.

### Invariant Prime

An **invariant prime** is an irreducible validity condition of a Genesis workspace:
- Necessary for validity; not derivable from the other primes
- Path-independent; checkable from artifacts, projections, event stream, or explicit F_H judgment
- Stable across implementations and profiles

### Terminal Manifestation

A **terminal manifestation** is a concrete required artifact, projection, or observable that demonstrates one or more invariant primes hold at convergence.

### The Five Invariant Primes

| Prime | Meaning |
|-------|---------|
| **Asset convergence** | Required stable assets exist and pass their required evaluators |
| **Traceability** | Lineage is correct across spec, feature vectors, code, tests, and review artifacts |
| **Observability** | The work is visible to the methodology through a complete enough event/projection record |
| **State legibility** | Workspace state is structurally valid, replayable, and machine-readable |
| **Homeostatic closure** | Detected gaps are classified, validated, and routed into governance/remediation paths |

### Classification of the Invariant Checklist

| Checklist item | Layer | Prime basis |
|----------------|-------|-------------|
| Code exists | Terminal manifestation | Asset convergence |
| Tests pass | Terminal manifestation | Asset convergence |
| REQ threading | Near-prime manifestation | Traceability |
| Feature vectors correctly formatted | Terminal manifestation | State legibility |
| Events emitted | Terminal manifestation | Observability |
| Gaps validated | Terminal manifestation | Homeostatic closure |
| Proposals drafted | Terminal manifestation | Homeostatic closure |
| STATUS.md current | Derived manifestation | Observability + State legibility |

`STATUS.md current` remains mandatory. Being a derived manifestation does not reduce its requirement — it clarifies *why* it is required. `REQ threading` is listed as "near-prime" because it sits at the boundary: it is both a concrete artifact check (grep for `# Implements:`) and a structural validity condition (without it the traceability chain is broken). Treat it as prime in practice.

### Conformance Rule

A workspace is valid at convergence when:
1. **All five invariant primes are satisfied** for all active features in scope
2. **All required terminal manifestations are present and accurate** — artifacts must correctly reflect the primes, not just exist

Both conditions are necessary. A workspace where all artifacts exist but are inaccurate (e.g., fabricated REQ tags) fails condition 2. Evidence is mandatory, not optional.

---

*Ratified: 2026-03-12*
*Applies to: all Genesis implementations*
