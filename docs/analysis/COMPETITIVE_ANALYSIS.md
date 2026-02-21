# Competitive Analysis: AI SDLC Methodology

## Scope and Framing

This is a **like-for-like comparison of spec-driven methodologies**.  
AI coding assistants and autonomous coding agents are intentionally out of scope here because they are implementation tools, not SDLC methodologies.

Primary framing for this project:

1. **Disambiguation happens at intent/spec/design layers first**.
2. **Code and runtime observability are secondary controls** used to unblock, validate, and feed improvements.
3. The method is evaluated by how well it preserves spec intent through implementation and verification.

## Competitive Matrix (Spec-Driven Methodologies)

| Criterion | AI SDLC Methodology (This Project) | Specification by Example / BDD-ATDD | Contract-First API Development (OpenAPI/AsyncAPI) | Model-Driven Engineering (MDA/EMF) | Formal Methods (TLA+/Alloy/Event-B) | MBSE / V-Model (SysML-centered) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Primary disambiguation layer** | **High (Spec+Design).** Explicit WHAT/HOW separation and edge-level disambiguation. | **Medium.** Behavioral examples clarify intent, but architecture-level ambiguity often remains. | **Medium-High.** Contracts disambiguate interfaces strongly; domain/process semantics can still leak. | **High.** Model abstraction forces up-front clarification. | **Very High.** Formal semantics remove ambiguity where modeled. | **High.** Strong up-front systems decomposition and requirement allocation. |
| **2. Spec-to-implementation traceability** | **High.** Designed as deterministic lineage across artifacts. | **Medium.** Good scenario-to-test traceability; weaker design/code lineage unless disciplined. | **Medium-High.** Excellent endpoint/schema lineage; weaker non-API system behavior lineage. | **High.** Strong model-to-generated-artifact traceability. | **Medium.** Strong proof/model traceability; implementation linkage depends on process/tooling. | **High.** Traditionally strong requirement-to-verification traceability. |
| **3. Quality gates as methodology primitive** | **High.** Evaluators are mandatory, not optional. | **Medium.** Commonly enforced by team culture and CI policy. | **Medium.** Contract linting/testing exists, but enforcement is usually external policy. | **High.** Model constraints and transformations act as strong gates. | **Very High.** Proof obligations and model checks are explicit gates. | **High.** Verification gates are explicit in lifecycle phases. |
| **4. Runtime/code observability role** | **Secondary by design.** Used to detect deviation and unblock, not to define intent. | **Secondary.** Primarily validates implemented behavior post-hoc. | **Secondary.** Runtime checks verify contract conformance. | **Secondary.** Often integrated later than modeling/design stages. | **Secondary.** Runtime observation validates assumptions but is not the semantic source of truth. | **Secondary.** Strong in validation phases, less central in early specification semantics. |
| **5. Adaptability to evolving requirements** | **High.** Spec evolution is first-class with explicit artifact propagation. | **Medium-High.** Scenario evolution is easy; systemic changes can become expensive. | **Medium.** Contract changes are clear but can create high coordination churn. | **Medium-Low.** Powerful but can be rigid/heavy under rapid change. | **Low-Medium.** High rigor can increase change cost unless scope is constrained. | **Medium-Low.** Process rigor supports control but can slow adaptation. |
| **6. Enterprise audit/compliance fit** | **High.** Method-level auditability is a core design goal. | **Medium.** Evidence is available but usually fragmented across tools. | **Medium-High.** Strong API evidence trail where APIs are central. | **High.** Formal artifacts and transformations are compliance-friendly. | **High.** Strong assurance arguments where formal scope is relevant. | **High.** Longstanding fit in regulated and safety-critical domains. |
| **7. Adoption friction / skill burden** | **Medium.** Requires teams to operate with spec/design discipline and explicit evaluators. | **Low-Medium.** Widely adoptable incrementally. | **Medium.** Good for API-centric orgs; less complete outside integration boundaries. | **High.** Specialized modeling skills and tooling investment. | **High.** Significant formal methods expertise required. | **High.** Process and tooling overhead can be substantial. |
| **8. AI-native integration** | **High.** AI is embedded in the method, bounded by spec/evaluator constraints. | **Low-Medium.** AI can help write scenarios/tests, but is external to method semantics. | **Medium.** AI can generate/validate contracts, but governance is contract-centric. | **Low-Medium.** AI can assist modeling, but methodology predates AI-native operation. | **Low-Medium.** AI can help with specs/proofs, but trust boundary remains strict. | **Low-Medium.** AI can assist artifact production; process is not AI-native by default. |

## Positioning Conclusions

1. This project should be positioned against **spec-driven methodologies**, not coding-agent products.
2. The core differentiation is **spec/design-layer disambiguation as the primary control surface**.
3. Observability is important but should be described as **secondary diagnostic and validation control**, not the primary source of intent.
4. Relative to peer methodologies, the strongest claim is the combination of:
   - formal spec-first control,
   - mandatory evaluator gates,
   - and practical AI-native execution within those constraints.

## References

1. Cucumber Docs (BDD): https://cucumber.io/docs  
2. OpenAPI Initiative: https://www.openapis.org/what-is-openapi  
3. OpenAPI Specification: https://spec.openapis.org/oas/latest.html  
4. AsyncAPI Docs: https://www.asyncapi.com/docs  
5. OMG Model Driven Architecture (MDA): https://www.omg.org/mda/  
6. Eclipse Modeling Framework (EMF): https://eclipse.dev/modeling/emf/  
7. TLA+ tools repository: https://github.com/tlaplus/tlaplus  
8. Alloy language/tools: https://alloytools.org/  
9. Event-B and Rodin platform: https://www.event-b.org/  
10. OMG SysML specification portal: https://www.omg.org/spec/SysML  
