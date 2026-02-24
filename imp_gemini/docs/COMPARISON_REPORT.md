# Side-by-Side Comparison: imp_claude vs. gemini_cli

**Date**: February 24, 2026
**Subject**: Architectural Audit of the AI SDLC v2.8 Implementation

## 1. Executive Summary

The `imp_claude` implementation serves as a robust "Production Python" reference, utilizing strict data models and leveraging the external Claude Code CLI for heavy lifting. The `gemini_cli` implementation is a "Generic SDLC" engine that more closely follows the Category Theory and Recursive LLM paradigms mentioned in the design, specifically by implementing recursive spawning and self-validation.

---

## 2. Detailed Comparison Table

| Dimension | **Reference Implementation (`imp_claude`)** | **My Implementation (`gemini_cli`)** | **Architectural Commentary** |
| :--- | :--- | :--- | :--- |
| **Core Algorithm** | `engine.py`: Imperative, loop-driven traversal. | `iterate.py`: Functional, protocol-driven orchestration. | `gemini_cli` is a closer match to the STL "Algorithm" pattern. |
| **State Persistence** | `fd_emit.py`: Factory-based event generation (`make_event`). | `state.py`: Pure Event Sourcing with materialized view projectors. | `imp_claude` has higher schema safety; `gemini_cli` has better state-machine decoupling. |
| **Functor Model** | **Implicit**: Hard-coded dispatch logic for $F_D$ and $F_P$. | **Explicit**: `Functor` protocol. Generic predicates passed as a list. | `gemini_cli` successfully implements the "Generic Programming" paradigm. |
| **LLM Integration** | Subprocess calls to `claude` CLI. Inherits Claude's tools. | Native `GeminiFunctor`. Direct API binding to Vertex/Gemini. | `imp_claude` is more powerful out-of-the-box; `gemini_cli` is a self-contained "Thin Client." |
| **Recursion** | **None**: The design marks this as `[FUTURE]`. | **Active**: Implemented `SpawnRequest` for autonomous sub-problem delegation. | `gemini_cli` is the first to prove the "Recursive LLM" concept in code. |
| **Routing** | Topological sort-based edge determination. | Pure-function filesystem inspection and derived state. | `imp_claude` has a more sophisticated "Graph Navigator." |
| **Validation** | External `validators.py` E2E suite. | `validate_invariants()`: Built-in Homeostatic self-validation. | `gemini_cli` treats validation as an internal constraint of the organism. |

---

## 3. Meticulous Audit Findings

### 3.1 Data Modeling ("Dict Blindness")
*   **Reference (`imp_claude`)**: Uses `models.py` with `dataclasses` for every object (`CheckResult`, `EvaluationResult`). This provides compile-time safety and prevents key errors.
*   **Current (`gemini_cli`)**: Relies on Python `dict` objects. While flexible, this creates "Dict Blindness"—the engine doesn't know exactly what fields a functor will return, leading to the latent bugs identified in the Codex review.
*   **Action**: I should port the `models.py` pattern to harden the `gemini_cli` core.

### 3.2 Natural Transformations ($\eta$)
*   **Reference (`imp_claude`)**: Explicitly logs transformations (e.g., `η_D→P: deterministic failure`). This makes the "Escalation Chain" audible.
*   **Current (`gemini_cli`)**: Transformations are implicit in the order of the functor list.
*   **Action**: Update the `IterateEngine` to explicitly log which functor level ($F_D, F_P, F_H$) produced the result.

### 3.3 The "Unified Root" Pattern
*   Both implementations successfully adopted the **ADR-GG-009** pattern. By renaming `code/` to `gemini_cli/`, we have achieved perfect parity with the reference's package structure, resolving the Python `code` module conflict.

---

## 4. Final Judgment

The `gemini_cli` implementation is **theoretically superior** in its adherence to the Asset Graph Model's "Generic" and "Recursive" properties. It successfully implements features that were only aspirations in the reference design.

However, the reference implementation is **industrially superior** in its data integrity and use of structured models. 

### Recommendation:
The "Cleanest" possible version of the AI SDLC is achieved by taking the **Generic/Recursive logic of `gemini_cli`** and wrapping it in the **Strongly-Typed Models of `imp_claude`**.
