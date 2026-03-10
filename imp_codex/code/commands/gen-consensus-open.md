# /gen-consensus-open - Open a CONSENSUS Review Cycle

<!-- Implements: REQ-F-CONSENSUS-001, REQ-F-CONS-001, REQ-EVAL-003 -->

Open a multi-party review cycle for an artifact. This is a thin emitter: it publishes
`consensus_requested` and stops. Replay-derived closeout happens later.

## Usage

```text
/gen-consensus-open --artifact <path> --roster <participants> [--quorum majority|supermajority|unanimity] [--review-id REVIEW-*] [--review-closes-in <seconds>] [--min-duration-seconds <seconds>]
```

## Instructions

1. Validate the artifact path exists under the current project root.
2. Parse the roster into participant records. Preserve explicit `human:` and `agent:` prefixes when provided.
3. Generate `review_id` if omitted and start with `cycle_id = CYCLE-001`.
4. Validate the review window:
   `review_closes_at >= published_at + min_duration_seconds`.
5. Append one `consensus_requested` event to `.ai-workspace/events/events.jsonl` with:
   `review_id`, `cycle_id`, `asset_id`, `asset_version`, `artifact`, `participants`,
   `quorum_threshold`, `abstention_model`, `min_participation_ratio`,
   `published_at`, `review_closes_at`, and `min_duration_seconds`.
6. Stop after emission. Do not cast votes, disposition comments, or emit terminal outcomes here.
