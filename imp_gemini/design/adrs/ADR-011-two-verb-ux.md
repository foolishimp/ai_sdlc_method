# ADR-011: Two-Verb UX Architecture

**Status**: Accepted
**Date**: 2026-02-27

## Context
Traditional methodologies have steep learning curves with many commands to remember.

## Decision
Implement a simplified UX layer based on two primary verbs: **Start** ("Go.") and **Status** ("Where am I?"). These commands automatically detect the project state and delegate to more granular tools (`init`, `spawn`, `iterate`, etc.).

## Consequences
- Reduced cognitive load for methodology users.
- Enables automated, state-driven workflow orchestration.
