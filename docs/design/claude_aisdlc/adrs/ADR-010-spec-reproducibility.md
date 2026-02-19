# ADR-010: Spec Reproducibility

**Status**: Accepted
**Date**: 2026-02-19
**Deciders**: Methodology Author
**Requirements**: REQ-INTENT-004

---

## Context

The Asset Graph Model (§5.2) defines that a Spec — the combination of Intent + Context[] — must be reproducible. Given the same Spec, any implementation of iterate() should produce equivalent candidates. This is the bridge between non-deterministic LLM generation and deterministic engineering requirements.

REQ-INTENT-004 specifies five acceptance criteria:
1. Canonical serialisation format for Spec (deterministic byte sequence)
2. Content-addressable hash of the Spec
3. Hash recorded at each iteration
4. Independent tools compute the same hash from the same Spec
5. Immutable Spec versions (evolution produces new versions, not mutations)

We need to decide how to implement spec reproducibility in Claude Code.

### Options Considered

1. **Git-based versioning only** — rely on git commit hashes as the version identity
2. **Content-addressable manifest** — deterministic serialisation + SHA-256 hash, stored in a manifest file
3. **Content-addressable storage (CAS)** — full content-addressable object store (like git's object model)

---

## Decision

**We will implement a content-addressable manifest (`context_manifest.yml`) that records the deterministic hash of the Context[] store at each checkpoint.**

The approach:
- **Canonical serialisation**: sorted directory traversal, deterministic YAML/markdown rendering, UTF-8 normalisation
- **Hash function**: SHA-256 of the canonical byte sequence
- **Manifest file**: `.ai-workspace/context/context_manifest.yml` listing each context entry with its individual hash and the aggregate hash
- **Recording**: each `/aisdlc-checkpoint` and each `/aisdlc-iterate` invocation records the context hash in the feature vector state
- **Immutability**: context versions are append-only; mutation produces a new version with a new hash

---

## Rationale

### Why Content-Addressable Manifest (vs Git Only)

**1. Git tracks file changes, not semantic context** — A git commit hash includes everything in the repo (code, tests, docs, configs). The context manifest hashes only the Context[] store — the actual constraint surface that parameterises iterate(). This is a more precise identity.

**2. Reproducibility across environments** — Two developers with the same `context_manifest.yml` hash have the same constraint surface, even if their repos differ in other ways (different branches, different work-in-progress code). Git commit identity doesn't give you this.

**3. Independent verification** — REQ-INTENT-004 requires that independent tools compute the same hash. A well-defined canonical serialisation algorithm is verifiable by any tool that reads the same files. Git hashes depend on git metadata (author, timestamp, parent commit), not just content.

**4. Iteration lineage** — Recording the context hash at each iterate() invocation creates a precise audit trail: "This code candidate was produced with Context[] hash `sha256:a1b2...`". If the context changes, subsequent iterations produce different candidates from a different constraint surface.

### Why Not Full CAS

A full content-addressable object store (like git's internal model) adds implementation complexity disproportionate to the benefit. The manifest file achieves the reproducibility guarantee without requiring a storage engine. If full CAS becomes needed (e.g., for enterprise audit requirements), the manifest is forward-compatible — it already contains the hashes that a CAS would use as keys.

---

## Canonical Serialisation Algorithm

```
1. Enumerate all files in .ai-workspace/context/ (excluding context_manifest.yml)
2. Sort by relative path (lexicographic, UTF-8)
3. For each file:
   a. Read raw bytes
   b. Normalise to UTF-8 NFC
   c. Compute SHA-256
   d. Record: { path, hash, size, type }
4. Serialise the sorted entry list as deterministic YAML:
   - Sorted keys
   - No flow style
   - UTF-8 encoding
   - LF line endings
5. Compute SHA-256 of the serialised entry list
6. This is the aggregate context hash
```

### Determinism Guarantees

- **File ordering**: lexicographic sort on relative paths (locale-independent)
- **Content normalisation**: UTF-8 NFC form (handles combining characters)
- **YAML serialisation**: sorted keys, block style, no comments
- **Line endings**: LF only (normalise CRLF)
- **No metadata**: timestamps, permissions, ownership are excluded

---

## Consequences

### Positive

- **Audit trail** — every iteration records which constraint surface produced it
- **Reproducibility** — same context hash guarantees same constraints, regardless of environment
- **Forward-compatible** — manifest can feed into more sophisticated CAS if needed
- **Tool-independent** — any tool implementing the serialisation algorithm produces the same hash
- **Lightweight** — just a YAML file, no infrastructure

### Negative

- **Serialisation complexity** — deterministic serialisation has edge cases (binary files, encoding issues, symlinks). The algorithm must be precisely specified to ensure cross-tool agreement.
- **Hash computation overhead** — computing SHA-256 of all context files on each checkpoint. For typical projects this is negligible; for very large context stores it could be noticeable.
- **Manifest staleness** — if a developer modifies context files without running checkpoint, the manifest is stale. The iterate agent should warn if context file mtimes are newer than the manifest.

### Mitigation

- Start with text files only (markdown, YAML) — defer binary file handling
- The `/aisdlc-checkpoint` command always regenerates the manifest
- The iterate agent checks manifest freshness before proceeding
- Document the canonical serialisation algorithm in the methodology reference

---

## Manifest Format

```yaml
# .ai-workspace/context/context_manifest.yml
version: "1.0.0"
generated_at: "2026-02-19T10:30:00Z"
algorithm: "sha256-canonical-v1"

aggregate_hash: "sha256:a1b2c3d4e5f6..."

entries:
  - path: "adrs/ADR-001-platform.md"
    hash: "sha256:1a2b3c..."
    size: 7437
    type: adr

  - path: "graph/asset_types.yml"
    hash: "sha256:4d5e6f..."
    size: 1024
    type: graph_topology

  - path: "graph/transitions.yml"
    hash: "sha256:7g8h9i..."
    size: 2048
    type: graph_topology

  - path: "templates/code_standard.md"
    hash: "sha256:0j1k2l..."
    size: 512
    type: template
```

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §5.2 (Spec Reproducibility)
- [AISDLC_V2_DESIGN.md](../AISDLC_V2_DESIGN.md) §2.3 (Context Management)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) REQ-INTENT-004
