# AI SDLC on Google Cloud: Native Architecture

**Goal**: Transition the AI SDLC methodology from a local, CLI-bound filesystem architecture to a highly scalable, distributed Google Cloud Platform (GCP) native architecture powered by Vertex AI (Gemini).

## 1. Architectural Paradigm Shift

The current design (`imp_gemini` / `imp_claude`) relies on local directories (`.ai-workspace`), filesystem-based event logs (`events.jsonl`), and local execution of tests and agents. 

A GCP-native implementation shifts the **Control Plane** to the cloud. The CLI becomes a "thin client" (a local observer/actuator), while the state, orchestration, and heavy lifting move to managed services.

## 2. Mapping the Four Primitives to GCP Services

### Primitive 1: The Graph & State (Event Sourcing)
*Current: `.ai-workspace/events/events.jsonl` and YAML feature vectors.*
* **Event Stream**: **Google Cloud Pub/Sub**. All methodology events (`intent_raised`, `edge_converged`, `iteration_completed`) are published to a central topic.
* **Source of Truth (Event Log)**: **BigQuery** (via Pub/Sub to BigQuery subscription) for immutable, querying, and auditing of the entire SDLC history.
* **Materialized State (Feature Vectors)**: **Firestore**. A Cloud Function listens to Pub/Sub and updates the materialized view of active Feature Vectors, Tasks, and the Asset Graph topology.
* **Asset Storage**: **Cloud Storage (GCS)**. Blobs, generated code snippets, large design documents, and context snapshots are stored here, referenced by URI in Firestore.

### Primitive 2: The Iterate Engine (Constructor)
*Current: Local `gen-iterate` script calling an LLM.*
* **The Orchestrator**: **Cloud Run**. A stateless container hosts the `iterate()` logic. It reads the edge config, pulls context from Firestore/GCS, and determines the next step.
* **The Intelligence ($F_P$)**: **Vertex AI (Gemini 1.5 Pro/Flash)**. Cloud Run invokes Gemini via the Vertex AI SDK. Gemini's massive context window (up to 2M tokens) is ideal for loading entire context surfaces (ADRs, existing code, test results) in a single shot.

### Primitive 3: Evaluators
*Current: Local `pytest`, local LLM checks, local human prompts.*
* **Deterministic ($F_D$)**: **Cloud Build**. When the iterate engine needs to compile code or run tests, it triggers a Cloud Build execution. The pass/fail results are published back to Pub/Sub as an event.
* **Probabilistic ($F_P$)**: **Vertex AI**. Used for coherence checks, gap analysis, and heuristic validation.
* **Human ($F_H$)**: **Identity-Aware Proxy (IAP) + Web App / CLI Polling**. Human reviews are queued in Firestore. The developer can use the CLI (`/gen-review`) to pull pending approvals, or a lightweight internal App Engine dashboard.

### Primitive 4: Spec + Context (Constraint Surface)
*Current: Local `context/` folders.*
* **Context Store**: **Cloud Storage (GCS)** for documents (ADRs, Templates). 
* **Vector Search**: **Vertex AI Vector Search**. For large codebases, context retrieval is enhanced by embedding ADRs and prior code. The Iterate engine queries Vector Search to dynamically build the `Context[]` payload for Gemini.

## 3. The Sensory Service (Homeostasis) on GCP

The "ambitious" consciousness loop and background monitoring map perfectly to GCP's event-driven architecture.

* **Interoceptive Monitors** (Internal Health): **Cloud Scheduler** triggers **Cloud Functions** to check Firestore for "stalled" feature vectors or query BigQuery for SLA drops in iteration speed.
* **Exteroceptive Monitors** (Ecosystem): 
    * **Security Command Center (SCC)** natively detects vulnerabilities. SCC alerts are routed to Pub/Sub, transforming automatically into `exteroceptive_signal` events.
    * **Cloud Monitoring** detects production SLA breaches, firing alerts to Pub/Sub to generate `runtime_feedback` intents.
* **Affect Triage**: A dedicated **Cloud Run** service consumes sensory signals from Pub/Sub, classifies them, and if escalation is needed, invokes Vertex AI to draft an `intent_raised` proposal.

## 4. Multi-Agent Coordination

*Current: Complex local inbox folders and "ingestion order" logic to prevent collisions.*
* **GCP Native**: **Firestore Transactions**. Agents (running in parallel Cloud Run instances) attempt to claim an edge by running an atomic transaction on the Feature Vector document in Firestore. If `status == available`, it claims it. No lock files, no local serialiser needed. Massive horizontal scaling.

## 5. The Developer Experience (UX)

The developer still uses the Gemini CLI locally, but its role changes:
1. **`gemini start`**: CLI authenticates via `gcloud auth`. It polls Firestore for the user's assigned tasks.
2. **Local Sync**: The CLI syncs the necessary code from Cloud Source Repositories / GitHub to the local disk so the developer can see the files.
3. **Delegation**: When the user types `gemini iterate`, the CLI simply publishes an `edge_start_requested` event to Pub/Sub. The Cloud Run engine picks it up, runs Gemini, triggers Cloud Build, and publishes the result.
4. **`gemini status`**: CLI reads the materialized views directly from Firestore for instant, real-time global state.

## Summary: Does it work?
Yes, exceptionally well. The AI SDLC methodology is essentially a **distributed state machine**. GCP is designed specifically to host scalable, event-driven state machines. By moving the heavy lifting to Cloud Run, Pub/Sub, and Vertex AI, you eliminate the fragility of local file parsing and gain true, concurrent multi-agent capabilities.