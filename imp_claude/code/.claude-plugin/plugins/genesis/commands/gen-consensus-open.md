# /gen-consensus-open — Open a CONSENSUS Review Session

<!-- Implements: REQ-F-CONSENSUS-001, REQ-EVAL-003 -->
<!-- Reference: ADR-S-025 (CONSENSUS Functor), ADR-S-025 §Phase 1 (Publication) -->

Open a multi-stakeholder evaluation session on a spec artifact. Emits
`proposal_published`, invokes each roster agent with explicit trigger context,
then monitors for votes until quorum is reached or the window closes.

## Usage

```
/gen-consensus-open --artifact <path> --roster <agents> [--quorum majority|supermajority|unanimity] [--min-duration <ISO duration>]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--artifact` | required | Path to the artifact under review (relative to project root) |
| `--roster` | required | Comma-separated agent IDs (e.g. `gen-dev-observer,gen-cicd-observer,gen-ops-observer`) |
| `--quorum` | `majority` | Quorum threshold |
| `--min-duration` | `PT0S` (immediate) | ISO 8601 minimum deliberation window (e.g. `PT1H`, `P1D`) |
| `--review-id` | auto-generated | Override the review session ID |

## Instructions

### Step 1: Validate inputs

1. Confirm `--artifact` file exists at the given path
2. Parse `--roster` into a list of agent IDs
3. Generate `review_id` if not provided: `REVIEW-{artifact-slug}-{seq}` where seq is count of existing review sessions + 1
4. Set `review_closes_at` = now + 24h (default window; override with `--min-duration`)
5. Set `published_at` = now

### Step 2: Read the artifact

Read the full contents of `--artifact`. This is the document agents will evaluate.

### Step 3: Emit `proposal_published` event

Append to `.ai-workspace/events/events.jsonl`:

```json
{
  "event_type": "proposal_published",
  "review_id": "{review_id}",
  "timestamp": "{ISO 8601}",
  "project": "{project_name}",
  "actor": "local-user",
  "data": {
    "artifact": "{artifact_path}",
    "asset_version": "v1",
    "published_by": "local-user",
    "roster": ["{agent_id}", "..."],
    "quorum": "{quorum_threshold}",
    "min_participation_ratio": 0.5,
    "published_at": "{ISO 8601}",
    "review_closes_at": "{ISO 8601}"
  }
}
```

### Step 4: Invoke each roster agent

For each agent in the roster, invoke it with explicit trigger context.

**Trigger payload** (passed as JSON to each agent invocation):

```json
{
  "trigger_reason": "review_opened",
  "review_id": "{review_id}",
  "artifact": "{artifact_path}",
  "artifact_content": "{full artifact text}",
  "roster": ["{agent_id}", "..."],
  "quorum": "{quorum_threshold}",
  "review_closes_at": "{ISO 8601}",
  "instruction": "You are a reviewer in a CONSENSUS session. Read the artifact and the existing comment thread (events.jsonl filtered by review_id), then cast your vote using /gen-vote or emit a vote_cast event directly. Your first act must be to verify your trigger context. If review_id is missing or does not match an open review, do nothing and exit."
}
```

Invoke agents sequentially (not parallel) so each agent sees the previous agent's vote in the event log before forming its own opinion. This produces richer deliberation.

### Step 5: Run quorum check after each agent

After each agent responds, run the quorum check:

```bash
python -c "
from imp_claude.code.genesis.consensus_engine import evaluate_quorum, project_review_state, ReviewConfig, QuorumThreshold, AbstentionModel
from datetime import datetime, timezone
import json, pathlib

events = [json.loads(l) for l in pathlib.Path('.ai-workspace/events/events.jsonl').read_text().splitlines() if l.strip()]
close_time = datetime.fromisoformat('{review_closes_at}'.replace('Z', '+00:00'))
config = ReviewConfig(
    roster={roster_list},
    quorum=QuorumThreshold.{quorum_upper},
    abstention_model=AbstentionModel.NEUTRAL,
    min_participation_ratio=0.5,
    published_at=datetime.fromisoformat('{published_at}'.replace('Z', '+00:00')),
    review_closes_at=close_time,
    min_duration_seconds=0,
)
votes, comments = project_review_state(events, '{review_id}', close_time)
result = evaluate_quorum(config, votes, comments, now=datetime.now(timezone.utc))
print('converged:', result.converged, 'approve:', result.approve_votes, 'reject:', result.reject_votes, 'abstain:', result.abstain_votes)
"
```

### Step 6: Terminal outcomes

**If `result.converged == True`**:

1. Emit `consensus_reached` event:
```json
{
  "event_type": "consensus_reached",
  "review_id": "{review_id}",
  "timestamp": "{ISO 8601}",
  "project": "{project_name}",
  "data": {
    "artifact": "{artifact_path}",
    "asset_version": "v1",
    "quorum_threshold": "{quorum}",
    "roster_size": 0,
    "approve_votes": 0,
    "reject_votes": 0,
    "abstain_votes": 0,
    "approve_ratio": 0.0,
    "participation_ratio": 0.0,
    "gating_comments_dispositioned": 0
  }
}
```

2. Update the artifact's ADR status to `Accepted` if the artifact is an ADR markdown file (change `**Status**: Proposed` → `**Status**: Accepted`)

3. Report: `✓ consensus_reached on {review_id} — {approve}/{total} approve ({ratio}%)`

**If `result.converged == False` after all agents have voted**:

1. Emit `consensus_failed` event with `failure_reason` and `available_paths`
2. Report: `✗ consensus_failed — {failure_reason}. Available: {available_paths}`
3. Do NOT automatically re-open. Recovery path selection is an F_H decision.

### Step 7: Display summary

```
CONSENSUS Review: {review_id}
==============================
Artifact:  {artifact_path}
Roster:    {agent_ids}
Quorum:    {quorum_threshold}

Votes:
  ✓ approve:  {n}
  ✗ reject:   {n}
  ~ abstain:  {n}
  · pending:  {n}

Approve ratio: {ratio}%
Result: {consensus_reached | consensus_failed: {reason}}
```

## Examples

```bash
# Review ADR-S-027 (veto semantics) with 3 agents, majority quorum
/gen-consensus-open \
  --artifact specification/adrs/ADR-S-027-spec-consolidation-authority-boundaries.md \
  --roster gen-dev-observer,gen-cicd-observer,gen-ops-observer \
  --quorum majority

# Review a feature proposal requiring supermajority
/gen-consensus-open \
  --artifact .ai-workspace/reviews/pending/PROP-001.yml \
  --roster gen-dev-observer,gen-cicd-observer \
  --quorum supermajority \
  --min-duration PT4H
```
