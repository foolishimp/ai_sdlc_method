# AI SDLC — Gemini Genesis Implementation Design (v1.0)

**Version**: 1.0.0
**Date**: 2026-02-21
**Derived From**: [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) (v2.6.0)
**Reference Implementation**: [AISDLC_V2_DESIGN.md](../claude_aisdlc/AISDLC_V2_DESIGN.md)
**Platform**: Gemini CLI

---

## Design Intent

This document is the |design⟩ asset for the AI SDLC tooling implementation on **Gemini CLI**. It is a sibling implementation to the Claude Code binding, sharing the same underlying Asset Graph Model but adapting the runtime architecture to Gemini's specific capabilities (Sub-agents, Skills, Tools, Memory).

**Key Differentiator**: Gemini CLI's architecture allows for a more autonomous, agentic implementation of the "Universal Iteration Function" and "Sensory Service" compared to the slash-command-driven Claude binding.

**Core Objectives**:
1.  **1-to-1 Mapping**: Implement all 4 primitives (Graph, Iterate, Evaluators, Context) and 16 event types defined in the model.
2.  **Native Integration**: Map `iterate()` to a Gemini **Sub-agent**, Context to **Skills/Memory**, and Commands to **Tools**.
3.  **Enhanced UX**: Leverage Gemini's background process capabilities for the Sensory Service and interactive `ask_user` tool for refinement loops.

---

## 1. Architecture Overview

### 1.1 The Three Layers (Gemini Mapping)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER (Developer)                              │
│                   Natural Language / Tool Invocations                │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AGENT LAYER (Gemini CLI)                        │
│  Orchestrator that routes intent to Sub-agents or Tools             │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SKILL/TOOL LAYER                                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                  Asset Graph Engine (Skill)                  │   │
│  │  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐  │   │
│  │  │ Graph    │  │  iterate()   │  │ Evaluator Framework   │  │   │
│  │  │ Topology │  │  (Sub-agent) │  │ (Tools/Sub-agents)    │  │   │
│  │  └──────────┘  └──────────────┘  └───────────────────────┘  │   │
│  │                                                              │   │
│  │  - aisdlc_start (Orchestrator Tool)                          │   │
│  │  - aisdlc_status (Situational Awareness Tool)                │   │
│  │                                                              │   │
│  │  [Hidden Internal Tools: init, iterate, checkpoint, restore]  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      WORKSPACE LAYER (Unified Root)                  │
│  imp_gemini/                                                         │
│  ├── code/            Gemini tool implementation                     │
│  ├── design/          Gemini design docs and ADRs                    │
│  ├── tests/           Gemini implementation tests                    │
│  │                                                                   │
│  └── .ai-workspace/   Self-referential Dogfooding State              │
│      ├── spec/        Shared tech-agnostic specification             │
│      ├── events/      Shared immutable event log (Source of Truth)   │
│      ├── features/    Shared feature vector tracking                 │
│      ├── tasks/       Task management (active, completed)            │
│      └── snapshots/   Session recovery (immutable checkpoints)       │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Mapping: Agent vs. Tool

| Concept | Claude Code Implementation | Gemini CLI Implementation |
| :--- | :--- | :--- |
| **Iterate Engine** | `aisdlc-iterate.md` (System Prompt) | `aisdlc_investigator` (Sub-agent) + `aisdlc_iterate` (Tool) |
| **Context** | Files in `.ai-workspace/context` | Files + `save_memory` (Global) + `activate_skill` (Project) |
| **Commands** | `/slash-commands` | Native Tools (`aisdlc_init`, `aisdlc_status`) |
| **Sensory Service** | MCP Server (External Process) | Background `run_shell_command` or dedicated Sub-agent |
| **Refinement** | Chat loop | `ask_user` tool (Structured interactive feedback) |

### 1.3 The Universal Iterate Sub-Agent

Instead of a single system prompt, Gemini will use a specialized **Sub-agent** (`aisdlc_investigator` or similar role) that is activated when the `aisdlc_iterate` tool is called.

**Workflow:**
1.  User calls `aisdlc_iterate(edge="design->code", feature="REQ-F-AUTH-001")`.
2.  The Tool:
    -   Reads `graph_topology.yml` and `edge_params`.
    -   Loads `Context[]` and current `Asset`.
    -   Constructs the "Prompt Context" for the Sub-agent.
3.  The Sub-agent:
    -   Performs the construction (e.g., writes code).
    -   Invokes **Evaluator Tools** (e.g., `run_tests`, `check_style`).
    -   Loops until convergence or user intervention.

---

## 2. Component Design

### 2.1 Asset Graph Engine

**Configuration:**
The `graph_topology.yml` and `edge_params/*.yml` files remain the **canonical source of truth**, ensuring compatibility between Claude and Gemini bindings. The Gemini implementation will parse these same YAML files to configure its behavior.

**Tool Definitions:**

```typescript
// aisdlc_iterate
{
  name: "aisdlc_iterate",
  description: "Invokes the universal iteration function on a specific graph edge.",
  parameters: {
    edge: { type: "STRING", description: "The transition to traverse (e.g., 'design->code')" },
    feature: { type: "STRING", description: "The feature vector ID (REQ-F-*)" },
    auto: { type: "BOOLEAN", description: "Auto-iterate until convergence" }
  }
}
```

```typescript
// aisdlc_status
{
  name: "aisdlc_status",
  description: "Displays the current state of feature vectors and graph coverage.",
  parameters: {
    feature: { type: "STRING", description: "Optional: Filter by feature ID" },
    view: { type: "STRING", enum: ["summary", "gantt", "matrix"] }
  }
}
```

### 2.2 Context Management & Recovery (Enhanced)

**Implements**: REQ-CTX-001, REQ-TOOL-008, **REQ-TOOL-NEW-001 (Restore)**, **ADR-GG-006 (Multi-tenancy)**

Gemini's `save_memory` tool is excellent for global user context, but project context is now partitioned by design implementation.

**Multi-tenancy Implementation:**
1.  **Scoped Context**: The `aisdlc_iterate` tool resolves context files within `.ai-workspace/{design_name}/`.
2.  **Shared Spec**: The `spec/` directory remains the shared source of truth for all requirements, ensuring that REQ keys are technology-independent.
3.  **Tenant Initialization**: `aisdlc_init --design <name>` scaffolds the design-specific sub-directories and context manifest.

**NEW: Recovery Capability**
To address the "Recovery" gap identified in the gap analysis, Gemini Genesis includes a native restore capability.

```typescript
// aisdlc_restore
{
  name: "aisdlc_restore",
  description: "Restores the workspace to a previous checkpoint or reconstructs state from the event log.",
  parameters: {
    checkpoint_id: { type: "STRING", description: "Snapshot ID or 'latest'" },
    reconstruct: { type: "BOOLEAN", description: "If true, replays events.jsonl to rebuild derived views (features/tasks/status)" }
  }
}
```

**Reconstruction Logic:**
1.  `reconstruct=true` triggers an "Event Replay" mode.
2.  It parses `.ai-workspace/events/events.jsonl`.
3.  It sequentially updates feature vector files (`.yml`), `STATUS.md`, and `ACTIVE_TASKS.md` based on the immutable event stream.
4.  This allows "Time Travel" debugging and recovery from corrupted state.

### 2.3 Sensory Service (Gemini Native)

Instead of requiring an external MCP server, Gemini can manage the Sensory Service as a background process or a periodic "Health Check" tool invocation.

**Implementation:**
-   **`aisdlc_sense` Tool**: A tool that runs the `INTRO-*` and `EXTRO-*` monitors defined in the design.
-   **Auto-Invocation**: The Gemini Agent can be instructed (via `GEMINI.md`) to run `aisdlc_sense` at the start of a session or after significant changes.
-   **Background Watcher**: For advanced users, `run_shell_command(is_background=true)` can launch a lightweight python script that watches `events.jsonl` and notifies the user via terminal output (which Gemini reads).

### 2.4 Interactive Refinement (Improved UX)

Claude's `/aisdlc-review` is a static "stop and ask" command. Gemini can improve this using `ask_user`.

**Workflow:**
1.  Iterate Agent reaches a decision point (e.g., "Design requires clarification").
2.  Instead of just stopping, it calls `ask_user`:
    ```json
    {
      "questions": [
        {
          "header": "Ambiguity",
          "question": "The requirement REQ-F-AUTH-001 implies 2FA but doesn't specify the method. Which do you prefer?",
          "type": "choice",
          "options": [
            { "label": "TOTP", "description": "Google Authenticator compatible" },
            { "label": "SMS", "description": "Legacy support" },
            { "label": "Email", "description": "Magic link" }
          ]
        }
      ]
    }
    ```
3.  This captures the decision structured data, which is immediately recorded in an **ADR** and the **Event Log**.

---

## 3. Migration & Interoperability

**Co-existence:**
Since both bindings use the same `.ai-workspace` structure and file formats (YAML/Markdown/JSONL), a user can switch between Claude Code and Gemini CLI on the same project without data loss.

**Shared Configuration:**
-   `graph_topology.yml` (Shared)
-   `events.jsonl` (Shared Source of Truth)
-   `project_constraints.yml` (Shared)

**Differences:**
-   Gemini stores its local tool definitions internally or in a `gemini_skills` directory, separate from `.claude`.

---

## 4. Implementation Plan

### Phase 1: Core Primitives (The "Gemini Binding")
1.  **Skill Definition**: Create a Gemini Skill that wraps the AI SDLC logic.
2.  **Tool Implementation**: Implement `init`, `iterate`, `status`, `checkpoint`, `restore` as Python scripts executable by Gemini.
3.  **Investigator Agent**: Configure the `codebase_investigator` prompt to understand the Asset Graph Model.

### Phase 2: Enhanced UX
1.  **Refinement Loop**: Implement `ask_user` integration for ADR generation.
2.  **Sensory Integration**: Create the `aisdlc_sense` tool and "Auto-Sense" workflow.

### Phase 3: "Genesis" (The Self-Creating Project)
1.  **Pre-Init Discovery**: A conversational flow to help users draft the initial `INTENT.md` before running `init`.
2.  **Tech Stack Advisor**: A logic module that reads `INTENT.md` and suggests `project_constraints.yml` settings.

---

## 5. Addressing the Gaps

| Identified Gap | Gemini Genesis Solution |
| :--- | :--- |
| **No Restore Command** | Implemented `aisdlc_restore` with Event Replay. |
| **Guided Intent Discovery** | Added "Pre-Init Discovery" conversational flow. |
| **Tech Stack Advisor** | Added "Tech Stack Advisor" logic in Phase 3. |
| **Interactive Dashboard** | While still text-based, `ask_user` provides interactive decision trees, and `aisdlc_status` can render rich ASCII tables/Gantt. |
| **Self-Healing** | `aisdlc_restore --reconstruct` provides self-healing from the event log. |
