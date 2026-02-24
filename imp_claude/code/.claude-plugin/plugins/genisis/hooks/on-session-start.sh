#!/bin/bash
# ============================================================================
# on-session-start.sh — SessionStart hook for workspace health check
#
# Fires when a new Claude Code session opens. Runs quick diagnostics
# on workspace integrity and surfaces any issues before work begins.
#
# This is F_D(Sense) — deterministic observation of workspace health.
# No judgment, no modification — just data collection and reporting.
#
# Implements: REQ-UX-005 (Recovery & Self-Healing)
# Processing regime: REFLEX (§4.3) — fires unconditionally at session boundary
# Reference: /gen-start Step 10, ADR-017 (Functor Execution Model)
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

# Clear session-scoped artifact tracking (ADR-CG-006)
rm -f "$WORKSPACE/.session_assets_seen"

EVENTS_FILE="$WORKSPACE/events/events.jsonl"
ISSUES=""
ISSUE_COUNT=0

# -----------------------------------------------------------------------
# Check 1: Event log exists and is valid JSON
# -----------------------------------------------------------------------
if [ -f "$EVENTS_FILE" ]; then
  EVENT_COUNT=$(wc -l < "$EVENTS_FILE" | tr -d ' ')

  # Check for corrupted lines (invalid JSON)
  INVALID_LINES=0
  while IFS= read -r line; do
    if [ -n "$line" ] && ! echo "$line" | jq empty 2>/dev/null; then
      INVALID_LINES=$((INVALID_LINES + 1))
    fi
  done < "$EVENTS_FILE"

  if [ "$INVALID_LINES" -gt 0 ]; then
    ISSUES="${ISSUES}  [!] Event log: ${INVALID_LINES} corrupted JSON line(s) in events.jsonl\n"
    ISSUE_COUNT=$((ISSUE_COUNT + 1))
  fi

  # Check for staleness (days since last event)
  LAST_TIMESTAMP=$(tail -1 "$EVENTS_FILE" 2>/dev/null | jq -r '.timestamp // empty' 2>/dev/null || true)
  if [ -n "$LAST_TIMESTAMP" ]; then
    LAST_EPOCH=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${LAST_TIMESTAMP%%[.Z]*}" "+%s" 2>/dev/null || \
                 date -d "${LAST_TIMESTAMP%%[.Z]*}" "+%s" 2>/dev/null || echo "0")
    NOW_EPOCH=$(date "+%s")
    if [ "$LAST_EPOCH" -gt 0 ]; then
      DAYS_STALE=$(( (NOW_EPOCH - LAST_EPOCH) / 86400 ))
      if [ "$DAYS_STALE" -ge 7 ]; then
        ISSUES="${ISSUES}  [!] Event staleness: last event was ${DAYS_STALE} days ago\n"
        ISSUE_COUNT=$((ISSUE_COUNT + 1))
      fi
    fi
  fi
else
  if [ -d "$WORKSPACE/events" ]; then
    ISSUES="${ISSUES}  [!] Event log: events.jsonl does not exist (workspace initialised but no events)\n"
    ISSUE_COUNT=$((ISSUE_COUNT + 1))
  fi
  EVENT_COUNT=0
fi

# -----------------------------------------------------------------------
# Check 2: Feature vector consistency
# -----------------------------------------------------------------------
ACTIVE_COUNT=0
STUCK_COUNT=0
if [ -d "$WORKSPACE/features/active" ]; then
  for f in "$WORKSPACE/features/active"/*.yml; do
    if [ -f "$f" ]; then
      ACTIVE_COUNT=$((ACTIVE_COUNT + 1))

      # Check for valid feature ID format
      FEATURE_ID=$(grep '^feature:' "$f" 2>/dev/null | sed 's/feature: *"\{0,1\}\([^"]*\)"\{0,1\}/\1/' || true)
      if [ -n "$FEATURE_ID" ] && ! echo "$FEATURE_ID" | grep -qE '^REQ-F-[A-Z]+-[0-9]+$'; then
        if ! echo "$FEATURE_ID" | grep -q '{'; then  # skip template placeholders
          ISSUES="${ISSUES}  [!] Feature format: ${FEATURE_ID} does not match REQ-F-*-NNN pattern\n"
          ISSUE_COUNT=$((ISSUE_COUNT + 1))
        fi
      fi
    fi
  done
fi

# -----------------------------------------------------------------------
# Check 3: Abandoned iteration detection (REQ-SUPV-003)
# If .edge_in_progress exists from a prior session, the previous session
# ended without completing an iteration. Emit iteration_abandoned event.
# -----------------------------------------------------------------------
EDGE_FILE="$WORKSPACE/.edge_in_progress"
if [ -f "$EDGE_FILE" ]; then
  ABANDONED_EDGE=$(cat "$EDGE_FILE")
  ABANDONED_START=$(cat "$WORKSPACE/.edge_start_time" 2>/dev/null || echo "0")
  NOW_EPOCH=$(date "+%s")
  SECONDS_SINCE=$((NOW_EPOCH - ABANDONED_START))

  # Find the last iteration number for this edge from events
  LAST_ITER=0
  if [ -f "$EVENTS_FILE" ]; then
    LAST_ITER=$(grep '"iteration_completed"' "$EVENTS_FILE" 2>/dev/null | \
      grep "\"edge\":\"${ABANDONED_EDGE}\"" 2>/dev/null | \
      tail -1 | jq -r '.iteration // .data.iteration // 0' 2>/dev/null || echo "0")
  fi

  # Emit iteration_abandoned event
  if [ -f "$EVENTS_FILE" ] || [ -d "$WORKSPACE/events" ]; then
    PROJ_NAME=$(grep 'name:' "$WORKSPACE"/*/context/project_constraints.yml 2>/dev/null | head -1 | sed 's/.*name: *"\{0,1\}\([^"]*\)"\{0,1\}/\1/' || echo "unknown")
    TIMESTAMP=$(date -u "+%Y-%m-%dT%H:%M:%SZ")
    EVENT="{\"event_type\":\"iteration_abandoned\",\"timestamp\":\"$TIMESTAMP\",\"project\":\"$PROJ_NAME\",\"feature\":\"\",\"edge\":\"$ABANDONED_EDGE\",\"data\":{\"last_iteration\":$LAST_ITER,\"seconds_since_last_event\":$SECONDS_SINCE}}"
    echo "$EVENT" >> "${EVENTS_FILE:-$WORKSPACE/events/events.jsonl}"
  fi

  ISSUES="${ISSUES}  [!] Abandoned iteration: edge '${ABANDONED_EDGE}' was in progress when previous session ended\n"
  ISSUE_COUNT=$((ISSUE_COUNT + 1))

  # Clean up stale state
  rm -f "$EDGE_FILE" "$WORKSPACE/.edge_start_time" "$WORKSPACE/.edge_events_baseline"
fi

# -----------------------------------------------------------------------
# Check 4: STATUS.md freshness
# -----------------------------------------------------------------------
STATUS_FILE="$WORKSPACE/STATUS.md"
if [ -f "$STATUS_FILE" ] && [ -f "$EVENTS_FILE" ]; then
  STATUS_MTIME=$(stat -f%m "$STATUS_FILE" 2>/dev/null || stat -c%Y "$STATUS_FILE" 2>/dev/null || echo "0")
  EVENTS_MTIME=$(stat -f%m "$EVENTS_FILE" 2>/dev/null || stat -c%Y "$EVENTS_FILE" 2>/dev/null || echo "0")
  if [ "$STATUS_MTIME" -lt "$EVENTS_MTIME" ]; then
    ISSUES="${ISSUES}  [i] STATUS.md is older than events.jsonl — consider running /gen-status\n"
    # info level, don't count as issue
  fi
fi

# -----------------------------------------------------------------------
# Report
# -----------------------------------------------------------------------
if [ "$ISSUE_COUNT" -gt 0 ]; then
  REPORT=$(printf "Workspace health check: ${ISSUE_COUNT} issue(s) found\n${ISSUES}\n  Run /gen-status --health for full diagnostics.")
  echo "$REPORT"
elif [ "$EVENT_COUNT" -gt 0 ]; then
  echo "Workspace healthy: ${EVENT_COUNT} events, ${ACTIVE_COUNT} active features."
fi

exit 0
