
``` mermaid
flowchart TD

    %% --- 1. Bootstrap from Real World to Intent ---
    subgraph BOOTSTRAP["Bootstrap: Real World → Intent"]
        RW["Real World"]
        P["Person / Domain Expert"]
        MM["Mental Model"]
        IM["Intent Manager"]

        RW -->|"Observes problem / event"| P
        P -->|"Updates understanding"| MM
        MM -->|"Mismatch: desired vs actual"| IM
    end

    %% --- 2. Intent Categorisation ---
    subgraph INTENTS["Intent Categories"]
        IC{"Classify Intent"}
        IM --> IC
        IC -->|"Builder Intent"| B_BUILDER["Builder Workflow"]
        IC -->|"Discovery Intent"| B_DISC["Discovery Workflow"]
        IC -->|"Feedback Intent"| B_FEED["Remediation Workflow"]
    end

    %% --- 3. Builder Workflow Detail (Expanded AI SDLC) ---
    subgraph BUILDER["Builder Stage (AI SDLC)"]

        %% High-level Builder node driven by all intent types
        B_ENTRY["Builder (AI SDLC + Agent LLM)"]

        B_BUILDER --> B_ENTRY
        B_DISC --> B_ENTRY
        B_FEED --> B_ENTRY

        %% AI SDLC internal pipeline
        REQ["Requirements"]
        DES["Design"]
        TASKS["Tasks / Work Items"]
        CODE["Code"]
        ST["System Test"]
        UAT["User Acceptance Test"]

        %% Main build flow
        B_ENTRY --> REQ
        REQ --> DES
        DES --> TASKS
        TASKS --> CODE
        CODE --> ST

        %% UAT is driven by Requirements but validates built behaviour
        REQ --> UAT
        ST --> UAT

        %% Output to Deployer
        UAT -->|"Approved, versioned assets"| D["Deployer"]
    end

    %% --- 4. Deploy + Execute ---
    subgraph RUNTIME["Deploy & Execute"]
        EX["Executor (Runtime System)"]
        DD[("Domain Data")]
        D -->|"Release / promote"| EX
        EX -->|"Execute on data"| DD
    end

    %% --- 5. Observer / Evaluator Loop ---
    subgraph GOVERN["Governance Loop"]
        OB["Observer"]
        EV["Evaluator (Homeostasis Model)"]
        EX -->|"Metrics / logs / lineage"| OB
        OB -->|"Observations"| EV
        EV -->|"Deviation detected / new insight"| IM
    end

    %% --- 6. Continuous Improvement ---
    EV -.->|"Feeds new Intent"| IM
    IM -.->|"Continuous AI SDLC loop"| IC
```

``` mermaid
flowchart TD

    %% --- 1. Bootstrap from Real World to Intent ---
    subgraph BOOTSTRAP["Bootstrap: Real World → Intent"]
        RW["Real World"]
        P["Person / Domain Expert"]
        MM["Mental Model"]
        IM["Intent Manager"]

        RW -->|"Observes problem / opportunity / risk"| P
        P -->|"Updates understanding"| MM
        MM -->|"Mismatch: desired vs actual"| IM
    end

    %% --- 2. Intent Categorisation -> CRUD ---
    subgraph INTENTS["Intent → Work Type (CRUD)"]
        IC{"Classify Intent\n(Work Type)"}
        IM --> IC

        IC -->|"New capability"| OP_CREATE["Create"]
        IC -->|"Improve / change behaviour"| OP_UPDATE["Update"]
        IC -->|"Bug / incident / breach"| OP_REMEDIATE["Update (Remediation)"]
        IC -->|"Analysis / discovery"| OP_READ["Read / Analyse"]
        IC -->|"Decommission / retire"| OP_DELETE["Delete / Retire"]
    end

    %% --- 3. Builder.CRUD (AI SDLC) ---
    subgraph BUILDER["Builder.CRUD (AI SDLC)"]

        B_ENTRY["Builder (AI SDLC + Agent LLM)"]

        %% All work types feed one Builder engine with op type metadata
        OP_CREATE --> B_ENTRY
        OP_UPDATE --> B_ENTRY
        OP_REMEDIATE --> B_ENTRY
        OP_READ --> B_ENTRY
        OP_DELETE --> B_ENTRY

        %% Internal SDLC pipeline
        REQ["Requirements\n(incl. risk / SLA / control context)"]
        DES["Design"]
        TASKS["Tasks / Work Items"]
        CODE["Code / Config Change"]
        ST["System Test"]
        UAT["User Acceptance Test"]

        B_ENTRY --> REQ
        REQ --> DES
        DES --> TASKS
        TASKS --> CODE
        CODE --> ST
        REQ --> UAT
        ST --> UAT

        %% Specialisation: remediation still goes through same pipeline,
        %% but with stricter policies baked into REQ / TEST
        OP_REMEDIATE -. "Risk-driven constraints,\nregression focus" .-> REQ

        %% Output to Deployer
        UAT -->|"Approved, versioned assets"| D["Deployer"]
    end

    %% --- 4. Deploy + Execute ---
    subgraph RUNTIME["Deploy & Execute"]
        EX["Executor (Runtime System)"]
        DD[("Domain Data")]
        D -->|"Release / promote"| EX
        EX -->|"Execute on data / traffic"| DD
    end

    %% --- 5. Observer / Evaluator Loop ---
    subgraph GOVERN["Governance Loop"]
        OB["Observer"]
        EV["Evaluator (Homeostasis Model)"]
        EX -->|"Metrics / logs / lineage"| OB
        OB -->|"Observations"| EV
        EV -->|"Deviation detected / new insight"| IM
    end

    %% --- 6. Continuous Improvement ---
    EV -.->|"Feeds new Intent"| IM
    IM -.->|"Continuous AI SDLC loop"| IC
```

AI SDLC

``` mermaid
flowchart TD

    %% 1. Intent & Requirements (capture all intent)
    subgraph REQ_STAGE["Requirements – Intent Capture"]
        IM["Intent Manager
(collects all intent)"]
        REQ["Requirements
Personas: Product Owner, Business Analyst
Assets: Req spec, user stories, NFRs"]
        IM -->|"Intent (problems, goals, risks)"| REQ
    end

    %% 2. Design stage with Tech Lead using architecture + data architecture contexts
    subgraph DESIGN_STAGE["Design – Solution & Data Design (Tech Lead)"]
        DES["Design
Persona: Tech Lead
Assets: Solution design, integration patterns, data design"]
        
        ARCH_CTX["Architecture Context
(tech stack, platforms, standards, patterns)"]

        DATA_CTX["Data Architecture Context
(models, schemas, contracts, lineage, retention, privacy)"]

        REQ -->|"Refined requirements"| DES

        ARCH_CTX -->|"Guide solution architecture"| DES
        DATA_CTX -->|"Guide data modelling & flows"| DES

        DES -->|"Iterate / refine design"| DES
    end

    %% 3. Tasks / Work breakdown
    subgraph TASK_STAGE["Tasks – Work Breakdown"]
        TASKS["Tasks / Backlog
Personas: PO, Tech Lead
Assets: Epics, stories, tickets"]
        DES -->|"Create work items (app + data + infra)"| TASKS
        TASKS -->|"Re-scope / re-prioritise"| TASKS
    end

    %% 4. Code stage with coding standards
    subgraph CODE_STAGE["Code – Implementation"]
        CODE["Code / Config
Persona: Coder
Assets: Source code, configs, pipelines, models"]
        STANDARDS["Coding & Data Standards
(style, security, modelling, naming)"]
        TASKS -->|"Implement solution & data assets"| CODE
        STANDARDS -->|"Guide implementation"| CODE
        CODE -->|"Refactor / improve"| CODE
    end

    %% 5. System Test stage
    subgraph STAGE_TEST["System Test – Verification"]
        ST["System Test
Persona: System Tester
Assets: Functional tests, integration tests, data quality tests"]
        CODE -->|"Build for testing"| ST
        ST -->|"Add/adjust tests"| ST
    end

    %% 6. UAT stage
    subgraph STAGE_UAT["UAT – Validation"]
        UAT["User Acceptance Test
Persona: UAT Tester / Business SME
Assets: UAT scripts, sign-off, issues"]
        REQ -->|"Acceptance criteria (business + data)"| UAT
        ST -->|"Tested build + test results"| UAT
        UAT -->|"UAT cycles / re-tests"| UAT
    end

    %% 7. Feedback loops back to Requirements (gap detection)
    DES -.->|"Functional, NFR or data gaps"| REQ
    TASKS -.->|"Scope / feasibility issues"| REQ
    CODE -.->|"Implementation constraints / discoveries"| REQ
    ST -.->|"Defects, missing scenarios, data issues"| REQ
    UAT -.->|"Business mismatch, new needs"| REQ

    %% 8. Handover of approved assets
    UAT -->|"Approved, versioned assets"| D["Deployer / Release Mgmt"]

    %% 9. Optional: Link back into runtime & observer (external loop)
    D -->|"Release to runtime"| EX["Executor / Runtime System"]
    EX -->|"Behaviour, metrics, incidents"| IM

```