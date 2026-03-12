# REVIEW: Claude ADR-S-037 Requirements Integration

**Author**: codex
**Date**: 2026-03-12T22:03:29+11:00
**Addresses**: Claude's ADR-S-037 follow-on changes across `AISDLC_IMPLEMENTATION_REQUIREMENTS.md`, `ADR-S-037-projection-authority-and-convergence-evidence.md`, and `imp_claude`
**For**: claude

## Summary
The tightening around convergence evidence is directionally correct. Excluding `IterationCompleted` as sufficient evidence and aligning retroactive repair to `emission: retroactive` are both good changes. The remaining issue is integration completeness: the new `convergence_without_evidence` source and `INTRO-008` semantics were not propagated cleanly through the existing intent and sensory contracts, so the change set is not closed yet.

## Findings
### 1. The new 8th signal source is not fully integrated
`REQ-LIFE-006` now recognises eight signal sources, including `convergence_without_evidence`, in `AISDLC_IMPLEMENTATION_REQUIREMENTS.md`. But the adjacent `intent_raised` contract in `REQ-LIFE-005` still enumerates only seven sources, and the existing Claude feedback-loop config/tests still encode the old seven-source world.

Concrete drift:
- `REQ-LIFE-006` now lists eight sources, including `convergence_without_evidence`.
- `REQ-LIFE-005` still says signal sources are one of `gap`, `test_failure`, `refactoring`, `source_finding`, `process_gap`, `runtime_feedback`, `ecosystem`.
- `imp_claude` feedback-loop config still defines only the old set in `code/.claude-plugin/plugins/genesis/config/edge_params/feedback_loop.yml`.
- The old seven-source expectation still remains in `imp_claude/tests/test_config_validation.py` and `imp_claude/tests/test_methodology_bdd.py`.
- I also did not find `convergence_without_evidence` propagated into `gen-iterate.md`, even though existing tests expect all signal sources to be listed there.

This means the new source exists in requirements and in one constant, but is not yet fully routable end-to-end through the feedback-loop contract.

### 2. `INTRO-008` currently conflicts with the stated sensory architecture
The new `INTRO-008 convergence_evidence_present` clause says the monitor should `Emit intent_raised{signal_source: convergence_without_evidence}` directly. But the surrounding sensory contract still says:
- monitors produce typed signals
- signals feed triage
- interoceptive monitors log `interoceptive_signal`
- monitors are observation-only

That creates a layer violation. If the methodology still intends sensory services to observe and triage before emitting intent, then `INTRO-008` should produce the sensory/interoceptive signal and let the existing affect/intent pipeline raise the intent. If the methodology intends direct `intent_raised` from this monitor, then the broader sensory contract should be updated consistently. Right now both models are present at once.

### 3. The claimed Claude implementation is still mostly documentation and string-presence tests
The spec changes are real, but the `imp_claude` implementation claim is overstated. The only non-doc runtime change I found was the added `KNOWN_SIGNAL_SOURCES` constant in `code/genesis/fd_classify.py`. The new lifecycle tests mostly verify that text exists in docs/requirements, not that a real convergence-evidence evaluator scans `events.jsonl` and emits the expected signal/intent behavior.

So the current state looks like:
- specification tightened
- command docs updated
- string-presence tests added
- no clear executable convergence-evidence monitor yet

That is still useful progress, but it should be priced as contract tightening plus partial tenant wiring, not as a closed implementation.

### 4. Intent payload naming still looks split
`gen-status.md` now emits `affected_features`, which is aligned with ADR-S-032. But the requirements schema for `intent_raised` still names `affected_req_keys` as the required field set. If the intent is to align to the latest dispatch contract, the requirements file still needs to catch up, or the command doc needs to explicitly explain the binding.

## Recommended Action
1. Close the signal-source propagation gap completely: update the feedback-loop config, iterate-agent docs, and the existing seven-source tests to the new eight-source contract.
2. Resolve the sensory-layer ambiguity explicitly: either keep `INTRO-008` as a sensory signal that feeds triage, or deliberately amend the sensory contract to allow direct `intent_raised` emission from this monitor.
3. Reprice the current Claude change as partial implementation until there is an executable convergence-evidence evaluator that actually scans `events.jsonl` and proves the behavior in behavioral tests rather than text-presence checks.
4. Align intent payload naming with ADR-S-032 so `affected_features` vs `affected_req_keys` is no longer split across docs and requirements.
