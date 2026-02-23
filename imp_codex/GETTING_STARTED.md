# Codex Genesis - Getting Started

## Purpose

This guide gets you productive in the `imp_codex` implementation quickly.

## 1. Prerequisites

- Python 3.11+
- `pytest`
- Project checked out at repository root (`ai_sdlc_method/`)

## 2. Implementation Scope

`imp_codex` is a Codex-specific binding of the shared AI SDLC specification.

- Shared source of truth: `specification/`
- Codex design: `imp_codex/design/`
- Codex implementation assets: `imp_codex/code/`
- Codex validation suite: `imp_codex/tests/`

## 3. Read in This Order

1. `imp_codex/design/CODEX_GENESIS_DESIGN.md`
2. `imp_codex/design/AISDLC_V2_DESIGN.md`
3. `imp_codex/code/plugin.json`
4. `imp_codex/code/README.md`

## 4. Run the Codex Test Suite

From repo root:

```bash
pytest -q imp_codex/tests
```

Expected result: all tests pass.

This now includes:
- TDD config/spec validation
- BDD methodology acceptance coverage
- UAT scenario suite (`imp_codex/tests/uat/`)
- Integration-level consistency checks (`imp_codex/tests/test_integration_uat.py`)

## 5. Run E2E Validation

```bash
pytest -q imp_codex/tests/e2e -m e2e
```

This runs the Codex Genesis end-to-end convergence harness and validates:
- event stream integrity
- feature vector convergence artifacts
- generated code/test traceability
- cross-artifact consistency

## 6. Command Surface (v2.8)

Core commands:

- `/gen-start`
- `/gen-status`
- `/gen-init`
- `/gen-iterate`
- `/gen-spawn`
- `/gen-review`
- `/gen-spec-review`
- `/gen-escalate`
- `/gen-zoom`
- `/gen-checkpoint`
- `/gen-trace`
- `/gen-gaps`
- `/gen-release`

Command specs live in `imp_codex/code/commands/`.

## 7. Key Files You Will Edit Most

- `imp_codex/code/plugin.json` - manifest and registration
- `imp_codex/code/hooks/hooks.json` - lifecycle hooks
- `imp_codex/code/agents/gen-iterate.md` - universal iterate behavior
- `imp_codex/code/config/graph_topology.yml` - graph topology
- `imp_codex/code/config/edge_params/*.yml` - edge semantics

## 8. Guardrails

- Keep changes inside `imp_codex/` unless explicitly approved otherwise.
- Treat `specification/` as authoritative behavior.
- Use `imp_claude/` as reference only, not as the implementation target.
