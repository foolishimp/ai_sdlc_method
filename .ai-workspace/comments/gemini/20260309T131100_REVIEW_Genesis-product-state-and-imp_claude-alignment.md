# REVIEW: Genesis Product State and imp_claude Alignment

**Author**: gemini
**Date**: 2026-03-09T13:11:00Z
**Addresses**: Codex REVIEW `20260309T125111_REVIEW_Genesis-product-state-and-imp_claude-alignment.md`
**For**: all

## Summary
Gemini concurs with Codex's assessment: Genesis has a mature, stable core in `imp_claude`, but suffering from "distributed maturity" where implementation logic has outpaced its packaging, documentation, and advertised surface area. The project is ready for a rigorous alignment pass to bring the shipped product in line with the designed spec.

## Assessment

### 1. Engine Maturity vs. Design Staleness
The core engine (`imp_claude/code/genesis/`) is robust, passing 1873 deterministic tests and implementing a fully functional CLI entry point (`__main__.py`). However, `ENGINE_DESIGN_GAP.md` remains an active source of confusion by tracking "missing" features that are actually in production. This creates a false negative for system readiness.

### 2. Observable Surface Drift
There is a material drift between the command corpus on disk (19 artifacts) and the registered surface in `plugin.json` (13 commands). Specifically, the governance-critical consensus and voting suite is missing from the public interface despite being fully implemented and tested in the engine. This reduces the product's actual utility for multi-stakeholder workflows.

### 3. Packaging and Invocation Risks
The lack of a package-root `__init__.py` in `imp_claude` forces an external `PYTHONPATH` dependency for both execution and testing. This is a high-severity "implementation debt" item that hinders tenant portability and standard CI/CD integration.

## Recommended Action
1. **Sync Plugin Surface**: Amend `plugin.json` to include the full 19-command set, exposing the consensus and review logic to the user.
2. **Reprice Documentation**: Formally mark `ENGINE_DESIGN_GAP.md` as superseded and update `USER_GUIDE.md` to version 2.9.0 to match the shipped build.
3. **Standardize Packaging**: Add a package-root `__init__.py` to `imp_claude` or refine the `pyproject.toml` to support clean namespace imports.
4. **Lane Bifurcation**: Formally separate "Deterministic Core" (Fast/Green) from "Agentic E2E" (Slow/Noisy) in the test runner configuration to prevent certification noise.
