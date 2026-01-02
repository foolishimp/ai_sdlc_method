# Domain & Mapping Requirements - Disambiguation Document

**Version**: 1.0
**Purpose**: Extract and clarify requirements for Source Domain, Target Domain, and Mapping Documents
**Requirements Agent**: Requirement disambiguation from mapper_requirements.md
**Linked to**: INT-CDME-001

---

## Overview

This document disambiguates the technical requirements around:
1. **Source Domain** (Logical Context A)
2. **Target Domain** (Logical Context B)
3. **Mapping Document** (Integration Bridge/Synthesis Rules)

---

## 1. Existing Requirements Analysis

### 1.1 Domain Definition Requirements

From the main requirements document, domains are referenced as:
- **"Logical Context"** or **"Bounded Context"**
- **"Category"** (in Category Theory terms)

**Current Requirements**:

#### REQ-LDM-01: Strict Graph (Domain Structure)
- The LDM must be defined as a directed multigraph
- **Applies to**: Both Source and Target domains
- **Status**: Defined ✅

#### REQ-LDM-06: Grain & Type Metadata
- Every Entity in the LDM must be explicitly tagged with its **Grain** and **Type**
- **Applies to**: All entities in both Source and Target domains
- **Status**: Defined ✅

**Gap Identified** ❌:
- **No explicit requirement for "Domain" as a first-class object**
- **No requirement for domain boundaries or isolation**
- **No requirement for domain versioning**

---

### 1.2 Integration/Mapping Requirements

**Existing Integration Requirements (REQ-INT-*)**: 8 requirements found

#### REQ-INT-01: Isomorphic Synthesis
- Users can define new attributes via **Pure Functions** over existing entities
- **Maps to**: Transformation logic in mapping document
- **Status**: Defined ✅

#### REQ-INT-02: Subsequent Aggregation
- Support aggregating over already-aggregated data (multi-level)
- **Constraint**: Must satisfy Monoid Laws at each level
- **Maps to**: Complex mapping scenarios
- **Status**: Defined ✅

#### REQ-INT-03: Traceability
- **Full lineage** mapping every target value back to source
- **Maps to**: Mapping document must capture provenance
- **Status**: Defined ✅ (POC success criteria #3)

#### REQ-INT-04: Complex Business Logic
- Support conditional expressions, fallbacks, composition
- **Maps to**: Mapping document syntax/capabilities
- **Status**: Defined ✅

#### REQ-INT-05: Multi-Grain Formulation
- Allow formulas referencing different grains with explicit aggregation
- **Maps to**: Cross-grain mapping rules
- **Status**: Defined ✅

#### REQ-INT-06: Versioned Lookups
- Reference data must be explicitly versioned in transformations
- **Maps to**: Mapping document references external lookup tables
- **Status**: Defined ✅

#### REQ-INT-07: Identity Synthesis
- Deterministic key generation (same input → same key)
- **Maps to**: ID generation rules in mapping
- **Status**: Defined ✅

#### REQ-INT-08: External Computational Morphisms
- Support **Black Box Calculators** as standard morphisms
- **Maps to**: Mapping can reference external functions
- **Status**: Defined ✅

**Gap Identified** ❌:
- **No explicit "Mapping Document" format/schema requirement**
- **No requirement for mapping validation**
- **No requirement for mapping versioning**

---

## 2. Missing Requirements - What We Need to Define

### 2.1 Source Domain Requirements

**REQ-DOMAIN-SRC-001**: **Source Domain Definition**
- **Type**: Functional
- **Priority**: Critical
- **Description**: A Source Domain is a Logical Context (Category) with:
  - Unique domain identifier
  - Set of Entities (nodes)
  - Set of Morphisms (edges)
  - Grain metadata for all entities
  - Type system definitions
- **Acceptance Criteria**:
  - [ ] Source domain can be defined programmatically
  - [ ] Source domain has immutable identifier
  - [ ] Source domain validates internal consistency (REQ-LDM-01, REQ-LDM-03)
- **Related to**: REQ-LDM-01, REQ-LDM-06
- **Maps to Intent**: INT-CDME-001 (Week 1: Define Trade → Legs → Cashflows)

**REQ-DOMAIN-SRC-002**: **Source Domain Versioning**
- **Type**: Non-Functional
- **Priority**: High
- **Description**: Source domains must be versioned to support evolution
- **Acceptance Criteria**:
  - [ ] Domain has semantic version (major.minor.patch)
  - [ ] Adding entities/morphisms increments version
  - [ ] Breaking changes (removing/renaming) require major version bump
- **Related to**: REQ-INT-06 (versioned lookups)

**REQ-DOMAIN-SRC-003**: **Source Domain Isolation**
- **Type**: Functional
- **Priority**: Medium
- **Description**: Source domain must be self-contained (no external references within domain)
- **Acceptance Criteria**:
  - [ ] All morphisms connect entities within the same domain
  - [ ] External references only via Integration Bridges (see REQ-MAP-*)
- **Related to**: Bounded Context pattern

---

### 2.2 Target Domain Requirements

**REQ-DOMAIN-TGT-001**: **Target Domain Definition**
- **Type**: Functional
- **Priority**: Critical
- **Description**: A Target Domain is a Logical Context (Category) with:
  - Unique domain identifier (different from source)
  - Set of Entities (may overlap names with source but are distinct objects)
  - Set of Morphisms
  - Grain metadata for all entities
  - Type system definitions
- **Acceptance Criteria**:
  - [ ] Target domain can be defined independently of source
  - [ ] Target domain has immutable identifier
  - [ ] Target domain validates internal consistency
- **Related to**: REQ-LDM-01, REQ-LDM-06
- **Maps to Intent**: INT-CDME-001 (implied: Regulatory Domain for output)

**REQ-DOMAIN-TGT-002**: **Target Domain Versioning**
- **Type**: Non-Functional
- **Priority**: High
- **Description**: Target domains must be versioned independently of source
- **Acceptance Criteria**:
  - [ ] Target domain version independent of source domain version
  - [ ] Mapping document references specific versions of both domains

**REQ-DOMAIN-TGT-003**: **Target Domain Derivation Rules**
- **Type**: Functional
- **Priority**: Medium
- **Description**: Target domain may contain derived entities (not directly mapped from source)
- **Acceptance Criteria**:
  - [ ] Derived entities marked with metadata
  - [ ] Derivation logic captured in domain definition or mapping document

---

### 2.3 Mapping Document Requirements

**REQ-MAP-001**: **Mapping Document Structure**
- **Type**: Functional
- **Priority**: Critical
- **Description**: A Mapping Document defines the transformation from Source Domain to Target Domain
- **Required Elements**:
  1. Source Domain reference (id + version)
  2. Target Domain reference (id + version)
  3. Entity mappings (source entity → target entity)
  4. Attribute mappings (source attributes → target attributes)
  5. Transformation rules (synthesis functions)
  6. Aggregation rules (when crossing grain boundaries)
  7. Lookup references (versioned reference data)
  8. Error handling rules (Error Domain routing)
- **Acceptance Criteria**:
  - [ ] Mapping document is declarative (not procedural code)
  - [ ] Mapping document validates against both source and target domains
  - [ ] Mapping document can be serialized (YAML/JSON)
- **Related to**: REQ-INT-01 through REQ-INT-08
- **Maps to Intent**: INT-CDME-001 (implicit: need mapping definition format)

**REQ-MAP-002**: **Mapping Validation (Compile-Time)**
- **Type**: Functional
- **Priority**: Critical
- **Description**: Mapping document must be validated at "compile time" (before execution)
- **Validation Rules**:
  1. Source entities/attributes exist in source domain
  2. Target entities/attributes exist in target domain
  3. Paths through source domain are valid (REQ-LDM-03)
  4. Type compatibility (REQ-TYP-06)
  5. Grain transitions are valid (REQ-TRV-02)
  6. All aggregations satisfy Monoid Laws (REQ-LDM-04)
  7. Lookup references are versioned (REQ-INT-06)
- **Acceptance Criteria**:
  - [ ] Invalid mapping rejected with clear error message
  - [ ] Validation occurs before data processing
  - [ ] AI-generated mappings pass same validation (REQ-AI-01)
- **Related to**: REQ-AI-01 (AI hallucination rejection)
- **Maps to Intent**: INT-CDME-001 POC Success #2 (reject grain mixing)

**REQ-MAP-003**: **Mapping Lineage Capture**
- **Type**: Functional
- **Priority**: High
- **Description**: Mapping document must capture sufficient metadata for full lineage
- **Acceptance Criteria**:
  - [ ] Every target attribute traces to source path
  - [ ] Lineage includes all intermediate transformations
  - [ ] Lineage includes versioned lookup references
- **Related to**: REQ-INT-03, REQ-TRV-05
- **Maps to Intent**: INT-CDME-001 POC Success #3 (emit lineage graph)

**REQ-MAP-004**: **Mapping Versioning**
- **Type**: Non-Functional
- **Priority**: High
- **Description**: Mapping documents must be versioned
- **Acceptance Criteria**:
  - [ ] Mapping has semantic version
  - [ ] Mapping references specific domain versions
  - [ ] Changing transformation logic increments version
- **Related to**: REQ-TRV-05 (reproducibility)

**REQ-MAP-005**: **Mapping Composition**
- **Type**: Functional
- **Priority**: Medium
- **Description**: Multiple mappings can be composed (A → B → C)
- **Acceptance Criteria**:
  - [ ] Mapping B-to-C can consume output of mapping A-to-B
  - [ ] Composition validates domain compatibility
  - [ ] Lineage tracks full chain
- **Related to**: REQ-LDM-03 (composition validity)

**REQ-MAP-006**: **Mapping Syntax**
- **Type**: Functional
- **Priority**: Critical
- **Description**: Define concrete syntax for mapping document
- **Options to Consider**:
  1. **Declarative YAML/JSON**
     ```yaml
     mapping:
       source_domain: TradingDomain:1.0.0
       target_domain: RegulatoryDomain:1.0.0
       entity_mappings:
         - source: Trade
           target: RegulatoryReport
           transformations:
             - attribute: report_amount
               source_path: Trade.legs.cashflows.amount
               aggregation: SUM
     ```
  2. **Python DSL** (Domain-Specific Language)
     ```python
     mapping = Mapping(
         source=TradingDomain("1.0.0"),
         target=RegulatoryDomain("1.0.0")
     )
     mapping.map(
         "RegulatoryReport.report_amount",
         SUM("Trade.legs.cashflows.amount")
     )
     ```
  3. **SQL-like Declarative**
     ```sql
     MAP Trade.legs.cashflows.amount
     TO RegulatoryReport.report_amount
     USING SUM
     WHERE Trade.status = 'ACTIVE'
     ```
- **Acceptance Criteria**:
  - [ ] Syntax is human-readable
  - [ ] Syntax supports all REQ-INT-* requirements
  - [ ] Syntax can express grain aggregations
  - [ ] Syntax can reference versioned lookups
- **Decision Required**: Choose one syntax approach

**REQ-MAP-007**: **Mapping Error Handling**
- **Type**: Functional
- **Priority**: High
- **Description**: Mapping must define how errors are handled
- **Acceptance Criteria**:
  - [ ] Failed transformations route to Error Domain (REQ-TYP-03)
  - [ ] Error routing rules defined in mapping
  - [ ] Partial failure doesn't corrupt valid data
- **Related to**: REQ-TYP-03, REQ-ERROR-01

---

## 3. Disambiguation Questions for User

### Question 1: Domain Definition Scope

**Context**: Currently, "domain" is implicit in the topology definition.

**Question**: Should we create an explicit `Domain` class that wraps a `Topology` and adds:
- Domain ID
- Domain version
- Domain metadata (owner, description, etc.)

**Options**:
- **Option A**: Yes, create explicit `Domain` class
- **Option B**: No, keep domains as just `Topology` objects
- **Option C**: Create `Domain` as metadata wrapper, but core logic uses `Topology`

**Your preference**: ?

---

### Question 2: Mapping Document Format

**Context**: We need to choose a concrete syntax for mapping documents.

**Question**: Which format should we use for POC?

**Options**:
- **Option A**: Declarative YAML (easy to read, tool-agnostic)
- **Option B**: Python DSL (type-safe, IDE support)
- **Option C**: SQL-like syntax (familiar to data engineers)
- **Option D**: Multiple formats supported (more complex)

**Your preference**: ?

---

### Question 3: Mapping Validation Timing

**Context**: When should mapping validation occur?

**Question**: Should validation be:

**Options**:
- **Option A**: Eager (validate immediately when mapping created)
- **Option B**: Lazy (validate only when compilation requested)
- **Option C**: Two-phase (basic validation on create, full validation on compile)

**Your preference**: ?

---

### Question 4: Domain Evolution

**Context**: Domains will evolve over time.

**Question**: How should we handle domain version compatibility?

**Options**:
- **Option A**: Strict versioning (mappings break if domain changes)
- **Option B**: Semantic versioning with compatibility rules (minor changes allowed)
- **Option C**: Migration tool (auto-upgrade mappings when domain changes)

**Your preference**: ?

---

### Question 5: Cross-Domain References

**Context**: Can source domain reference external lookup data?

**Question**: Should lookups be:

**Options**:
- **Option A**: Separate "Reference Domains" (third domain type)
- **Option B**: Built into mapping document as external parameters
- **Option C**: Modeled as morphisms to external entities

**Your preference**: ?

---

## 4. Proposed New Requirements Summary

### Source Domain (3 new)
- REQ-DOMAIN-SRC-001: Source Domain Definition
- REQ-DOMAIN-SRC-002: Source Domain Versioning
- REQ-DOMAIN-SRC-003: Source Domain Isolation

### Target Domain (3 new)
- REQ-DOMAIN-TGT-001: Target Domain Definition
- REQ-DOMAIN-TGT-002: Target Domain Versioning
- REQ-DOMAIN-TGT-003: Target Domain Derivation Rules

### Mapping Document (7 new)
- REQ-MAP-001: Mapping Document Structure
- REQ-MAP-002: Mapping Validation (Compile-Time)
- REQ-MAP-003: Mapping Lineage Capture
- REQ-MAP-004: Mapping Versioning
- REQ-MAP-005: Mapping Composition
- REQ-MAP-006: Mapping Syntax
- REQ-MAP-007: Mapping Error Handling

**Total New Requirements**: 13

---

## 5. Requirement Traceability

| New Requirement | Existing Requirements | Intent |
|-----------------|----------------------|--------|
| REQ-DOMAIN-SRC-001 | REQ-LDM-01, REQ-LDM-06 | INT-CDME-001 |
| REQ-DOMAIN-TGT-001 | REQ-LDM-01, REQ-LDM-06 | INT-CDME-001 |
| REQ-MAP-001 | REQ-INT-01 through REQ-INT-08 | INT-CDME-001 |
| REQ-MAP-002 | REQ-AI-01, REQ-LDM-03, REQ-TRV-02 | INT-CDME-001 POC #2 |
| REQ-MAP-003 | REQ-INT-03, REQ-TRV-05 | INT-CDME-001 POC #3 |

---

## 6. Next Steps

1. **Answer disambiguation questions** (above)
2. **Finalize new requirements** based on answers
3. **Update main requirements document** (mapper_requirements.md)
4. **Update POC design** to reflect mapping document format
5. **Proceed to implementation** (Code Stage)

---

**Requirements Agent Sign-Off**: ⏸️ **Awaiting User Input**

🎯 **Ready for user to answer disambiguation questions!**
