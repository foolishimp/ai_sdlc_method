# On-Demand Data Architecture

## Event-Driven Systems, Domain Modeling, and Systematic Modernization

*A comprehensive framework for building composable, evolvable enterprise data systems*

---

# Slide 1: The Challenge

## Information Systems Lag Reality

```mermaid
flowchart TB
    subgraph Reality["Reality (The Business)"]
        R1["Traders buy and sell"]
        R2["Deals are made"]
        R3["Money changes hands"]
        R4["Companies shift ownership"]
    end

    subgraph Model["Business Domain Model"]
        M1["Conceptual<br/>Abstraction"]
        M2["Scoped to<br/>reasonable complexity"]
    end

    subgraph Systems["Information Systems"]
        S1["Encode snapshots<br/>of processes"]
        S2["Rigid and slow<br/>to change"]
        S3["Lag the changing<br/>business landscape"]
    end

    Reality -->|"Business reduces<br/>complexity"| Model
    Model -->|"Development teams<br/>build"| Systems

    style Systems fill:#ffccbc
```

**The problem**: Systems traditionally are rigid, slow to change, slow to extend - generally lagging the changing business landscape reflected by reality.

---

# Slide 2: The Domain Landscape

## From Reality to Systems

```mermaid
flowchart TB
    REALITY["Reality<br/>(In the real world things happen)"]

    BA["Business Domain Model<br/>(Conceptual Abstraction)"]

    TEAMS["Development Teams"]

    SYSTEMS["Information Systems<br/>(Encode snapshot of processes)"]

    REALITY -->|"Business reduces<br/>complexity to what's relevant"| BA
    BA -->|"Scope domain model<br/>to reasonable area"| TEAMS
    TEAMS --> SYSTEMS

    style SYSTEMS fill:#bbdefb
```

**Key insight**: The broader the domain model, the more abstract it needs to be. We don't try to model the entire business end-to-end in a single domain.

---

# Slide 3: Bounded Contexts

## Managing Complexity Through Separation

```mermaid
flowchart TB
    subgraph CGM["CGM Context"]
        CGM_DEAL["Deal"]
        CGM_TRADE["Trade"]
        CGM_CONTRACT["Contract"]
        CGM_DEAL --- CGM_TRADE
        CGM_DEAL --- CGM_CONTRACT
    end

    subgraph MacCap["MacCap Context"]
        MAC_DEAL["Deal"]
        MAC_TRADE["Trade"]
        MAC_CONTRACT["Contract"]
        MAC_DEAL --- MAC_TRADE
        MAC_DEAL --- MAC_CONTRACT
    end

    subgraph RMG["RMG Context"]
        RMG_DEAL["Deal"]
        RMG_TRADE["Trade"]
        RMG_CONTRACT["Contract"]
        RMG_DEAL --- RMG_CONTRACT
        RMG_CONTRACT --- RMG_TRADE
    end

    CGM <-->|"Mapping between<br/>bounded contexts"| MacCap
    MacCap <-->|"Mapping"| RMG

    style CGM fill:#ef9a9a
    style MacCap fill:#a5d6a7
    style RMG fill:#fff59d
```

**Bounded Context principle**:
- An organization is complex
- Single model = excessively challenging, costly, hard to maintain
- Separate into areas with **consistent language, operations, and data model**
- Each context may use the same term but with subtly different definitions

---

# Slide 4: Corporate Anti-Patterns

## What We're Fighting Against

| Anti-Pattern | Description |
|--------------|-------------|
| **Monolithic Big Ball of Mud** | Everything coupled together, no clear boundaries |
| **File Transfers** | Custom point-to-point integrations |
| **Manual Processes** | Humans bridging gaps in integrations |
| **Output-Only Focus** | Ignoring the transform, focusing only on output data |
| **Attribute-Level Thinking** | Dealing with data at attribute level instead of Entity level |

```mermaid
flowchart LR
    subgraph AntiPatterns["Anti-Patterns"]
        MUD["Big Ball<br/>of Mud"]
        FILES["File<br/>Transfers"]
        MANUAL["Manual<br/>Processes"]
    end

    subgraph Target["Target State"]
        DOMAIN["Domain<br/>Services"]
        EVENTS["Event<br/>Streams"]
        AUTO["Automated<br/>Pipelines"]
    end

    AntiPatterns -->|"Refactor to"| Target

    style AntiPatterns fill:#ffccbc
    style Target fill:#c8e6c9
```

---

# Slide 5: Event-Driven Architecture

## Systems Composable Through Events

```mermaid
flowchart TB
    subgraph Call["API Call"]
        C_ID["Identity"]
        C_CRED["Credential (AuthN,AuthZ)"]
        C_CMD["CMD"]
        C_INPUT["Input"]
    end

    subgraph Function["Containerised Function"]
        subgraph Wrapper["Fn Wrapper"]
            INTERFACE["Interface<br/>• Identity<br/>• CMD<br/>• Input<br/>• Output"]
            FN["Fn( Input ):Output"]
        end
        SIDE["Side Effects"]
    end

    subgraph EventLog["Event Log"]
        EVENT["Event<br/>• Identity<br/>• Interface.Identity<br/>• Call.Identity<br/>• Credential<br/>• CMD<br/>• Input<br/>• Time<br/>• Output"]
    end

    subgraph Consumer["Event Consumer"]
        CONS_FN["Consumer<br/>Function"]
    end

    Call --> Function
    Function -->|"Recovery Event"| EventLog
    Function -->|"End Event"| EventLog
    EventLog -->|"Event Publisher"| Consumer

    style EventLog fill:#fff3e0
```

**Identity structure**:
- GUID
- Credential (AuthN, AuthZ)
- Creation Time UTC

---

# Slide 6: What Does a Good Event Look Like?

## Event Design Principles

**Every event must have**:

1. **Captured and available** to authorized subscribers
2. **Security token** under which it was authorized
3. **Signature of parent event** (lineage)
4. **Adaptive to schema changes** over time

```mermaid
flowchart LR
    subgraph Event["Well-Formed Event"]
        ID["Identity (GUID)"]
        AUTH["Auth Token"]
        PARENT["Parent Event Signature"]
        TIME["Timestamp"]
        PAYLOAD["Payload (Schema-versioned)"]
    end

    SCHEMA["Independent Schema<br/>Registry"] -->|"Verification"| Event
```

**Data pipelines need to be adaptive** to changes in data over time - independent source for schema verification consumed by integration endpoints.

---

# Slide 7: Event Consumer Use Cases

## Four Patterns for Event Consumption

```mermaid
flowchart TB
    PUB["Event<br/>Publisher"]

    subgraph Pattern1["1. Event-Aware Service"]
        P1["Event Consumer &<br/>Business Function<br/>= Same Program"]
    end

    subgraph Pattern2["2. Decoupled Consumer"]
        P2["Business Function Interface<br/>takes Events from Publisher<br/>(as 1 but decoupled)"]
    end

    subgraph Pattern3["3. Adaptor Service"]
        P3["Event Consumer coded to<br/>specific Domain Event →<br/>specific API Mapping"]
    end

    subgraph Pattern4["4. Generic Mapper"]
        P4["Event Consumer is<br/>Generic Config-driven<br/>Mapper from Event to API"]
    end

    PUB --> Pattern1
    PUB --> Pattern2
    PUB --> Pattern3
    PUB --> Pattern4

    Pattern1 --> FN["Containerised<br/>Function"]
    Pattern2 --> FN
    Pattern3 --> FN
    Pattern4 --> FN
```

---

# Slide 8: Use Case - Serverless Application

## Event Flow Through Functions

```mermaid
flowchart LR
    C1["c1<br/>(Cmd)"]
    F1["F1<br/>(Function)"]
    E1["e1<br/>(Event)"]
    LOG["Log<br/>(e1(s1))"]
    STREAM["Stream<br/>(FIFO)"]
    E1B["e1"]
    A1["a1<br/>(Adaptor)"]
    C2["c2<br/>(Cmd)"]
    F2["F2<br/>(Function)"]
    SIDE1["Side<br/>Effects"]
    SIDE2["Side<br/>Effects"]

    C1 --> F1
    F1 --> E1
    F1 --> LOG
    F1 --> SIDE1
    E1 --> STREAM
    STREAM --> E1B
    E1B --> A1
    A1 --> C2
    C2 --> F2
    F2 --> SIDE2

    style STREAM fill:#e0e0e0
```

**Key pattern**:
- `State ++ Event -> Current State`
- Current State refers to the accumulated state from events
- Reliance on ODBC or equivalent for side effects

---

# Slide 9: Event-Driven Scoring Service Example

## Real-World Architecture

```mermaid
flowchart TB
    subgraph APIs["API Layer"]
        CMD["Command API"]
        QUERY["Adhoc Query API"]
    end

    subgraph Service["Scoring Service"]
        UPDATE["API_UpdateScore<br/>(score)"]
        GET["API_GetScore<br/>(ID)"]
        FN_UP["FN_UpdateScore"]
        FN_Q["FN_QueryScore"]
        DB["Database"]
    end

    subgraph Events["Event Infrastructure"]
        STREAM["Event Stream<br/>Topics"]
        S3["AWS S3 Bucket"]
        LOG["Event Log<br/>(Avro.json)"]
    end

    subgraph Analytics["Analytics"]
        SPARK["Apache Spark<br/>Cluster"]
        AWS["AWS"]
    end

    CMD --> UPDATE
    QUERY --> GET
    UPDATE --> FN_UP
    GET --> FN_Q
    FN_UP --> DB
    FN_Q --> DB
    FN_UP --> LOG
    LOG --> S3
    STREAM -->|"AWS Kinesis<br/>OR Kafka"| Analytics

    style Events fill:#fff3e0
```

---

# Slide 10: On-Demand Resource Pipeline (Data Pipes V3)

## Complete Architecture

```mermaid
flowchart TB
    subgraph External["External State"]
        EXT["External<br/>Systems"]
    end

    subgraph Plato["PLATO"]
        SCHEMA["Entity<br/>Schema"]
        OPENAPI["Open API<br/>Gen"]
        TRANSFORM["Transform<br/>Code"]
    end

    subgraph Ingestion["Ingestion Service"]
        ADHOC["Adhoc API<br/>Request<br/>FN Interface"]
        PATH["Path Query<br/>To Query Engine"]
        EVENT["Event<br/>Notification"]
        PUBSUB["Pub/Sub to<br/>External State"]
        DATASET["DATA SET"]
        BULK["Bulk Import<br/>Pipeline"]
    end

    subgraph DomainServices["Generic Domain Services Stack"]
        subgraph API["API"]
            FN1["Fn()"]
            INPUT["Input<br/>Entity 1,2,Id,<br/>3,Id"]
            QUERY["Query<br/>Entity 1"]
            OUTPUT["Output<br/>Entity 1"]
        end
        FN2["Fn()"]
        TRANS_FN["TRANSFORMATION<br/>FUNCTION"]
        TRANS_CODE["Transform<br/>Code"]

        subgraph Entities["Entity Dependencies"]
            E1["Entity 1<br/>ID"]
            E2["Entity 2<br/>ID"]
            E3["Entity 3<br/>ID"]
        end

        subgraph DataAccess["Data Access Layer"]
            CACHE["Looks Like Internal State<br/>(Cache)"]
            CUSTOM["Custom Query<br/>Interpreter"]
            ENTITY_ID["Entity<br/>ID"]
        end

        INTERNAL["Internal State<br/>e.g. DB"]
        INTERP["Query<br/>Interpreter"]
    end

    External --> Ingestion
    Plato --> DomainServices
    Ingestion --> DomainServices

    style DomainServices fill:#e8f5e9
```

---

# Slide 11: On-Demand Function Modules

## Serverless Execution Architecture

```mermaid
flowchart TB
    subgraph Repository["Repository"]
        GRAPH["Graph<br/>Definitions"]
        BUSINESS["Business<br/>Fn Definitions"]
        DATASETS["Dataset<br/>Definitions"]
        ENV["Environment<br/>Definitions"]
    end

    CICD["CI/CD<br/>Pipeline"]

    subgraph Execution["Execution Graph"]
        GRAPHDEF["Graph Definition<br/>Graph Definition<br/>Graph Definition"]
        SAGA["Saga Pattern -<br/>Orchestration of<br/>Business Functions"]
    end

    subgraph Compute["Compute"]
        subgraph Containers["Function Containers"]
            BF1["Business<br/>Functions"]
            BF2["Business<br/>Functions"]
            BF3["Business<br/>Functions"]
        end
    end

    subgraph Storage["Storage"]
        subgraph Managed["Managed Storage"]
            INITIAL["Initial<br/>Data Sets"]
            PERSIST["Persistent<br/>Data Sets"]
            TEMP["Temporary<br/>Data Sets"]
        end
    end

    Repository --> CICD
    CICD --> Execution
    Execution --> Compute
    Compute --> Storage

    style Execution fill:#fff3e0
    style Compute fill:#bbdefb
    style Storage fill:#c8e6c9
```

---

# Slide 12: Spark Invoker Use Case

## Workflow Orchestration

```mermaid
flowchart TB
    RUN["Run"]

    subgraph Workflow["Workflow"]
        WF_VER["Workflow<br/>-version"]
        STEPS["Step Functions<br/>+ Tasks to<br/>Lambdas"]
    end

    subgraph SparkInvoker["SparkInvoker"]
        SPARK["Run Spark Job()"]
        LAMBDA["Lambda"]
        GENERIC["Generic Spark<br/>Invoker"]
        PYTHON["Python"]
    end

    LIVY["Livy<br/>Invoke"]
    REST["REST Call"]
    DYNAMO["Dynamo_db"]
    FNLOG["Fn Run Log"]

    subgraph ExternalRepo["External Repository"]
        FN_DEF["Fn Definitions"]
        GRAPH_DEF["Graph Definitions"]
        INST_CONF["Instance Config<br/>Definitions"]
    end

    RUN -->|"Run ID"| Workflow
    Workflow -->|"Read Task<br/>New TaskID"| SparkInvoker
    SparkInvoker --> LIVY
    SparkInvoker --> REST
    REST --> DYNAMO
    DYNAMO -->|"Instance Config (Fn<br/>Config + Data Def +<br/>Env)"| FNLOG

    style SparkInvoker fill:#bbdefb
```

---

# Slide 13: Fine-Graining Your Functions

## Improving Lineage Through Decomposition

**Problem**: User-defined function does filtering internally, reducing trackable granularity.

```mermaid
flowchart LR
    subgraph Before["Before: Coarse-Grained"]
        IN1["Full<br/>Incoming<br/>data set"]
        FN1["def User_Function( FullSet )<br/>subset = FullSet.filter(pred)<br/>return sum(subset)"]
        OUT1["sum(subset)"]

        IN1 --> FN1 --> OUT1
    end
```

**Lineage Outcome**: ResultSet was generated by User_Function using InputSet (no detail on filter)

```mermaid
flowchart LR
    subgraph After["After: Fine-Grained"]
        IN2["Full<br/>Incoming<br/>data set"]
        FILTER["Operation:<br/>Filter Data(pred)"]
        INTER["subset<br/>(Intermediate)"]
        FN2["def User_Function(subset)<br/>return sum(subset)"]
        OUT2["sum(subset)"]

        IN2 --> FILTER --> INTER --> FN2 --> OUT2
    end
```

**To improve granularity**: The filtering functionality should be a separate function.

---

# Slide 14: Managed Data Sets

## Technology-Agnostic Data Storage

```mermaid
flowchart TB
    subgraph Bucket["Technology Bucket"]
        IMDS["Immutable Managed<br/>Data Set"]
        DATA["Data"]
        MANIFEST["Manifest by Key"]
    end

    subgraph MetaDetails["Meta Details (IMDS)"]
        GOV["Governance<br/>Controls"]
        DESC["Data Set<br/>Description"]
        SCHEMA["Schema"]
    end

    subgraph Properties["Properties"]
        ACL["ACL: Authorised<br/>Readers/Writers"]
        FREQ["Frequency<br/>Quality<br/>Source"]
        TOPO["Topology<br/>Typing"]
    end

    Bucket --> MetaDetails
    MetaDetails --> Properties
```

**S3 Implementation**:
| Property | Value |
|----------|-------|
| Security | IMS |
| Governance | Configurable |
| Physical Location | Regional Replication |
| Access Methods | Sockets, Object Model |
| Encoding | Configurable |

---

# Slide 15: CDH Domain Model Modules

## Data Storage Architecture

```mermaid
flowchart LR
    subgraph Consumption["Consumption"]
        ELASTIC["Elastic"]
        IMPALA["Impala"]
        KUDU["Kudu"]
        PSQL["PSQL"]
    end

    subgraph ConsStorage["Consumption Storage"]
        FLAT["Flattened View"]
        NORM["Normalised View"]
    end

    subgraph OptStorage["Optimised Consumption Storage"]
        direction TB
    end

    subgraph DataVault["Data Vault (Logical or Physical)"]
        subgraph FeatureView["Feature View"]
            KEY["Key Index"]
            LATEST["Latest<br/>State"]
            HIST["Historical<br/>State"]
            META["Meta<br/>View"]
        end
    end

    subgraph RawView["Raw View (Immutable Log)"]
        ORIG["Original<br/>Topology<br/>/ Schema"]
    end

    INGEST["Ingestion"]

    Consumption --> ConsStorage
    ConsStorage --> OptStorage
    OptStorage --> DataVault
    DataVault --> RawView
    RawView --> INGEST
```

---

# Slide 16: Refactoring - You Got to Have a Plan

## The Two-Phase Approach

**There is no point refactoring towards a technology unless it is in service to your model.**

```mermaid
flowchart LR
    subgraph Phase1["Phase 1"]
        P1["Refactoring towards<br/>a DOMAIN MODEL"]
    end

    subgraph Phase2["Phase 2"]
        P2["Refactoring towards<br/>TECHNOLOGY to<br/>support the model"]
    end

    Phase1 -->|"Then"| Phase2

    style Phase1 fill:#4a86c7,color:#fff
    style Phase2 fill:#c8e6c9
```

**Key insight**: Technology serves the model, not the other way around.

---

# Slide 17: Refactoring a Slice Pattern

## Consumer-Backward Approach

**Step 1**: Go to the end point and identify the model the consumer needs
- E.g., FP&A CTOs report has a specific 'bounded context'
- It may have a unique language and requirement

**Step 2**: Work backwards from the Consumer
- Identify entities needed to fulfill the consumer's model
- Build the model for those entities

```mermaid
flowchart RL
    CONSUMER["Consumer<br/>(Report/API)"]
    MODEL["Consumer's<br/>Domain Model"]
    ENTITIES["Required<br/>Entities"]
    SOURCES["Source<br/>Systems"]

    CONSUMER -->|"Identify needs"| MODEL
    MODEL -->|"Decompose"| ENTITIES
    ENTITIES -->|"Trace to"| SOURCES
```

---

# Slide 18: Section Outlines - The Refactoring Roadmap

## From Current State to Future State

```mermaid
flowchart TB
    subgraph Landscape["Domain Landscape"]
        BOUND["The Bounded<br/>Context"]
    end

    subgraph Refactoring["Refactoring"]
        PATTERNS["Refactoring<br/>Patterns"]
        FUNC["Functional<br/>Slice"]
        CONST["Constant<br/>Enrichment"]
        DECOUPLE["Decouple"]
    end

    subgraph Blocks["Solution Building Blocks"]
        INT["Integrations"]
        WF["Workflow"]
        TRANS["Transform"]
    end

    subgraph AntiPatterns["Corporate Anti-Patterns"]
        FILES["Files"]
        MANUAL["Manual<br/>Process"]
        MUD["Ball of<br/>Mud /<br/>Monolith"]
    end

    Landscape --> Refactoring
    Refactoring --> Blocks
    AntiPatterns -.->|"Address"| Blocks
```

**The Journey**:
0. Example Future State
1. Domain Model Consumer
2. Domain Model Sources
3. Create APIs over each Model
4. Integrate
5. Solution Building Blocks
6. Parallel Verification

---

# Slide 19: Orchestra - Philosophy of Product Development

## Domain-Driven, Event-Sourced Architecture

**Philosophy of Designing for Product**:
1. Background in Start-ups & Product-driven development
2. Elements of a start-up culture:
   - Use a real-world problem to bootstrap a product
   - Separate the Business Domain from the Capabilities needed
   - Discover requirements through iteration - don't be paralysed by lack of requirements

**Philosophy of Orchestra**:
1. **Domain-Driven Design** to define your services
2. **Event-Driven Architecture / Event Sourcing** for modeling
3. **Orchestrating Domain Services**:
   - Avoiding creating dependency chains
   - Introducing the **Saga Pattern**

---

# Slide 20: The Saga Pattern

## Orchestrating Without Dependency Chains

```mermaid
flowchart TB
    subgraph Saga["Saga Orchestrator"]
        ORCH["Orchestrator"]
    end

    subgraph Services["Domain Services"]
        S1["Service A"]
        S2["Service B"]
        S3["Service C"]
    end

    subgraph Events["Event Log"]
        E1["Event A"]
        E2["Event B"]
        E3["Event C"]
    end

    ORCH -->|"Command"| S1
    ORCH -->|"Command"| S2
    ORCH -->|"Command"| S3

    S1 -->|"Publish"| E1
    S2 -->|"Publish"| E2
    S3 -->|"Publish"| E3

    E1 -->|"Subscribe"| ORCH
    E2 -->|"Subscribe"| ORCH
    E3 -->|"Subscribe"| ORCH

    style Saga fill:#fff3e0
```

**Key benefits**:
- No direct service-to-service dependencies
- Compensating transactions for rollback
- Event log provides complete audit trail
- Services remain independently deployable

---

# Slide 21: Bi-Temporal Views

## Business View vs Systems View

```mermaid
flowchart TB
    subgraph SystemsTime["Systems Activity Time Line: As At"]
        T1["T1:a"]
        T2["T2:x"]
        T3["T3:y"]
        T4["T4:z"]
        T5["T5:b"]
        T6["T6:c"]
        T7["T7:d"]
        T8["T8:e"]
        T9["T9:f"]
    end

    subgraph BusinessTime["Business Activity Time Line: As Of"]
        B1["1"]
        B2["2"]
        B3["3"]
        B4["4"]
        B5["5"]
        B6["6"]
        B7["7"]
    end

    T1 --> B1
    T2 --> B2
    T3 --> B2
    T4 --> B3
    T5 --> B4
    T6 --> B5
    T7 --> B6
    T8 --> B6
    T9 --> B7
```

**Two timelines**:
- **As At**: When the system recorded the event
- **As Of**: When the business event actually occurred

**View: As of Till** - Business activity timeline is a view of the underlying system events.

---

# Slide 22: Information Systems & Intentional Design

## From Reality to Composable Architecture

```mermaid
flowchart LR
    REALITY["Reality"]

    BA["Business<br/>(deals directly<br/>with reality)"]

    EVENT["Event Storming<br/>(builds abstract<br/>domain)"]

    DOMAIN["Abstract<br/>Problem Domain<br/>(e.g. How users see CATS)"]

    ARCH["Architect &<br/>Programmer"]

    SYSTEMS["Systems Architecture<br/>& Programs"]

    TECH["Technology"]

    REALITY --> BA --> EVENT --> DOMAIN --> ARCH --> SYSTEMS
    ARCH --> TECH

    style DOMAIN fill:#bbdefb
    style SYSTEMS fill:#c8e6c9
```

**Event Storming** helps build the abstract domain by focusing on what actually happens in the business.

---

# Slide 23: Parallel Registration Strategy

## Phased Migration Approach

**Stage 1: Full Segregation**
- Separation on Product Boundaries
- Users register independently
- **Data unified at Registered Person Records** coming out of both systems
- Advantages: Easiest, cheapest, quickest to stand up
- Disadvantages: Double registration for cross-product users

**Stage 2: Registration Integration**
- WSA implements registration synchronization from existing system
- Consistent user experience with minimal re-keying

**Stage 3: Product Migration**
- Selective controlled product migration from existing systems to WSA

---

# Slide 24: Patterns of Integration

## The Two Fundamental Patterns

```mermaid
flowchart TB
    subgraph Patterns["Integration Patterns"]
        EVENTS["Events<br/>(Asynchronous)"]
        APIS["APIs<br/>(Synchronous)"]
    end

    subgraph EventTypes["Event Types"]
        DOMAIN["Domain Events"]
        INTEG["Integration Events"]
        CMD["Command Events"]
    end

    subgraph APITypes["API Types"]
        REST["REST"]
        GRPC["gRPC"]
        ODBC["ODBC"]
    end

    EVENTS --> EventTypes
    APIS --> APITypes
```

**APIs** include all programmatic interfaces such as REST & ODBC.

---

# Slide 25: Highest Value Automation Testing

## Outside-In Testing Strategy

**For highest value, test from the outside in:**

1. **Test from outside to inwards** of your releasable Product
2. Examples:
   - Releasing an **Application** → test its interfaces, imports and exports
   - Releasing a **Library** → test its interface calls

3. **If modules need refactoring** → automate testing their interfaces where possible

4. **BUT**: If your automated API tests exercise the execution paths, then the need for internal testing is greatly mitigated

```mermaid
flowchart TB
    subgraph Product["Releasable Product"]
        INTERFACE["Public Interface"]
        INTERNAL["Internal Modules"]
    end

    TESTS["Automated<br/>API Tests"] -->|"Exercise"| INTERFACE
    INTERFACE -->|"Exercises"| INTERNAL

    style TESTS fill:#c8e6c9
```

---

# Slide 26: Summary - The Complete Picture

## On-Demand Data Architecture

```mermaid
flowchart TB
    subgraph Foundation["Foundation"]
        DOMAIN["Domain-Driven<br/>Design"]
        BOUNDED["Bounded<br/>Contexts"]
        EVENTS["Event-Driven<br/>Architecture"]
    end

    subgraph Patterns["Key Patterns"]
        SAGA["Saga Pattern"]
        BITEMPORAL["Bi-Temporal<br/>Views"]
        FINE["Fine-Grained<br/>Functions"]
    end

    subgraph Infrastructure["Infrastructure"]
        MANAGED["Managed<br/>Data Sets"]
        PIPELINES["On-Demand<br/>Pipelines"]
        SERVERLESS["Serverless<br/>Functions"]
    end

    subgraph Process["Process"]
        REFACTOR["Systematic<br/>Refactoring"]
        SLICE["Consumer-Backward<br/>Slicing"]
        PARALLEL["Parallel<br/>Migration"]
    end

    Foundation --> Patterns
    Patterns --> Infrastructure
    Infrastructure --> Process
```

**Key Takeaways**:

1. **Domain First** - Refactor towards domain model, then technology
2. **Bounded Contexts** - Manage complexity through separation
3. **Events as First-Class** - Every business event captured and available
4. **Saga for Orchestration** - Avoid dependency chains
5. **Fine-Grained Functions** - Improve lineage through decomposition
6. **Consumer-Backward** - Start from the end and work backwards
7. **Parallel Migration** - Staged approach minimizes risk

---

*This presentation covers the architecture patterns for building composable, event-driven, domain-modeled enterprise data systems.*

**Version**: 1.0
**Date**: February 2026
