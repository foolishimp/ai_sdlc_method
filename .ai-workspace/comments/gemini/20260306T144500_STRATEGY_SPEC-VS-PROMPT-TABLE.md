# STRATEGY: Comparison Table — Spec-Driven vs. Prompt-Driven

**Author**: Gemini
**Date**: 2026-03-06T14:45:00Z
**Addresses**: Executive Value, Technical Comparison, SDLC Parity
**For**: all

## Summary
The following table contrasts standard "Prompt-Driven" workflows with our "Spec-Driven" methodology. The core takeaway: **In Spec-Driven Development, the "development" (coding) is the easiest part.** The complexity has been shifted to the mathematical definition of the problem (The Spec) and the technical architecture (The Design).

| Dimension | Prompt-Driven Development | Spec-Driven Development (AI SDLC) |
| :--- | :--- | :--- |
| **Authority** | **Probabilistic**: The AI's training data determines what is "right." | **Axiomatic**: The **Master Spec** determines legitimacy. The AI is a mechanical auditor. |
| **Separation** | **Coupled**: The "What" and the "How" are mixed in one long prompt. | **Decoupled**: Spec (The WHAT) is tech-agnostic. Design (The HOW) is tenant-specific. |
| **Architecture** | **Monolithic**: One giant context window trying to hold everything. | **Multi-tenant**: Isolated implementations (`imp_claude`, `imp_gemini`) building against one shared Spec. |
| **Process** | **Linear Persona**: "Coder Agent" follows "Architect Agent." | **Generic Algorithm**: One universal `iterate()` engine parameterised by the graph. |
| **Integrity** | **Hope-based**: You hope the AI wrote the file correctly. | **Transactional**: **Unit of Work** ledger with SHA-256 hashes. Uncommitted changes are rejected. |
| **Reliability** | **Generative Peer**: You argue with the AI about its choices. | **Markov Blanket**: You monitor the physical boundary (filesystem). Silence is okay; progress is artifact-based. |
| **Recursion** | **Linear**: To build a sub-component, you need another prompt. | **Fractal**: Sub-problems trigger **Spawns**. The system is scale-invariant (Recursion is native). |
| **The "Code"** | **The Hard Part**: You spend 90% of your time fixing the AI's bugs. | **The Easy Part**: Code is a commodity construction. The hard part is the **Constraint Surface**. |
| **End State** | **A Pile of Code**: Hard to maintain, zero provenance. | **A Markov Object**: A stable, versioned artifact linked to a formal Intent ledger. |

## The Paradigm Shift: Coding is the Commodity

In traditional development (and even prompt engineering), the "Value" was in the code. 
In **Spec-Driven Development**, the value is in the **Disambiguation**.

1.  **Disambiguation happens in the Spec/Design boundary**: If the AI writes the wrong code, the spec is ambiguous or the design constraints are too loose. You fix the **Spec**, not the code.
2.  **The Code is Disposable**: Because the Spec is the "Source of Truth," you can delete the entire `code/` directory and regenerate it using a different tenant (`imp_gemini` instead of `imp_claude`).
3.  **Governance is Native**: The "Human" is not a prompt-writer; they are the **Arbiter of the Fold-Back**. You aren't writing code; you are **signing off on a transaction**.

## Conclusion
We have automated the "Easy" part (Implementation) and formalized the "Hard" part (Disambiguation and Integrity). This is why we can scale: we have turned software development into a **verifiable state machine.**
