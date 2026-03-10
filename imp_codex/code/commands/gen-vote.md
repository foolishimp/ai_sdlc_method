# /gen-vote - Cast a CONSENSUS Vote

<!-- Implements: REQ-F-CONSENSUS-001, REQ-F-CONS-005, REQ-EVAL-003 -->

Cast or revise a vote for the active review cycle. Replay keeps the most recent vote
per participant for the current cycle.

## Usage

```text
/gen-vote --review-id <id> --verdict approve|reject|abstain [--participant <id>] [--rationale "<text>"] [--gating]
```

## Instructions

1. Load the current cycle for `review_id` and verify it is still open.
2. Reject votes after `review_closes_at`.
3. Append one `vote_cast` event with:
   `review_id`, `cycle_id`, `participant`, `asset_version`, `verdict`, `rationale`, `conditions`.
4. If `--gating` is set and a rationale is present, also append a `comment_received`
   event for the same cycle with `gating: true`.
5. Recompute the replay-derived tally:
   approve, reject, abstain, non-response, approve ratio, participation ratio.
6. Do not emit `consensus_reached` or `consensus_failed` here; closeout is separate.
