# /gen-vote — Cast a Vote in a CONSENSUS Review Session

<!-- Implements: REQ-F-CONSENSUS-001, REQ-EVAL-003 -->
<!-- Reference: ADR-S-025 (CONSENSUS Functor) §Phase 3 (Deliberation) -->

Cast a vote (`approve`, `reject`, or `abstain`) in an open CONSENSUS review session.
Emits a `vote_cast` event and runs the quorum check to detect if consensus is reached.

## Usage

```
/gen-vote --review-id <id> --verdict <approve|reject|abstain> [--rationale "<text>"] [--gating]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--review-id` | required | The review session ID (e.g. `REVIEW-ADR-S-027-1`) |
| `--verdict` | required | `approve`, `reject`, or `abstain` |
| `--rationale` | optional | Explanation for your vote (strongly recommended) |
| `--gating` | false | Mark this vote as containing a gating comment (blocks consensus until dispositioned) |
| `--participant` | auto | Override participant ID (defaults to current agent/user) |

## Instructions

### Step 1: Validate inputs

1. Confirm `--review-id` is provided
2. Confirm `--verdict` is one of `approve`, `reject`, `abstain`
3. Read `.ai-workspace/events/events.jsonl` — verify a `proposal_published` event exists for this `review_id`
4. Verify no prior `consensus_reached` or `consensus_failed` event exists for this `review_id` (session must be open)
5. Check if this participant has already voted for this `review_id` — if so, warn and exit (duplicate votes are rejected)

### Step 2: Identify participant

Determine the participant ID:
- If `--participant` is specified, use it
- Otherwise, use the current agent role name (e.g. `gen-dev-observer`, `gen-cicd-observer`, `gen-ops-observer`)
- For human votes: use `local-user`

Verify the participant is in the roster from the `proposal_published` event.
If not in roster, emit a warning: `{participant} is not in the review roster — vote recorded but may not count toward quorum`

### Step 3: Emit `vote_cast` event

Append to `.ai-workspace/events/events.jsonl`:

```json
{
  "event_type": "vote_cast",
  "review_id": "{review_id}",
  "timestamp": "{ISO 8601}",
  "project": "{project_name}",
  "actor": "{participant_id}",
  "data": {
    "participant": "{participant_id}",
    "verdict": "{approve|reject|abstain}",
    "rationale": "{rationale text or empty string}",
    "gating": false,
    "content": "{rationale text or empty string}"
  }
}
```

If `--gating` is set, also emit a `comment_received` event with `gating: true` so the rationale appears in the comment thread:

```json
{
  "event_type": "comment_received",
  "review_id": "{review_id}",
  "timestamp": "{ISO 8601}",
  "project": "{project_name}",
  "actor": "{participant_id}",
  "data": {
    "participant": "{participant_id}",
    "content": "{rationale}",
    "gating": true,
    "disposition": null
  }
}
```

### Step 4: Run quorum check

Run the inline quorum check (same as gen-consensus-open Step 5):

```bash
python -c "
from imp_claude.code.genesis.consensus_engine import evaluate_quorum, project_review_state, ReviewConfig, QuorumThreshold, AbstentionModel
from datetime import datetime, timezone
import json, pathlib

events = [json.loads(l) for l in pathlib.Path('.ai-workspace/events/events.jsonl').read_text().splitlines() if l.strip()]
pub_ev = next((e for e in events if e.get('event_type') in ('proposal_published', 'ProposalPublished') and e.get('review_id') == '{review_id}'), None)
if not pub_ev:
    print('no_session')
    exit()
data = pub_ev.get('data', {})
roster = data.get('roster', [])
close_time = datetime.fromisoformat(data.get('review_closes_at', '').replace('Z', '+00:00'))
config = ReviewConfig(
    roster=roster,
    quorum=QuorumThreshold[data.get('quorum', 'majority').upper()],
    abstention_model=AbstentionModel.NEUTRAL,
    min_participation_ratio=float(data.get('min_participation_ratio', 0.5)),
    published_at=datetime.fromisoformat(data.get('published_at', pub_ev.get('timestamp', '')).replace('Z', '+00:00')),
    review_closes_at=close_time,
    min_duration_seconds=0,
)
votes, comments = project_review_state(events, '{review_id}', close_time)
result = evaluate_quorum(config, votes, comments, now=datetime.now(timezone.utc))
print('converged:', result.converged, 'approve:', result.approve_votes, 'reject:', result.reject_votes, 'abstain:', result.abstain_votes)
"
```

### Step 5: Report

```
Vote cast: {review_id}
  Participant: {participant_id}
  Verdict:     {approve ✓ | reject ✗ | abstain ~}
  Rationale:   {rationale or "(none)"}

Current tally:
  ✓ approve:  {n}
  ✗ reject:   {n}
  ~ abstain:  {n}
  · pending:  {n}

{If converged}: ✓ Quorum reached — consensus_reached
{If not yet}:  ~ Awaiting {pending} more vote(s)
```

## Examples

```bash
# Approve an ADR as the dev observer
/gen-vote \
  --review-id REVIEW-ADR-S-027-1 \
  --verdict approve \
  --rationale "Veto semantics are well-specified and consistent with ADR-S-025 quorum algebra."

# Reject with a gating concern
/gen-vote \
  --review-id REVIEW-ADR-S-027-1 \
  --verdict reject \
  --rationale "Missing: rollback path if veto is exercised mid-sequence." \
  --gating

# Abstain (no opinion on this domain)
/gen-vote \
  --review-id REVIEW-ADR-S-027-1 \
  --verdict abstain \
  --rationale "CI/CD-neutral change — no opinion from this observer."
```
