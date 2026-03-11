# Intent: Genesis Navigator

**Version**: 1.0.0 | **Date**: 2026-03-12 | **Status**: Draft

---

## The Problem

Genesis practitioners working across multiple projects have no visual way to answer
the three questions that matter at the start of every work session:

1. **Where am I?** — What is the state of every feature vector across my projects?
2. **What's missing?** — Where are the gaps between spec and reality?
3. **What should I do next?** — Which work item is highest priority right now?

The current tooling (`/gen-status`, `/gen-gaps`) answers these questions as CLI output
inside a Claude Code session. There is no standalone visual tool that lets a practitioner
scan their projects, understand state at a glance, and choose what to work on — without
first opening a model session.

---

## What We Want

A **Genesis Navigator**: a local web application a practitioner opens to survey their
Genesis-managed projects, understand each project's state visually, and identify the
next actionable item.

The navigator is **not a live monitor**. It is a point-in-time reader that refreshes on
demand. It is **not** a replacement for Claude Code — it is the **pre-session planning
tool** and **post-session review tool** that makes Claude Code sessions more intentional.

---

## Primary User Journey

1. Run `genesis-nav /path/to/projects` from a terminal
2. Browser opens — project list shows all directories with `.ai-workspace/`
3. Select a project → see its state:
   - All feature vectors and their convergence status
   - Gap summary (REQ keys without tests, without telemetry)
   - Project-level state (ITERATING / QUIESCENT / CONVERGED / BOUNDED)
   - Pending human gates and unactioned intents
4. Decide what to work on → navigator surfaces the exact command to run in Claude Code
5. Browse session history (archived e2e runs) as postmortems

---

## Key Views

| View | Question it answers |
|------|---------------------|
| **Project List** | Which of my projects have Genesis workspaces? What is each one's state? |
| **Status** | Where is every feature vector? What's converged, iterating, blocked, stuck? |
| **Gaps** | What REQ keys are missing tests? Missing telemetry? Missing code tags? |
| **Decision Queue** | What are the highest-priority next actions? What command do I run? |
| **Session History** | What happened in previous runs? How did convergence progress over time? |

---

## What It Is Not

- Not a live monitor (no SSE streaming, no filesystem watching)
- Not a replacement for Claude Code or the Genesis engine
- Not a tool that executes Genesis commands — it surfaces them for the practitioner to run

---

## Technology

**Frontend**: React + Vite + TypeScript
**Backend**: Thin Python server (FastAPI) that reads `.ai-workspace/` and returns JSON
**Communication**: REST — refresh on demand, no WebSockets
**Entry point**: `genesis-nav` CLI — starts API server, opens browser

The frontend is decoupled from the backend via a defined API contract. Future hosts:
VS Code extension webview, Electron, hosted web — same frontend, different data adapter.

---

## Business Value

Every Claude Code session currently starts with "what state am I in?" — re-reading
workspace files, running `/gen-status`, figuring out what to do. The navigator eliminates
that overhead. Session starts with a clear picture; the practitioner arrives at Claude Code
with a specific instruction, not a question.

---

## Success Criteria

- Scan a folder tree and see all Genesis projects in under 2 seconds
- Understand full feature vector state for any project without opening Claude Code
- Gap analysis results visible without running `/gen-gaps` in a model session
- Practitioner can identify the highest-priority next action and copy the command to run
- Postmortem view shows timeline of a previous convergence run
