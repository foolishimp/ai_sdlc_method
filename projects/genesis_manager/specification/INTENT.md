# Intent — genesis_manager

**Version**: 0.1.0
**Date**: 2026-03-13
**Status**: Draft

---

## The Problem

Genesis builds software autonomously. The person using Genesis — the customer — has no clean surface to supervise that work, trust its output, or steer it deliberately.

---

## The Intent

Build a **builder supervision console** — the control surface for a person using Genesis to create projects.

The primary user is:
- building one or more projects through Genesis
- usually focused on one project at a time
- supervising, steering, approving, and trusting the system
- occasionally switching across projects

The product must answer these questions at any moment:

1. What is Genesis building for me?
2. How far has it gotten?
3. What is blocked, wrong, or uncertain?
4. What does Genesis want to do next?
5. What does Genesis need from me right now?
6. Why should I trust its current status?
7. What changed since I last looked?
8. Is this ready for me to accept, review, or ship?

---

## The Product Shape

A clean-room product — not a repackaging of genesis_monitor — with these top-level work areas:

| Area | Purpose |
|------|---------|
| **Projects** | Move between projects; see which need attention |
| **Overview** | One-screen answer to "what is Genesis doing?" |
| **Supervision** | Monitor active autonomous work; see what needs attention |
| **Evidence** | Answer "why should I trust this?" |
| **Control** | Steer Genesis deliberately (start, iterate, approve, repair) |
| **Release** | Make the ship/no-ship question explicit |

---

## Core Product Invariant

**Every visible technical identifier is a navigation handle into deeper context.**

REQ keys, feature IDs, run IDs, decision IDs — all are clickable addresses into canonical detail pages. The user should be able to traverse from any reference to its full history, dependencies, evidence, and evolution.

---

## What This Is Not

- Not a PM dashboard
- Not a methodology teaching tool
- Not a raw observability interface
- Not a team coordination tool (initially)

It is specifically a **supervision console for the customer of Genesis**.

---

## Source

Synthesised from three Codex strategy posts:
- `20260313T020625_STRATEGY_genesis_manager-product-spec-v1.md`
- `20260313T021252_STRATEGY_genesis_manager-customer-supervision-amendment.md`
- `20260313T022013_STRATEGY_genesis_manager-navigability-amendment.md`
