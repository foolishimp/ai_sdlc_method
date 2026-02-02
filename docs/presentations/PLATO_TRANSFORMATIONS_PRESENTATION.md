# Plato Transformations

## Structure-Preserving Transforms Through Functors

*A framework for automatic, provably correct data transformations using category theory*

---

# Slide 1: The Problem

## Data Transformation is Hard

Every enterprise faces the same challenge:

```mermaid
flowchart LR
    subgraph Sources["Source Systems"]
        S1["System A<br/>(XML)"]
        S2["System B<br/>(JSON)"]
        S3["System C<br/>(SQL)"]
    end

    subgraph Targets["Target Systems"]
        T1["Data Warehouse"]
        T2["Analytics"]
        T3["Reporting"]
    end

    S1 -->|"Custom ETL"| T1
    S2 -->|"Custom ETL"| T2
    S3 -->|"Custom ETL"| T3

    style Sources fill:#ffccbc
    style Targets fill:#ffccbc
```

**The pain**:
- N sources × M targets = N×M custom transformations
- Each transformation is hand-coded
- Changes propagate unpredictably
- No guarantees about correctness

---

# Slide 2: The Observe/Interpret/Solve Cycle

## How We Actually Solve Problems

```mermaid
flowchart LR
    REALITY["Reality<br/>(The Business Domain)"]

    OBS["Observation &<br/>Interpretation"]

    ABSTRACT["The Abstract<br/>Problem Domain"]

    SOLUTIONS["Diverse<br/>Solution Sets"]

    SOLUTION["The Solution"]

    REALITY -->|"Each person brings<br/>life experience"| OBS
    OBS --> ABSTRACT
    ABSTRACT -->|"Solution sets<br/>collaboratively applied"| SOLUTIONS
    SOLUTIONS --> SOLUTION
    SOLUTION -->|"Tethered to reality<br/>by testing"| REALITY
```

**Key insight**: This is the scientific method applied at every granularity.

---

# Slide 3: Business Domain Software Life Cycle

## The Traditional Approach

```mermaid
flowchart LR
    REALITY["Reality<br/>(Business deals with their reality)"]

    BA["Business Analyst<br/>translates into<br/>abstract domain"]

    ABSTRACT["Abstract<br/>Problem Domain"]

    ARCH["Data Architect<br/>creates Directed Graphs<br/>representing domain"]

    DAG["DAG<br/>(sub-model along<br/>query path)"]

    DEV["Developer writes<br/>transforms between DAGs"]

    PIPELINE["Transformation<br/>Pipeline"]

    APP["The Application"]

    REALITY --> BA --> ABSTRACT --> ARCH --> DAG
    DAG --> DEV --> PIPELINE --> APP
```

**Problem**: Developer manually writes transforms between DAGs - error-prone and expensive.

---

# Slide 4: Business Domain Life Cycle with Plato

## The Automated Approach

```mermaid
flowchart LR
    REALITY["Reality"]

    BA["Business Analyst"]

    ABSTRACT["Abstract<br/>Problem Domain"]

    ARCH["Data Architect<br/>creates Graph over Domain"]

    PLATO["PLATO<br/>(Transformation Engine)"]

    GEN["Plato generates:<br/>• Destination Schema<br/>• Transformation Code"]

    PIPELINE["Transformation Pipeline<br/>(Hydra/Spark)"]

    APP["The Application"]

    REALITY --> BA --> ABSTRACT --> ARCH
    ARCH --> PLATO
    PLATO --> GEN
    GEN --> PIPELINE --> APP

    style PLATO fill:#4a86c7,color:#fff
```

**Key change**: Developer declares the destination DAG; Plato generates the transformation code automatically.

---

# Slide 5: TLDR - What Plato Does

## The Value Proposition

**Plato allows**:
1. Definition of a **network of entities and their relationships**
2. The Transformation module generates **instructions to copy data** from any projection to any other projection
3. The DSL can be converted to **any target language** (Spark, Java, Python, Beam, SQL)
4. Generated code used by **Hydra or standalone**

**Example flow**:
```
Source: Trade XML in Avro format
    ↓ (Plato projection definition)
User defines: Destination Projection from common Universe
    ↓ (Transformation module)
Generated: DSL instruction set (source → destination)
    ↓ (Adaptor)
Output: Executable Spark code for Hydra
```

---

# Slide 6: The Core Concept - Structure Preservation

## Automatic Structure-Preserving Transformation

```mermaid
flowchart LR
    subgraph Universe["Universe (Common Domain Model)"]
        A["A"]
        B["B"]
        C["C"]
        D["D"]
        E["E"]

        A --- B
        B --- C
        B --- D
        D --- E
    end

    subgraph ProjectionX["Projection X (Flattened)"]
        A1["A.1"]
        B2["B.2"]
        C3["C.3"]
        D2["D.2"]
        D3["D.3"]
        E3["E.3"]
        E4["E.4"]

        A1 --- B2
        B2 --- C3
        B2 --- D2
        D2 --- D3
        D3 --- E3
        E3 --- E4
    end

    subgraph ProjectionY["Projection Y (Collapsed)"]
        E1["E.1"]
        D2Y["D.2"]
        B3["B.3"]
    end

    Universe -->|"Traverse DAG"| ProjectionX
    Universe -->|"Traverse DAG"| ProjectionY
```

**Language** (minimal instruction set):
1. `CREATE node`
2. `COPY (node).ATTRIBUTES (a).FILTER(predicate)`

---

# Slide 7: Graph Representation

## Entities, Relationships, and Arcs

```mermaid
flowchart LR
    subgraph Graph["Domain Graph"]
        B["B"]
        D["D"]

        B -->|"B Compose -D"| D
        B -->|"B link -D"| D
        B -->|"B.x Compose -D.y"| D
        D -->|"B Compose -D"| B
        B ---|"B.g link-D.h"| D
    end
```

**Arc properties**:
- **Relationship**: Table key (Link, Composition)
- **Multiplicity**: Foreign Key - Mono (Single, Many)
- **Direction**: Mono(Left, Right), BiDirection

**Processing rules**:
- A → Adjacent Nodes & Arcs
- For each Arc: check if reference exists → FK if Mono
- For each unique Arc to same table: different reference name
- If Bidirectional: Create Join table for each unique Arc

---

# Slide 8: The Plato DSL

## SQL Code Construction from Plato DSL

```
Plato DSL Commands:
    CREATE, COPY
    Copy Result([source.Path]) to [destination.Path]
    Result <= Query( A )(Result A)

Path = Seq[Arc] from Src to Dest
Arc = (left_node, right_node, ref_type(link,composition))

Query( Path(n) => Arc 'n)
    (L1, R1) => (L2, R2) => (L3, R3) => (L4, R4) ...
    Where A'n( Ln, Rn) :: R(n) == L(n+1)

Result'n ( Query(Arc(L,R) ) )
```

```mermaid
flowchart LR
    B["B"] -->|"B Compose -D"| D["D"]
    B -->|"B link -D"| D
    B -->|"B.x Compose -D.y"| D
    D -->|"B Compose -D"| B
```

---

# Slide 9: Copy Transform Algorithm

## How Transformations Are Generated

```
create A
copy ( A=>A ) ::
create D
copy ( A=>D ) :: [ A, B, right, link, many, A_id, B_id],
                 [ B, D, right, link, many, B_id, D_id]
create B
copy ( A=>B ) :: [ A, B, right, link, many, A_id, B_id]
```

**SQL Generation**:
```sql
Select * from D where d_id in
    ( select d_id from B where b_id in
        ( select b_id from A ) )

RESULT_SET = select * from D
RESULT_KEYS = select d_id from B
RESULT_SET = Query_SET ( RESULT_KEYS )
RESULT_KEYS = Query_KEYS( Path, Arc = Path.head, RESULT_KEYS )
```

---

# Slide 10: The Algorithm - Network to Projections

## Transform ( {U:P1->X} -> {U:P2->Y} )

```mermaid
flowchart LR
    subgraph Network["Network Definition"]
        NA["A"]
        NB["B"]
        NC["C"]
        ND["D"]
        NE["E"]
        NA --- NB
        NB --- NC
        NB --- ND
        ND --- NE
    end

    subgraph X["Projection X"]
        XA["A.1"]
        XB["B.2"]
        XC["C.3"]
        XD2["D.2"]
        XD3["D.3"]
        XE["E.3 - E.4"]
    end

    subgraph Y["Projection Y"]
        YE["E.1"]
        YD["D.2"]
        YB["B.3"]
    end

    Network --> X
    Network --> Y
```

**Algorithm**:
1. Given Y, traverse over X.Data → Y.Data
2. META SETS - Mapping each node type
3. Traverse DAG Y
4. Traverse Y.E → Query X for Y.E → Create Y.E (X.E <- Query X)
5. Construct E.attribute <- Query(U:X.E).attributes
6. Resolve Links from B.E to B.D

---

# Slide 11: Plato Meta Model

## HOCON Definition Structure

```hocon
{
  // bundles of attributes - independent of nodes
  // nodes need the same tags as attributes
  attributes_lists: {
    Attrib_bundle1:[]
    Attrib_bundle2:[]
  }

  // nodes don't need to be defined all here
  // these are the common universe spanning definitions
  Nodes: { }

  // still need to think about how universes map (bounded context)
  PlatonicUniverse: {
    universeName: u {
      Nodes: [n1,n2]
      Arcs: [
        [n1,n2]
      ]
    }
  }

  // can all projections be stored as projection set rules?
  ProjectionSets: {
    projName: {
      Universe: u
      From: n1
      Ruleset: [
        // Arc definitions with type, multiplicity, direction
        {
          start: Trade,
          end: Order,
          type: composition,
          multiplicity: single,
          direction: bidirectional,
          end_identity_alias: "trade_key2_order_id"
        }
      ]
    }
  }
}
```

---

# Slide 12: Plato Module Architecture

## System Components

```mermaid
flowchart LR
    subgraph Inputs["Configuration Inputs"]
        CONF1["Model Conf"]
        CONF2["Conf TCL"]
        CONF3["Conf Open API"]
    end

    subgraph Core["Plato Core"]
        APP["App"]
        META["Meta Model<br/>Loader"]
        SESSION["Session"]
        API["Plato API"]
        CLI["Plato CLI"]

        subgraph ModelRefs["Model References"]
            NODES["Nodes"]
            GRAPHS["Graphs"]
            ARCS["Arcs"]
        end
    end

    subgraph Processing["Processing Modules"]
        PROJ["Projections"]
        TRANS["Transforms"]
        PROJ_ENC["Projection<br/>Encodings"]
        TRANS_ENC["Transform<br/>Language<br/>Encodings"]
        RULES["Rulesets"]
    end

    subgraph Outputs["Generated Outputs"]
        SCHEMA["Schema<br/>Encodings"]
        MODEL["Model<br/>Conf"]
        CODE["Code<br/>Transformations"]
    end

    Inputs --> META
    META --> SESSION
    APP --> SESSION
    SESSION --> Processing
    Processing --> Outputs

    style Core fill:#bbdefb
    style Outputs fill:#c8e6c9
```

---

# Slide 13: Transformation Engine

## Code Generation Pipeline

```mermaid
flowchart LR
    subgraph Input["Input"]
        INSTR["Instruction Set<br/>1. Create<br/>2. Copy A -> B<br/>3. etc"]
        CODEGEN["Code Gen<br/>Encoder"]
    end

    subgraph Engine["Transformation Engine"]
        PARSE["Parse into<br/>Command Set"]
        ENCODE["Transformation<br/>Engine<br/>Encoding"]

        subgraph Encodings["Encoding Types"]
            SYN["Syntax Encoding"]
            ACC["Accessor Encoding"]
            PERS["Persistence Encoding"]
            STRUCT["Structural Encoding"]
        end

        TEMPLATE["Transformation<br/>Engine Template"]
        TEMPLATES["Template 1<br/>Template 2<br/>Template n"]
        NATIVE["Native Library<br/>Support Code"]
    end

    subgraph Output["Output"]
        NATIVE_CODE["Native<br/>Transformation<br/>Code"]
    end

    INSTR --> PARSE
    CODEGEN --> TEMPLATE
    PARSE --> ENCODE
    ENCODE --> Encodings
    TEMPLATE --> TEMPLATES
    Encodings --> NATIVE_CODE
    TEMPLATES --> NATIVE_CODE
    NATIVE --> NATIVE_CODE

    style Engine fill:#fff3e0
```

---

# Slide 14: Projections and Ideologies

## Monads for Different Target Structures

```mermaid
flowchart LR
    subgraph Source["Source Graph"]
        GA["A"]
        GB["B"]
        GA --- GB
    end

    RULES["Rules"]

    subgraph Base["Base DAG"]
        BA["A"]
        BB["B"]
        BA --> BB
    end

    Source --> RULES --> Base

    subgraph DataVault["Data Vault DAG"]
        DVA["A"]
        DVAS["A.S"]
        DVAID["A.ID"]
        DVAL["A.L"]
        DVB["B"]
        DVBS["B.S"]
        DVBID["B.ID"]
        DVBL["B.L"]
    end

    subgraph Relational["Relational DAG"]
        RA["A"]
        RAB["AB"]
        RB["B"]
        RA --> RAB --> RB
    end

    Base -->|"Ideological<br/>Projection"| DataVault
    Base -->|"Ideological<br/>Projection"| Relational
```

**Composability** is against the base DAG, but prior to encoding needs to be projected into the adjacent category.

---

# Slide 15: Projection From a Universe

## Session and Lineage Tracking

```mermaid
flowchart LR
    subgraph Factory["Session Instance (factory)"]
        UNIVERSE1["Universe"]
        RULESET1["Projection Ruleset"]
        GEN["Generate Projections"]
    end

    subgraph ProjFactory["Projection (class factory)"]
        CREATE1["Create Projection"]
        CREATE2["Create Projection<br/>with Ideology"]
    end

    subgraph Instance1["First Projection (instance)"]
        U1["Universe"]
        P1["Projection"]
        R1["Projection<br/>Ruleset"]
        L1["Lineage"]
    end

    subgraph Instance2["Second Projection (instance)"]
        U2["Universe"]
        P2A["Projection"]
        P2B["Projection"]
        R2["Projection<br/>Ruleset"]
        L2["Lineage"]
    end

    Factory --> ProjFactory
    ProjFactory --> Instance1
    ProjFactory --> Instance2

    style Factory fill:#bbdefb
    style Instance1 fill:#c8e6c9
    style Instance2 fill:#c8e6c9
```

---

# Slide 16: Graph Joins

## Composing Universes

```mermaid
flowchart LR
    subgraph U1["Universe U1"]
        U1B["B₁"]
        U1A["A₁"]
        U1B --- U1A
    end

    subgraph U2["Universe U2"]
        U2C["C₂"]
        U2A["A₂"]
        U2C --- U2A
    end

    JOIN["U1 joins U2"]

    subgraph Joined["Joined Universe"]
        JC["C₁₂"]
        JA["A₁₂"]
        JB["B₁₂"]
        JC --- JA
        JA --- JB
    end

    subgraph Projected["Projected (with Hub/Sat)"]
        PB["Bᵢ"]
        PA["Aᵢ"]
        LINK["link"]
        HUB["hub"]
        SAT["sat"]
    end

    U1 --> JOIN
    U2 --> JOIN
    JOIN --> Joined
    Joined --> Projected
```

---

# Slide 17: Transformation Between DAGs

## Path-Based Transformation

```mermaid
flowchart LR
    subgraph U0["Universe U0"]
        U0A["A"]
        U0B["B"]
        U0C["C"]
        U0D["D"]
        U0E["E"]
        U0X["X"]
        U0Y["Y"]

        U0A --- U0B
        U0B --- U0C
        U0A --- U0D
        U0D --- U0E
        U0C --- U0X
        U0X --- U0Y
    end

    subgraph P0["Projection P0"]
        P0A["A"]
        P0B["B"]
        P0C["C"]
    end

    subgraph P1["Projection P1 (N-Reln)"]
        P1A["A"]
        P1B["B"]
        P1C["C"]
    end

    U0 --> P0
    U0 --> P1
```

**Pre-Condition**:
1. Get Path: U0.Path(A,B)
2. Missing Nodes P0 needs to be fully contained within P0 - U0.Path(A,B)

**Transformation**:
```
P1.Traverse(P0.Path(A,B)).Arcs_Sequence.map(
    (p1.A, Seq(p0.A)) => Create_Node( Read_Node(p0.A), p1.A )
)
```

---

# Slide 18: Transform Instruction Set

## Aggregation and Optimization

```mermaid
flowchart LR
    subgraph Basic["Basic Instruction Set"]
        I1["1. Create destination Node<br/>(have schema in place)"]
        I2["2. Collect data from sources"]
        I3["• Set of Sources"]
    end

    subgraph Sources["Sources as Paths to A"]
        S1["● — A"]
        S2["● — A"]
        S3["● — A"]
        AGG1["Aggregate → A"]
    end

    subgraph Optimized["Optimisation 1: Copy all A"]
        O1["● — A"]
        O2["● — A"]
        O3["● — A"]
        AGG2["Aggregate → A"]
    end

    Basic --> Sources
    Sources -->|"Just need<br/>adjacent entities"| Optimized
```

---

# Slide 19: Transforms Over Entities

## Two Fundamental Transform Types

### Type 1: Identity Preserving Transforms

- Usually **row-level operations** where entity identity is preserved through transformation
- New Aggregate Entities are created, but composing entity identities are preserved in the new aggregate

### Type 2: Aggregate Transforms

- New Aggregate Entities are created
- Composing entity identities are preserved in the new aggregate

```mermaid
flowchart LR
    subgraph Type1["Type 1: Identity Preserving"]
        E1["Entity A<br/>(id: 1)"]
        E1T["Entity A'<br/>(id: 1)"]
        E1 -->|"Transform"| E1T
    end

    subgraph Type2["Type 2: Aggregate"]
        E2A["Entity A (id: 1)"]
        E2B["Entity A (id: 2)"]
        E2C["Entity A (id: 3)"]
        AGG["Aggregate B<br/>(contains: 1,2,3)"]

        E2A --> AGG
        E2B --> AGG
        E2C --> AGG
    end
```

---

# Slide 20: Connection to Constraint Ontology

## Plato as Constraint-Preserving Transformation

```mermaid
flowchart LR
    subgraph Ontology["Constraint-Emergence Ontology"]
        O1["Reality = Constraint network"]
        O2["Morphisms = Admissible transformations"]
        O3["Structure preservation = Functor"]
    end

    subgraph Plato["Plato Framework"]
        P1["Universe = Constraint network (domain model)"]
        P2["Transforms = Morphisms between projections"]
        P3["Projections = Structure-preserving mappings"]
    end

    Ontology -->|"Instantiated as"| Plato
```

| Category Theory | Plato Implementation |
|-----------------|---------------------|
| **Objects** | Entities (Nodes) |
| **Morphisms** | Arcs (Relationships) |
| **Functor** | Projection (structure-preserving map) |
| **Natural Transformation** | Transform between projections |
| **Composition** | Path traversal |

**Plato is category theory made practical** - it automates what mathematicians call "functorial mappings" between data structures.

---

# Slide 21: Why This Matters

## The Business Value

```mermaid
flowchart LR
    subgraph Before["Before Plato"]
        B1["N×M custom ETL jobs"]
        B2["Manual coding"]
        B3["No correctness guarantees"]
        B4["Change = rewrite"]
    end

    subgraph After["After Plato"]
        A1["Define Universe once"]
        A2["Declare projections"]
        A3["Auto-generate transforms"]
        A4["Provably correct"]
    end

    Before -->|"Plato"| After

    style Before fill:#ffccbc
    style After fill:#c8e6c9
```

**Benefits**:
1. **Reduced development time** - Declare, don't code
2. **Correctness by construction** - Structure preservation is guaranteed
3. **Change resilience** - Modify universe, regenerate transforms
4. **Multi-target** - Same model → Spark, SQL, Python, etc.
5. **Lineage built-in** - Every transformation is traceable

---

# Slide 22: Summary

## Plato Transformations

```mermaid
flowchart LR
    subgraph Core["Core Concepts"]
        UNI["Universe<br/>(Domain Model)"]
        PROJ["Projections<br/>(Views)"]
        TRANS["Transforms<br/>(Generated)"]
    end

    subgraph Output["Outputs"]
        SPARK["Spark Code"]
        SQL["SQL"]
        PYTHON["Python"]
    end

    UNI --> PROJ
    PROJ --> TRANS
    TRANS --> Output
```

**Key Takeaways**:

1. **Define once, transform anywhere** - Single domain model, multiple projections
2. **Structure preservation** - Category-theoretic guarantees
3. **Automatic code generation** - DSL → executable transformation code
4. **Ideological projections** - Same model → Data Vault, Relational, etc.
5. **Composable universes** - Graph joins for cross-domain integration

> **The insight**: Data transformation is not about writing code - it's about declaring structure and letting mathematics generate the correct transformations.

---

*This presentation covers the Plato Transformations framework for automatic, structure-preserving data transformations using category theory principles.*

**Version**: 1.0
**Date**: February 2026
