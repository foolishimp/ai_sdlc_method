#!/bin/bash
# ============================================================================
# on-observer-check.sh — Observer Agent Dispatch Hook
#
# Dispatches the appropriate observer agent based on workspace context:
#   - gen-dev-observer:  fires when inside an active feature iteration
#   - gen-cicd-observer: fires when CI/CD assets (build logs, pipeline results)
#                        are present in the workspace
#   - gen-ops-observer:  fires when deployed system telemetry is configured
#
# This hook wires the three observer agents to actual runtime triggers.
# Agents exist as prompts; this hook is the mechanism that calls them.
#
# Processing regime: REFLEX (§4.3) — fires unconditionally at check boundary.
# All three observers are stateless (same inputs → same outputs).
# This hook only determines WHICH observer to dispatch; the agent does the work.
#
# Implements: REQ-LIFE-010, REQ-LIFE-011, REQ-LIFE-012
# Reference: AI_SDLC_ASSET_GRAPH_MODEL.md §7.1 (Observer Loop),
#            ADR-017 (Functor Execution Model), sensory_monitors.yml
# ============================================================================

set -euo pipefail

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
TRIGGER_EVENT=$(echo "$INPUT" | jq -r '.trigger_event // "manual"')

if [ -z "$CWD" ]; then
  exit 0
fi

WORKSPACE="$CWD/.ai-workspace"

# Only activate if .ai-workspace exists (project is initialised)
if [ ! -d "$WORKSPACE" ]; then
  exit 0
fi

EVENTS_FILE="$WORKSPACE/events/events.jsonl"
TIMESTAMP=$(date -u "+%Y-%m-%dT%H:%M:%SZ")

# Resolve project name for events
PROJ_NAME=$(grep 'name:' "$WORKSPACE"/*/context/project_constraints.yml 2>/dev/null | \
  head -1 | sed 's/.*name: *"\{0,1\}\([^"]*\)"\{0,1\}/\1/' || echo "unknown")

emit_event() {
  local event_type="$1"
  local observer_id="$2"
  local context="$3"
  local ts
  ts=$(date -u "+%Y-%m-%dT%H:%M:%SZ")

  if [ -d "$WORKSPACE/events" ]; then
    EVENT="{\"event_type\":\"${event_type}\",\"timestamp\":\"${ts}\",\"project\":\"${PROJ_NAME}\",\"observer_id\":\"${observer_id}\",\"data\":{\"trigger\":\"${TRIGGER_EVENT}\",\"context\":\"${context}\",\"hook\":\"on-observer-check.sh\"}}"
    echo "$EVENT" >> "${EVENTS_FILE:-$WORKSPACE/events/events.jsonl}"
  fi
}

DISPATCHED=0

# -----------------------------------------------------------------------
# Dispatch 1: gen-dev-observer (REQ-LIFE-010)
# Trigger: active feature iteration detected — there are features in the
# iterating or pending state, or recent iteration_completed/edge_started
# events exist in the event log.
# -----------------------------------------------------------------------
DEV_OBSERVER_TRIGGERED=false

# Check 1a: any active feature vectors exist
if [ -d "$WORKSPACE/features/active" ] && ls "$WORKSPACE/features/active"/*.yml 2>/dev/null | head -1 >/dev/null 2>&1; then
  DEV_OBSERVER_TRIGGERED=true
fi

# Check 1b: recent iteration events (last 50 events for speed)
if [ -f "$EVENTS_FILE" ] && ! $DEV_OBSERVER_TRIGGERED; then
  if tail -50 "$EVENTS_FILE" 2>/dev/null | \
     grep -qE '"event_type"\s*:\s*"(iteration_completed|edge_started|iteration_abandoned)"' 2>/dev/null; then
    DEV_OBSERVER_TRIGGERED=true
  fi
fi

# Check 1c: explicit iteration trigger
if [ "$TRIGGER_EVENT" = "iteration_completed" ] || \
   [ "$TRIGGER_EVENT" = "edge_converged" ] || \
   [ "$TRIGGER_EVENT" = "gaps_validated" ]; then
  DEV_OBSERVER_TRIGGERED=true
fi

if $DEV_OBSERVER_TRIGGERED; then
  emit_event "observer_dispatched" "dev_observer" "active_feature_iteration"
  DISPATCHED=$((DISPATCHED + 1))
  echo "[observer] gen-dev-observer dispatched (active feature iteration detected)"
  echo "  → Load agent: agents/gen-dev-observer.md"
  echo "  → Implements: REQ-LIFE-010"
fi

# -----------------------------------------------------------------------
# Dispatch 2: gen-cicd-observer (REQ-LIFE-011)
# Trigger: CI/CD assets are present — build logs, workflow configs,
# pipeline results, or deployment manifests in the workspace.
# -----------------------------------------------------------------------
CICD_OBSERVER_TRIGGERED=false

# Check 2a: GitHub Actions workflow files
if [ -d "$CWD/.github/workflows" ] && ls "$CWD/.github/workflows"/*.yml 2>/dev/null | head -1 >/dev/null 2>&1; then
  CICD_OBSERVER_TRIGGERED=true
fi

# Check 2b: CI config files (common CI/CD systems)
for ci_file in \
  "$CWD/.travis.yml" \
  "$CWD/Jenkinsfile" \
  "$CWD/.circleci/config.yml" \
  "$CWD/azure-pipelines.yml" \
  "$CWD/Makefile" \
  "$CWD/deploy.sh"; do
  if [ -f "$ci_file" ]; then
    CICD_OBSERVER_TRIGGERED=true
    break
  fi
done

# Check 2c: build artifacts exist
for artifact_dir in \
  "$CWD/dist" \
  "$CWD/build" \
  "$CWD/.coverage"; do
  if [ -d "$artifact_dir" ] || [ -f "$artifact_dir" ]; then
    CICD_OBSERVER_TRIGGERED=true
    break
  fi
done

# Check 2d: cicd asset in workspace (feature vector at uat_tests or cicd edge)
if [ -d "$WORKSPACE/features/active" ] && ! $CICD_OBSERVER_TRIGGERED; then
  for f in "$WORKSPACE/features/active"/*.yml; do
    if [ -f "$f" ] && grep -q 'uat_tests\|cicd\|running_system' "$f" 2>/dev/null; then
      CICD_OBSERVER_TRIGGERED=true
      break
    fi
  done
fi

# Check 2e: explicit cicd trigger event
if [ "$TRIGGER_EVENT" = "release_created" ] || \
   [ "$TRIGGER_EVENT" = "pipeline_completed" ] || \
   [ "$TRIGGER_EVENT" = "build_completed" ]; then
  CICD_OBSERVER_TRIGGERED=true
fi

if $CICD_OBSERVER_TRIGGERED; then
  emit_event "observer_dispatched" "cicd_observer" "cicd_assets_present"
  DISPATCHED=$((DISPATCHED + 1))
  echo "[observer] gen-cicd-observer dispatched (CI/CD assets detected)"
  echo "  → Load agent: agents/gen-cicd-observer.md"
  echo "  → Implements: REQ-LIFE-011"
fi

# -----------------------------------------------------------------------
# Dispatch 3: gen-ops-observer (REQ-LIFE-012)
# Trigger: deployed system telemetry is configured — telemetry endpoint
# in project_constraints.yml, or telemetry events in the event log,
# or a running_system asset exists in a feature vector.
# -----------------------------------------------------------------------
OPS_OBSERVER_TRIGGERED=false

# Check 3a: telemetry endpoint configured in project_constraints.yml
for constraints_file in \
  "$WORKSPACE"/*/context/project_constraints.yml \
  "$WORKSPACE/context/project_constraints.yml"; do
  if [ -f "$constraints_file" ] && grep -q 'telemetry_endpoint\|performance_envelope\|sla_latency' "$constraints_file" 2>/dev/null; then
    OPS_OBSERVER_TRIGGERED=true
    break
  fi
done

# Check 3b: telemetry or running_system in feature vector trajectory
if [ -d "$WORKSPACE/features/active" ] && ! $OPS_OBSERVER_TRIGGERED; then
  for f in "$WORKSPACE/features/active"/*.yml; do
    if [ -f "$f" ] && grep -q 'running_system\|telemetry' "$f" 2>/dev/null; then
      OPS_OBSERVER_TRIGGERED=true
      break
    fi
  done
fi

# Check 3c: interoceptive/exteroceptive signals in recent events
if [ -f "$EVENTS_FILE" ] && ! $OPS_OBSERVER_TRIGGERED; then
  if tail -50 "$EVENTS_FILE" 2>/dev/null | \
     grep -qE '"event_type"\s*:\s*"(interoceptive_signal|exteroceptive_signal|observer_signal)"' 2>/dev/null; then
    OPS_OBSERVER_TRIGGERED=true
  fi
fi

# Check 3d: explicit ops trigger event
if [ "$TRIGGER_EVENT" = "monitoring_alert" ] || \
   [ "$TRIGGER_EVENT" = "sla_breach" ] || \
   [ "$TRIGGER_EVENT" = "deployment_completed" ]; then
  OPS_OBSERVER_TRIGGERED=true
fi

if $OPS_OBSERVER_TRIGGERED; then
  emit_event "observer_dispatched" "ops_observer" "telemetry_configured"
  DISPATCHED=$((DISPATCHED + 1))
  echo "[observer] gen-ops-observer dispatched (operational telemetry detected)"
  echo "  → Load agent: agents/gen-ops-observer.md"
  echo "  → Implements: REQ-LIFE-012"
fi

# -----------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------
if [ "$DISPATCHED" -eq 0 ]; then
  echo "[observer] No observer dispatch conditions met (workspace not ready for observation)"
else
  echo "[observer] ${DISPATCHED} observer agent(s) dispatched"
fi

exit 0
