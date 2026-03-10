# /gen-dispose - Disposition a Gating CONSENSUS Comment

<!-- Implements: REQ-F-CONSENSUS-001, REQ-F-CONS-003 -->

Disposition one gating comment in the active review cycle. This extends the review
projection by appending `comment_dispositioned`; it does not mutate prior events.

## Usage

```text
/gen-dispose --review-id <id> --comment-id COMMENT-* --disposition resolved|rejected|acknowledged|scope_change --rationale "<text>"
```

## Instructions

1. Load the current cycle for `review_id`.
2. Verify the target `comment_id` exists in that cycle and is gating.
3. Verify it has not already been dispositioned.
4. Append one `comment_dispositioned` event with:
   `review_id`, `cycle_id`, `comment_id`, `original_participant`,
   `disposition`, `rationale`, `material_change`.
5. If the disposition is `scope_change`, also append `spec_modified` with
   `trigger: "comment_dispositioned scope_change"`.
6. Recompute the replay-derived disposition state and report remaining gating comments.
