# The AI SDLC: Spec-Driven Development and the "Hard" Engineering Ledger

**Date**: March 6, 2026
**Version**: 1.0.0
**Target Audience**: Executives, Architects, and Implementation Teams

---

## 1. The Crisis of "Agentic" Persona Pipelines

The first wave of AI-assisted engineering relied on the "Agentic Pipeline"—a sequence of specialized personas (e.g., "Requirements Agent," "Coding Agent") each with its own local context and prompt. To a novice, this looked like breakthrough automation. To an experienced systems engineer, it looked like **Monolithic Object-Oriented Design**: fragile, tightly coupled, and rigid.

If the technology stack shifted, every agent had to be manually "retrained" via prompting. If a new asset type was needed, a new agent had to be built. The logic was hidden in the prompts, and the process relied entirely on the "cleverness" of the LLM.

**Project Genesis marks the transition from Prompt Engineering to Spec-Driven Development.**

---

## 2. Generic Programming for the SDLC

We have applied the principles of **Alexander Stepanov’s Standard Template Library (STL)** to the entire software development lifecycle. By decoupling the **Algorithm** from the **Data Structure**, we have built a methodology that is domain-blind and scale-invariant.

### The Universal Engine (`iterate`)
In our model, there is only **one operation**: `iterate(Asset, Context, Evaluators)`. This engine doesn't know if it's sorting a list or writing a kernel module. It only knows how to sense a **Delta ($\delta$)** between a current state and a target state (The Spec), and how to produce a new candidate that reduces that delta.

### The Universal Functor (The properly constrained LLM)
In the STL, you pass a predicate or "Functor" to an algorithm to define the logic of comparison. In the AI SDLC, the **LLM is the Universal Functor**. 

Because an LLM can reason over non-numeric data, it acts as a **Generic Predicate** that can evaluate any edge in the graph. By surrounding it with a **Constraint Surface** (REQ Keys, ADRs, and Markov Criteria), we transform it from a "Generative Peer" into a **Mechanical Evaluator**.

---

## 3. The Comparison: Spec-Driven vs. Prompt-Driven

The fundamental shift is that **in Spec-Driven Development, the "development" (coding) is the easiest part.** The complexity has been shifted to the mathematical definition of the problem (The Spec) and the technical architecture (The Design).

| Dimension | Prompt-Driven Development | Spec-Driven Development (AI SDLC) |
| :--- | :--- | :--- |
| **Authority** | **Probabilistic**: The AI's training data determines what is "right." | **Axiomatic**: The **Master Spec** determines legitimacy. The AI is an auditor. |
| **Integrity** | **Hope-based**: You hope the AI wrote the file correctly. | **Transactional**: **Unit of Work** ledger with SHA-256 hashes. |
| **Reliability** | **Generative Peer**: You argue with the AI about its choices. | **Markov Blanket**: You monitor the physical boundary (filesystem). |
| **Recursion** | **Linear**: To build a sub-component, you need another prompt. | **Fractal**: Sub-problems trigger **Spawns**. Scale-invariant. |
| **The "Code"** | **The Hard Part**: You spend 90% of your time fixing bugs. | **The Easy Part**: Code is a commodity. The hard part is the **Spec**. |

---

## 4. Logical Encapsulation and the Markov Blanket

We treat AI-native engineering as a physical process. We wrap the AI's execution in a **Markov Blanket**—a physical boundary monitored by the engine. 

*   **Physical Liveness**: We don't watch "text output." We monitor the **filesystem fingerprint**. If files are being created, the agent is alive.
*   **The Integrity Ledger**: We use a **Write-Ahead Log (WAL)**. Every iteration is a transaction. We record hashes of the project state *before* and *after*. If the `COMPLETE` event isn't in the ledger, the code is "uncommitted" and rejected.

---

## 5. Multi-Tenant Autonomy: The Tournament Pattern

Our approach is **Multi-Tenant by Design**. We build one shared Spec (The WHAT) and allow multiple isolated implementations (`imp_claude`, `imp_gemini`) to build against it (The HOW).

This unlocks the **Tournament Pattern**:
1.  **Parallel Spawn**: The graph triggers two parallel child vectors. One using Claude, one using Gemini.
2.  **Isolated Iteration**: Each agent works inside its own Markov Object (archive).
3.  **Arbitration**: A human or agent reviews the parallel results and selects the winner (or a merge).
4.  **Fold-Back**: The winning code is committed to the primary ledger.

---

## 6. Conclusion: From Tools to Operating Systems

We aren't building a better prompt; we are building an **Operating System for AI-Native Engineering**. 

By formalizing the **Constraint Surface**, we have automated the "Easy" part (Implementation) and hardened the "Hard" part (Disambiguation and Integrity). The engineering task is no longer "writing code"—it is **shaping the Spec** so that the Universal Evaluator can converge the Asset Graph toward a stable, high-quality, and mathematically verifiable product.
