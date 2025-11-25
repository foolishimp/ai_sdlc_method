# Codex Plugins (Extensions)

Purpose
- Codex-native distribution of the AISDLC methodology, skills, and standards.
- Mirrors the Claude plugin set but ships as Python packages with entrypoints.

Structure
```
codex-code/plugins/
├── aisdlc-core/           # Foundation (traceability, REQ tagging)
├── aisdlc-methodology/    # 7-stage method + personas
├── principles-key/        # Key Principles enforcement
├── python-standards/      # Language standards (example)
├── code-skills/           # Coding/refactoring helpers
├── design-skills/         # Design/ADR helpers
├── requirements-skills/   # Requirements helpers
├── runtime-skills/        # Runtime/telemetry helpers
├── testing-skills/        # TDD/BDD helpers
└── bundles/               # startup/datascience/qa/enterprise bundles
```

Packaging Model
- Pip-installable packages exposing:
  - Commands: `codex-sdlc-*` (context, checkpoint, finish, commit, release, refresh)
  - Skills: entrypoints per domain (traceability, testing, workspace, release, observability)
  - Persona presets: stage configs consumable by Codex (requirements/design/tasks/code/system_test/uat/runtime)
- SemVer with dependency ranges matching Claude equivalents.
- Layered configuration: global → project, later overrides earlier.

Alignment & Docs
- Behavior mirrors Claude plugins; differences must be ADR-documented (`docs/design/codex_aisdlc/adrs/`).
- See `docs/design/codex_aisdlc/` for design and implementation guidance.
