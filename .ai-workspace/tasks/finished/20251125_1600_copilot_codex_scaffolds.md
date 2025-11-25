# Task: Add Codex & Copilot AISDLC Scaffolds (Mirror Claude Structure)

**Status**: Completed  
**Date**: 2025-11-25  
**Time**: 16:00  
**Actual Time**: ~1.5 hours (Estimated: 2 hours)

**Task ID**: #14  
**Requirements**: REQ-F-PLUGIN-001, REQ-F-PLUGIN-002, REQ-F-PLUGIN-003, REQ-F-PLUGIN-004, REQ-F-CMD-001, REQ-F-CMD-002, REQ-NFR-FEDERATE-001, REQ-NFR-TRACE-001

---

## Problem

We needed platform-parity scaffolds for Codex and GitHub Copilot, mirroring the Claude asset structure (plugins, bundles, project templates, installers) and design docs, so multiple implementations can coexist with traceability.

---

## Investigation

1. Reviewed existing Claude structure (`claude-code/`) and design folder conventions.  
2. Assessed Codex and Roo placeholders to identify missing parity elements.  
3. Confirmed workspace rules and requirements (traceability, federated plugins, commands/personas).

---

## Solution

**Architectural Changes**:
- Added `codex-code/` and `copilot-code/` trees mirroring `claude-code/` (plugins, bundles, project-template, installers placeholders).
- Created design roots `docs/design/codex_aisdlc/` and `docs/design/copilot_aisdlc/` with requirements lists, design summaries, implementation designs, and ADR namespaces.
- Added platform-specific README stubs for plugins/bundles/skills and project templates to anchor future implementations.

**TDD Process**:
1. **RED Phase**: Not applicable (documentation scaffolding).  
2. **GREEN Phase**: Authored scaffold files and parity docs.  
3. **REFACTOR Phase**: Removed unused `implementations/` folder in `codex_aisdlc` to avoid duplication with `codex-code/`.

---

## Files Modified

- `codex-code/README.md` – Added Codex asset overview and structure.  
- `codex-code/plugins/README.md` and plugin/bundle READMEs – Parity placeholders.  
- `codex-code/project-template/README.md` (+ `codex/`, `.ai-workspace/` READMEs) – Template scaffold.  
- `codex-code/installers/README.md` – Installer placeholder notes.  
- `docs/design/codex_aisdlc/*` – Design, requirements, implementation design, ADR namespace.  
- `copilot-code/README.md` and sub-READMEs (plugins, bundles, project-template, installers) – Copilot scaffold.  
- `docs/design/copilot_aisdlc/*` – Copilot design, requirements, implementation design, ADR namespace.  
- Removed `docs/design/codex_aisdlc/implementations/` – Consolidated implementations under `codex-code/`.

---

## Test Coverage

Documentation-only changes; no automated tests run. Coverage unaffected.

---

## Feature Flag

Not applicable.

---

## Code Changes

Documentation and scaffold directory additions only (no runtime code). Key outcome is structured placeholders aligned with Claude assets.

---

## Testing

Manual validation:
- Verified directory structures mirror Claude layout.  
- Checked design docs reference correct requirement sets and ADR namespaces.

---

## Result

✅ Codex and Copilot scaffolds now exist with parity to Claude, including design references, requirements lists, ADR namespaces, and plugin/template placeholders.  
✅ Removed redundant `implementations/` folder from `codex_aisdlc` to reduce confusion.

---

## Side Effects

**Positive**:
- Clear landing zones for future Codex/Copilot implementations.  
- Maintains federated plugin narrative across platforms.

**Considerations**:
- Placeholders still need functional content (scripts, prompts, snippets, real plugins).

---

## Future Considerations

1. Populate Copilot prompt packs/snippets and wiring to workspace scripts.  
2. Implement Codex/Copilot installer scripts to mirror Claude behavior.  
3. Add ADRs documenting platform-specific decisions as implementations solidify.  
4. Wire traceability regeneration to platform scripts (e.g., `validate_traceability.py` equivalents).

---

## Lessons Learned

1. Keeping strict structural parity simplifies multi-platform support and traceability.  
2. Clearly removing redundant folders prevents confusion about implementation locations.  
3. ADR namespaces per platform help isolate decisions and divergences.

---

## Traceability

**Requirements Coverage**:
- REQ-F-PLUGIN-001/002/003/004: Platform plugin scaffolds and bundles added.  
- REQ-F-CMD-001/002: Command/persona equivalents planned via prompts/scripts (placeholders added).  
- REQ-NFR-FEDERATE-001: Federated structure mirrored across platforms.  
- REQ-NFR-TRACE-001: Design docs and requirements mapping established for future enforcement.

**Downstream Traceability**:
- No code commits yet; scaffolds ready for future implementations.

---

## Metrics

- **Lines Added**: ~400 (docs/scaffolds)  
- **Lines Removed**: ~10 (implementation folder removal)

---

## Related

- Platform parity with `claude-code/` and `docs/design/claude_aisdlc/`.  
- Roo counterpart: `docs/design/roo_aisdlc/` and `roo-code-iclaude/`.
