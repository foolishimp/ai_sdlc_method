<style>
table { page-break-inside: avoid; }
</style>

# The Genesis Delivery Model: Specification as Governance Architecture

**Technical Manifesto for Enterprise Architects and Technical Executives**

**Dimitar Popov**

---

Software governance rests on one assumption: that an organisation can account for what its systems do.

Which rule does this component enforce? Which control does this process satisfy? When this behaviour changes, what changes with it?

AI development has broken that chain at scale.

A developer can now produce in an afternoon what previously required a team a week. That output is already in enterprise production systems, executing business logic, making decisions. Without deliberate intervention, the chain from business requirement to running behaviour is a sequence of informal handoffs with no mechanism that verifies the chain is intact — or detects when it breaks.

Compliance frameworks assume you can trace a control to the code that enforces it. Audit examinations assume you can show which requirement a system satisfies. Change management assumes you can predict which systems are affected when a requirement changes. These assumptions hold only while the derivation chain from requirement to code is documented and verifiable.

The Genesis Delivery Model is a formal governance architecture for AI-augmented software delivery. It makes the accountability chain structural rather than procedural — embedded in the delivery mechanism itself, not layered on top of it.

---

## History Repeating Itself

Two decades ago, every business adopted spreadsheets enthusiastically. Fast, flexible, no IT involvement required. Every department built on them.

Business-critical calculations ended up on personal drives. Pricing logic lived in models only one person understood. Risk computations ran outside any system of record. When auditors asked how a number was arrived at, the answer was a file called FINAL_v3_REVISED.xlsx, last modified by someone who had since left.

Organisations spent twenty years trying to regain visibility over what their own systems were computing.

AI-generated code is that problem, running at an exponential scale. The spreadsheet problem was contained by what a spreadsheet could do. An AI has no such limit. It writes entire systems.

One difference makes this iteration more serious. Spreadsheets were built by users who understood their purpose, even if the documentation was poor. AI builds against a description — a prompt — that captures whatever the developer articulated in the moment. The developer's knowledge of the organisation's constraints, the regulatory context, the edge cases discovered in previous system generations: none of that is in the model. The model produces something that looks correct. Whether it is correct depends on whether the description was adequate.

Spec-Driven Development is the governance framework built for this moment. It gives organisations the full productivity of AI construction with complete traceability of what is being built, why, and whether the result matches what the business required. The specification is the system. Change the specification, and the system follows.

---

## The Problem with Process

Every enterprise has a delivery process. It specifies how requirements become designs, designs become code, and code becomes a deployed system. The process is documented. Teams follow it with varying fidelity.

Under deadline pressure, teams compress the process. Design documents are written after the code. Architecture reviews happen informally. Requirements change without audit trail updates. These are rational decisions under pressure. They are also the primary mechanism by which technical debt accumulates, governance findings emerge, and audit trails break.

Process governance fails when process compliance is voluntary. A control that can be argued around under sufficient pressure is a norm. A norm is not a control.

The Genesis model replaces compliance-as-norm with compliance-as-topology. The delivery graph encodes which transitions are admissible between stages. The transition from business intent to production code without passing through architecture review is not a rule violation — it is a non-existent path. The graph does not contain it. There is nowhere for that work to travel.

The audit question "was the architecture reviewed?" resolves to the same operation as "did the code compile?" It is a structural fact about the delivery artifact, not a question about team behaviour.

---

## I. Process Enforcement: Governance by Topology

Every stage of the delivery lifecycle — Intent, Requirements, Feature Decomposition, Architecture, Code, Tests, Deployment — is a node in a directed graph. Work moves between nodes only along defined, admissible transitions. Connections that represent governance violations are absent from the graph by construction.

A requirement key defined at the specification stage propagates forward as a structural constraint. Every downstream stage either carries the key or fails to close. The architecture cannot close without attesting to each requirement key. The code cannot close without a test tagged to each key. The deployment record carries the complete chain.

This is the delivery process — not a reporting system overlaid on it. The traceability chain exists because the process cannot produce a closed artifact without satisfying it.

### What This Means for Governance

An organisation operating under Genesis cannot accumulate the class of governance debt that arises from informal handoffs. The delivery record is not a description of what the team intended. It is a proof of what the process enforced.

A requirement that appears in the specification but is absent from any feature's declared scope causes the feature decomposition stage to fail. A feature whose code has no tagged test causes the development stage to fail. A deployment whose artifacts do not match the fingerprints recorded at acceptance is flagged as uncommitted. None of these require human vigilance to detect. They are structural facts about stage closure.

### What This Means for Audit

During examination — regulatory audit, internal review, post-incident investigation — the question "why does this code exist?" is answered by reading the delivery graph. The answer is not in a document describing what was intended. It is in a record proving what was done, because the graph enforced the derivation.

Every REQ key in the specification appears in a feature's declared scope, in the architecture that governs it, in the code that implements it, in the test that validates it, and in the production monitor that watches it. The chain exists because the process cannot close without it.

---

## II. Resource Optimisation: The Escalation Chain

The scarcest asset in any engineering organisation is senior human judgment. Applied to rote quality checks, it creates a bottleneck. Removed from irreducible decisions, it creates accountability gaps.

Genesis formalises quality evaluation as a three-tier escalation chain. Each tier handles the class of question appropriate to it. Escalation to a higher tier occurs only when the lower tier exhausts its delegated authority.

**Deterministic evaluation** handles zero-ambiguity questions. Type checks, schema validation, test suite results, coverage reports — these pass or fail. They execute on every iteration and gate advancement before higher tiers are consulted. No human attention is required.

**Agentic evaluation** handles bounded-ambiguity questions. Does the implementation satisfy the architecture constraint? Does the feature decomposition address the requirement fully? An AI evaluator checks systematically, flags gaps, and drives the work through iteration until the delta closes. Human attention is not requested until the agent cannot resolve the ambiguity within its delegated scope.

**Human evaluation** handles irreducible ambiguity. Is this the correct MVP boundary? Does this architectural trade-off reflect the organisation's risk tolerance? The human gate opens at exactly these decisions — where judgment is genuinely required — and nowhere else.

### What This Means for Engineering Organisations

Skilled people stop performing rote quality checks. They define the specification, review the architecture boundary decisions, and approve the MVP scope. The system handles everything between.

Quality is a measurable metric, not a subjective assessment. A work unit closes when the delta between specification and output reaches zero across all three tiers. If convergence cannot be reached, the system produces a gap report identifying exactly which constraint the output fails to satisfy. The human reviewer addresses the root cause, not symptoms.

The governance functions that exist in most engineering organisations — architects who check alignment, leads who review coverage, QA who validates completeness — are not displaced by this model. They are elevated. Their time moves from execution-layer checking to specification-layer definition. The mechanism handles the checking.

---

## III. Fault Isolation: Stable Boundaries Enable Safe Parallelism

Software systems fail in two modes. The first is component failure — a bug in a module. The second is propagation — the bug corrupts state that other components depend on, and the failure spreads. The second mode is the expensive one.

Governance fails by the same mechanism. Informal context leaks across organisational boundaries. A design decision made implicitly in one team affects another team's code in ways neither team can trace. A requirement change cascades into unexpected regressions that take weeks to isolate.

Genesis treats every deliverable — every feature, every design component, every code unit — as a stable object with a typed boundary. A stable object satisfies a formal definition: its interface is typed and declared, it is conditionally independent of the internal construction history of other objects, and all its evaluators have reported convergence.

A stable feature can be handed to another team, another agent, or another implementation without transmitting its internal construction history. The boundary is the contract. Everything inside belongs to that unit. Nothing propagates across the boundary except through declared interfaces.

### What This Means for Technical Programmes

Large programmes fail at integration boundaries. Teams build independently against assumptions about each other's interfaces. The assumptions are rarely written down, and they drift as both sides evolve. Integration becomes a negotiation about which set of informal assumptions is authoritative.

With formal stable boundaries, interface contracts are explicit at the point of specification. The feature decomposition stage defines the contracts before construction begins. When two features integrate, they do so against declared, versioned contracts — not against accumulated assumptions.

Safe parallelism becomes structurally available. Multiple teams and multiple AI agents can work on separate features simultaneously. Changes propagate only through declared interfaces. Silent interference is structurally impossible, not merely unlikely.

### What This Means for Technical Debt

Technical debt accumulates at informal boundaries. A module that works but whose internal logic is understood only by its author carries hidden coupling to every other module that makes assumptions about it. When the author leaves, the module becomes legacy — not because the code is old, but because the knowledge of its boundary conditions was never formal.

Stable objects carry their boundary conditions in the specification. The object's interface, its evaluator results, and the constraints it satisfies are on record at the point of closure. The next team, the next agent, and the next technology generation all work from the same documented boundary.

---

## IV. Operational Simplicity: One Process, All Scales

Enterprise organisations maintain multiple delivery processes. A five-line hotfix follows a different process from a three-month programme. The consequence is two problems: inconsistent audit trail structures for the same kind of change, and teams selecting the lighter process when the work requires the heavier one.

The Genesis model applies identical primitives at every scale. The difference between a hotfix and a major programme is not a different process. It is the same process running at different levels of resolution.

### How Resolution Works

A single transition in the delivery graph — Design to Code, for instance — can expand into a sub-graph when the work at that transition requires its own governance structure. The sub-graph is structurally identical to the parent: same event format, same artifact versioning, same audit record schema. When the sub-graph converges, it folds back into a single confirmed result in the parent.

The parent governance view sees one transition completed. The detailed view sees all internal structure. Both are valid simultaneously. The parent view is not a summarisation of the detailed view — it is a different resolution of the same event record.

A hotfix traverses a minimal graph with a single evaluator tier and produces a complete audit record. A major programme traverses a full graph with all three evaluator tiers and produces the same format audit record at greater depth. An audit examiner reads the same structure regardless of delivery scope.

### What This Means for Enterprise Process Governance

Process selection — which methodology applies to which project — is a governance problem in organisations running multiple parallel methodologies. The wrong selection creates audit gaps; the right selection requires a judgement call that is itself undocumented.

Genesis eliminates the selection decision. The process is invariant. The resolution adjusts to the work automatically. A change that requires one iteration through one evaluator tier produces one layer of audit record. A change that requires fifty iterations through all three tiers produces fifty layers of audit record in the same structure. The examiner's job does not change.

---

## V. Continuous Compliance: The Homeostatic System

The most dangerous production failure mode is not a crash. A crash is detected immediately. A system that drifts from its specification accumulates deviation invisibly until the deviation becomes material — at which point investigation must reconstruct both the current behaviour and the specified behaviour from separate, often stale sources.

For regulated industries, specification drift is a control failure. A control that governs a business rule is valid only while the production system implements the rule as specified. Drift between the specification and the running system invalidates the control, whether or not it has been detected.

The traditional monitoring architecture detects operational failure. It does not detect specification drift. The control that governs a business rule can silently become ineffective, and no alert fires.

### Specification Monitoring in Production

Genesis closes the feedback loop at production. The running system emits signals tagged with the same requirement identifiers that governed its construction. A signal tagged REQ-F-AUTH-001 carries the same key that appears in the architecture, the code, and the test that was accepted at deployment.

When behaviour on that signal deviates from the specified tolerance — error rates, latency profiles, output distributions — the system identifies which requirement is in drift. The deviation is not classified as an operational incident. It is a specification event, with the same formal properties as any event in the delivery chain.

Production is not a separate system that monitoring watches from the outside. It is the final stage of the delivery graph, continuously evaluated against the specification that governed construction.

### Self-Correcting Reconstruction

A specification event re-enters the delivery graph as a new intent. The response runs through the same process that built the system — specification reviewed, design updated, code reconstructed, tests confirmed, deployment recorded. The audit trail from anomaly to corrected deployment is complete and in the same format as every other delivery record.

Emergency patches are the primary mechanism by which technical debt accumulates and audit trails break down. A governance framework that eliminates the class of problem requiring emergency patches produces a compounding reduction in governance debt.

---

## The Asset Question

Software is a liability when the organisation cannot account for what it does. The organisation carries it, maintains it, defends it under examination — but cannot fully explain it, because the derivation chain from business requirement to running behaviour was lost at construction time.

Software is an asset when the organisation owns the specification it was built against and can regenerate it on demand. The specification is the knowledge. The code is a projection of it at a point in time.

Two organisations with equivalent AI construction capability diverge at this point. The one with a formal specification owns a permanent record of what its systems must do, independent of which AI model or development team produced the current implementation. When requirements change — regulatory update, market opportunity, architectural migration — the operation is to update the specification and reconstruct what needs rebuilding. The delivery chain is the same. The audit trail is the same. The cost of change is proportional to the scope of the specification change.

The organisation without a formal specification owns code that encodes decisions made during development by people who may no longer be there. Changing it requires understanding it first. Understanding it requires reconstructing the intent from the artifact — the intent that was never written down, held informally by developers who interpreted a series of prompts. This is the mechanism by which systems become legacy.

Legacy status is not a function of age. It is the loss of the knowledge the system was built against.

### Regeneration as a Competitive Capability

A specification corpus — a formalised record of business rules, constraints, architectural decisions, and requirement derivations, built incrementally across delivery cycles — is an organisational asset that cannot be replicated by copying code. The code is a projection of it. The specification is the original.

Competitors can copy implementation patterns. They cannot copy the formal knowledge of how an organisation's specific rules, constraints, and accumulated decisions produce the behaviour of its systems. That knowledge, held in a structured specification corpus, is the durable competitive advantage that AI velocity does not commoditise.

---

## What the Evidence Shows

The correlation between formal delivery standards and measurable outcomes is consistent across the research literature. The methodology addresses a problem that has been studied rigorously; the evidence predates AI-augmented development, and the mechanism is more compelling under AI conditions than it was under manual ones.

The DORA research programme tracked thousands of organisations over four years. Elite performers — fastest delivery, lowest failure rates — shared one consistent characteristic: documented standards enforced by automated checks. Teams relying on human interpretation of informal standards did not appear in the elite category. The mechanism is not culture or motivation. A constraint enforced by a machine is consistent. A constraint enforced by a human is variable — degraded by deadline pressure, team turnover, and the natural limits of memory and attention.

Google's internal engineering practice requires formal design documents before significant work begins. Analysis of their delivery outcomes consistently showed fewer post-deployment regressions on projects with upfront written specifications than on comparable projects without them. The mechanism is straightforward: an ambiguity that would have surfaced as a production regression is surfaced as a specification gap before construction begins. Resolving a specification gap costs a fraction of resolving a production regression.

ThoughtWorks has recommended Architectural Decision Records as a core engineering practice since 2016. The stated reason: when the people who made a decision leave, the written constraint remains. The written constraint applied uniformly to every subsequent decision is more reliable than the memory of the person who made the original choice.

The Specification by Example movement, documented extensively by Gojko Adzic, showed that formalising requirements as machine-checkable specifications — rather than prose — reduced misunderstandings between business and development teams by measurable margins. The mechanism: ambiguity in natural language disappears when the requirement must be stated precisely enough that a machine can check it.

The pattern is consistent: human consistency degrades with scale, time, and team turnover. Written constraints applied by automated systems do not.

The AI condition amplifies the mechanism. The DORA, Google, and specification-by-example research was conducted when humans were doing the construction. A human developer who misunderstands a constraint will at least understand that they have misunderstood it. An AI that misunderstands a constraint will produce a plausible, confident, incorrect result. The case for formal specification was already strong when humans built the software. When the constructor has no knowledge of your organisation's constraints, the specification is the only mechanism that keeps the construction accountable.

---

## Competitive Position

AI removes the scarcity in code construction. Producing code is no longer the bottleneck.

The bottleneck shifts to the quality of specification — the precision with which an organisation translates its requirements into formal constraints that govern AI construction. The capability to state requirements precisely enough that a machine can check conformance determines delivery quality.

Every delivery cycle on a governed trajectory adds to a specification corpus — a formalised record of business rules and constraints. That corpus becomes the durable organisational asset. It can regenerate systems on demand against any technology generation. It can assess the impact of a regulatory change before reconstruction begins. It provides the constraint surface that makes each AI model generation more effective, not merely faster.

Teams with rigorous specification practice deliver faster, with fewer governance findings, with cleaner audit trails, and with production systems that remain aligned to their specifications. They change their systems at the cost of changing their specifications. They can account for what every system does and demonstrate the derivation under examination.

Teams without that practice produce output faster than before. They accumulate unverifiable behaviour faster than before. Their inventory of systems that cannot be fully accounted for grows at the velocity of AI construction.

Both trajectories compound. The divergence between them increases with every delivery cycle.

---

## Current Proof

This methodology is being developed using itself. One formal specification. Three independent AI development agents — Claude, Gemini, and Codex — building distinct implementations simultaneously against the same specification, each evaluated against the same formal criteria.

The process is the demonstration. A governance methodology that cannot govern its own construction has no grounds to claim it governs anything else.

The specification, implementation records, and the complete log of architectural decisions — over thirty records, each governing a specific aspect of conforming implementations — are available for technical review.

---

## For Technical Leaders: What Changes at Each Stage

The table below shows what each stage of the delivery lifecycle looks like under three approaches: conventional development, AI prompt-driven development, and the Genesis Model. The audit question after each stage is the one a regulatory examiner, a risk officer, or a senior technical reviewer would ask.

---

### Requirements

| | Traditional | Prompt-Driven | Genesis |
|---|---|---|---|
| **How it works** | Workshops, Word documents, Jira tickets, informal sign-off | Developer describes the requirement in natural language; AI interprets intent | Every requirement has a unique identifier (REQ-*) defined once in a formal document, reviewed and baselined |
| **Completeness check** | Human reviewer, informally | None — the AI does not know what it does not know | Automated gate: every requirement identifier must be covered before delivery can advance |
| **Audit answer: "What were you asked to build?"** | Find the correct version of the correct document | Reconstruct from conversation history | Read the baselined requirements file; every item has a unique key and a version timestamp |

---

### Feature Decomposition and Planning

| | Traditional | Prompt-Driven | Genesis |
|---|---|---|---|
| **How it works** | Sprint planning, backlog grooming, estimation sessions | "Break this down into tasks" — AI suggests a plan | Requirements are formally decomposed into features; each feature declares which requirements it satisfies |
| **Completeness check** | Team judgment; gaps surface during build | None — missing requirements are discovered late or not at all | Automated gate: every requirement identifier must be claimed by at least one feature. Delivery cannot advance until the check passes |
| **Audit answer: "Did you plan for everything?"** | Difficult to establish without reconstructing meeting notes | Cannot prove | Show the coverage report: N requirements, all N covered, timestamp, approver |

The gate here is not a review meeting. It is a rule the system enforces: if any requirement is uncovered, the system reports the gap and delivery does not advance. A human then either adds the missing feature or disputes the requirement. Either way, the decision is on record.

---

### Architecture and Design

| | Traditional | Prompt-Driven | Genesis |
|---|---|---|---|
| **How it works** | Architects document decisions in Confluence or Visio; developers interpret | "Design this system" — AI proposes an architecture with no knowledge of organisational constraints | Technology choices, integration patterns, and constraints are encoded as formal Architectural Decision Records (ADRs), each tracing to the requirements it satisfies |
| **Technology constraints** | Documented in a wiki; may or may not be applied | The AI uses whatever it finds plausible | The constraint surface is loaded into every subsequent AI invocation as mandatory context |
| **Audit answer: "Why was this architectural decision made?"** | Find the relevant Confluence page and verify it is current | Cannot answer | The ADR is numbered, dated, states the alternatives considered, the trade-offs, and the requirements it addresses |

---

### Development

| | Traditional | Prompt-Driven | Genesis |
|---|---|---|---|
| **How it works** | Developers write code manually | AI generates code; developer reviews and iterates | AI generates code against the specification; automated and AI-assisted evaluators check conformance before the output is accepted |
| **Quality gate** | Code review, manual testing | Developer judgment | The work cannot close until it passes a defined evaluator set. A partial or non-conforming output does not advance |
| **Audit answer: "Which requirement does this code satisfy?"** | Read comments if they exist; ask the developer | Cannot reliably answer | Every code unit carries the requirement identifier it implements, tagged and searchable |

---

### Testing

| | Traditional | Prompt-Driven | Genesis |
|---|---|---|---|
| **How it works** | QA team writes and runs test cases, often manually | AI reports it tested; coverage is informal | Test cases are generated and tagged to the requirement they validate; coverage is a verifiable number |
| **Completeness** | Depends on QA capacity and judgment | Unknown | Every requirement identifier must appear in at least one passing test |
| **Audit answer: "How do you know this requirement is validated?"** | Show the test case and hope the mapping is documented | Cannot answer | Show the test tagged REQ-F-AUTH-001 and the record showing it passed |

---

### Deployment

| | Traditional | Prompt-Driven | Genesis |
|---|---|---|---|
| **How it works** | Release process, change advisory board, manual verification | Build what the AI produced and deploy it | Every artifact deployed carries a fingerprint computed at acceptance. The deployment record includes what was deployed, from which verified state, and which requirements it satisfies |
| **Change record** | Change management ticket, often completed after the fact | Informal | The delivery record is generated continuously during build; the deployment record is a projection of it |
| **Audit answer: "What exactly was deployed on this date?"** | Find the release notes and verify their completeness | Cannot answer | Read the delivery record: requirements satisfied, artifacts fingerprinted, evaluators that confirmed acceptance |

---

### Production Operations

| | Traditional | Prompt-Driven | Genesis |
|---|---|---|---|
| **How it works** | Monitoring, alerting, incident response | Wait for something to break, then re-prompt a fix | The production system emits signals tagged to the same requirement identifiers used in development; deviation from specified behaviour is detected automatically |
| **Drift detection** | Humans notice when something breaks | No mechanism | When a signal tagged REQ-F-AUTH-001 shows anomalous behaviour, the system identifies which specified requirement is in drift and initiates a governed response |
| **Audit answer: "How do you know the live system still satisfies this requirement?"** | Manual review, penetration testing, periodic audit | Cannot answer | The production monitor watches it continuously, using the same requirement identifier that governed its construction |

---

---

# Appendix: This Is Not a Prompt

A reasonable question from anyone familiar with AI tooling is what makes Genesis different from sophisticated prompt engineering.

A prompt is a natural language instruction. The model applies its best judgment about intent. Two prompts that appear similar can produce meaningfully different outputs. There is no formal definition of what a correct response looks like, and no mechanism to check conformance automatically.

A constraint document specifies rules that must be satisfied, stated precisely enough that a system can check compliance automatically. The model works within a defined space and is evaluated against defined criteria.

Below are excerpts from this project's constraint documents. There are currently over thirty such documents in the specification, each governing a specific aspect of how any conforming implementation must behave.

---

## Fragment 1: The Completeness Gate (ADR-S-013)

This document governs what it means for the feature planning stage to be complete.

> **The feature decomposition stage converges when, and only when, two conditions are both true:**
>
> **Condition A — Coverage Check (automated):** Every requirement identifier defined in the requirements document must appear in at least one feature's declared scope. This is computed automatically. If any requirement is missing, the check fails. There is no partial credit.
>
> **Condition B — Human Approval:** A human reviewer must explicitly confirm that the feature list is the correct decomposition of the requirements — not merely complete, but correctly structured, correctly ordered, and correctly scoped to the agreed delivery boundary.
>
> *Coverage alone is not sufficient. A feature list can cover every requirement and still be the wrong plan — wrong granularity, wrong sequencing, wrong MVP boundary. The automated check gates the human review. The human review gates advancement.*

This rule applies uniformly — every implementation, every team, every delivery cycle. The gate is not a guideline.

---

## Fragment 2: The Execution Contract (ADR-S-015)

This document governs how work is recorded at runtime.

> **Every stage transition opens a transaction when it begins and closes it only when work is confirmed complete.**
>
> | Phase | What is recorded | Meaning |
> |---|---|---|
> | Begin | START — input artifacts fingerprinted | Work has commenced; prior state is on record |
> | Execute | Nothing | Work is in progress; no commitment yet |
> | Accept | COMPLETE — output artifacts fingerprinted | Work is confirmed; this is the point of record |
> | Reject | FAIL or ABORT | Prior state remains authoritative |
>
> *An artifact written to the system without a corresponding COMPLETE record is uncommitted work. On restart, the system detects the open transaction, compares the current state of every affected file against the fingerprints recorded at the start, and flags any file that was modified but never committed.*

The fingerprint is a SHA-256 hash. Change a single character; the hash changes. Applying it to every artifact at every stage is what makes the audit trail mathematically verifiable rather than document-based.

---

## Fragment 3: The Derivation Constraint (ADR-S-004)

This document governs how documents in the specification hierarchy relate to each other.

> **A downstream document may not contradict an upstream document.**
>
> In any conflict, the upstream document is authoritative. The downstream document is wrong and must be corrected.
>
> Downstream documents may not:
> - Contradict an upstream statement
> - Relax an upstream constraint
> - Silently omit an upstream requirement (omission is a violation)
> - Redefine upstream terminology with a different meaning
>
> *Alternatives considered included: "downstream can override with justification" — rejected. The downstream document will always have a rationale. "Justification" becomes a bypass.*

A governance rule that can be argued around is not a governance rule. That sentence is the reason the alternative was rejected, stated plainly.

---

## Fragment 4: One Agent for All Stages (ADR-008)

This document governs how the AI construction mechanism is implemented.

> **The agent has no hard-coded knowledge of "stages". It reads:**
> - The edge type (which transition is being traversed)
> - The evaluator configuration (which checks constitute convergence)
> - The context (which constraints bound construction)
> - The asset type schema (what the output must satisfy)
>
> *Using multiple stage-specific agents would be the implementation contradicting its own theory.*

New delivery stages require only a configuration file. No new code. No new agent. The methodology extends by configuration.

---

## Fragment 5: Design That Monitors Itself (ADR-016)

This document governs how architectural decisions are maintained over time.

> **When a tolerance is breached, the pipeline fires:**
>
> Tolerance breached → monitor detects → severity classified →
>
> Zero ambiguity: log and auto-tune
> Bounded: generate optimisation intent
> Persistent: propose architectural rebinding
>
> *A persistent breach means the binding decision itself should be revisited. The ADR that made the choice becomes the target of a new design iteration. The methodology maintains the system — and evolves the design.*

This is the mechanism by which systems avoid becoming legacy: not through scheduled rewrites, but through continuous monitoring of their own architectural fitness against defined tolerances.

---

## Fragment 6: Scale Invariance by Construction (ADR-S-017)

This document resolves what happens when the delivery unit changes scale — from a single AI invocation to a full feature, from a feature to a programme.

> **Spawn is zoom in. Fold-back is zoom out.**
>
> When a step discovers sub-structure requiring its own convergence loop, it spawns a child unit of work. The child is structurally identical to the parent — same format, same event schema, same artifact versioning — but at finer grain.
>
> The parent graph still sees the original transition as one step. The zoomed view sees the internal structure. Both are valid simultaneously.
>
> *Spawn and fold-back are not special mechanisms added to support recursion. They are the natural expression of scale invariance in a model where the same primitives apply at every resolution.*

Scale-invariance means the same governance rules apply whether the unit of work is a single evaluation or an entire programme. There is no project-level process that bypasses the methodology. The process applies at every level.

---

These six fragments are a representative subset of over thirty constraint documents in the specification. Each was written, reviewed, and recorded before a line of production code was produced.

That is the difference between a prompt and a specification. The prompt describes intent. The specification creates an accountable system.

---

*The formal specification (v3.0.0), implementation records, and architectural decision log (ADR-S-001 through ADR-S-034) are available for technical review on request.*
