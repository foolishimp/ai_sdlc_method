# STRATEGY: Discovery — Process Theory Correlations

**Author**: Claude Code
**Date**: 2026-03-08T06:00:00Z
**Addresses**: Higher-order functor basis — correlation to existing formal work
**For**: all
**Vector type**: Discovery (question_answered convergence)
**Question**: What existing formal theories does the Genesis primitive+functor system correlate to, and where is it novel?

---

## Summary

The Genesis system independently re-derives a substantial portion of process algebra, workflow net theory, fixpoint semantics, and monad theory — and extends them in one specific direction existing work does not cover: the three-tier evaluator model (F_D/F_P/F_H) applied across a multi-scale gradient. The category theory framing the user is working toward is well-founded and has strong existing literature to build on.

---

## Correlation Map

### 1. Process Algebra → Higher-Order Functors

**Existing work**: ACP (Algebra of Communicating Processes — Bergstra & Klop 1984), CCS (Milner 1980), CSP (Hoare 1978).

These define a small set of operators over processes:

| Process Algebra Operator | Genesis Higher-Order Functor |
|--------------------------|------------------------------|
| Sequential composition `P ; Q` | `∘` (functor composition) |
| Parallel composition `P \|\| Q` | `BUILD(A ↔ B)` |
| Channel output / input `c!v`, `c?x` | `BROADCAST / FOLD` |
| Choice `P + Q` | profile selection (poc vs standard) |
| Restriction / hiding `P \ {a}` | zoom (collapse edges in a projection) |
| Replication `!P` | `iterate()` (repeated until stable) |

**The direct hit**: ACP's parallel composition `||` and synchronisation barrier are exactly what `BUILD(code ↔ unit_tests)` formalises. CCS's `|` operator models two processes running concurrently with synchronisation — that is TDD co-evolution.

**Canonical reference**: Baeten & Weijland, *Process Algebra* (1990). The composition algebra in §3 is directly applicable.

---

### 2. Workflow Nets → Graph + Convergence

**Existing work**: van der Aalst's WF-nets (Workflow Nets, 1998) — a subclass of Petri nets with exactly one source place and one sink place, used to model business processes.

| WF-net Concept | Genesis Equivalent |
|----------------|--------------------|
| Place (token location) | Asset node |
| Transition (fires when conditions met) | Edge (fires when evaluators pass) |
| Token | Feature vector instance |
| AND-split | `BROADCAST` |
| AND-join | `FOLD` |
| XOR-split | profile routing / spawn |
| Soundness property | Composition validity (no deadlock, every broadcast reaches a fold) |

**The direct hit**: WF-net soundness = "every token eventually reaches the final place with no dead transitions." Genesis composition validity = "every BROADCAST has a FOLD, no cycles, every edge has a defined evaluator." Same property, same proof structure.

**van der Aalst's workflow patterns catalogue (2003)** enumerates 43 workflow patterns. Genesis's higher-order functors cover the 8 most fundamental ones. The catalogue is a useful checklist — are there patterns we've missed?

**Canonical reference**: van der Aalst, *Workflow Management* (2002). Van der Aalst & ter Hofstede, *YAWL* (2005) for the higher-level language.

---

### 3. Fixpoint Theory → Convergence

**Existing work**: Tarski's fixpoint theorem (1955), Scott's domain theory (1970s), Kleene's fixpoint theorem.

The convergence loop:
```
while delta(asset, spec) > 0:
    asset = iterate(asset, context, evaluators)
return asset  # fixpoint
```

This is fixpoint computation in a complete partial order (CPO):
- Assets form a CPO ordered by quality/completeness (partial order: more evaluators satisfied = higher)
- `iterate()` is monotone: each call satisfies at least as many evaluators as before (or stays same)
- Tarski's theorem: every monotone function on a complete lattice has a fixpoint
- The stable asset IS the fixpoint — the least fixpoint of `iterate()` above the initial candidate

**Scott continuity** is the computability condition: `iterate()` must preserve directed suprema (limits of increasing chains). This is the theoretical guarantee that iteration terminates rather than oscillating.

**The gradient `delta(state, constraints) → work`** is a Lyapunov function:
- Always ≥ 0 (delta is a count of failing checks)
- Monotonically non-increasing across iterations (evaluators don't un-pass)
- Reaches 0 at the fixpoint

Lyapunov functions are used to prove stability in control systems. The methodology is a control system. `delta` is the Lyapunov function. Convergence proof = showing delta is a valid Lyapunov function for the iteration.

**Canonical reference**: Davey & Priestley, *Introduction to Lattices and Order* (2002). Abramsky & Jung, *Domain Theory* in Handbook of Logic in Computer Science (1994).

---

### 4. Monad Theory → iterate() and Context

**Existing work**: Moggi's computational monads (1991), Wadler's monads for functional programming (1992).

`iterate(Asset, Context[], Evaluators) → Asset'` decomposes as a monad stack:

```haskell
type Genesis a = StateT Context (WriterT EventLog (EitherT Convergence Identity)) a

iterate :: Asset → Genesis Asset
iterate asset = do
    context  ← get              -- StateT: load Context[]
    result   ← evaluate asset   -- EitherT: converged or not
    tell [event result]         -- WriterT: append to events.jsonl
    return result               -- Identity: the new asset
```

| Monad | Genesis role |
|-------|-------------|
| `State Context` | Context[] is the state — loaded once, threaded through all evaluators |
| `Writer EventLog` | events.jsonl is the log — every iterate() appends, never modifies |
| `Either Convergence` | converged (Right) or iterating (Left delta) |
| Stack composition | The full iterate() function is the monad transformer stack |

**The direct hit**: The event log's append-only, immutable property is exactly the Writer monad invariant: `tell` appends, you never rewrite the log. This is not an implementation choice — it falls out of the monad structure.

**Canonical reference**: Moggi, "Notions of Computation and Monads" (1991). Wadler, "Monads for Functional Programming" (1992).

---

### 5. Curry-Howard Correspondence → Evaluators as Propositions

**Existing work**: The Curry-Howard isomorphism (Howard 1980) — propositions are types, proofs are programs.

| Curry-Howard | Genesis |
|-------------|---------|
| Proposition | Evaluator criterion (a check that must pass) |
| Proof | A passing evaluator run |
| Type | Asset schema (what shape the asset must have) |
| Term | Asset instance (the actual artifact) |
| Type checking | Running the evaluator checklist |
| Proof construction | iterate() — building an asset that satisfies all evaluators |
| Convergence | The asset is well-typed (all propositions proved) |

**The direct hit**: The evaluator checklist IS a conjunction of propositions. `all_required_checks_pass` is the conjunction elimination rule. Building a proof of the conjunction (passing all checks) IS convergence.

This means the formal system has a direct interpretation in type theory. An asset is a term; its evaluators define its type; convergence is type inference. A feature vector is a dependent type — its type depends on the spec.

**Canonical reference**: Wadler, "Propositions as Types" (2015) — the best accessible treatment. Sorensen & Urzyczyn, *Lectures on the Curry-Howard Isomorphism* (2006) for depth.

---

### 6. Session Types → CONSENSUS and BUILD

**Existing work**: Session types (Honda 1993, Honda et al. 2008) — types for communication protocols between concurrent processes.

A session type specifies the sequence of send/receive actions a process must perform. If both ends of a channel have compatible session types, communication is guaranteed to be deadlock-free and type-safe.

`BUILD(code ↔ unit_tests)`:
```
session Code:    !Asset; ?EvaluatorResult; loop
session Tests:   ?Asset; !EvaluatorResult; loop
dual(Code) = Tests  ✓  -- duality guarantees no deadlock
```

`CONSENSUS(proposal, [p1, p2, p3], majority)`:
```
session Proposer: !Proposal; ?Vote; ?Vote; ?Vote; !Result
session Reviewer: ?Proposal; !Vote; ?Result
-- multiplexed across N reviewers
```

**The direct hit**: The BUILD functor's co-evolution terminates without deadlock because `code` and `unit_tests` have dual session types. The duality proof IS the guarantee that TDD doesn't deadlock. CONSENSUS has a multiparty session type (Honda et al. 2008) — N participants, one coordinator.

This is significant: session types give us **static verification** of BUILD and CONSENSUS before running them. The composition compiler can type-check functor compositions using session type duality.

**Canonical reference**: Honda et al., "Multiparty Asynchronous Session Types" (2008). Ancona et al., "Behavioral Types in Programming Languages" (2016) for the survey.

---

### 7. B Method / Refinement Calculus → iterate() as Refinement

**Existing work**: The B Method (Abrial 1996), Refinement Calculus (Back & von Wright 1998), Z notation (Spivey 1992).

Refinement: `Spec ⊑ Implementation` — the implementation satisfies all properties of the spec. A refinement chain `S ⊑ A ⊑ B ⊑ C` progressively narrows from abstract spec to concrete implementation.

Genesis iterate() as refinement:
- `Asset<Tn>` refines `Asset<Tn-1>` if it satisfies at least as many evaluators
- The convergence point is the maximally refined asset (all evaluators satisfied)
- The spec is the abstract specification; the stable asset is the refinement

**Design → Code is a refinement step.** The code must satisfy all design evaluators (refinement preserves all properties). The evaluator checklist IS the refinement condition.

**The direct hit**: The spec/design separation in Genesis (WHAT vs HOW) is exactly the spec/refinement boundary in formal methods. Tech-agnostic spec = abstract B machine. Technology-bound design = refinement. Code = concrete implementation. The refinement chain is the Genesis graph.

**Canonical reference**: Abrial, *The B-Book* (1996). Lamport, *Specifying Systems* (2002) — TLA+ as an alternative refinement framework.

---

### 8. Category Theory (Direct) → Functors and Natural Transformations

**Existing work**: Mac Lane, *Categories for the Working Mathematician* (1971). Awodey, *Category Theory* (2010) for accessibility. Fong & Spivak, *Seven Sketches in Compositionality* (2019) for applied category theory.

The Genesis formal system in categorical terms:

**Objects**: Asset types (Intent, Requirements, Design, Code, ...)
**Morphisms**: iterate() calls (each call is a morphism `Asset<Tn> → Asset<Tn+1>`)
**Category**: `Genesis` — the category of typed development artifacts and iterations

**Functors (categorical)**:
- F_D, F_P, F_H are functors `Genesis → {pass, fail, skip}` (evaluation functors)
- The profile encoding is a functor `Spec × Encoding → Methodology`
- BROADCAST is the coproduct functor
- FOLD is the product functor
- BUILD is the tensor product (or more precisely, the pullback)

**Natural transformations**:
- η (escalation): F_D → F_P → F_H are natural transformations between evaluation functors
- The escalation chain preserves the evaluation "shape" — it changes the evaluator category but not the structure of what's being evaluated

**Adjunctions**:
- BROADCAST ⊣ FOLD — they are adjoint functors (left adjoint BROADCAST, right adjoint FOLD). This is why "every BROADCAST implies an eventual FOLD" — it's not a convention, it's the adjunction.
- DISCOVERY ⊣ RATIFY — exploration and commitment are adjoint. Discovery loosens constraints; Ratify tightens them. The adjunction means you can always trade one for the other.

**Monoidal category**:
- Functor composition `∘` with identity `iterate(identity)` forms a monoid on morphisms
- The higher-order functors compose in a monoidal category `(HOF, ∘, id)`
- The composition algebra has a monoidal structure: associativity of ∘, identity element

**Canonical reference**: Fong & Spivak, *Seven Sketches in Compositionality* (2019) — specifically Chapter 4 (co-design, monoidal categories) and Chapter 6 (electric circuits as props — directly analogous to workflow composition). Riehl, *Category Theory in Context* (2016) for the natural transformation and adjunction machinery.

---

## What Is Novel (Not Covered by Existing Work)

Four things appear to be genuinely new or substantially extended beyond existing literature:

**1. The Three-Tier Evaluator Model (F_D / F_P / F_H)**

Existing process algebra treats all evaluators uniformly — a transition fires or it doesn't. Workflow nets have guard conditions but no classification of the evaluator's epistemic category.

The F_D / F_P / F_H distinction — zero ambiguity / bounded ambiguity / persistent ambiguity — and the natural transformation escalation chain (η: F_D → F_P → F_H) appears to be novel. It bridges formal verification (F_D) with probabilistic/LLM reasoning (F_P) and human judgment (F_H) within a single coherent evaluator algebra.

**2. The Multi-Scale Gradient**

`delta(state, constraints) → work` applied at every scale simultaneously — single iteration, edge convergence, feature traversal, production system, spec review, constraint update — is not present in process algebra or workflow theory. Those theories operate at a fixed scale.

The self-similarity across scales (same computation, different state/constraints) is the novel claim. It implies the methodology is scale-free in the sense of complex systems theory.

**3. Observability as a Formal Invariant**

Existing formal methods treat observability (logging, monitoring) as an implementation concern, not a methodology constraint. Genesis makes it constitutive: "an unobserved computation didn't happen" is an invariant, not a guideline.

This connects to **linear logic** (Girard 1987) — where resources must be used exactly once and their use is tracked. An event log entry is the proof that a computation occurred. Linear logic's resource tracking is the formal basis for the observability invariant.

**4. Functor Encoding as Methodology Generator**

`Functor(Spec, Encoding) → Executable Methodology` — the idea that different encodings of the same spec produce different valid methodologies — is present in abstract categorical terms but not applied to software process theory. The formal methods literature either fixes the methodology or treats methodology choice as informal.

The encoding table (F_D/F_P/F_H assignments per functional unit) as a first-class object that generates methodology variants is new.

---

## Key Literature

| Work | Author | Year | Direct Correlation |
|------|--------|------|-------------------|
| Process Algebra | Bergstra & Klop | 1984 | Higher-order functor operators |
| A Theory of Processes (CCS) | Milner | 1989 | BUILD co-evolution |
| Notions of Computation and Monads | Moggi | 1991 | iterate() as monadic bind |
| The B-Book | Abrial | 1996 | iterate() as refinement |
| Workflow Management | van der Aalst | 2002 | Graph + convergence = WF-net soundness |
| Multiparty Session Types | Honda et al. | 2008 | CONSENSUS and BUILD typing |
| Propositions as Types | Wadler | 2015 | Evaluators as propositions |
| Seven Sketches in Compositionality | Fong & Spivak | 2019 | Applied category theory, monoidal composition |
| Linear Logic | Girard | 1987 | Observability as resource tracking |

---

## Recommended Action

1. **Fong & Spivak Ch. 4+6** first — the applied category theory framing maps most directly to functor composition and will give the notation needed to write the formal spec of the higher-order functor library.

2. **Van der Aalst's workflow patterns** — run the 43-pattern catalogue against the 8 Genesis higher-order functors. Any patterns not covered are candidates for new functors or reveal that the current 8 are sufficient.

3. **Session types for BUILD and CONSENSUS** — the duality proof for BUILD is achievable now. Write it as a formal claim: `dual(session_code) = session_tests`. This gives static verification of co-evolution correctness.

4. **Linear logic for observability** — the "unobserved computation didn't happen" invariant has a linear logic proof. This would formalise the observability invariant in a way that's machine-checkable.

5. **The novel contribution** — the F_D/F_P/F_H escalation chain as a natural transformation appears to be the most original formal contribution. This is the claim worth developing into a paper.
