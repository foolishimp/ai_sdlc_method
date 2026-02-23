# ADR-010: Spec Reproducibility — Bedrock Genesis Adaptation

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Bedrock Genesis Design Authors
**Requirements**: REQ-INTENT-004, REQ-CTX-002
**Adapts**: Claude ADR-010 (Spec Reproducibility) for AWS Bedrock

---

## Context

The Asset Graph Model (§5.2) defines that a Spec — the combination of Intent + Context[] — must be reproducible. Given the same Spec, any implementation of iterate() should produce equivalent candidates. This is the bridge between non-deterministic LLM generation and deterministic engineering requirements.

REQ-INTENT-004 specifies five acceptance criteria:
1. Canonical serialisation format for Spec (deterministic byte sequence)
2. Content-addressable hash of the Spec
3. Hash recorded at each iteration
4. Independent tools compute the same hash from the same Spec
5. Immutable Spec versions (evolution produces new versions, not mutations)

The Claude reference implementation (ADR-010) uses a `context_manifest.yml` file in the local `.ai-workspace/context/` directory with SHA-256 hashes computed via a canonical serialisation algorithm. This works well for single-machine, filesystem-based workflows.

Bedrock Genesis operates across two storage tiers: S3 for cloud-canonical state and local `.ai-workspace/` for developer experience (ADR-AB-008). Context is split between Bedrock Knowledge Bases (RAG for large documents) and direct S3 reads (for small configs) per ADR-AB-003. Reproducibility must span both tiers and both context retrieval mechanisms.

Additionally, S3 provides native content-addressable storage via object versioning. Each S3 `PutObject` creates an immutable version with a unique `VersionId`. This is a managed implementation of the content-addressable storage that ADR-010 considered but rejected as over-engineered for the Claude CLI. In the cloud context, it comes for free.

### Options Considered

1. **Local manifest only** — identical to Claude: `context_manifest.yml` in `.ai-workspace/context/` with file-based SHA-256 hashing. Ignore S3 versioning.
2. **S3 versioning only** — rely on S3 version IDs as the content-addressable identity. No separate manifest.
3. **Hybrid: Content-addressable manifest in DynamoDB + S3 version IDs** — manifest stored in DynamoDB for team access, incorporating both SHA-256 hashes and S3 version IDs for dual verification.

---

## Decision

**We implement a content-addressable manifest stored in DynamoDB, incorporating both SHA-256 hashes (for cross-platform compatibility) and S3 version IDs (for cloud-native verification). The manifest is the bridge between the methodology's canonical serialisation algorithm and AWS's native content-addressing.**

### Manifest Storage

The manifest is stored in DynamoDB rather than a local file:

```
Table: {project_prefix}-context-manifests

Primary Key:
  PK (Partition Key): project_id          (String)
  SK (Sort Key):      manifest_version    (String, "v{n}" monotonic)

Attributes:
  aggregate_hash    (String)   — SHA-256 of canonical serialisation
  algorithm         (String)   — "sha256-canonical-v1"
  generated_at      (String)   — ISO-8601 timestamp
  generator         (String)   — "bedrock-genesis" | "claude" | "manual"

  knowledge_base    (Map)
    kb_id           (String)   — Bedrock Knowledge Base ID
    sync_status     (String)   — "COMPLETE" | "IN_PROGRESS"
    last_sync       (String)   — ISO-8601 timestamp
    source_hash     (String)   — SHA-256 of all KB source documents

  direct_entries    (List of Map)
    - path          (String)   — relative path within config
      hash          (String)   — SHA-256 of file content
      size          (Number)   — bytes
      s3_version_id (String)   — S3 object VersionId
      s3_etag       (String)   — S3 ETag (MD5 for non-multipart)
```

### Dual Verification

Every context entry carries two independent content identifiers:

1. **SHA-256 hash** — computed via the canonical serialisation algorithm (identical to Claude ADR-010). This is the cross-platform identifier: a Claude workspace and a Bedrock workspace with the same context files produce the same hash.

2. **S3 version ID** — the AWS-native immutable content identifier. This is the cloud-specific verifier: given a version ID, S3 returns exactly that content, regardless of subsequent modifications.

The `aggregate_hash` is computed using only SHA-256 hashes (not S3 version IDs), preserving cross-platform compatibility. A Claude installation and a Bedrock installation with identical context files produce identical `aggregate_hash` values.

S3 version IDs provide an additional verification layer within the AWS ecosystem. The iterate engine can verify context integrity by checking that the SHA-256 hash of the S3 object at the recorded version ID matches the manifest's hash entry.

### Canonical Serialisation Algorithm

The algorithm is identical to Claude ADR-010 for cross-platform reproducibility:

```
1. Enumerate all context files (S3 objects in config prefix, excluding manifest)
2. Sort by relative path (lexicographic, UTF-8)
3. For each file:
   a. Read raw bytes (S3 GetObject with VersionId for pinned reads)
   b. Normalise to UTF-8 NFC
   c. Compute SHA-256
   d. Record: { path, hash, size, s3_version_id, s3_etag }
4. Serialise the sorted entry list as deterministic YAML:
   - Sorted keys
   - No flow style
   - UTF-8 encoding
   - LF line endings
5. Compute SHA-256 of the serialised entry list
6. This is the aggregate context hash
```

Steps 1-5 produce a byte-identical result whether the files are read from S3 or from local `.ai-workspace/`. This satisfies REQ-INTENT-004 criterion 4: "Independent tools compute the same hash from the same Spec."

### Knowledge Base Reproducibility

Bedrock Knowledge Bases (ADR-AB-003) introduce a challenge: RAG retrieval is non-deterministic (embedding similarity, top-k selection). The manifest tracks Knowledge Base state via:

- **`source_hash`**: SHA-256 of the concatenated source documents fed to the Knowledge Base. If the sources change, the hash changes, and the manifest version increments.
- **`sync_status`**: whether the Knowledge Base has completed re-indexing after a source change.
- **`last_sync`**: when the Knowledge Base last synchronised with its S3 data source.

The manifest does NOT hash RAG retrieval results (these are non-deterministic). It hashes the RAG source corpus. Two iterate invocations with the same `source_hash` are operating against the same corpus, even if RAG retrieval returns slightly different passages.

### Manifest Lifecycle

1. **Generation**: `gen-checkpoint` generates a new manifest version by scanning the S3 config prefix and computing hashes. The manifest is written to DynamoDB as a new item with an incremented version key.

2. **Recording**: each iterate invocation records the `aggregate_hash` and `manifest_version` in the DynamoDB events table alongside the `iteration_completed` event.

3. **Verification**: before constructing a candidate, the `LoadConfig` Lambda can optionally verify that the current context matches the recorded manifest. If context files have been modified since the last checkpoint, a warning is emitted.

4. **Immutability**: manifest versions are append-only in DynamoDB. Mutation produces a new version, never an update to an existing one. DynamoDB's `attribute_not_exists(SK)` condition prevents accidental overwrites.

### Local Manifest Mirror

For developer experience, the manifest is also written to `.ai-workspace/context/context_manifest.yml` during `gen-sync pull`. This local copy follows the same YAML format as the Claude implementation, minus the S3-specific fields (`s3_version_id`, `s3_etag`, `knowledge_base`). Developers can inspect the manifest locally using standard tools.

---

## Rationale

### Why DynamoDB Manifest (vs Local File Only)

**1. Team access** — A local manifest file is accessible only to the developer who generated it. DynamoDB stores the manifest centrally, enabling team members and CI/CD pipelines to verify context state.

**2. Append-only history** — DynamoDB's sort key (`manifest_version`) provides a natural append-only history. Each checkpoint adds a new item. The full history of context evolution is queryable. A local file would need git history for the same capability.

**3. Atomic writes** — Multiple concurrent processes (Step Functions, Lambda, CLI) can read the manifest simultaneously. DynamoDB provides strongly consistent reads and conditional writes, preventing race conditions that could affect a local file.

### Why Dual Verification (vs SHA-256 Only)

**1. S3 version IDs are free** — S3 versioning is already enabled for config storage (ADR-AB-008). Recording the version ID alongside the SHA-256 hash costs nothing and provides an independent verification path.

**2. Pinned reads** — An S3 `GetObject` with a `VersionId` parameter returns exactly that version of the object, even if the object has been subsequently modified. This allows the iterate engine to reconstruct the exact constraint surface from a manifest, even if configs have changed since the checkpoint.

**3. Cross-platform hash is preserved** — The `aggregate_hash` uses only SHA-256, not S3 version IDs. A Bedrock manifest and a Claude manifest for the same context produce the same hash. Platform-specific identifiers are supplementary, not primary.

### Why Not S3 Versioning Only

S3 version IDs are opaque strings assigned by AWS. They are not content-addressable in the cryptographic sense — two identical files uploaded at different times receive different version IDs. SHA-256 hashing provides true content addressing: identical content always produces the same hash, regardless of when or where it was stored.

Additionally, S3 version IDs are AWS-specific. The methodology's reproducibility guarantee must be cross-platform (REQ-INTENT-004 criterion 4).

---

## Consequences

### Positive

- **Audit trail** — every iteration records which constraint surface produced it, stored in DynamoDB for team access
- **Reproducibility** — same `aggregate_hash` guarantees same constraints, regardless of whether context was read from S3, local disk, or Knowledge Base source corpus
- **Cross-platform compatibility** — SHA-256 aggregate hash is identical across Claude, Gemini, Codex, and Bedrock implementations for the same context
- **Pinned reconstruction** — S3 version IDs enable exact reconstruction of any historical constraint surface
- **Team visibility** — DynamoDB manifest is queryable by all team members and CI/CD pipelines
- **Forward-compatible** — manifest can feed into more sophisticated CAS or provenance systems

### Negative

- **DynamoDB cost** — manifest reads/writes add incremental DynamoDB charges. For typical projects (checkpoints every few hours), this is negligible.
- **Knowledge Base non-determinism** — RAG retrieval is non-deterministic even with identical source corpora. The manifest tracks source corpus identity, not retrieval identity. Two iterate invocations with the same manifest may receive different RAG passages.
- **Sync latency for local mirror** — the local `context_manifest.yml` may lag behind the DynamoDB canonical version until the next `gen-sync pull`.
- **Serialisation complexity** — deterministic serialisation has edge cases (binary files, encoding issues). The algorithm must be precisely specified.

### Mitigation

- DynamoDB on-demand pricing ensures cost scales linearly with checkpoint frequency. No provisioned capacity needed.
- Knowledge Base non-determinism is inherent to RAG. The manifest documents the source corpus; the iterate engine logs the actual retrieved passages in the iteration event for forensic analysis.
- `gen-status --health` reports manifest sync freshness and warns if the local mirror is stale.
- Start with text files only (markdown, YAML) — defer binary file handling. The canonical serialisation algorithm is tested against known input/output pairs in the test suite.

---

## Manifest Format (DynamoDB + Local Mirror)

**DynamoDB item:**

```json
{
  "PK": "project-foo",
  "SK": "v42",
  "aggregate_hash": "sha256:a1b2c3d4e5f6...",
  "algorithm": "sha256-canonical-v1",
  "generated_at": "2026-02-23T10:30:00Z",
  "generator": "bedrock-genesis",
  "knowledge_base": {
    "kb_id": "KB-xxxxxxxx",
    "sync_status": "COMPLETE",
    "last_sync": "2026-02-23T10:25:00Z",
    "source_hash": "sha256:9f8e7d..."
  },
  "direct_entries": [
    {
      "path": "config/graph_topology.yml",
      "hash": "sha256:1a2b3c...",
      "size": 2048,
      "s3_version_id": "v1.abc123",
      "s3_etag": "\"d41d8cd98f00b204e9800998ecf8427e\""
    }
  ]
}
```

**Local mirror (`.ai-workspace/context/context_manifest.yml`):**

```yaml
version: "1.0.0"
generated_at: "2026-02-23T10:30:00Z"
algorithm: "sha256-canonical-v1"
aggregate_hash: "sha256:a1b2c3d4e5f6..."

entries:
  - path: "config/graph_topology.yml"
    hash: "sha256:1a2b3c..."
    size: 2048
    type: graph_topology

  - path: "config/edges/intent_requirements.yml"
    hash: "sha256:4d5e6f..."
    size: 1024
    type: edge_config
```

The local mirror omits S3-specific fields (`s3_version_id`, `s3_etag`, `knowledge_base`) to maintain format compatibility with the Claude implementation.

---

## References

- [ADR-AB-001](ADR-AB-001-bedrock-runtime-as-platform.md) — Bedrock Runtime as Target Platform
- [ADR-AB-003](ADR-AB-003-context-management-knowledge-bases.md) — Context Management via Knowledge Bases (RAG + direct S3 reads)
- [ADR-AB-005](ADR-AB-005-event-sourcing-dynamodb.md) — Event Sourcing via DynamoDB (iteration events record manifest hash)
- [BEDROCK_GENESIS_DESIGN.md](../BEDROCK_GENESIS_DESIGN.md) — Bedrock implementation design
- [ADR-010: Spec Reproducibility (Claude)](../../imp_claude/design/adrs/ADR-010-spec-reproducibility.md) — reference implementation (local manifest, SHA-256)
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §5.2 (Spec Reproducibility)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) REQ-INTENT-004, REQ-CTX-002
