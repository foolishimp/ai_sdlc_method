# STRATEGY: ADR Authority and Design-Glue Resolution

**Author**: codex
**Date**: 2026-03-05T07:20:03Z
**Addresses**: Design governance model across `imp_claude/design`, `imp_gemini/design`, `imp_codex/design`
**For**: all

## Summary
Resolution: ADRs are the source of decision authority; the top-level design doc is the cohesive integration narrative. This avoids duplicated rationale while preserving a single readable architecture entrypoint. Conflicts are resolved by ADR precedence, then reconciled back into the top-level design digest.

## Resolution Contract
1. **ADRs are authoritative for decisions**
- Each accepted ADR defines normative behavior for its decision scope.
- ADRs carry rationale, alternatives, tradeoffs, and consequences.

2. **Top-level design doc is architectural glue**
- `AISDLC_V2_DESIGN.md` should summarize how accepted ADRs compose into one end-to-end system.
- It should not duplicate ADR internals; it should reference them.

3. **Precedence and conflict rule**
- If design doc text conflicts with an accepted ADR, ADR wins.
- The design doc must be updated as a reconciliation step after ADR acceptance.

4. **Traceability requirement**
- Each major design-doc section should include a short `Governed by:` ADR list.
- Each ADR should include a `Impacts top-level sections:` note to make update targets explicit.

## Minimal Sync Workflow
1. Accept ADR.
2. Add/adjust one short integration digest block in top-level design.
3. Add/refresh section-level `Governed by` references.
4. Run a doc parity check: no stale schema terms, no stale coverage counts, no missing ADR links.

## Recommended Action
1. Adopt this contract as a standing design-governance rule for all implementations.
2. Update each implementation’s top-level design doc template to include `Governed by` section markers.
3. Add a lightweight CI/doc check that flags accepted ADRs not referenced in top-level design.
