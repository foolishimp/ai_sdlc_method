# genesis_core/specification/

Platform-agnostic engine specification for the Asset Graph Model.

## What This Is

This directory contains the **shared contract** that all Genesis implementations (`imp_claude/`, `imp_gemini/`, `imp_codex/`, `imp_bedrock/`) design and build against. It defines WHAT the engine does — not HOW any particular platform implements it.

## Documents

| Document | Purpose |
|----------|---------|
| [GENESIS_ENGINE_SPEC.md](GENESIS_ENGINE_SPEC.md) | Core specification: data model, evaluation pipeline, orchestration, event contract, configuration, binding points, structural constraints |

## Relationship to Other Artifacts

```
specification/                        → The formal system (4 primitives, 1 operation)
genesis_core/specification/           → The engine contract (how to implement iterate())
imp_<name>/design/                    → Platform-specific design (ADRs binding this contract)
imp_<name>/code/                      → Platform-specific code (satisfying the design)
```

Design is always tenanted. Each `imp_<name>/design/` produces its own binding ADR that maps this specification to concrete platform technology:

- Claude: `imp_claude/design/adrs/ADR-020-genesis-engine-binding.md`
- Gemini: (to be created)
- Codex: (to be created)
- Bedrock: (to be created)

## Rules

1. **Specification only** — no code, no configs, no YAML. Just `.md` documents.
2. **No design here** — design is tenanted. This directory has no `design/` subdirectory.
3. **Tech-agnostic** — no references to Claude, Gemini, Python, or any specific platform.
4. **Versioned independently** — tracks the engine contract, not the methodology version.
