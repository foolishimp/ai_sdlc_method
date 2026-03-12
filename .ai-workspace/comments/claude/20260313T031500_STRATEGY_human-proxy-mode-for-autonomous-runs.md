# STRATEGY: Human Proxy Mode for Autonomous Overnight Runs

**Author**: claude
**Date**: 2026-03-13T03:15:00+11:00
**Observed during**: genesis_manager first boot, F_H gate at intent→requirements
**For**: all

## Observation

The current F_H gate model assumes a human is present at the terminal. When `--auto` hits a
`required: true` human evaluator, it pauses and waits for input. This makes overnight or
unattended runs stop at the first F_H gate regardless of how mature the artifact is.

The right fix is not to remove human gates. It is to allow a **designated human proxy** to
fulfill the F_H role when the human is unavailable.

## The Human Proxy Pattern

A human proxy is an agent that:
- has been explicitly authorized by the human to act on their behalf
- evaluates the artifact against the F_H criterion using the same context the human would have
- emits a disposition with explicit reasoning attached
- is auditable — every proxy decision is recorded and reviewable

Claude running with `--dangerously-skip-permissions` already satisfies this contract. It has:
- full context (bootloader, spec, INTENT.md, UX.md)
- the ability to read and evaluate the artifact
- the authority level the human granted by launching it with skip-permissions
- the ability to emit `review_approved` events with structured rationale

## Why This Is Better Than Removing Human Gates

Removing F_H gates (`required: false`) loses the audit trail — the system just continues
with no record of why.

A human proxy fulfilling the F_H gate produces:
- a structured approval/rejection with reasoning
- a record of what was checked and what was found
- a disposition that the human can review and override on return
- the same event schema as a real human review

The result is richer than a human pressing Enter.

## The CONSENSUS Connection

This is the CONSENSUS architecture applied to single-agent F_H evaluation. CONSENSUS allows
multiple agents to vote on an artifact. The human proxy pattern is the degenerate case:
one authorized agent, one vote, quorum = 1.

The same `vote_cast` → `consensus_reached` flow applies. The human proxy emits
`review_approved` just as a human would. The event log records the proxy identity.

## Proposed Mechanism

A `--human-proxy` flag on `/gen-start --auto`:

```
/gen-start --auto --human-proxy
```

When `--human-proxy` is set:
- F_H gates do not pause the loop
- Instead, the LLM evaluates the artifact against the F_H criterion
- If satisfied: emits `review_approved` with `actor: human-proxy`, `reasoning: {text}`
- If not satisfied: emits `review_approved` with `decision: rejected`, `reasoning: {text}`
  and pauses (rejection requires human resolution — proxy cannot self-correct)
- All proxy decisions are written to `.ai-workspace/reviews/proxy-log/` for morning review

The human wakes up to a run that went as far as it could, with every F_H decision documented
and reviewable. They can override any proxy decision and re-run from that point.

## What This Unlocks

- Overnight runs that traverse requirements, feature decomposition, and design autonomously
- A full audit trail of every F_H decision, better than a human pressing Enter
- A natural morning review workflow: scan proxy decisions, approve or override, continue
- The foundation for a team proxy model (multiple authorized agents, quorum > 1)

## Recommended Action

1. Add `--human-proxy` mode to `/gen-start --auto` spec
2. Define the proxy approval event schema (actor field, reasoning field)
3. Define the proxy log location and format
4. Add a morning review workflow to `/gen-status` — surface proxy decisions made since
   last human session

This is not removing human oversight. It is making human oversight asynchronous and auditable.
