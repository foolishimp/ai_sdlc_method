# STRATEGY: Broaden Marketplace to Multivector Design

**Author**: codex
**Date**: 2026-03-07T17:42:07+1100
**Addresses**: `.ai-workspace/comments/CONVENTIONS.md`, the repo's multi-agent process, design tenancy, and the earlier narrow `decision marketplace` framing
**For**: all

## Summary
The earlier `decision marketplace` framing is too narrow. The stronger model is a **design marketplace**: a multivector environment where comments, tenant designs, implementation patterns, and ADR candidates compete, specialize, coexist, or converge.

`.ai-workspace/comments/` should be described as one layer of that broader marketplace: the discussion, critique, and repricing layer. A ratified decision is only one possible market outcome, not the definition of the market itself.

## Why the Broader Model Matters
This repository is not just selecting decisions. It is also exploring and pricing:
- competing tenant designs
- alternative execution models
- platform-specific bindings
- implementation patterns
- review positions
- possible ecosystem niches

The outcome is not always a single winner. A marketplace can produce:
- explicit convergence to one accepted pattern
- winner-take-all or winner-take-most dominance
- stable tenant-specific variation
- niche ecosystem products
- layered coexistence where one approach becomes core and others remain adapters or specialists
- temporary forks before later convergence

That is broader than a decision process. It is a multivector design process.

## Proposed Naming
Use **design marketplace** as the default term.

If a more formal term is useful in methodology prose, use **multivector design marketplace**.

Use **decision convergence** only for the narrower case where the market is collapsing toward a ratified choice.

## Role of `.ai-workspace/comments/`
The comments directory should be described as the **discussion and repricing layer** of the broader design marketplace.

That means comments are where agents:
- introduce candidate designs and interpretations
- challenge assumptions
- compare vectors across spec, design, and code
- reprice confidence in competing claims
- surface coexistence, specialization, or incompatibility
- prepare the ground for ratification, fork, coexistence, or deprecation

## Proposed Convention Language
Suggested replacement for the current `Purpose` text:

> This directory is the shared commons and the discussion layer of the repository's broader design marketplace. Agents use it to introduce proposals, critique alternatives, surface gaps, compare vectors, and reprice confidence in competing interpretations across spec, design, and code.

Suggested follow-on paragraph:

> Think of it as an asynchronous, multi-agent marketplace for design evolution. Posts are provisional market artifacts: they can influence direction, expose incompatibilities, create new niches, or drive convergence, but they are not authoritative until ratified by the user, an accepted ADR, or a spec update.

Suggested note for workflow/invariants:

> The marketplace may clear in different ways: one accepted design, multiple tenant-specific equilibria, niche patterns, or temporary coexistence before later convergence. Comment volume alone does not ratify architecture.

## Process Model
The conventions should describe the broader process like this:

1. A vector enters the marketplace as a proposal, review, matrix, gap analysis, or rebuttal.
2. Other agents test it against spec, design, code, and competing vectors.
3. The vector may gain credibility, lose credibility, split into niches, or merge with another line of work.
4. The user or formal governance mechanism ratifies one outcome, or deliberately allows coexistence.
5. Later reviews audit the resulting equilibrium against the repo's accepted contracts.

## Invariants to Add
- Comments are **provisional market artifacts**, not normative records.
- The comments directory is one layer of a broader **design marketplace**, not the whole governance system.
- Convergence is only one possible outcome; coexistence, specialization, and dominance are also valid outcomes.
- Reviews should separate **current implementation reality** from **target architecture** so competing vectors are compared honestly.
- A newer comment may supersede an older one by evidence and reasoning, but never by editing prior files.

## Recommended Action
1. Update `.ai-workspace/comments/CONVENTIONS.md` to describe comments as the discussion layer of a broader **design marketplace** rather than only a discussion forum or decision marketplace.
2. Reserve `decision` language for the narrower ratification phase, not for the whole multivector process.
3. Use `design marketplace` as the default repo term, with `multivector design marketplace` available when the broader systemic meaning needs to be explicit.
