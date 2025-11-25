# Agents & Skills Interoperation (Codex Solution)

Purpose
- Show how Codex stage personas and skills collaborate to deliver the AI SDLC method with full traceability.

Personas (Stage Presets)
- Requirements → Codex preset loads REQ templates, key gates, and traceability rules.
- Design → Links REQ keys to solution docs; prompts include architecture patterns and ADR hooks.
- Tasks → Maps design outputs to work items; respects workspace task formats.
- Code → Enforces Key Principles + TDD; injects coverage gates and REQ tagging hints.
- System Test → BDD scaffolds tied to REQ keys; requires ≥95% requirement coverage for system tests.
- UAT → Business-language BDD and sign-off mapping to REQ keys.
- Runtime Feedback → Telemetry/alerts tagged with REQ keys; feeds new intents back to requirements.

Skills (Reusable Capabilities)
- Traceability: Generate/update matrix rows, validate REQ tags in code/tests, surface missing links.
- Testing: Scaffold unit/BDD tests, run coverage, enforce thresholds, suggest gaps.
- Workspace: Validate `.ai-workspace` layout, create finished task docs, checkpoint tasks.
- Release: Version bump, changelog generation, git tagging; aligns with `codex-sdlc-release`.
- Observability: Insert telemetry/logging snippets with REQ tags; stub alerts for runtime feedback.

Interop Patterns
- Personas call skills to perform checks or scaffolding; skills never bypass persona gates.
- Skills accept REQ IDs and optional solution name (`codex_aisdlc`) to keep provenance in outputs.
- Commands orchestrate persona + skill calls (e.g., `codex-sdlc-checkpoint` invokes traceability and workspace skills).

Traceability & Safeguards
- All persona outputs must include REQ references; skills validate before writing.
- Commands operate idempotently; destructive changes require explicit flags.
- Divergences from Claude behavior must be ADR-documented in `adrs/`.
