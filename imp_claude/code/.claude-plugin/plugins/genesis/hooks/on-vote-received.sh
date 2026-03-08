#!/bin/bash
# ============================================================================
# on-vote-received.sh — CONSENSUS Quorum Check Hook
#
# Fires after a vote_cast event is written to events.jsonl.
# Runs the deterministic quorum projection and:
#   - If quorum met → emits consensus_reached, triggers instigating agent
#   - If window closed without quorum → emits consensus_failed
#   - Otherwise → logs current tally and waits for next vote
#
# Usage (manual):
#   echo '{"cwd":"/path/to/project","review_id":"REVIEW-ADR-S-027-1"}' | ./on-vote-received.sh
#
# Usage (automatic, via gen-consensus-open):
#   Called inline by the command after each roster agent votes.
#
# Processing regime: REFLEX (§VI) — fires unconditionally after each vote.
#   Quorum is deterministic (F_D). No LLM needed.
#
# Implements: REQ-F-CONSENSUS-001, REQ-EVAL-003
# Reference: ADR-S-025 §Phase 4 (Five Quorum Checks), consensus_engine.py
# ============================================================================

set -euo pipefail

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
REVIEW_ID=$(echo "$INPUT" | jq -r '.review_id // empty')
EVENTS_FILE="${CWD}/.ai-workspace/events/events.jsonl"

if [ -z "$CWD" ] || [ -z "$REVIEW_ID" ]; then
  echo "[on-vote-received] ERROR: cwd and review_id are required" >&2
  exit 1
fi

if [ ! -f "$EVENTS_FILE" ]; then
  echo "[on-vote-received] No events.jsonl found at $EVENTS_FILE" >&2
  exit 1
fi

# Resolve project name from events.jsonl (first event with project field)
PROJ_NAME=$(grep '"project"' "$EVENTS_FILE" | head -1 | jq -r '.project // "unknown"' 2>/dev/null || echo "unknown")

TIMESTAMP=$(date -u "+%Y-%m-%dT%H:%M:%SZ")

# ─── Run quorum projection ─────────────────────────────────────────────────

QUORUM_OUTPUT=$(python3 - <<PYEOF
from __future__ import annotations
import json, pathlib, sys
from datetime import datetime, timezone

# Allow running from any CWD
import importlib.util, os

# Try to import from installed package first, then fall back to source path
try:
    from imp_claude.code.genesis.consensus_engine import (
        evaluate_quorum, project_review_state, ReviewConfig,
        QuorumThreshold, AbstentionModel,
    )
except ImportError:
    # Not installed — find the module relative to this script
    script_dir = pathlib.Path("${BASH_SOURCE[0]}").resolve().parent
    repo_root = script_dir.parents[5]  # hooks/ → genesis/ → .claude-plugin/ → plugins/ → code/ → imp_claude/ → root
    sys.path.insert(0, str(repo_root))
    from imp_claude.code.genesis.consensus_engine import (
        evaluate_quorum, project_review_state, ReviewConfig,
        QuorumThreshold, AbstentionModel,
    )

REVIEW_ID = "${REVIEW_ID}"
EVENTS_FILE = pathlib.Path("${EVENTS_FILE}")

lines = [l for l in EVENTS_FILE.read_text().splitlines() if l.strip()]
events = []
for line in lines:
    try:
        events.append(json.loads(line))
    except json.JSONDecodeError:
        continue

# Find the proposal_published event for this review
pub_ev = next(
    (e for e in events
     if e.get("event_type") in ("proposal_published", "ProposalPublished")
     and e.get("review_id") == REVIEW_ID),
    None,
)
if not pub_ev:
    print(json.dumps({"error": f"No proposal_published found for {REVIEW_ID}"}))
    sys.exit(0)

data = pub_ev.get("data", {})
roster = data.get("roster", [])
quorum_str = data.get("quorum", "majority").upper()
min_participation_ratio = float(data.get("min_participation_ratio", 0.5))
review_closes_at_str = data.get("review_closes_at", "")
published_at_str = data.get("published_at", pub_ev.get("timestamp", ""))
min_duration_str = data.get("min_duration_seconds", 0)

QUORUM_MAP = {
    "MAJORITY": QuorumThreshold.MAJORITY,
    "SUPERMAJORITY": QuorumThreshold.SUPERMAJORITY,
    "UNANIMITY": QuorumThreshold.UNANIMITY,
}
quorum_threshold = QUORUM_MAP.get(quorum_str, QuorumThreshold.MAJORITY)

def parse_dt(s):
    if not s:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

review_closes_at = parse_dt(review_closes_at_str)
published_at = parse_dt(published_at_str)
min_duration_seconds = float(min_duration_str) if min_duration_str else 0.0

config = ReviewConfig(
    roster=roster,
    quorum=quorum_threshold,
    abstention_model=AbstentionModel.NEUTRAL,
    min_participation_ratio=min_participation_ratio,
    published_at=published_at,
    review_closes_at=review_closes_at,
    min_duration_seconds=min_duration_seconds,
)

now = datetime.now(timezone.utc)
votes, comments = project_review_state(events, REVIEW_ID, review_closes_at)
result = evaluate_quorum(config, votes, comments, now=now)

print(json.dumps({
    "converged": result.converged,
    "approve_votes": result.approve_votes,
    "reject_votes": result.reject_votes,
    "abstain_votes": result.abstain_votes,
    "non_response_count": result.non_response_count,
    "failure_reason": result.failure_reason.value if result.failure_reason else None,
    "available_paths": result.available_paths,
    "roster_size": len(roster),
    "roster": roster,
    "quorum": quorum_str,
    "artifact": data.get("artifact", ""),
    "approve_ratio": round(result.approve_votes / max(1, result.approve_votes + result.reject_votes), 3),
}))
PYEOF
)

CONVERGED=$(echo "$QUORUM_OUTPUT" | jq -r '.converged // false')
APPROVE=$(echo "$QUORUM_OUTPUT" | jq -r '.approve_votes // 0')
REJECT=$(echo "$QUORUM_OUTPUT" | jq -r '.reject_votes // 0')
ABSTAIN=$(echo "$QUORUM_OUTPUT" | jq -r '.abstain_votes // 0')
PENDING=$(echo "$QUORUM_OUTPUT" | jq -r '.non_response_count // 0')
ROSTER_SIZE=$(echo "$QUORUM_OUTPUT" | jq -r '.roster_size // 0')
QUORUM_TYPE=$(echo "$QUORUM_OUTPUT" | jq -r '.quorum // "MAJORITY"')
ARTIFACT=$(echo "$QUORUM_OUTPUT" | jq -r '.artifact // ""')
APPROVE_RATIO=$(echo "$QUORUM_OUTPUT" | jq -r '.approve_ratio // 0')
ERROR=$(echo "$QUORUM_OUTPUT" | jq -r '.error // empty')

if [ -n "$ERROR" ]; then
  echo "[on-vote-received] WARN: $ERROR"
  exit 0
fi

echo "[on-vote-received] Review: $REVIEW_ID | ✓$APPROVE ✗$REJECT ~$ABSTAIN ·$PENDING / $ROSTER_SIZE | ratio: $APPROVE_RATIO | quorum: $QUORUM_TYPE"

# ─── Terminal outcomes ─────────────────────────────────────────────────────

if [ "$CONVERGED" = "true" ]; then
  echo "[on-vote-received] ✓ QUORUM REACHED — emitting consensus_reached"

  # 1. Emit consensus_reached event
  TOTAL_VOTED=$((APPROVE + REJECT + ABSTAIN))
  PARTICIPATION_RATIO=$(python3 -c "print(round($TOTAL_VOTED / max(1, $ROSTER_SIZE), 3))")

  EVENT=$(jq -n \
    --arg event_type "consensus_reached" \
    --arg review_id "$REVIEW_ID" \
    --arg ts "$TIMESTAMP" \
    --arg project "$PROJ_NAME" \
    --arg artifact "$ARTIFACT" \
    --argjson approve_votes "$APPROVE" \
    --argjson reject_votes "$REJECT" \
    --argjson abstain_votes "$ABSTAIN" \
    --argjson roster_size "$ROSTER_SIZE" \
    --arg approve_ratio "$APPROVE_RATIO" \
    --arg participation_ratio "$PARTICIPATION_RATIO" \
    --arg quorum_threshold "$QUORUM_TYPE" \
    '{
      event_type: $event_type,
      review_id: $review_id,
      timestamp: $ts,
      project: $project,
      data: {
        artifact: $artifact,
        asset_version: "v1",
        quorum_threshold: $quorum_threshold,
        roster_size: $roster_size,
        approve_votes: $approve_votes,
        reject_votes: $reject_votes,
        abstain_votes: $abstain_votes,
        approve_ratio: ($approve_ratio | tonumber),
        participation_ratio: ($participation_ratio | tonumber),
        gating_comments_dispositioned: 0
      }
    }')

  echo "$EVENT" >> "$EVENTS_FILE"
  echo "[on-vote-received] → consensus_reached written to events.jsonl"

  # 2. If artifact is an ADR markdown file, update Status → Accepted
  if [ -n "$ARTIFACT" ] && [ -f "${CWD}/${ARTIFACT}" ]; then
    ARTIFACT_PATH="${CWD}/${ARTIFACT}"
    if grep -q '\*\*Status\*\*: Proposed' "$ARTIFACT_PATH" 2>/dev/null; then
      sed -i '' 's/\*\*Status\*\*: Proposed/**Status**: Accepted/' "$ARTIFACT_PATH"
      echo "[on-vote-received] → ADR status updated: Proposed → Accepted in $ARTIFACT"
    elif grep -q '\*\*Status\*\*: Provisional' "$ARTIFACT_PATH" 2>/dev/null; then
      sed -i '' 's/\*\*Status\*\*: Provisional/**Status**: Accepted/' "$ARTIFACT_PATH"
      echo "[on-vote-received] → ADR status updated: Provisional → Accepted in $ARTIFACT"
    fi
  fi

  echo ""
  echo "✓ consensus_reached on $REVIEW_ID — $APPROVE/$ROSTER_SIZE approve ($(echo "$APPROVE_RATIO * 100" | bc -l | xargs printf "%.0f")%)"

else
  FAILURE_REASON=$(echo "$QUORUM_OUTPUT" | jq -r '.failure_reason // "insufficient_votes"')
  AVAILABLE_PATHS=$(echo "$QUORUM_OUTPUT" | jq -c '.available_paths // []')

  if [ "$FAILURE_REASON" = "window_not_closed" ] || [ "$FAILURE_REASON" = "insufficient_votes" ]; then
    # Not yet closed — still waiting for votes
    echo "[on-vote-received] ~ Review open — waiting ($PENDING pending votes)"
    echo "  → reason: $FAILURE_REASON"
  else
    # Definitively failed (quorum_not_met after window closed, etc.)
    echo "[on-vote-received] ✗ CONSENSUS FAILED — $FAILURE_REASON"

    EVENT=$(jq -n \
      --arg event_type "consensus_failed" \
      --arg review_id "$REVIEW_ID" \
      --arg ts "$TIMESTAMP" \
      --arg project "$PROJ_NAME" \
      --arg artifact "$ARTIFACT" \
      --arg failure_reason "$FAILURE_REASON" \
      --argjson approve_votes "$APPROVE" \
      --argjson reject_votes "$REJECT" \
      --argjson abstain_votes "$ABSTAIN" \
      --argjson available_paths "$AVAILABLE_PATHS" \
      '{
        event_type: $event_type,
        review_id: $review_id,
        timestamp: $ts,
        project: $project,
        data: {
          artifact: $artifact,
          failure_reason: $failure_reason,
          approve_votes: $approve_votes,
          reject_votes: $reject_votes,
          abstain_votes: $abstain_votes,
          available_paths: $available_paths
        }
      }')

    echo "$EVENT" >> "$EVENTS_FILE"
    echo "[on-vote-received] → consensus_failed written to events.jsonl"
    echo ""
    echo "✗ consensus_failed — $FAILURE_REASON. Available: $AVAILABLE_PATHS"
  fi
fi

exit 0
