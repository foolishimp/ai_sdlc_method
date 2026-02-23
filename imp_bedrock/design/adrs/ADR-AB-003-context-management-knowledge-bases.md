# ADR-AB-003: Context Management via Knowledge Bases and Direct S3

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Bedrock Genesis Design Authors
**Requirements**: REQ-CTX-001, REQ-CTX-002, REQ-INTENT-004

---

## Context

The Asset Graph Model defines Context[] as the standing constraint surface that bounds construction at every iterate() invocation. Context includes ADRs, specs, data models, templates, prior implementations, and policy documents. The implementation must:

1. Make relevant context available to the Bedrock Converse API at iterate time (REQ-CTX-001).
2. Support hierarchical context composition — global, organisation, team, project levels (REQ-CTX-002).
3. Ensure spec reproducibility through content-addressable hashing and immutable versioning (REQ-INTENT-004).

Bedrock Genesis faces a unique challenge compared to CLI-based implementations (Claude, Gemini, Codex): context must be assembled for a stateless API call rather than loaded from a local filesystem in a long-lived session. The Converse API has a finite context window, and specification documents, ADR sets, and cross-cutting context can easily exceed 50KB — approaching or exceeding practical prompt limits when combined with the construction task itself.

AWS provides **Bedrock Knowledge Bases** — a managed RAG (Retrieval-Augmented Generation) service that ingests documents from S3, chunks and embeds them into a vector store (OpenSearch Serverless), and retrieves relevant passages at query time. This is a natural fit for large, semi-structured specification context. However, small deterministic configs (edge parameters, feature vectors, graph topology) are better served by direct reads — RAG adds unnecessary latency and non-determinism for content that should be assembled verbatim.

### Options Considered

1. **Knowledge Bases only** — All context (specs, ADRs, edge configs, feature vectors) ingested into a single Knowledge Base. Retrieval at every iterate call.
2. **Direct prompt assembly only** — All context loaded from S3 and assembled directly into Converse API messages. No RAG.
3. **Hybrid: Knowledge Bases for large context + direct S3 reads for small configs** — Two-tier strategy based on context size and determinism requirements.

---

## Decision

**We adopt the hybrid two-tier context strategy (Option 3): Bedrock Knowledge Bases for large specification context, direct S3/local reads for edge configurations and small deterministic context.**

### Tier 1: Bedrock Knowledge Bases (RAG) — Large Context

**When**: Specification documents, ADR sets, cross-cutting context, design documents — typically >50KB aggregate or requiring semantic search across many documents.

**Setup**:
1. S3 data source bucket: `s3://project-bucket/knowledge-base/` containing spec, ADR, and design markdown files.
2. Bedrock Knowledge Base with automatic chunking (default 300 tokens, 20% overlap) and embedding (Titan Embeddings v2).
3. OpenSearch Serverless vector store as the index backend.
4. Retrieval at iterate time: the iterate Step Functions workflow queries the Knowledge Base with the current edge context + construction task, retrieving top-k relevant passages.

**Usage pattern**:
- Spec-level queries: "What are the acceptance criteria for REQ-CTX-001?"
- ADR lookup: "What decisions constrain the evaluator framework?"
- Cross-cutting context: design principles, methodology constraints, prior disambiguation decisions.

### Tier 2: Direct S3/Local Reads — Small Configs

**When**: Edge parameters, feature vectors, graph topology, evaluator defaults, project constraints — typically <50KB, required verbatim (not semantically searched).

**Setup**:
1. S3 config prefix: `s3://project-bucket/config/` (or local `.ai-workspace/` for hybrid mode).
2. Direct `GetObject` calls from Lambda or Step Functions.
3. Content assembled verbatim into Converse API system/user messages.

**Usage pattern**:
- Edge params: `edges/intent_requirements.yml` loaded in full for the current transition.
- Feature vectors: `features/active/REQ-F-AUTH-001.yml` loaded for state tracking.
- Graph topology: `graph_topology.yml` loaded for routing decisions.
- Evaluator defaults: `evaluator_defaults.yml` for convergence thresholds.

### Context Manifest and Reproducibility

The context manifest (`context_manifest.yml`) is stored in DynamoDB with the following structure:

```yaml
# DynamoDB: context_manifests table
# Partition key: project_id
# Sort key: manifest_version

version: "1.0.0"
generated_at: "2026-02-23T10:30:00Z"
algorithm: "sha256-canonical-v1"
aggregate_hash: "sha256:a1b2c3d4e5f6..."

knowledge_base:
  kb_id: "KB-xxxxxxxx"
  sync_status: "COMPLETE"
  last_sync: "2026-02-23T10:25:00Z"
  source_hash: "sha256:9f8e7d..."    # Hash of all KB source documents

direct_context:
  entries:
    - path: "config/graph_topology.yml"
      hash: "sha256:1a2b3c..."
      size: 2048
      s3_version_id: "v1.abc123"
    - path: "config/edges/intent_requirements.yml"
      hash: "sha256:4d5e6f..."
      size: 1024
      s3_version_id: "v1.def456"
```

**S3 object versioning** is enabled on the config bucket, providing content-addressable history. Each S3 version ID maps to an immutable object — mutation produces a new version, not an overwrite. The manifest records the S3 version ID for each direct-read context entry, ensuring that a given manifest hash can reconstruct the exact constraint surface.

**SHA-256 hashing** follows the same canonical serialisation algorithm as ADR-010 (Spec Reproducibility): sorted directory traversal, UTF-8 NFC normalisation, deterministic YAML rendering, LF line endings.

### Tier Selection Logic

```
if context_type in {spec, adr, design_doc, cross_cutting} AND aggregate_size > 50KB:
    → Knowledge Base retrieval (semantic search, top-k passages)
elif context_type in {edge_params, feature_vector, graph_topology, evaluator_config, project_constraints}:
    → Direct S3 read (verbatim assembly)
else:
    → Direct S3 read (default to deterministic path)
```

The 50KB threshold is configurable in `project_constraints.yml` under `context.rag_threshold_bytes`. Projects with small specs may use direct reads exclusively; projects with extensive specification sets benefit from RAG.

---

## Rationale

### Why Hybrid (vs Knowledge Bases Only)

1. **Determinism for configs**: Edge parameters and evaluator thresholds must be loaded verbatim. RAG retrieval introduces non-determinism (embedding similarity, chunk boundaries, top-k selection) that is unacceptable for configuration that directly controls iterate() behavior.
2. **Latency**: Direct S3 reads complete in single-digit milliseconds. Knowledge Base queries add embedding + vector search + retrieval latency (typically 200-500ms). For small configs loaded on every iteration, this overhead is wasteful.
3. **Cost**: Knowledge Base queries incur embedding compute + vector store query costs. Direct reads are S3 GET requests — orders of magnitude cheaper for content that doesn't benefit from semantic search.

### Why Hybrid (vs Direct Assembly Only)

1. **Context window limits**: The Converse API has model-dependent context windows (100K-200K tokens for Claude on Bedrock, less for other models). A full specification set (spec + 18 ADRs + design doc + implementation requirements) can easily exceed 100KB of markdown. Direct assembly would consume the entire context window, leaving no room for the construction task.
2. **Semantic relevance**: When iterating on a specific edge (e.g., `requirements → design`), only a subset of the specification is relevant. Knowledge Base retrieval returns the most relevant passages, not the entire document set. This improves both quality (focused context) and cost (fewer input tokens).
3. **Scalability**: As the specification grows, direct assembly breaks. Knowledge Bases scale with the document corpus — adding more ADRs doesn't degrade query performance.

### Why S3 Versioning for Reproducibility

S3 object versioning is AWS's native content-addressable storage mechanism. Each `PutObject` to a versioned bucket creates a new version with a unique `VersionId`. This maps directly to REQ-INTENT-004's requirement that "Spec versions are immutable — evolution produces new versions, not mutations." No custom CAS implementation is needed.

---

## Consequences

### Positive

- **RAG scales to large specification sets** — Projects with 50+ ADRs and extensive specs get semantic retrieval without context window exhaustion.
- **Direct reads are fast and cheap** — Edge configs load in milliseconds with no embedding overhead, preserving iterate() performance.
- **S3 versioning provides audit trail** — Every context change is tracked with a unique version ID; no custom version control needed.
- **Model-agnostic** — Knowledge Base retrieval works with any foundation model available on Bedrock (Claude, Llama, Mistral, etc.) since retrieved passages are injected as plain text.
- **Context manifest preserves reproducibility** — DynamoDB manifest with SHA-256 hashes and S3 version IDs ensures any iterate() invocation can reconstruct its exact constraint surface.
- **Configurable threshold** — Teams can tune the RAG/direct boundary based on their project size and latency requirements.

### Negative

- **Knowledge Base sync latency** — After updating specification documents in S3, the Knowledge Base must re-sync (re-chunk, re-embed). This can take minutes for large document sets. Iterating immediately after a spec change may use stale RAG context.
- **Embedding cost** — Titan Embeddings charges per token for both ingestion and query. For projects with frequent spec updates, re-embedding costs accumulate.
- **Chunk boundary issues** — RAG chunking may split a requirement or ADR section mid-paragraph, losing local coherence. Tuning chunk size and overlap mitigates but does not eliminate this risk.
- **Two-tier complexity** — Developers must understand which context tier applies. Miscategorising a config as RAG-eligible (or vice versa) can cause subtle correctness or performance issues.

### Mitigation

- **Sync freshness check**: The iterate workflow checks Knowledge Base sync status before proceeding. If `last_sync` is older than the most recent S3 object modification time, a warning is emitted and the user can force re-sync.
- **Metadata-aware chunking**: Use Knowledge Base chunking strategies that respect markdown heading boundaries (H1/H2 as chunk delimiters) to keep ADR sections and requirement blocks intact.
- **Tier override**: `project_constraints.yml` allows explicit tier assignment per context path, overriding the size-based heuristic.
- **Cost monitoring**: CloudWatch metrics on Knowledge Base query count and Titan Embeddings token usage, with budget alerts via EventBridge.

---

## References

- [ADR-AB-001-bedrock-runtime-as-platform.md](ADR-AB-001-bedrock-runtime-as-platform.md) — Platform binding (Bedrock Converse API)
- [ADR-AB-002-iterate-engine-step-functions.md](ADR-AB-002-iterate-engine-step-functions.md) — Iterate engine (Step Functions workflow loads context at step 2)
- [ADR-010-spec-reproducibility.md](ADR-010-spec-reproducibility.md) — Canonical serialisation and content-addressable hashing algorithm
- [BEDROCK_GENESIS_DESIGN.md](../BEDROCK_GENESIS_DESIGN.md) §2.3 (Context Management and Reproducibility)
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §5.1 (What Context Contains), §5.2 (Context as Constraint Density)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) REQ-CTX-001, REQ-CTX-002, REQ-INTENT-004
