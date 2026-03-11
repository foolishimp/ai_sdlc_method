# Codex Genesis Getting Started

This guide is for `imp_codex` only.

It covers:
- installing the Codex runtime from this repo
- creating a new project workspace
- using Codex as the primary operator
- running the deterministic flow from the shell
- proving the executable consensus loop without requiring a live multi-party model conversation

It does not cover Claude or Gemini bindings.

## Current Shape

`imp_codex` currently has:
- a Python runtime CLI: `python -m imp_codex.runtime`
- deterministic and runtime-level consensus commands
- a first `start --auto` / intent-dispatch path
- live e2e proof for Codex homeostasis

`imp_codex` does not yet have:
- a one-command external installer like `imp_claude`
- a background autonomous `consensus-observer` daemon that watches comments and responds by itself

Today, the consensus proof is command-driven and event-sourced. Comments, dispositions, votes, and closeout are all written to `.ai-workspace/events/events.jsonl` and `.ai-workspace/reviews/consensus/...`.

## Recommended UX

The default user experience should be:
- you tell Codex what outcome you want
- Codex invokes the runtime commands for you
- you only drop to shell commands when scripting, debugging, or running CI

So for normal use, prefer prompts like:
- `initialize this project for Codex Genesis`
- `start the next deterministic step`
- `open a consensus review for specification/adrs/ADR-001.md with alice and dev-observer`
- `record alice's comment and respond to it`
- `show me the current consensus status`

Treat `python -m imp_codex.runtime ...` as the explicit automation surface, not the primary human UX.

## 1. Install

From the repo root:

```bash
cd /Users/jim/src/apps/ai_sdlc_method
python -m pip install -e ".[test]"
```

Verify the runtime is available:

```bash
python -m imp_codex.runtime --help
```

Optional smoke test:

```bash
python -m pytest imp_codex/tests/test_runtime_commands.py -q
```

## 2. Create a New Project

Create an empty project directory anywhere:

```bash
mkdir -p /tmp/codex-demo
cd /tmp/codex-demo
```

Initialize the Codex workspace:

```bash
python -m imp_codex.runtime init \
  --project-root "$PWD" \
  --project-name codex-demo
```

This creates:

```text
.ai-workspace/
  events/events.jsonl
  features/
  graph/
  profiles/
  tasks/
  intents/
  snapshots/
  codex/context/project_constraints.yml
  codex/context/context_manifest.yml
  reviews/consensus/
specification/INTENT.md
```

Check status:

```bash
python -m imp_codex.runtime status --project-root "$PWD" --health
```

## 3. Normal Interactive Flow

For normal usage, ask Codex to drive the runtime for you.

### Project bootstrap

Tell Codex:

```text
Initialize this folder as a Codex Genesis project.
```

Codex should run the equivalent of:

```bash
python -m imp_codex.runtime init --project-root "$PWD" --project-name <name>
```

### Deterministic progression

Tell Codex:

```text
Run the next deterministic step for feature REQ-F-DEMO-001.
```

Or:

```text
Advance REQ-F-DEMO-001 through intent→requirements using the minimal profile.
```

Codex should translate that into the appropriate runtime invocation and then report the resulting state.

### Consensus review

Tell Codex:

```text
Open a consensus review for specification/adrs/ADR-001.md with alice and dev-observer.
```

Then:

```text
Record alice's comment: "Please make the rollback path explicit."
```

Then:

```text
Respond to COMMENT-001 as resolved with rationale "Rollback section added."
```

Then:

```text
Cast approval votes for alice and dev-observer and close the review if it passes.
```

That is the preferred UX.

## 4. Scripted Flow From the Command Line

Use this section when:
- scripting
- building CI checks
- debugging the runtime directly
- proving the exact event/artifact sequence outside the interactive Codex UX

The shortest deterministic walkthrough uses the `minimal` profile.

### Step 1: Drive the first edge

```bash
python -m imp_codex.runtime iterate \
  --project-root "$PWD" \
  --feature REQ-F-DEMO-001 \
  --edge 'intent→requirements' \
  --profile minimal \
  --delta 0 \
  --converged
```

This creates the feature vector if it does not exist, appends iteration events, and updates projections like `STATUS.md`, `ACTIVE_TASKS.md`, and `feature_index.yml`.

### Step 2: Ask Codex what is next

```bash
python -m imp_codex.runtime start --project-root "$PWD"
```

On the minimal profile, the next edge should route to `design→code`.

### Step 3: Materialize an artifact for the next edge

```bash
mkdir -p src
cat > src/demo.py <<'EOF'
# Implements: REQ-F-DEMO-001

def demo():
    return True
EOF
```

### Step 4: Converge the code edge

```bash
python -m imp_codex.runtime iterate \
  --project-root "$PWD" \
  --feature REQ-F-DEMO-001 \
  --edge 'design→code' \
  --profile minimal \
  --artifact-path src/demo.py \
  --delta 0 \
  --converged
```

### Step 5: Inspect the result

```bash
python -m imp_codex.runtime status --project-root "$PWD" --health
python -m imp_codex.runtime trace --project-root "$PWD" --req-key REQ-F-DEMO-001
```

At this point the deterministic flow has:
- emitted runtime events
- updated the feature trajectory
- recorded the produced artifact reference
- advanced the project state without needing a live model

## 5. Run `start --auto`

If you want Codex to take the first available intent-dispatch path instead of explicitly calling `iterate`, use:

```bash
python -m imp_codex.runtime start \
  --project-root "$PWD" \
  --auto \
  --max-steps 10
```

Notes:
- this is the current Codex autopilot entrypoint
- it is real, but still earlier-stage than the Claude engine decomposition
- for a deterministic walkthrough, explicit `iterate` calls are easier to reason about

## 6. Deterministic Consensus Proof

This is the current way to prove the consensus loop in Codex.

It is not a live model-authored multi-party review conversation.
It is an executable event/artifact flow.

For normal usage, Codex should run these steps for the user.
The shell commands below are the explicit scripted form.

### Step 1: Create an artifact to review

```bash
mkdir -p specification/adrs
cat > specification/adrs/ADR-001.md <<'EOF'
# ADR-001: Demo Decision

We will use the Codex runtime for deterministic execution proofs.
EOF
```

### Step 2: Open a consensus cycle

```bash
python -m imp_codex.runtime consensus-open \
  --project-root "$PWD" \
  --artifact specification/adrs/ADR-001.md \
  --roster human:alice,agent:dev-observer \
  --review-id REVIEW-ADR-001-1 \
  --review-closes-in 900 \
  --min-participation-ratio 1.0
```

### Step 3: Add a comment

```bash
python -m imp_codex.runtime comment \
  --project-root "$PWD" \
  --review-id REVIEW-ADR-001-1 \
  --participant alice \
  --content "Please make the rollback path explicit."
```

### Step 4: Respond to the comment

This is the current deterministic "observer response" step.

```bash
python -m imp_codex.runtime dispose \
  --project-root "$PWD" \
  --review-id REVIEW-ADR-001-1 \
  --comment-id COMMENT-001 \
  --disposition resolved \
  --rationale "Rollback section added."
```

### Step 5: Cast votes

```bash
python -m imp_codex.runtime vote \
  --project-root "$PWD" \
  --review-id REVIEW-ADR-001-1 \
  --participant alice \
  --verdict approve \
  --rationale "Looks good now."

python -m imp_codex.runtime vote \
  --project-root "$PWD" \
  --review-id REVIEW-ADR-001-1 \
  --participant dev-observer \
  --verdict approve \
  --rationale "Approved."
```

### Step 6: Project and close the cycle

```bash
python -m imp_codex.runtime consensus-status \
  --project-root "$PWD" \
  --review-id REVIEW-ADR-001-1

python -m imp_codex.runtime consensus-close \
  --project-root "$PWD" \
  --review-id REVIEW-ADR-001-1
```

### What gets written

The review trail is written under:

```text
.ai-workspace/reviews/consensus/REVIEW-ADR-001-1/CYCLE-001/
  review.yml
  comments/COMMENT-001.md
  dispositions/COMMENT-001.yml
  votes/alice.yml
  votes/dev-observer.yml
  outcome.yml
```

The event stream is written to:

```text
.ai-workspace/events/events.jsonl
```

Expected semantic event sequence for the pass path:
- `ConsensusRequested`
- `CommentReceived`
- `CommentDispositioned`
- `VoteCast`
- `VoteCast`
- `ConsensusReached`

## 7. Triggered Comment Path

If you want to prove that a response artifact is written automatically from a vote, use a gating vote:

```bash
python -m imp_codex.runtime vote \
  --project-root "$PWD" \
  --review-id REVIEW-ADR-001-1 \
  --participant alice \
  --verdict reject \
  --gating \
  --rationale "Need narrower scope before approval."
```

This appends:
- one `vote_cast` event
- one `comment_received` event

And writes:
- `votes/alice.yml`
- `comments/COMMENT-001.md` (or the next available comment id)

This is the cleanest current proof that Codex can react to a review action by generating follow-on written telemetry and artifacts.

## 8. What "Consensus Observer" Means Today

Today in `imp_codex`, "consensus observer" is not a background service.

The executable behavior is:
- `comment` emits review feedback into the event stream and review trail
- `dispose` records the response to that comment
- `vote --gating` can emit a follow-on comment automatically
- `consensus-status` recomputes the current projected state from replay
- `consensus-close` emits the terminal outcome
- `consensus-recover` re-opens or narrows scope after failure

So the current startup flow is command-oriented, not daemon-oriented.

From a user-experience perspective, that means:
- the user should ask Codex to manage the review flow
- Codex should call `consensus-open`, `comment`, `dispose`, `vote`, `consensus-status`, and `consensus-close`
- the user should not need to remember those commands unless they are scripting

If you want a future autonomous observer, it should be a thin watcher over:
- `.ai-workspace/events/events.jsonl`
- `.ai-workspace/reviews/consensus/*`

And it should call the existing runtime commands rather than invent a second consensus engine.

## 9. Proof Commands

Deterministic consensus proof:

```bash
python -m pytest imp_codex/tests/e2e/test_e2e_consensus.py -q
```

Deterministic convergence proof:

```bash
python -m pytest imp_codex/tests/e2e/test_e2e_convergence.py -q
```

Live Codex homeostasis proof:

```bash
CODEX_E2E_MODE=real python -B -m pytest imp_codex/tests/e2e/test_e2e_homeostasis.py -q -s
```

## 10. Related Files

- `imp_codex/runtime/__main__.py`
- `imp_codex/runtime/commands.py`
- `imp_codex/runtime/consensus.py`
- `imp_codex/tests/e2e/test_e2e_convergence.py`
- `imp_codex/tests/e2e/test_e2e_consensus.py`
- `imp_codex/tests/e2e/test_e2e_homeostasis.py`
