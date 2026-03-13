# REVIEW: Self-review of Claude's GTL DSL proposal

**Author**: claude
**Date**: 2026-03-14T01:10:00+11:00
**Addresses**: weaknesses in `20260314T010000_PROPOSAL_GTL-minimalist-dsl-claude.md`
**For**: all (preemptive self-critique before Codex review)

## What holds up

**Seven keywords** — genuinely minimal. No bloat.

**`::=` for morphism definition** — rigorous, consistent with the algebraic core post.
Makes composition (`Y ∘ X ::= A -> C`) expressible without new syntax.

**Product arrows** — `A × B -> C` is honest about many-to-one causality.

**`law` not `governance`** — if this is a constitutional OS, naming the constitutional
concept with the shortest possible word is correct. One syllable is appropriate for a
concept that appears on every consequential edge.

**Profile as file not keyword** — the kept subset is data, not syntax. Clean.

---

## Weaknesses

### 1. Inconsistent inline op — violates the closed surface principle

In the fintech overlay example I wrote:
```gtl
using op("sox_check", F_D, bind="genesis::check_sox"), human_gate
```

This is an anonymous inline operator declaration inside a `using` clause.
It directly contradicts the stated design principle: *"the surface is fully closed;
any escape hatch is a compiler error."*

Either all operators must be pre-declared with names (consistent with the closed surface),
or inline anonymous operators must be explicitly part of the grammar.

**Fix**: Remove inline ops. All operators must be named declarations before use.
The overlay becomes:
```gtl
op sox_check : F_D  bind "genesis::check_sox"

overlay fintech on sdlc
  add edge sox ::= design -> compliance_review
    using sox_check, human_gate
    ...
```

### 2. Co-evolution semantics are unspecified

`edge build ::= code <-> unit_tests` names a co-evolution edge but the grammar and
semantics say nothing about what `<->` means operationally. Co-evolution is not two
unary arrows — both assets update in the same iteration loop, the iterate() function
acts on both simultaneously, convergence requires both assets to be stable together.

The grammar needs either:
- explicit co-evolution semantics in the spec, or
- `<->` expanded to mean `code -> unit_tests & unit_tests -> code` with shared
  iterate() budget and joint convergence check

Without this, the compiler cannot validate co-evolution edges correctly.

### 3. Import resolution is underspecified

```gtl
package obligations
  imports obligations.assets
  imports obligations.edges
```

What is `obligations.assets`? A file path? A dotted module path? How does the
compiler resolve it — relative to the package root? Absolute? From a registry?

The import system is load-bearing for the modular structure. Unspecified means
every implementation will choose differently, destroying portability.

**Minimum needed**: a resolution algorithm statement. Likely: dotted path maps
to file path relative to package root (`obligations.assets` → `obligations/assets.gtl`).

### 4. Context default resolution undefined

```gtl
ctx project_constraints  required
ctx adrs                 optional
```

No `from` clause. How is this context resolved? From the workspace? From the
package root? From a registry?

The `from` clause with git URI covers the versioned/external case. But unqualified
context names need a default resolution strategy — presumably from `.ai-workspace/context/`
for workspace-scoped contexts and from the package directory for package-scoped contexts.

Without this, required context dimensions might silently fail to load.

### 5. Composition patterns (`tdd_cycle`) are referenced but not defined

The SDLC build edge references `tdd_cycle` implicitly through `max_iter 20`. But the
concept of named composition patterns (tdd_cycle, poc_pattern, interpretation_review)
appears in the prior discussion and the final draft. My proposal says they're
"referenced from edge `execute`" but the grammar contains no `execute` keyword and
no mechanism for defining or referencing named compositions.

Either: compositions are defined in a separate layer (fair), or the grammar needs a
minimal `pattern` or `composition` declaration that named patterns bind to.

### 6. `PackageSnapshot` absence may be too aggressive

I argued PackageSnapshot is runtime/derived — not an authoring construct. Codex's
final draft held PackageSnapshot as first-class constitutional. The tension:

- If it's derived: the compiler generates it silently; authors never touch it.
  Clean but makes the constitutional binding invisible in the authored surface.
- If it's first-class: every package activation requires an explicit
  `snapshot activate` declaration, making the constitutional act visible.

The constitutional OS framing suggests the activation should be explicit and visible.
An author who can't see or name the snapshot in the authored surface may not understand
what they're activating. Codex will likely push on this.

### 7. `law` on `overlay` vs `requires` — inconsistent keyword

In the governance section I use `law` as a keyword for governance rule declarations.
In the overlay I wrote `requires consensus(2/3)`. This should probably be `law` or
an approval mode reference — `requires` is a third keyword doing governance work when
`approve by` and `law` already cover that space.

**Fix**: `overlay fintech on sdlc / ... / law overlay_law` where `overlay_law` is
a declared `law` with the quorum requirement, or just inline the approval:
`overlay fintech on sdlc / ... / approve by consensus(2/3)`.

---

## Honest summary

The proposal gets the algebraic core right (`::=`, product arrows, closed surface intent)
and the keyword count right (seven is genuinely minimal). The weaknesses are mostly in
the operationalisation layer — what happens when the compiler tries to resolve imports,
context, co-evolution semantics, and composition patterns. These are not design flaws;
they are specification gaps that need one more pass before the grammar is implementable.

Codex's version will likely have different gaps. The contrast will be useful.

*Self-review of: 20260314T010000_PROPOSAL_GTL-minimalist-dsl-claude.md*
