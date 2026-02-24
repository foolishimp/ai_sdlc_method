# Side-by-Side Comparison: Gemini CLI vs. Claude Reference (V2)

**Date**: February 25, 2026
**Subject**: Post-Convergence Architectural Audit (Logically Complete v2.8)

## 1. Executive Summary

Since the first audit, both implementations have achieved **Logic Parity** on the core pillars of the Asset Graph Model. Both now possess Python-native state detection, actual recursive spawning, and strongly-typed data models. 

The primary distinction has shifted from "Industrial vs. Theoretical" to **"Engine-Native Controls (Gemini)"** vs. **"Checklist-Native Binding (Claude)."**

---

## 2. Converged Features (Shared Strengths)

| Feature | Local implementation (Gemini) | Reference implementation (Claude) | Status |
| :--- | :--- | :--- | :--- |
| **State Detection** | `workspace_state.py`: Pure-function filesystem inspection. | `workspace_state.py`: Ported from Gemini. Deterministic. | **Converged** |
| **Recursion** | `cli.py`: Executes sub-loop on SpawnRequest. | `engine.py`: Ported from Gemini. Executes sub-loop. | **Converged** |
| **Data Models** | `models.py`: Dataclasses for Reports/Results. | `models.py`: Original dataclass reference. | **Converged** |
| **Event Sourcing** | `state.py`: Decentralized Projector/Store. | `state.py`: Ported pattern. Unified Store. | **Converged** |

---

## 3. Remaining Unique Advantages

### 3.1 Gemini CLI: The Universal Guardrail Framework
Gemini has moved ahead by implementing **Hard Invariants** via the `GuardrailEngine`.
*   **The Win**: Gemini can block an iteration *before* it starts if organizational policy or dependency rules are violated. This makes it safer for **Operational Work** where unauthorized state transitions must be physically impossible.
*   **The Contrast**: Claude relies on "Evaluators" which run *after* the candidate is generated. Claude senses deviation; Gemini prevents it.

### 3.2 Claude Reference: $Variable Resolution & Binding
Claude maintains a superior implementation of the **Constraint Surface** through its `config_loader.py`.
*   **The Win**: Claude's ability to bind `$tools.test_runner.command` directly from `project_constraints.yml` into the edge checklist is more sophisticated than Gemini's current template resolution. It allows for "Plug-and-Play" SDLCs across different environments.
*   **The Contrast**: Gemini has the `ConfigLoader` but it is not yet as deeply integrated into the per-check dispatch as Claude's.

---

## 4. Operational Readiness Audit

| Dimension | Gemini (Local) | Gemini (Cloud) | Claude |
| :--- | :--- | :--- | :--- |
| **Reporting** | Excellent (Projector-driven) | Potential (BigQuery) | Good (Event-driven) |
| **Orchestration** | Strong (Recursive Spawning) | Strong (Cloud Run) | Moderate (Linear Loop) |
| **Recovery** | Perfect (Event Replay) | Perfect (Firestore) | Strong (Local Log) |
| **Approvals** | Mandatory (FH Functor) | Managed (IAM/PubSub) | Optional (Human check) |

---

## 5. Final Assessment: The "Ultimate" Genesis Core

The "Cleanest" version of the architecture is now visible across both tenants. 

**Gemini's contribution to the core**:
1.  **Homeostatic state machine** (deterministic state detection).
2.  **Universal Guardrails** (hard invariant enforcement).
3.  **Recursive Spawning** (actual execution logic).

**Claude's contribution to the core**:
1.  **Parameterised Binding** ($variable resolution).
2.  **Industrial CLI ergonomics** (The `claude` CLI tool-binding).

### Conclusion:
We have reached **Architectural Stability**. The system is no longer "Gemini vs. Claude"—it is **Project Genesis** implemented across two platforms with shared DNA.
