# ADR-103: Codex Plugin Packaging and Marketplace Mapping

**Status**: accepted (metadata created; functionality TBD)  
**Date**: 2025-11-26  
**Requirements**: REQ-F-PLUGIN-001, REQ-F-PLUGIN-002, REQ-F-PLUGIN-003, REQ-F-PLUGIN-004  
**Decision Drivers**: Codex needs discoverable, versioned plugin metadata and bundle definitions parallel to Claude/Gemini, with clear dependency mapping and federated loading.

## Context
- Claude plugins use `.claude-plugin/plugin.json`; Codex lacked metadata and marketplace entries.
- Marketplace must list Codex assets with platform markers to enable selection and override behavior.
- Dependencies should point to Codex-namespaced packages to avoid collisions across platforms.

## Decision
- Name Codex plugins with a `-codex` suffix (e.g., `aisdlc-core-codex`) and place metadata at `codex-code/plugins/*/.codex-plugin/plugin.json`.
- Register Codex plugins and bundles in `marketplace.json` with `provider: openai`, SemVer, paths under `codex-code/plugins/...`, and dependencies referencing the `-codex` names.
- Follow the same bundle set as Claude: startup, datascience, qa, enterprise.
- Document federated loading (global → project) in Codex docs and installers.

## Consequences
- Codex assets are discoverable and versioned; SemVer applies independently from Claude/Gemini.
- Bundles resolve against Codex package names, preventing cross-platform dependency confusion.
- Marketplace now contains Codex entries for parity and future installation tooling.

## Workarounds / Gaps
- Plugin functionality is not yet implemented; packages are metadata-only. Until code exists, use Claude commands/skills on the shared workspace or manually follow method guides.
- Federated loading rules must be documented and enforced in installers; current state is design-only.
