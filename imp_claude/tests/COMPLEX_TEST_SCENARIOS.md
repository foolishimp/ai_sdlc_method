# Complex Test Scenarios — Cost-Benefit Boundary Analysis

**File**: `test_functor_complex.py` (23 tests, ~17s, no LLM calls)
**Validates**: REQ-ITER-003, REQ-EVAL-002, REQ-SENSE-001, REQ-SUPV-003

---

## Test Map — Scenarios vs Graph Edges

```mermaid
graph LR
    subgraph "Standard Profile (4 edges)"
        IR["intent→requirements"]
        RD["requirements→design"]
        DC["design→code"]
        TDD["code↔unit_tests"]
        IR --> RD --> DC --> TDD
    end

    subgraph "Scenario Coverage"
        A["A: Agent-Dominated<br/>3 tests"]
        B["B: Multi-Edge<br/>4 tests"]
        C["C: Profile-Param<br/>5 tests"]
        D["D: η Chain<br/>4 tests"]
        E["E: Multi-Feature<br/>3 tests"]
        F["F: Cost Model<br/>4 tests"]
    end

    A -. "worst-case<br/>engine cost" .-> IR
    B -. "traversal<br/>+ stop" .-> IR
    B -. "traversal" .-> RD
    C -. "hotfix skips" .-x RD
    C -. "spike stops" .-x TDD
    D -. "η_D→P" .-> TDD
    D -. "η_P→H" .-> IR
    E -. "shared workspace" .-> TDD
    F -. "all edges" .-> IR
    F -. "all edges" .-> RD
    F -. "all edges" .-> DC
    F -. "all edges" .-> TDD

    style A fill:#f96,stroke:#333
    style B fill:#69f,stroke:#333
    style C fill:#9c6,stroke:#333
    style D fill:#f6c,stroke:#333
    style E fill:#cc9,stroke:#333
    style F fill:#6cf,stroke:#333
```

---

## Check Type Distribution Per Edge

```mermaid
%%{init: {'theme': 'default'}}%%
graph TB
    subgraph "intent→requirements (14 checks)"
        IR_A["12 Agent"]
        IR_H["2 Human"]
        IR_D["0 Deterministic"]
    end

    subgraph "requirements→design (15 checks)"
        RD_A["14 Agent"]
        RD_H["1 Human"]
        RD_D["0 Deterministic"]
    end

    subgraph "design→code (8 checks)"
        DC_A["3 Agent"]
        DC_D["5 Deterministic"]
    end

    subgraph "code↔unit_tests (15 checks)"
        TDD_A["7 Agent"]
        TDD_D["8 Deterministic"]
    end

    style IR_A fill:#f96
    style IR_H fill:#ff9
    style IR_D fill:#9f9
    style RD_A fill:#f96
    style RD_H fill:#ff9
    style RD_D fill:#9f9
    style DC_A fill:#f96
    style DC_D fill:#9f9
    style TDD_A fill:#f96
    style TDD_D fill:#9f9
```

**Legend**: Red = Agent (engine: 1 `claude -p` call each), Yellow = Human (SKIP), Green = Deterministic (free)

---

## Scenario A: Agent-Dominated Edge

Tests the worst-case engine cost — `intent→requirements` has 0 deterministic checks.

```mermaid
flowchart TD
    A1["A1: check distribution<br/>Assert: 12 agent, 2 human, 0 det"]
    A2["A2: engine iterate_edge<br/>All agent → ERROR/SKIP<br/>All human → SKIP<br/>0 det passes"]
    A3["A3: cost ratio comparison<br/>intent→req: det:agent = 0:12<br/>code↔tests: det:agent > 0.5"]

    A1 --> A2 --> A3

    subgraph "Key Finding"
        K["Engine makes 12 cold-start<br/>claude -p calls on this edge<br/>vs 1 session in E2E model"]
    end

    A3 --> K

    style K fill:#fee,stroke:#c33
```

---

## Scenario B: Multi-Edge Traversal

Tests `run()` walking edges in sequence, stopping at first non-convergence.

```mermaid
flowchart LR
    subgraph "engine.run(feature_type='feature')"
        E1["intent→req<br/>(agent ERRORs)"]
        E2["req→design<br/>(not reached)"]
        E3["design→code<br/>(not reached)"]
        E4["code↔tests<br/>(not reached)"]
    end

    E1 -->|"converged=False<br/>STOP"| HALT["run() returns"]
    E1 -.->|"if converged"| E2 -.-> E3 -.-> E4

    subgraph "Tests"
        B1["B1: traverses ≥1 edge"]
        B2["B2: stops on non-convergence"]
        B3["B3: emits events per edge"]
        B4["B4: trajectory accumulates"]
    end

    style HALT fill:#fcc,stroke:#c33
    style E2 fill:#ddd,stroke:#999
    style E3 fill:#ddd,stroke:#999
    style E4 fill:#ddd,stroke:#999
```

---

## Scenario C: Profile-Parameterized Runs

Different profiles produce different graph subsets.

```mermaid
flowchart TD
    subgraph "Standard (4 edges)"
        S1["intent→req"] --> S2["req→design"] --> S3["design→code"] --> S4["code↔tests"]
    end

    subgraph "Hotfix (3 edges)"
        H1["intent→req"] --> H3["design→code"] --> H4["code↔tests"]
    end

    subgraph "Spike (3 edges)"
        SP1["intent→req"] --> SP2["req→design"] --> SP3["design→code"]
    end

    subgraph "Minimal (2 edges)"
        M1["intent→req"] --> M3["design→code"]
    end

    subgraph "Tests"
        C1["C1: hotfix skips req→design"]
        C2["C2: hotfix < standard checks"]
        C3["C3: TDD det > human"]
        C4["C4: spike excludes code↔tests"]
        C5["C5: minimal = fewest edges"]
    end

    style S2 fill:#fcc,stroke:#c33
    style S4 fill:#fcc,stroke:#c33
    style SP3 fill:#fcc,stroke:#c33
```

---

## Scenario D: η Escalation Chain

Tests natural transformation escalation: F_D fails → η_D→P, agent fails → η_P→H.

```mermaid
flowchart TD
    subgraph "Iteration 1"
        DET1["Deterministic check<br/>tests_pass → FAIL"] -->|"η_D→P"| ESC1["Escalation:<br/>η_D→P: tests_pass"]
        AGT1["Agent check<br/>→ ERROR (no CLI)"] -->|"η_P→H"| ESC2["Escalation:<br/>η_P→H: code_quality"]
    end

    subgraph "Iteration 2"
        DET2["tests_pass → FAIL<br/>(bug still there)"] -->|"η_D→P"| ESC3["Escalation"]
    end

    subgraph "Iteration 3"
        DET3["tests_pass → FAIL<br/>(budget exhausted)"] -->|"η_D→P"| ESC4["Escalation"]
    end

    ESC1 --> DET2
    ESC3 --> DET3

    subgraph "Invariants"
        D1["D1: det failure → η_D→P"]
        D2["D2: agent error → η_P→H"]
        D3["D3: every iteration has escalations"]
        D4["D4: len(escalations) == delta"]
    end

    style ESC1 fill:#f96
    style ESC2 fill:#f6c
    style ESC3 fill:#f96
    style ESC4 fill:#f96
```

---

## Scenario E: Multi-Feature Workspace

Tests two features sharing one workspace without cross-contamination.

```mermaid
flowchart LR
    subgraph "Shared Workspace"
        EL["events.jsonl"]
    end

    subgraph "FEAT-001 (stalled)"
        F1_1["iter 1: δ=2"]
        F1_2["iter 2: δ=2"]
        F1_3["iter 3: δ=2"]
        F1_4["iter 4: δ=2"]
    end

    subgraph "FEAT-002 (converging)"
        F2_1["iter 1: δ=3"]
        F2_2["iter 2: δ=1"]
        F2_3["iter 3: δ=0 ✓"]
    end

    F1_1 --> EL
    F1_2 --> EL
    F1_3 --> EL
    F1_4 --> EL
    F2_1 --> EL
    F2_2 --> EL
    F2_3 --> EL

    EL --> SENSE["sense_feature_stall()"]
    SENSE -->|"FEAT-001"| STALL["breached=True"]
    SENSE -->|"FEAT-002"| OK["breached=False"]

    style STALL fill:#fcc,stroke:#c33
    style OK fill:#cfc,stroke:#3c3
```

---

## Scenario F: Cost Model Validation

Pure data tests — no engine calls. Validates the numbers in FRAMEWORK_COMPARISON_ANALYSIS.md.

```mermaid
graph TD
    subgraph "Standard Profile — 52 total checks"
        F_IR["intent→req: 14<br/>(12A + 2H + 0D)"]
        F_RD["req→design: 15<br/>(14A + 1H + 0D)"]
        F_DC["design→code: 8<br/>(3A + 0H + 5D)"]
        F_TDD["code↔tests: 15<br/>(7A + 0H + 8D)"]
    end

    subgraph "Engine Cost Model"
        AGENT["Total agent checks = claude -p calls<br/>≥36 per standard run"]
        DET["Total deterministic = free<br/>≥13 per standard run"]
        HUMAN["Total human = SKIP<br/>≥3 per standard run"]
    end

    F_IR --> AGENT
    F_RD --> AGENT
    F_DC --> DET
    F_TDD --> DET

    subgraph "Tests"
        F1["F1: standard total ≥40"]
        F2["F2: hotfix < standard"]
        F3["F3: TDD highest det:agent"]
        F4["F4: agent counts per edge"]
    end

    style AGENT fill:#f96,stroke:#333
    style DET fill:#9f9,stroke:#333
    style HUMAN fill:#ff9,stroke:#333
```

---

## Coverage Matrix

| Gap (from plan) | Scenario | Tests | Status |
|-----------------|----------|-------|--------|
| Non-TDD edges through engine | A, B | A2, B1-B4 | Covered |
| Agent-dominated edge cost | A, F | A1-A3, F3-F4 | Covered |
| Multi-edge traversal with real eval | B | B1-B4 | Covered |
| Profile-parameterized runs | C | C1-C5 | Covered |
| Det-dominant vs agent-dominant crossover | F | F2-F3 | Covered |
| Multi-feature workspace | E | E1-E3 | Covered |
| η chain across iterations | D | D1-D4 | Covered |

---

## Running the Tests

```bash
# New tests only
pytest imp_claude/tests/test_functor_complex.py -v

# By scenario
pytest imp_claude/tests/test_functor_complex.py::TestCostModel -v
pytest imp_claude/tests/test_functor_complex.py::TestAgentDominatedEdge -v
pytest imp_claude/tests/test_functor_complex.py::TestMultiEdgeTraversal -v
pytest imp_claude/tests/test_functor_complex.py::TestProfileParameterized -v
pytest imp_claude/tests/test_functor_complex.py::TestEtaEscalationChain -v
pytest imp_claude/tests/test_functor_complex.py::TestMultiFeatureWorkspace -v

# Full regression (excluding E2E headless)
pytest imp_claude/tests/ --ignore=imp_claude/tests/e2e -v
```
