# STRATEGY: The monadic structure of Genesis

**Author**: claude
**Date**: 2026-03-13T14:30:00+11:00
**Addresses**: formal characterisation of the algebraic structure of Genesis — monoid, functor, state monad, and monad transformer stack
**For**: all

## Summary

Genesis has precise algebraic structure. This is not a metaphor. The composition operator is a monoid. The package type constructor is a functor. The iterate loop is a state monad over the event stream. The full Genesis computation is a monad transformer stack. Understanding this structure clarifies why GTL is not configuration and what composability guarantees the formal system actually provides.

## The Three Structural Claims

### 1. Graph package composition is a monoid

The GTL composition operator forms a monoid under package union:

```
obligations_emea = base_obligations + mifid_overlay + gdpr_overlay
```

- **Associativity**: `(A + B) + C = A + (B + C)` — rebracket any way, same package
- **Identity**: `P + ∅ = P` — the empty package is the unit

This is well-defined and verifiable at compile time. The compiler can check that composition produces a valid graph — no dangling edges, no evaluator conflicts, no missing convergence criteria. Monoid structure gives you that guarantee. Configuration gives you none of it — composition is manual and verified by inspection.

### 2. The package type constructor is a functor

A Genesis graph package maps domain graphs into the Genesis-wrapped computation context:

```
F : DomainGraph → GenesisPackage
```

The functor preserves structure:
- `F(identity) = identity` — the empty domain graph maps to the empty package
- `F(A ∘ B) = F(A) ∘ F(B)` — composing domain graphs then wrapping is the same as wrapping then composing packages

This is what makes Genesis domain-general. The four primitives are the functor. The domain graph is the input. The GTL package is the output. The SDLC graph is one instance of `F` applied. `genesis_obligations` is another. The functor is the same; only the input graph changes.

### 3. iterate() is a state monad over the event stream

The single operation of Genesis has exact state monad structure.

```
iterate : Asset → State[EventStream, Asset']
```

Expanded:

```
iterate(asset, context, evaluators) →
    read EventStream          -- get current state
    produce Asset'            -- transform the asset
    append Event to stream    -- extend the state
    return Asset'
```

This is the state monad: a computation that reads state, produces a value, and updates state. The convergence loop is state monad composition:

```
converge = iterate >>= iterate >>= iterate >>= ... until delta = 0
```

**Bind** (`>>=`): run this iteration, take the output asset, pass it to the next iteration as input.

**The three monad laws hold**:

- **Left identity**: `return(asset) >>= f = f(asset)` — the initial asset passed to the first iterate is just the asset; no prior state transformation
- **Right identity**: `m >>= return = m` — the final iterate at delta=0 returns the asset unchanged; the stream gains one convergence event but the asset is stable
- **Associativity**: `(m >>= f) >>= g = m >>= (λx. f(x) >>= g)` — the event stream is append-only and immutable; rebinding the iteration sequence produces the same stream in the same order

The event stream is not incidental to the state monad structure — it is the state. Assets are projections of the state. `iterate()` is the state transition function. This is why "assets are projections, not stored objects" is not just an implementation choice: it is a consequence of the monadic structure. Storing assets as mutable objects would break the state monad laws.

### 4. The full Genesis computation is a monad transformer stack

Combining the above:

```
Genesis = StateT[EventStream, PackageFunctor[Asset]]
```

A state monad transformer (`StateT`) over the event stream, applied to the package functor wrapping the asset type.

This gives the full computation:
- The **package functor** establishes which domain graph and convergence criteria apply
- The **state monad** threads the event stream through each iteration
- The **transformer stack** composes them: each iteration reads domain-specific convergence criteria from the package, applies them to the asset, and records the result in the shared event stream

This is why iterate() is the only operation. In a monad transformer stack, bind is the only composition mechanism. Everything else — graph topology, evaluators, profiles, compositions — is configuration of the functor. The operation is always bind.

## Why this matters for GTL

Configuration cannot express the monoid. You can write two YAML files and manually merge them, but the merge is not checked against monoid laws. The result may have conflicting edges, missing evaluators, or broken convergence criteria. You discover this at runtime, not at authoring time.

GTL expresses the monoid as a typed composition. The compiler checks:
- associativity of package union
- identity of the empty package
- functor law preservation across composition
- state monad law preservation across iterate() calls (no mutable asset state, append-only event stream)

These are compile-time guarantees. With config, they are conventions. The difference is where violations surface: at authoring time (GTL) or at runtime after iterate() has already produced events (config).

## Why this matters for domain generality

The functor structure is the formal basis for Genesis being domain-general. The four primitives define the functor. The domain graph is the input. GTL is the language for authoring valid inputs to that functor.

`genesis_obligations` does not require a different iterate(). It does not require a different event stream. It does not require different monad laws. It requires a different domain graph — a different input to the same functor. GTL makes that input expressible and checkable.

Without this structure being explicit, "Genesis is domain-general" is a claim. With it, it is a theorem.

## Coda

The event stream being the state of the state monad is the deepest consequence of this structure. It means:

- Replay is not a feature — it is the definition of state
- Projections are not views — they are the asset type in the monad
- Convergence is not a heuristic — it is the termination condition of the monadic bind chain
- Immutability of the event stream is not a convention — it is required by the right-identity law

The formal system did not choose these properties. They follow from the monadic structure.

*Reference: conversation 2026-03-13, GTL justification and algebraic structure*
*Relates to: ADR-S-012 (Event Stream as Model Substrate), ADR-S-035 (GTL), ADR-S-036 (Invariants as Termination Conditions)*
