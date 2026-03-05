# Agent Comment Conventions
NOTE to the LLM - if i'm reference this file in a prompt, it's because i want you to actually write a comment in the format specified here. This is not just for your reference, but an active instruction to produce output in this format.

**Purpose**: Public exchange space for LLMs to converse, peer-review, and hand off work to each other.
This directory is the shared commons — any LLM agent (Claude, Gemini, Codex, Bedrock, or others) writes to its own subdirectory and can read any other agent's subdirectory. It is the mechanism by which agents critique each other's ADRs, propose designs, flag gaps, and coordinate across sessions without a human acting as intermediary.

Think of it as an asynchronous, multi-agent discussion forum where each post is an immutable, self-contained artifact.

## Directory Structure

```
.ai-workspace/comments/
├── CONVENTIONS.md        ← this file
├── claude/               ← Claude Code writes here
│   └── YYYYMMDDTHHMMSS_CATEGORY_SUBJECT.md
├── gemini/               ← Gemini writes here
│   └── YYYYMMDDTHHMMSS_CATEGORY_SUBJECT.md
└── codex/                ← Codex writes here
    └── YYYYMMDDTHHMMSS_CATEGORY_SUBJECT.md
```

## File Naming

```
YYYYMMDDTHHMMSS_CATEGORY_SUBJECT.md
```

Example: `20260303T010000_REVIEW_ADR-S-011-openlineage.md`

## Categories

| Category | When to use |
|----------|-------------|
| `REVIEW` | Peer review of another agent's ADR, design, or code |
| `STRATEGY` | Proposed technical approach for a new feature or problem |
| `GAP` | Detailed analysis of a specific logic or process gap |
| `SCHEMA` | Proposed data model, event structure, or API shape |
| `HANDOFF` | Explicit task hand-off with context for the receiving agent |
| `MATRIX` | Multi-criteria decision evaluation — rows are proposals, columns are spec alignment / delivery risk / effort / decision / reasoning |

## File Structure

```markdown
# {CATEGORY}: {Subject}

**Author**: {agent name}
**Date**: {ISO 8601}
**Addresses**: {what ADR/feature/problem this responds to}
**For**: {intended reader — "claude", "gemini", "all"}

## Summary
{1-3 sentence executive summary}

## {Section}
{content}

## Recommended Action
{what the receiving agent should do with this}
```

For `MATRIX` category, the primary section is a decision table:

```markdown
## Decision Evaluation Matrix

| Item | Proposal | Spec Alignment | Delivery Risk | Effort | Decision | Reasoning |
|---|---|---:|---:|---:|---|---|
| 1 | {proposal} | High/Medium/Low | High/Medium/Low | High/Medium/Low | {Adopt now / Adopt as ADR candidate / Defer / Reject} | {one-line rationale} |

## Recommended Action
{ordered list of concrete next steps derived from the matrix}
```

## Workflow

1. **Agent A writes**: Produces analysis, posts to its own `comments/` folder
2. **User directs**: "Read `.ai-workspace/comments/gemini/latest_REVIEW.md` and implement"
3. **Agent B reads**: Loads the file, treats as high-priority constraint, executes
4. **Agent B responds**: Posts its own comment acknowledging or disagreeing

## Invariants

- Comments are **immutable once written** — append new files, do not edit old ones
- Each file is self-contained — no external references required to understand it
- These files are **workspace artifacts**, not spec documents — they live in `.ai-workspace/`, not `specification/`
- Session start: scan peer's `comments/` folder for new files since last session
