# /gen-consensus-recover - Select a CONSENSUS Recovery Path

<!-- Implements: REQ-F-CONSENSUS-001, REQ-F-CONS-008, REQ-F-CONS-009 -->

Choose a recovery path after a failed cycle. Codex keeps `review_id` stable and
opens a new `cycle_id` when re-opening.

## Usage

```text
/gen-consensus-recover --review-id <id> --path re_open|narrow_scope|abandon [--rationale "<text>"] [--review-closes-in <seconds>]
```

## Instructions

1. Load the replay-derived quorum state for `review_id`.
2. Verify the latest cycle is in a terminal failed state.
3. Verify the chosen recovery path is allowed for the current failure reason.
4. Append `recovery_path_selected` with:
   `review_id`, `cycle_id`, `asset_id`, `path`, `rationale`.
5. If `path = re_open`, append `review_reopened` with:
   `review_id`, `prior_cycle_id`, new `cycle_id`, `artifact`, `asset_version`,
   `participants`, `quorum_threshold`, `published_at`, `review_closes_at`,
   `min_duration_seconds`.
6. If `path = narrow_scope` or `abandon`, stop after the recovery selection event and report the next manual action.
