# INVESTIGATION: CrewAI as a Future Genesis Design Tenant

**Date**: 2026-03-13T10:45:00Z
**Type**: INVESTIGATION
**Priority**: Low — post-MVP, post-v3.0 stabilisation
**Traces To**: INT-AISDLC-001
**Status**: Parked — not blocking anything

---

## Observation

The agent dispatch pattern at the heart of Genesis — spawn actor → write result → read
result → continue — is structurally similar to what CrewAI, AutoGen, and Temporal
provide out of the box. A CrewAI design tenant (`imp_crewai/`) would implement the same
Asset Graph Model using CrewAI's task/agent primitives instead of the current
Claude-MCP fold-back protocol.

## What CrewAI Would Give For Free

- **Agent dispatch**: CrewAI Task + Agent definitions replace the fp_intent/fp_result
  manifest pair (ADR-023/024). Spawn is a first-class primitive.
- **Human-in-the-loop**: AutoGen's `HumanProxyAgent` maps directly to F_H gate
  handling — including the proxy pattern (REQ-F-PROXY-001).
- **Retry and error handling**: built-in; replaces the stuck-delta detection loop.
- **Tool integrations**: filesystem, web search, code execution — maintained by the
  community, not custom code.
- **Memory and context**: vector store integration for large context windows across
  long-running SDLC runs.

## What Would Still Need to Be Built

| Genesis concept | CrewAI equivalent | Gap |
|----------------|-------------------|-----|
| Append-only event stream | None native — would need a sidecar (Redis stream, SQLite append log) | Medium |
| `delta(state, constraints)` convergence | Task "done" signal is agent-defined — convergence criteria would need custom evaluator tools | High |
| Graph topology constraint (admissible transitions) | CrewAI flow / conditional routing — expressible but not formally enforced | Medium |
| REQ key traceability threading | Purely a convention — no framework enforcement | Low (discipline, not tooling) |
| Event sourcing + projection | Would need custom projection layer on top of the event sidecar | High |

## Architecture Sketch

```
imp_crewai/
  design/
    CREWAI_GENESIS_DESIGN.md
    adrs/
      ADR-CRW-001-event-sidecar.md         # how to replicate append-only stream
      ADR-CRW-002-convergence-as-tool.md   # delta evaluator as CrewAI tool
      ADR-CRW-003-graph-as-crew-flow.md    # graph topology → CrewAI conditional flow
  code/
    crews/
      requirements_crew.py    # intent→requirements as CrewAI crew
      design_crew.py          # requirements→design
      code_crew.py            # design→code↔unit_tests (TDD crew)
    tools/
      delta_evaluator.py      # F_D deterministic checks as CrewAI tools
      event_log.py            # append-only event sidecar
      proxy_reviewer.py       # F_H proxy as HumanProxyAgent
    config/
      graph_topology.yml      # same topology, different executor
```

## Why This Is Worth Investigating

1. **Maintenance**: CrewAI/AutoGen community absorbs framework maintenance. The
   current Claude fold-back protocol (ADR-023/024) is bespoke and Genesis-maintained.

2. **Ecosystem**: Tool integrations, memory backends, observability tooling — all
   maintained by a large community rather than built from scratch.

3. **Validation**: If the formal system (4 primitives, gradient, convergence) is truly
   framework-agnostic, a CrewAI tenant should be implementable without changing the
   spec. This would prove the spec/design separation holds.

4. **Multi-agent patterns**: CrewAI's sequential/hierarchical/consensual process modes
   map reasonably well to Genesis profiles (standard → sequential, full → hierarchical).

## Why It's Parked

- Genesis's event stream substrate (ADR-S-012) is load-bearing for replay, auditability,
  and projection equivalence. Replicating this with a CrewAI sidecar is non-trivial and
  risks drift between the sidecar and the formal model.
- The self-applying property (Genesis builds itself with Genesis) would not transfer to
  a CrewAI tenant without significant adaptation of the command layer.
- Current priority: stabilise v3.0, deliver genesis_manager. CrewAI investigation is
  post-stabilisation.

## Next Step (when ready)

Spawn a spike vector:
  `/gen-spawn --type spike --parent INT-AISDLC-001 --reason "Is CrewAI a viable design tenant for the Genesis Asset Graph Model? What is the minimum delta between CrewAI primitives and Genesis's formal system?" --duration "2 weeks"`

The spike answer determines whether to open `imp_crewai/` as a full peer tenant or
document CrewAI as an inspiration/reference only.
