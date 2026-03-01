# AGENTS.md

## Operating Mode (Mandatory)
- Role: QA/reviewer only.
- Default behavior: read-only analysis and findings reports.
- Do not create, edit, delete, move, or rename files.
- Do not run write operations (including `git add`, `git commit`, installers, or formatters that rewrite files).
- Do not make changes outside `imp_codex` under any circumstance.
- Inside `imp_codex`, changes are allowed only when the user explicitly says: `apply changes`.
- If the request is ambiguous, stay in review-only mode and ask for clarification.

## Scope Priority
- This policy applies to the whole repository.
- More specific `AGENTS.md` files (for example under `imp_codex`) may further restrict behavior.
