# STRATEGY: Public Review Node Between Intent and Requirements

**Author**: Claude Code
**Date**: 2026-03-08T05:00:00Z
**Addresses**: Graph topology extension — multi-stakeholder consensus before requirements promotion
**For**: all
**Status**: Proposal — precursor to a larger point (user note: "bigger point TBD")

---

## Summary

Adding a `proposal → public_review` node pair between `intent` and `requirements` enables multi-stakeholder review and consensus before spec requirements are locked. This surfaces six gaps in the current formal system, two of which are spec-level blockers that have implications beyond this specific feature.

---

## Proposed Graph Change

New path for `standard` / `full` profiles:

```
intent → proposal → public_review → requirements
```

`intent → requirements` becomes a zoom shortcut for `poc`, `spike`, `hotfix`, `minimal` profiles only.

### New Nodes

**`proposal`** — Tech-agnostic spec-level proposal document drafted from intent and posted for stakeholder comment.

Schema:
```yaml
id: PROP-{SEQ}
title: string
intent_id: INT-{SEQ}
summary: string          # ≤ 300 words
proposed_requirements: list  # draft, not yet assigned REQ-* keys
open_questions: list     # specific questions reviewers must address
review_period_days: int
```

**`public_review`** — Open comment and consensus phase. Proposal is live; participants provide structured feedback.

Schema:
```yaml
proposal_id: PROP-{SEQ}
participants: list
comments: list           # { participant, timestamp, comment, disposition }
votes: list              # { participant, vote: approve|reject|abstain, rationale }
quorum:
  threshold: majority | supermajority | unanimity
  required_count: int
  reached: bool
review_open_since: datetime
review_closes_at: datetime
```

### New Edges and Edge Params

**`intent → proposal`** (`edge_params/intent_proposal.yml`):
- construct: F_P — agent drafts jargon-free proposal from intent
- evaluate: proposal quality (jargon-free, open questions specific, scope explicit)
- human gate: author approves before publish
- key constraint: NO REQ-* keys yet, NO methodology jargon — must be legible to external reviewers

**`proposal → public_review`** (`edge_params/proposal_public_review.yml`):
- construct: F_H only — publication is a human accountable act (ADR-013 principle)
- evaluate: deterministic checks (roster non-empty, close date set, quorum config complete)
- human gate: publisher confirms all participants notified
- this edge converges immediately on publication — the open window IS the converged state

**`public_review → requirements`** (`edge_params/public_review_requirements.yml`):
- consensus gate (all deterministic, hard blocks):
  - `review_window_closed`: current time > review_closes_at
  - `quorum_reached`: votes_received >= required_count AND approve ratio satisfies threshold
  - `all_comments_dispositioned`: every comment has disposition (resolved | rejected | acknowledged | scope_change)
- construct: F_P — agent extracts requirements from approved proposal + resolved comment corpus
- comments are Context[] — the full review corpus feeds requirement extraction
- inherits all checklist items from `intent_requirements.yml`
- additional: `scope_changes_produce_spec_modifications` check
- human gate: author confirms consensus is legitimate

---

## Six Design Gaps Identified

### GAP-1: Multi-Stakeholder F_H (SPEC-LEVEL BLOCKER)

**Current state**: F_H is singular — one human approves/rejects. No model for N participants voting.

**Gap**: §VI (Evaluators) and §VIII (IntentEngine) define F_H as "persistent ambiguity → judgment" but don't specify whose judgment or how many. The quorum model proposed here has no formal backing in the spec.

**Needed**: New ADR-S-* specifying:
- Participant roster as a typed context element (not project_constraints.yml)
- Vote schema: `{ participant, vote: approve|reject|abstain, rationale, timestamp }`
- Quorum rules as configuration (majority / supermajority / unanimity)
- Abstention semantics (does it count toward quorum denominator?)
- How multi-stakeholder F_H composes with the IntentEngine's `observer → evaluator → typed_output` model

**Why this matters beyond public_review**: Any governance or approval workflow needs multi-stakeholder F_H. This is a fundamental gap in the evaluator model, not just a public_review concern.

---

### GAP-2: Minimum Duration Constraint (SPEC-LEVEL)

**Current state**: `time_box` = maximum duration → fold-back on expiry. No minimum duration model.

**Gap**: `review_window_closed` (cannot converge before T) has inverted semantics to `time_box_expired` (must converge before T). The spec §5.3 (constraint tolerances) defines thresholds for "breach triggers escalation" but not "cannot act before threshold".

**Needed**: §5.3 extension distinguishing:
- `time_box.max_duration` — upper bound, fold-back on expiry (current)
- `time_box.min_duration` — lower bound, blocks premature convergence (new)

Implemented as a deterministic check in the meantime.

---

### GAP-3: Comment Corpus as Context[] (CONFIG-LEVEL — BLOCKING)

**Gap**: Comments arrive asynchronously via external channels (email, GitHub, Slack). No protocol for:
- How comments are committed to a structured file before the agent runs
- What format the comment corpus file takes
- Who normalises them (human curator responsibility)

**Proposed convention**: `reviews/PROP-{SEQ}-comments.yml` with schema matching `public_review.comments`. Human publisher is responsible for collecting and structuring comments before invoking `public_review → requirements`. Must be documented in context_guidance.

---

### GAP-4: New OL Event Types (CONFIG-LEVEL)

Missing from `ol_event.py` / `KNOWN_EVENT_TYPES`:
- `proposal_published` — when `proposal→public_review` converges
- `comment_received` — per comment (emitted by human curator tool)
- `consensus_reached` — when quorum check passes

Without these, the monitor's Processing Phases classifier treats public_review convergence as an unclassified event, and the homeostatic loop cannot observe the review process.

---

### GAP-5: Consensus Failure Path (CONFIG-LEVEL — BLOCKING)

**Gap**: If the review window closes and quorum is not reached, there is no exit path. The current model only has `converged` and `blocked (stuck delta)`. Three plausible outcomes need modelling:

1. **Re-publish** — extend window, notify non-respondents → new iteration of `public_review`
2. **Narrow scope** — reject contested portions, iterate on smaller proposal → fold-back to `proposal`
3. **Abandon** — fold back to `intent` with `convergence_type: consensus_failed`

**Needed**: `convergence_type: consensus_failed` with fold-back protocol identical to `time_box_expired`. The edge_params should enumerate all three options for the human to select.

---

### GAP-6: Profile Routing Formalism (CONFIG-LEVEL)

**Gap**: Which profiles skip `public_review` is currently documentation-only (notes field). No `profile.shortcuts.allowed` formal field exists, so implementations can silently omit public_review without a config-level violation.

**Proposed addition** to profile YAMLs:
```yaml
# standard.yml
shortcuts:
  allowed:
    - source: intent
      target: requirements
      profiles: [poc, spike, hotfix, minimal]
  notes: "public_review is mandatory for standard/full — not skippable"
```

---

## Gap Severity Summary

| Gap | Type | Blocks Convergence? |
|-----|------|---------------------|
| GAP-1: Multi-stakeholder F_H | Spec — needs ADR-S-* | Yes — quorum has no formal backing |
| GAP-2: Minimum duration constraint | Spec — needs §5.3 extension | No — workaround as deterministic check |
| GAP-3: Comment corpus format | Config convention | Yes — agent can't load comments without it |
| GAP-4: New OL event types | Config — ol_event.py | No — monitor degrades gracefully |
| GAP-5: Consensus failure path | Config — edge_params | Yes — no exit if quorum fails |
| GAP-6: Profile routing formalism | Config — profile YAMLs | No — risk of drift only |

---

## Recommended Action

1. **Before building**: Resolve GAP-1 (multi-stakeholder F_H spec model) — this is the blocker with implications beyond public_review. User flagged this as a precursor to a bigger point.
2. **Simultaneously**: Establish GAP-3 comment corpus convention (trivial — one file schema).
3. **In edge_params**: Document GAP-5 consensus failure options explicitly; let human choose at convergence-failure time.
4. **Defer**: GAP-2, GAP-4, GAP-6 — none block the MVP of this feature.

The `intent_proposal.yml`, `proposal_public_review.yml`, and `public_review_requirements.yml` edge param configs are fully specified above and ready to write once GAP-1 is resolved at spec level.

---

## Note

User indicated this is a **precursor to a bigger point**. The multi-stakeholder F_H gap (GAP-1) likely connects to broader governance, DAG coordination, or agent-as-participant scenarios. Capture follow-on discussion here or in a new STRATEGY post.
