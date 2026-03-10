# /gen-comment - Record a CONSENSUS Review Comment

<!-- Implements: REQ-F-CONSENSUS-001, REQ-F-CONS-002 -->

Submit a comment for the active review cycle. Comments inside the open window are
gating comments; comments after close are late context only.

## Usage

```text
/gen-comment --review-id <id> --content "<text>" [--participant <id>]
```

## Instructions

1. Load the current cycle for `review_id` from `.ai-workspace/events/events.jsonl`.
2. Reject the command if the review does not exist.
3. Compute gating status:
   `gating = cycle is open AND now <= review_closes_at`.
4. Allocate the next `comment_id` for the current cycle.
5. Append one `comment_received` event carrying:
   `review_id`, `cycle_id`, `comment_id`, `participant`, `asset_version`, `content`, `gating`.
6. Report whether the comment is gating and how many gating comments remain undispositioned.
