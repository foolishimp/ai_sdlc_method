#!/bin/bash
# ============================================================================
# on-edge-converged.sh — PostEvent hook for dev-observer invocation
#
# Fires after edge_converged, gaps_validated, and release_created events.
# Reads the workspace state and spec, computes delta, and surfaces
# observations to the dev-observer agent for human review.
#
# This hook CLOSES the abiogenesis loop:
#   act → emit event → observe (this hook) → judge → feed back
#
# The hook itself is F_D (deterministic) — it collects data and formats
# the invocation. The dev-observer agent is F_P (probabilistic) — it
# interprets deltas and drafts intents.
#
# Implements: REQ-LIFE-010 (Dev Observer), REQ-SENSE-001, REQ-SENSE-002
# Processing regime: REFLEX (§4.3) — fires unconditionally after qualifying events
# Reference: ADR-011 (Consciousness Loop), ADR-017 (Functor Execution Model)
# ============================================================================

set -euo pipefail

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')

if [ -z "$CWD" ]; then
  exit 0
fi

WORKSPACE="$CWD/.ai-workspace"

# Only activate if .ai-workspace exists (project is initialised)
if [ ! -d "$WORKSPACE" ]; then
  exit 0
fi

EVENTS_FILE="$WORKSPACE/events/events.jsonl"

# -----------------------------------------------------------------------
# Collect workspace snapshot (F_D — deterministic data collection)
# -----------------------------------------------------------------------

# Count events
EVENT_COUNT=0
if [ -f "$EVENTS_FILE" ]; then
  EVENT_COUNT=$(wc -l < "$EVENTS_FILE" | tr -d ' ')
fi

# Count active feature vectors
ACTIVE_FEATURES=0
CONVERGED_FEATURES=0
STUCK_FEATURES=0
if [ -d "$WORKSPACE/features/active" ]; then
  for f in "$WORKSPACE/features/active"/*.yml; do
    if [ -f "$f" ]; then
      ACTIVE_FEATURES=$((ACTIVE_FEATURES + 1))
      # Check if converged
      if grep -q 'status: converged' "$f" 2>/dev/null; then
        CONVERGED_FEATURES=$((CONVERGED_FEATURES + 1))
      fi
    fi
  done
fi

# Detect stuck features (same delta 3+ consecutive iterations)
if [ -f "$EVENTS_FILE" ]; then
  # Find features where the last 3 iteration_completed events have the same non-zero delta
  STUCK_FEATURES=$(grep '"iteration_completed"' "$EVENTS_FILE" 2>/dev/null | \
    jq -r 'select(.delta != null and .delta > 0) | "\(.feature):\(.delta)"' 2>/dev/null | \
    sort | uniq -c | sort -rn | \
    awk '$1 >= 3 {count++} END {print count+0}' 2>/dev/null || echo "0")
fi

# Get last event type for context
LAST_EVENT_TYPE=""
if [ -f "$EVENTS_FILE" ]; then
  LAST_EVENT_TYPE=$(tail -1 "$EVENTS_FILE" 2>/dev/null | jq -r '.event_type // empty' 2>/dev/null || true)
fi

# Count unactioned intent_raised events (signals without corresponding spawn/spec_modified)
UNACTIONED_INTENTS=0
if [ -f "$EVENTS_FILE" ]; then
  INTENT_IDS=$(grep '"intent_raised"' "$EVENTS_FILE" 2>/dev/null | jq -r '.data.intent_id // empty' 2>/dev/null || true)
  if [ -n "$INTENT_IDS" ]; then
    for iid in $INTENT_IDS; do
      # Check if this intent was acted on (spawn_created or spec_modified referencing it)
      ACTED=$(grep -c "$iid" "$EVENTS_FILE" 2>/dev/null || echo "0")
      if [ "$ACTED" -le 1 ]; then
        UNACTIONED_INTENTS=$((UNACTIONED_INTENTS + 1))
      fi
    done
  fi
fi

# -----------------------------------------------------------------------
# Build observer invocation context (stdout goes to the agent)
# -----------------------------------------------------------------------

cat <<EOF
Dev Observer triggered by: ${LAST_EVENT_TYPE}

Workspace snapshot:
  Events:             ${EVENT_COUNT} total
  Active features:    ${ACTIVE_FEATURES} (${CONVERGED_FEATURES} converged)
  Stuck features:     ${STUCK_FEATURES}
  Unactioned intents: ${UNACTIONED_INTENTS}

The dev-observer agent (agents/gen-dev-observer.md) should now:
1. Read the last 20 events from events.jsonl
2. Read active feature vectors
3. Compute delta(workspace_state, spec)
4. Classify any non-zero deltas by signal source
5. Present findings for human review

If no significant deltas are found, acknowledge and continue.
EOF

exit 0
