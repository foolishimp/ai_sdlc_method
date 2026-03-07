# ADR: Writing Principles for Strategic and Technical Papers

**Status**: Accepted
**Author**: Dimitar Popov
**Date**: 2026-03-07

---

## Context

Strategic and technical papers written for sophisticated, time-scarce audiences — financial markets executives, senior technical decision-makers, engineering leaders — are routinely degraded by rhetorical structures borrowed from sales writing and AI-generated text. These structures add cognitive load without adding information. A reader who has to hold a contrast in mind while evaluating a claim is doing unnecessary work. A reader who is told what to conclude is being patronised.

The audience can reason. The document's job is to deliver the premises.

---

## Decision

### 1. Assume intelligence

State facts. The reader draws the inference. Do not write the conclusion the reader is supposed to reach — write the information that produces it.

**Wrong**: *Better prompts do not close the governance gap. The issue is not instruction quality — it is whether a formal methodology governs what AI builds.*
**Right**: *The differentiator is what the AI is building against.*

### 2. Eliminate contrast steering

"Not X, it is Y" and "not X, but Y" structures double the cognitive load of a claim. State the positive directly.

**Wrong**: *Legacy code is not primarily a technology problem. It is a knowledge problem.*
**Right**: *Legacy code encodes decades of business rules in a form that is expensive to maintain and difficult to explain.*

**Wrong**: *The consequence is not a heavier process. It is AI construction that operates within existing governance.*
**Right**: *AI construction operates within existing governance.*

### 3. No rhetorical flourishes

Remove dramatic em-dash endings that restate what was just said, speculative premises used to set up a claim, and qualifiers inserted for rhythm rather than meaning.

- `— not at delivery` — cut
- `— not smaller` — cut
- `As construction becomes fully automated,` — speculative premise doing rhetorical work, cut
- `when the moment of examination arrives` — dramatic, cut; say *under examination*
- `— current or future —` — inserted for sweep, cut

### 4. Use the audience's vocabulary

Calibrate terminology to the reader's domain. For financial markets: scarcity, commodity, baseline, risk management, exposure, liability, asset. These terms carry precise meaning for that audience. Do not introduce them and then explain them.

### 5. Methodology over tool

A specific implementation is one of several approaches to the same methodology. The methodology is the argument. Tools are replaceable and should be positioned as such.

**Wrong**: *Genesis addresses this problem.*
**Right**: *Genesis is one implementation of spec-driven development — one of several tooling approaches to the same methodology.*

### 6. No setup paragraphs

Open sections with substance. A paragraph that describes what the section is about before delivering its content is a paragraph that can be deleted.

**Wrong**: *Spec-Driven Development changes the relationship with legacy systems.* [followed by the actual content]
**Right**: Start with the content.

### 7. One idea per sentence

Each sentence carries one claim. A sentence that requires the reader to hold a contrast while evaluating a new claim should be split or rewritten as a direct positive statement.

---

## Consequences

- Papers are shorter and more credible to sophisticated readers
- The argument stands on its facts — if a claim is weak, it is visible immediately
- Revision is clean: removing a sentence that states a positive fact does not break surrounding logic
- AI-assisted drafting requires an additional pass against these principles; LLMs default to contrast framing and rhetorical padding

---

*Applied during the drafting of: docs/philosophy/STRATEGIC_BRIEF.md*
