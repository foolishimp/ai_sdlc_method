# REVIEW: ADR-S-019 / ADR-S-020 Spec Updates

**Author**: codex
**Date**: 2026-03-07T12:59:44+1100
**Addresses**: specification/adrs/ADR-S-019-markov-blankets-and-active-inference-grounding.md, specification/adrs/ADR-S-020-feature-trajectories-phase-space-hamiltonian.md, specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md §6.8
**For**: all

## Summary
ADR-S-019 is mostly consistent with the current core spec framing, but it imports implementation-specific dependencies into a spec-level ADR. ADR-S-020 has two higher-severity problems: the Hamiltonian is defined inconsistently across the change set, and the chosen formula cannot support the diagnostic behavior the ADR claims.

## Findings

### 1. High:  does not support the stated convergence diagnostics
ADR-S-020 defines the canonical metric as , where  increments every iteration and  is the current failing-check count (:95-112). The adjacent spec text repeats that definition (:1047-1062).

That formula makes the diagnostic table wrong:
- If a healthy feature reduces delta by exactly 1 each iteration, H is flat, not decreasing.
- If delta decreases more slowly than 1 per iteration, H increases during healthy progress.
- A flat H therefore does not imply a blocked feature, which invalidates the ADR's "H stuck" rule and the  density interpretation (:103-143; :1074-1089).

As written, the monitor could report healthy convergence as "blocked" or "non-improving".

### 2. High: the change set defines the Hamiltonian as two different quantities
ADR-S-020 says the Hamiltonian is  (:95-101, 173-176). The core spec section added in the same update then says  (:1081-1087). Those are not equivalent.

Example: delta history  yields , but . The prose also says H is "free energy integrated over the trajectory" (:178), which matches the sum/integral reading, not .

Until one definition wins, implementations and reviewers will compute different values from the same event log.

### 3. Medium: both spec ADRs rely on tenant-specific or missing artifacts instead of spec-owned references
ADR-S-019 uses  as the basis and status evidence for nested blankets and roadmap staging (:72, 102-117, 149, 158). ADR-S-020 does the same with  and with a genesis monitor codebase path (:165, 188-191).

In this repo,  and  exist only under , and  is not present. That makes accepted specification ADRs depend on one implementation tenant and on a path reviewers cannot inspect locally.

For spec-level decisions, those dependencies should either be promoted into the  series or rewritten as non-normative examples.

## Open Questions
- Is H intended to be a remaining-work signal, a sunk-cost signal, or an accumulated-work signal? The current text mixes all three.
- If the monitor needs trajectory-shape diagnostics, should the canonical observable be , with H treated as a separate summary scalar rather than the convergence signal itself?

## Recommended Action
1. Pick one canonical definition for H and align ADR-S-020 and §6.8 to it. If you keep , remove the monotonic/blocked claims; if you want those claims, define a different metric.
2. Rework the diagnostic table so it matches the actual math on sample trajectories before calling H the canonical status metric.
3. Replace  /  / missing monitor-path references with spec-owned ADRs or mark them explicitly as implementation examples.
