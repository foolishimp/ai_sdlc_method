# Requirements — REQ-F-PROXY-001: Human Proxy Mode

**Version**: 0.1.0
**Date**: 2026-03-13
**Status**: Candidate — awaiting human approval
**Traces To**: INT-AISDLC-001
**Feature Vector**: REQ-F-PROXY-001
**Parent Feature**: REQ-F-DISPATCH-001

---

## Overview

Genesis uses F_H (human) evaluators as required gate checks on major edges (requirements approval, design approval, code review). In interactive mode, these gates pause `/gen-start --auto` and wait for terminal input — correct behaviour for attended sessions, but a blocker for unattended overnight runs.

**Human Proxy Mode** allows the LLM to fulfil F_H gate evaluation on the human's behalf during unattended runs. The LLM reads the produced artifact, evaluates it against each F_H criterion, records a reasoned decision, emits the appropriate event, and continues the loop. All decisions are logged for morning review. The human retains full override authority.

**Scope**: Modifications to `/gen-start` and `/gen-iterate` command behaviour. A new proxy-log directory. A new `actor` field on `review_approved` events. No changes to F_H gate definitions in edge_params — gates remain in place and their criteria remain the evaluation surface.

**Scope boundary**: Proxy mode does not remove human gates. It defers human review from synchronous (blocking) to asynchronous (logged, reviewable, overridable). The human gate criteria are unchanged; only the timing of evaluation changes.

**Relationship to intent**: Enables unattended autonomous runs that go as far as possible without human intervention while preserving full auditability and override capability.

---

## Terminology

| Term | Definition |
|------|-----------|
| **F_H gate** | A convergence check of type `human` with `required: true` in an edge checklist that requires explicit approval before the edge can converge. |
| **Human proxy** | The LLM acting as an authorized evaluator at F_H gates during an unattended run. Not a bypass — a deferred evaluation with recorded reasoning. |
| **Proxy decision** | The outcome of an F_H evaluation by the LLM proxy: `approved` or `rejected`. Each decision is logged with criteria evidence and reasoning. |
| **Proxy log** | The directory `.ai-workspace/reviews/proxy-log/` containing one Markdown file per proxy decision. |
| **Morning review** | The human's inspection of proxy-log entries after an overnight run to verify, accept, or override each proxy decision. |
| **Self-correction** | An attempt by the proxy to reject a gate and then immediately construct a new artifact to re-satisfy that same gate. This is prohibited — proxy rejections must be resolved by the human. |
| **Attended session** | A Genesis run where a human is present at the terminal. Human proxy mode is not activated in attended sessions. |
| **Unattended run** | A Genesis run started with `--auto --human-proxy` intended to continue without human presence. |

---

## Functional Requirements

### REQ-F-HPRX-001: Human Proxy Flag

**Priority**: Critical
**Type**: Functional

**Description**: `/gen-start` must accept a `--human-proxy` flag that, when combined with `--auto`, activates proxy evaluation at all F_H gates encountered during the auto-loop.

**Acceptance Criteria**:
- `--human-proxy` is only valid in combination with `--auto`; used alone it must produce a clear error: "`--human-proxy` requires `--auto`"
- When active, the flag is visible in the terminal output at the start of each loop iteration: `[proxy mode active]`
- The flag is not persisted to the workspace — it is a per-invocation option only
- The flag has no effect on F_D or F_P evaluators; only F_H evaluators are affected

**Traces To**: INT-AISDLC-001

---

### REQ-F-HPRX-002: F_H Criterion Evaluation by Proxy

**Priority**: Critical
**Type**: Functional

**Description**: When `--human-proxy` is active and an F_H gate is reached, the LLM must evaluate the produced artifact against every F_H criterion defined for that gate and produce a structured decision.

**Acceptance Criteria**:
- For each F_H check in the edge checklist, the proxy evaluates: does the artifact satisfy this criterion? (yes/no with evidence)
- The overall decision is `approved` only if every required F_H criterion is met; `rejected` if any required criterion fails
- The evaluation must cite specific evidence from the artifact for each criterion assessment
- The evaluation must not use criteria outside those defined in the edge checklist — no additional standards introduced by the proxy

**Traces To**: INT-AISDLC-001

---

### REQ-F-HPRX-003: Proxy Decision Logging

**Priority**: Critical
**Type**: Functional

**Description**: Every proxy decision must be written to `.ai-workspace/reviews/proxy-log/` as a structured Markdown file before the auto-loop continues.

**Acceptance Criteria**:
- One file per proxy decision, named: `{ISO-timestamp}_{feature-id}_{edge}.md`
- Each file contains: feature ID, edge, iteration number, timestamp, each F_H criterion with assessment and evidence, overall decision (approved/rejected), and plain-language reasoning summary
- The file is written before the `review_approved` event is emitted — log precedes event
- If the proxy-log directory does not exist, it is created automatically

**Traces To**: INT-AISDLC-001

---

### REQ-F-HPRX-004: Proxy Event Emission

**Priority**: Critical
**Type**: Functional

**Description**: On every proxy decision, a `review_approved` event must be emitted to `events.jsonl` with an `actor` field identifying the decision as proxy-made.

**Acceptance Criteria**:
- Event schema: `{"event_type": "review_approved", "timestamp": "{ISO}", "project": "{name}", "data": {"feature": "{id}", "edge": "{edge}", "decision": "approved|rejected", "actor": "human-proxy", "reasoning": "{text}", "proxy_log": "{path-to-log-file}"}}`
- The `actor` field must be `"human-proxy"` — never `"human"` or absent
- The `proxy_log` field must be the relative path to the log file written in REQ-F-HPRX-003
- The event is append-only and immutable like all other events

**Traces To**: INT-AISDLC-001

---

### REQ-F-HPRX-005: Loop Continuation and Rejection Pause

**Priority**: Critical
**Type**: Functional

**Description**: On proxy approval, the auto-loop continues to the next edge. On proxy rejection, the loop pauses and reports the reason — proxy rejections require human resolution.

**Acceptance Criteria**:
- On approval: the F_H checks are marked passed, the auto-loop continues as if a human had approved interactively
- On rejection: the loop halts with a clear message identifying the feature, edge, and failing criterion; the message instructs the human to resolve and re-run
- The proxy may not attempt self-correction: after a rejection, it must not construct a revised artifact and re-evaluate the same gate in the same session
- Rejection does not corrupt the feature vector — the feature remains in `iterating` status at the failed edge

**Traces To**: INT-AISDLC-001

---

### REQ-F-HPRX-006: Morning Review Visibility

**Priority**: High
**Type**: Functional

**Description**: `/gen-status` must surface proxy decisions made since the last attended session so the human can inspect and override them before continuing work.

**Acceptance Criteria**:
- When proxy-log entries exist that post-date the last human-attended session, `/gen-status` displays a "Proxy decisions pending review" section listing each decision with: feature, edge, decision (approved/rejected), and a link to the log file
- The human can dismiss individual proxy decisions from the review queue without undoing them
- The human can override a proxy approval by running `/gen-review --feature {id} --edge {edge}` which re-opens the gate for human evaluation; if the human rejects at this point, the feature reverts to the pre-approval state on that edge

**Traces To**: INT-AISDLC-001

---

## Non-Functional Requirements

### REQ-NFR-HPRX-001: Proxy Log Completeness

**Priority**: High
**Type**: Non-Functional

**Description**: Every F_H gate encountered during a `--human-proxy` session must produce a log entry, regardless of whether the decision is approved or rejected.

**Acceptance Criteria**:
- If the session is interrupted mid-evaluation, a partial log entry is written with status `incomplete` before the session ends
- At session start with `--human-proxy`, any `incomplete` log entries from prior sessions are reported to the user before proceeding
- Zero proxy decisions may be made without a corresponding log entry

**Traces To**: INT-AISDLC-001

---

### REQ-NFR-HPRX-002: Proxy Identity Traceability

**Priority**: High
**Type**: Non-Functional

**Description**: It must be possible to distinguish proxy-approved events from human-approved events at any point in the event stream.

**Acceptance Criteria**:
- The `actor` field on all `review_approved` events is always present and always either `"human"` or `"human-proxy"` — never absent or null
- Existing `review_approved` events without an `actor` field are treated as `"human"` (backward compatibility)
- `/gen-status` counts proxy approvals and human approvals separately in its convergence report

**Traces To**: INT-AISDLC-001

---

## Business Rules

### REQ-BR-HPRX-001: No Proxy Self-Correction

**Priority**: Critical
**Type**: Business Rule

**Description**: A proxy rejection is a signal that requires human judgment. The proxy must not attempt to resolve its own rejection by constructing a revised artifact within the same session.

**Acceptance Criteria**:
- After a proxy rejection on edge E for feature F, the auto-loop halts for that feature — it does not re-invoke iterate on edge E in the same session
- The prohibition applies only to the rejected feature+edge pair; other features in the session are unaffected
- A human may manually re-invoke the edge after reviewing the rejection reason

**Traces To**: INT-AISDLC-001

---

### REQ-BR-HPRX-002: Proxy is Opt-In Only

**Priority**: Critical
**Type**: Business Rule

**Description**: Human proxy mode must never activate without explicit user opt-in via `--human-proxy`. Unattended auto-runs without this flag must behave exactly as before — pausing at F_H gates.

**Acceptance Criteria**:
- The default behaviour of `--auto` is unchanged: F_H gates pause the loop
- No configuration file, environment variable, or workspace setting can activate proxy mode — only the explicit CLI flag
- The flag must be re-supplied on every invocation; it is never implied or inferred

**Traces To**: INT-AISDLC-001

---

## Success Criteria

| Outcome | Measurable Test | REQ Keys |
|---------|----------------|---------|
| An overnight run traverses requirements + feature decomposition + design without human presence | End-to-end test: run with `--auto --human-proxy` from cold start; verify events.jsonl contains `review_approved{actor: human-proxy}` for each F_H gate, and each gate has a corresponding proxy-log entry | REQ-F-HPRX-001..005 |
| Morning review surfaces all proxy decisions | Start a session after a proxy run; verify `/gen-status` lists all proxy-log entries dated after last attended session | REQ-F-HPRX-006 |
| No proxy decision is untraceable | Scan events.jsonl for `review_approved` events; verify every `actor: human-proxy` entry has a valid `proxy_log` path pointing to an existing file | REQ-NFR-HPRX-001, REQ-NFR-HPRX-002 |
| Proxy rejection halts the loop | Inject a deliberately failing artifact; verify the loop stops and does not self-correct | REQ-F-HPRX-005, REQ-BR-HPRX-001 |

---

## Assumptions

| ID | Assumption | Risk if Wrong |
|----|-----------|---------------|
| ASS-001 | The LLM has sufficient context (bootloader, spec, edge config) to evaluate F_H criteria reliably | Proxy approvals may be low quality; morning review becomes high-burden |
| ASS-002 | F_H criteria in edge_params are written precisely enough to be evaluable without human domain knowledge | Vague criteria produce unreliable proxy decisions |
| ASS-003 | The human will review proxy-log entries before continuing work on proxy-approved edges | Unreviewed proxy approvals accumulate technical debt in the convergence record |
