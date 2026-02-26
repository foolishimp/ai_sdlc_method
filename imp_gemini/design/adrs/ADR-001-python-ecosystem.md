# ADR-001: Python 3.12 Ecosystem

**Status**: Accepted
**Date**: 2026-02-26

## Context
We need a modern, stable, and highly productive language ecosystem for implementing the AI SDLC tooling.

## Decision
Use Python 3.12+ as the primary implementation language.

## Alternatives Considered
- **Go**: Excellent concurrency, but less library support for LLM orchestration.
- **Node.js**: Good for CLI tools, but Python is the standard for AI/ML and has better type-hinting support in recent versions.

## Consequences
- Benefit from modern type hints and match statements.
- High compatibility with Gemini/Vertex AI SDKs.
- Requirement for users to have Python 3.12+ installed.
