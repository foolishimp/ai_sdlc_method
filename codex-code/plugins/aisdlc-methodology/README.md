# aisdlc-methodology (Codex)

Codex package delivering the 7-stage AISDLC methodology (personas, quality gates, workflows). Aligns with `docs/design/codex_aisdlc/`.

Contents
- Stage presets (requirements, design, tasks, code, system_test, uat, runtime) — to be added
- Shared rules (Key Principles, TDD/BDD workflows, req-tagging, workspace safeguards) — to be added
- Command helper: `commands/codex_sdlc_context.py` (non-destructive context loader)

Usage
- Copy into your project and register via Codex installers (`setup_workspace.py`, `setup_commands.py`, `setup_plugins.py`).
- Run `python commands/codex_sdlc_context.py` to load CODEx method references and ACTIVE_TASKS into your Codex session.
