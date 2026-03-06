#!/bin/bash
# ============================================================================
# post-commit-spec-watch.sh — Git post-commit hook for spec_modified events
#
# Detects changes to specification/ files in every git commit and emits
# spec_modified events to .ai-workspace/events/events.jsonl.
#
# Install:
#   cp post-commit-spec-watch.sh .git/hooks/post-commit
#   chmod +x .git/hooks/post-commit
#
# Or append to an existing post-commit:
#   cat post-commit-spec-watch.sh >> .git/hooks/post-commit
#
# Implements: REQ-EVOL-004 (spec_modified event on specification/ changes)
# Processing regime: REFLEX (§4.3) — fires unconditionally on git commit
# Reference: ol_event.spec_modified(), ADR-S-010 (Spec Evolution Pipeline)
# ============================================================================

# Never block — fail silently so git commits always succeed
set -uo pipefail
trap 'exit 0' ERR EXIT

# -----------------------------------------------------------------------
# Resolve project root and workspace
# -----------------------------------------------------------------------
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
WORKSPACE="$REPO_ROOT/.ai-workspace"
EVENTS_FILE="$WORKSPACE/events/events.jsonl"

# Only activate if .ai-workspace exists (project is initialised)
if [ ! -d "$WORKSPACE" ]; then
  exit 0
fi

# -----------------------------------------------------------------------
# Detect specification/ changes in the latest commit
# -----------------------------------------------------------------------
# Get list of changed files in HEAD that are under specification/
CHANGED_SPEC_FILES=$(git diff-tree --no-commit-id -r --name-only HEAD 2>/dev/null \
  | grep '^specification/' || true)

if [ -z "$CHANGED_SPEC_FILES" ]; then
  exit 0
fi

# -----------------------------------------------------------------------
# Prepare shared event fields
# -----------------------------------------------------------------------
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
PROJECT=$(basename "$REPO_ROOT")
COMMIT_HASH=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
COMMIT_MSG=$(git log -1 --pretty=format:%s 2>/dev/null | head -c 120 || echo "")
ACTOR=$(git log -1 --pretty=format:%ae 2>/dev/null || echo "unknown")

# -----------------------------------------------------------------------
# Ensure events directory exists
# -----------------------------------------------------------------------
mkdir -p "$(dirname "$EVENTS_FILE")"

# -----------------------------------------------------------------------
# Emit one spec_modified event per changed specification/ file
# -----------------------------------------------------------------------
sha256_of() {
  local file="$1"
  if command -v sha256sum &>/dev/null; then
    sha256sum "$file" | awk '{print $1}'
  elif command -v shasum &>/dev/null; then
    shasum -a 256 "$file" | awk '{print $1}'
  else
    echo "unknown"
  fi
}

sha256_of_git_object() {
  # $1 = ref (e.g. HEAD or HEAD^1), $2 = relative path
  local ref="$1"
  local path="$2"
  local content
  content=$(git show "${ref}:${path}" 2>/dev/null) || { echo "absent"; return; }
  if command -v sha256sum &>/dev/null; then
    echo "$content" | sha256sum | awk '{print $1}'
  elif command -v shasum &>/dev/null; then
    echo "$content" | shasum -a 256 | awk '{print $1}'
  else
    echo "unknown"
  fi
}

while IFS= read -r FILE; do
  [ -z "$FILE" ] && continue

  # Compute hashes
  NEW_HASH="sha256:$(sha256_of_git_object HEAD "$FILE")"
  PREV_HASH="sha256:$(sha256_of_git_object HEAD^1 "$FILE")"

  # Build what_changed description from commit message + file
  WHAT_CHANGED="commit ${COMMIT_HASH:0:8}: ${COMMIT_MSG:-manual edit}"

  # Emit spec_modified event (flat format matching fd_emit.make_event)
  EVENT=$(jq -nc \
    --arg ts         "$TIMESTAMP" \
    --arg proj       "$PROJECT" \
    --arg file       "$FILE" \
    --arg what       "$WHAT_CHANGED" \
    --arg prev_hash  "$PREV_HASH" \
    --arg new_hash   "$NEW_HASH" \
    --arg trigger_id "manual" \
    --arg trigger_ty "manual" \
    --arg actor      "$ACTOR" \
    '{
      event_type:       "spec_modified",
      timestamp:        $ts,
      project:          $proj,
      file:             $file,
      what_changed:     $what,
      previous_hash:    $prev_hash,
      new_hash:         $new_hash,
      trigger_event_id: $trigger_id,
      trigger_type:     $trigger_ty,
      actor:            $actor
    }')

  echo "$EVENT" >> "$EVENTS_FILE"

done <<< "$CHANGED_SPEC_FILES"

exit 0
