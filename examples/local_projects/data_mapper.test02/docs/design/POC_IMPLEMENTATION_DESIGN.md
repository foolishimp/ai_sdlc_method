# POC Implementation Design: Category Theory Data Mapper Engine

**Version**: 1.0
**Status**: Ready for Implementation
**Target**: Week 1 POC (from INTENT.md)
**Design Agent**: Traceability to Requirements

---

## Executive Summary

This document provides the **detailed technical design** for implementing the Week 1 Proof of Concept of the Category Theory Data Mapping Engine (CDME).

### POC Success Criteria (from INT-CDME-001)

**Week 1 Goals**:
1. Define: `Trade → Legs → Cashflows` (1:N relationship)
2. Reject: `sum(Trade.amount, Portfolio.total)` (grain mixing at compile time)
3. Emit: Lineage graph showing which trades → which cashflows

**Requirements Traceability**:
- REQ-LDM-01: Strict Graph definition
- REQ-LDM-02: Cardinality Types (1:1, N:1, 1:N)
- REQ-LDM-03: Strict Dot Hierarchy & Composition Validity
- REQ-TRV-02: Grain Safety (compile-time validation)
- REQ-TRV-05: Lineage Traceability

---

## 1. Architecture Overview

### 1.1 Component Diagram

```mermaid
graph TB
    subgraph "Core Engine (POC Scope)"
        TP[Topology<br/>REQ-LDM-01]
        ENT[Entity<br/>REQ-LDM-06]
        MOR[Morphism<br/>REQ-LDM-02]
        PC[PathCompiler<br/>REQ-LDM-03]
        GV[GrainValidator<br/>REQ-TRV-02]
        LT[LineageTracker<br/>REQ-TRV-05]
    end

    subgraph "Example Domain (POC Data)"
        TR[Trade Entity]
        LEG[Leg Entity]
        CF[Cashflow Entity]
    end

    subgraph "Validation Layer"
        ERR[ErrorCollector]
        RES[Result[T, Error]]
    end

    TP --> ENT
    TP --> MOR
    PC --> TP
    PC --> GV
    PC --> LT
    GV --> ERR
    LT --> RES

    TR --> TP
    LEG --> TP
    CF --> TP

    style TP fill:#e1f5ff
    style PC fill:#fff4e1
    style GV fill:#ffe1e1
    style LT fill:#e1ffe1
```

### 1.2 Technology Stack

**Language**: Python 3.11+ (type hints required)
**Core Libraries**:
- `dataclasses` - Entity/Morphism definitions
- `typing` - Type safety (Generic[T], Union, Optional)
- `enum` - Cardinality types
- `graphlib` - Topological sorting (built-in)

**Testing**:
- `pytest` - TDD framework
- `pytest-cov` - Coverage reporting (target: 80%+)

**Lineage Visualization**:
- `graphviz` or `networkx` - Lineage graph rendering

---

## 2. Core Data Structures

### 2.1 Topology (REQ-LDM-01)

```python
# Implements: REQ-LDM-01 (Strict Graph)
from dataclasses import dataclass, field
from typing import Dict, Set, List, Optional

@dataclass
class Topology:
    """
    A directed multigraph representing a logical data model.

    Implements: REQ-LDM-01 (Strict Graph definition)
    """
    name: str
    entities: Dict[str, 'Entity'] = field(default_factory=dict)
    morphisms: Dict[str, 'Morphism'] = field(default_factory=dict)

    def add_entity(self, entity: 'Entity') -> None:
        """Add entity to topology."""
        if entity.name in self.entities:
            raise ValueError(f"Entity {entity.name} already exists")
        self.entities[entity.name] = entity

    def add_morphism(self, morphism: 'Morphism') -> None:
        """
        Add morphism to topology.

        Validates: REQ-LDM-03 (composition validity)
        """
        # Validate source and target entities exist
        if morphism.source.name not in self.entities:
            raise ValueError(f"Source entity {morphism.source.name} not found")
        if morphism.target.name not in self.entities:
            raise ValueError(f"Target entity {morphism.target.name} not found")

        self.morphisms[morphism.name] = morphism

    def get_path(self, path_expr: str) -> 'Path':
        """
        Resolve dot notation path (e.g., 'Trade.legs.notional')

        Implements: REQ-LDM-03 (Strict Dot Hierarchy)
        Validates: REQ-TRV-02 (Grain Safety)
        """
        return PathCompiler(self).compile(path_expr)
```

### 2.2 Entity (REQ-LDM-06)

```python
# Implements: REQ-LDM-06 (Grain & Type Metadata)
from enum import Enum

class Grain(Enum):
    """
    Granularity levels for entities.

    Implements: REQ-LDM-06
    """
    ATOMIC = "atomic"        # Single record (e.g., Trade)
    AGGREGATE = "aggregate"  # Rolled-up (e.g., PortfolioTotal)

@dataclass
class Attribute:
    """Entity attribute with type information."""
    name: str
    type_: type  # Python type (int, str, float, etc.)

@dataclass
class Entity:
    """
    A node in the topology graph.

    Implements: REQ-LDM-06 (Grain & Type Metadata)
    """
    name: str
    grain: Grain
    attributes: Dict[str, Attribute] = field(default_factory=dict)

    def add_attribute(self, attr: Attribute) -> None:
        """Add attribute to entity."""
        self.attributes[attr.name] = attr

    def __hash__(self):
        return hash(self.name)
```

### 2.3 Morphism (REQ-LDM-02)

```python
# Implements: REQ-LDM-02 (Cardinality Types)
class Cardinality(Enum):
    """
    Cardinality types for relationships.

    Implements: REQ-LDM-02
    """
    ONE_TO_ONE = "1:1"     # Isomorphism
    MANY_TO_ONE = "N:1"    # Standard function
    ONE_TO_MANY = "1:N"    # Kleisli arrow (list monad)

@dataclass
class Morphism:
    """
    A directed edge in the topology graph.

    Implements: REQ-LDM-02 (Cardinality Types)
    """
    name: str
    source: Entity
    target: Entity
    cardinality: Cardinality

    def is_grain_preserving(self) -> bool:
        """
        Check if morphism preserves grain.

        Validates: REQ-TRV-02 (Grain Safety)

        Rules:
        - 1:1 preserves grain
        - N:1 can increase grain (aggregation)
        - 1:N decreases grain (fan-out)
        """
        if self.cardinality == Cardinality.ONE_TO_ONE:
            return self.source.grain == self.target.grain
        elif self.cardinality == Cardinality.MANY_TO_ONE:
            # Allowed: ATOMIC → AGGREGATE
            return True
        elif self.cardinality == Cardinality.ONE_TO_MANY:
            # Moving from coarse to fine grain
            if self.source.grain == Grain.AGGREGATE and self.target.grain == Grain.ATOMIC:
                return True
            return self.source.grain == self.target.grain
        return False

    def __hash__(self):
        return hash((self.name, self.source.name, self.target.name))
```

---

## 3. Path Compilation & Validation

### 3.1 PathCompiler (REQ-LDM-03)

```python
# Implements: REQ-LDM-03 (Strict Dot Hierarchy & Composition Validity)
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class PathStep:
    """Single step in a path traversal."""
    morphism: Morphism
    grain_before: Grain
    grain_after: Grain

@dataclass
class Path:
    """
    A validated path through the topology.

    Implements: REQ-LDM-03
    Validates: REQ-TRV-02
    """
    expression: str
    steps: List[PathStep]
    start_entity: Entity
    end_entity: Entity
    is_valid: bool
    errors: List[str] = field(default_factory=list)

    def final_grain(self) -> Grain:
        """Return the final grain after path traversal."""
        return self.steps[-1].grain_after if self.steps else self.start_entity.grain

class PathCompiler:
    """
    Compiles dot notation paths into validated path objects.

    Implements: REQ-LDM-03 (Path verification)
    Validates: REQ-TRV-02 (Grain check)
    """

    def __init__(self, topology: Topology):
        self.topology = topology
        self.grain_validator = GrainValidator()

    def compile(self, path_expr: str) -> Path:
        """
        Compile path expression like 'Trade.legs.notional'

        Steps:
        1. Parse dot notation
        2. Resolve each segment to morphism
        3. Validate composition (codomain → domain match)
        4. Validate grain safety

        Returns: Path object with validation result
        """
        segments = path_expr.split('.')

        if not segments:
            return Path(
                expression=path_expr,
                steps=[],
                start_entity=None,
                end_entity=None,
                is_valid=False,
                errors=["Empty path expression"]
            )

        # Start with first entity
        entity_name = segments[0]
        if entity_name not in self.topology.entities:
            return Path(
                expression=path_expr,
                steps=[],
                start_entity=None,
                end_entity=None,
                is_valid=False,
                errors=[f"Entity '{entity_name}' not found in topology"]
            )

        current_entity = self.topology.entities[entity_name]
        start_entity = current_entity
        steps = []
        errors = []

        # Traverse remaining segments
        for i, segment in enumerate(segments[1:], 1):
            # Find morphism from current entity
            morphism = self._find_morphism(current_entity, segment)

            if not morphism:
                errors.append(
                    f"No morphism '{segment}' from entity '{current_entity.name}'"
                )
                break

            # Validate grain transition
            grain_before = current_entity.grain
            grain_after = morphism.target.grain

            if not morphism.is_grain_preserving():
                # Check if this is an allowed grain transition
                if not self.grain_validator.is_valid_transition(
                    grain_before, grain_after, morphism.cardinality
                ):
                    errors.append(
                        f"Invalid grain transition at '{segment}': "
                        f"{grain_before.value} → {grain_after.value} "
                        f"via {morphism.cardinality.value}"
                    )

            steps.append(PathStep(
                morphism=morphism,
                grain_before=grain_before,
                grain_after=grain_after
            ))

            # Move to next entity
            current_entity = morphism.target

        return Path(
            expression=path_expr,
            steps=steps,
            start_entity=start_entity,
            end_entity=current_entity,
            is_valid=len(errors) == 0,
            errors=errors
        )

    def _find_morphism(self, source: Entity, name: str) -> Optional[Morphism]:
        """Find morphism by name from source entity."""
        for morph in self.topology.morphisms.values():
            if morph.source == source and morph.name == name:
                return morph
        return None
```

### 3.2 GrainValidator (REQ-TRV-02)

```python
# Implements: REQ-TRV-02 (Grain Safety)
class GrainValidator:
    """
    Validates grain transitions during path traversal.

    Implements: REQ-TRV-02 (Grain mixing prevention at compile time)
    """

    def is_valid_transition(
        self,
        from_grain: Grain,
        to_grain: Grain,
        cardinality: Cardinality
    ) -> bool:
        """
        Validate if grain transition is allowed.

        Rules:
        - ATOMIC → ATOMIC (1:1): OK
        - ATOMIC → ATOMIC (1:N): OK (fan-out to finer grain)
        - ATOMIC → AGGREGATE (N:1): OK (aggregation)
        - AGGREGATE → ATOMIC (N:1): FORBIDDEN (cannot disaggregate without explicit morphism)
        """
        if from_grain == to_grain:
            return True

        if from_grain == Grain.ATOMIC and to_grain == Grain.AGGREGATE:
            # Only allowed with aggregation (N:1 after 1:N expansion)
            return cardinality == Cardinality.MANY_TO_ONE

        if from_grain == Grain.AGGREGATE and to_grain == Grain.ATOMIC:
            # Forbidden: cannot disaggregate
            return False

        return True

    def detect_grain_mixing(self, path: Path) -> List[str]:
        """
        Detect grain mixing violations.

        Returns: List of error messages
        """
        errors = []

        for i, step in enumerate(path.steps):
            if not self.is_valid_transition(
                step.grain_before,
                step.grain_after,
                step.morphism.cardinality
            ):
                errors.append(
                    f"Grain mixing at step {i+1}: "
                    f"{step.morphism.source.name}.{step.morphism.name} "
                    f"({step.grain_before.value} → {step.grain_after.value})"
                )

        return errors
```

---

## 4. Lineage Tracking (REQ-TRV-05)

### 4.1 LineageTracker

```python
# Implements: REQ-TRV-05 (Deterministic Reproducibility & Audit Traceability)
from dataclasses import dataclass
from typing import List, Set
from datetime import datetime

@dataclass
class LineageNode:
    """A node in the lineage graph."""
    entity: Entity
    instance_id: Optional[str] = None  # e.g., "Trade-101"

@dataclass
class LineageEdge:
    """An edge in the lineage graph showing data flow."""
    source: LineageNode
    target: LineageNode
    morphism: Morphism
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class LineageGraph:
    """
    Complete lineage graph for a data flow.

    Implements: REQ-TRV-05 (Audit Traceability)
    """
    nodes: Set[LineageNode] = field(default_factory=set)
    edges: List[LineageEdge] = field(default_factory=list)

    def add_edge(self, edge: LineageEdge) -> None:
        """Add edge to lineage graph."""
        self.nodes.add(edge.source)
        self.nodes.add(edge.target)
        self.edges.append(edge)

    def to_graphviz(self) -> str:
        """
        Export lineage graph to Graphviz DOT format.

        POC Feature: Visual lineage display
        """
        lines = ["digraph lineage {"]
        lines.append("  rankdir=LR;")

        # Add nodes
        for node in self.nodes:
            node_id = f"{node.entity.name}_{node.instance_id}" if node.instance_id else node.entity.name
            lines.append(f'  "{node_id}" [label="{node.entity.name}\\n({node.entity.grain.value})"];')

        # Add edges
        for edge in self.edges:
            src_id = f"{edge.source.entity.name}_{edge.source.instance_id}" if edge.source.instance_id else edge.source.entity.name
            tgt_id = f"{edge.target.entity.name}_{edge.target.instance_id}" if edge.target.instance_id else edge.target.entity.name
            lines.append(f'  "{src_id}" -> "{tgt_id}" [label="{edge.morphism.name}\\n{edge.morphism.cardinality.value}"];')

        lines.append("}")
        return "\n".join(lines)

class LineageTracker:
    """
    Tracks data lineage during path execution.

    Implements: REQ-TRV-05
    """

    def __init__(self):
        self.lineage = LineageGraph()

    def record_traversal(
        self,
        source_entity: Entity,
        target_entity: Entity,
        morphism: Morphism,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None
    ) -> None:
        """Record a single step in lineage."""
        edge = LineageEdge(
            source=LineageNode(source_entity, source_id),
            target=LineageNode(target_entity, target_id),
            morphism=morphism
        )
        self.lineage.add_edge(edge)

    def get_lineage(self) -> LineageGraph:
        """Return complete lineage graph."""
        return self.lineage
```

---

## 5. POC Example: Trade → Legs → Cashflows

### 5.1 Domain Model Setup

```python
# POC Example Domain (from INTENT.md Week 1 Success Criteria)

def create_trading_topology() -> Topology:
    """
    Create the POC topology: Trade → Legs → Cashflows

    Implements: Week 1 POC from INT-CDME-001
    """
    topology = Topology(name="TradingDomain")

    # Entities (REQ-LDM-06)
    trade = Entity(name="Trade", grain=Grain.ATOMIC)
    trade.add_attribute(Attribute("trade_id", str))
    trade.add_attribute(Attribute("amount", float))

    leg = Entity(name="Leg", grain=Grain.ATOMIC)
    leg.add_attribute(Attribute("leg_id", str))
    leg.add_attribute(Attribute("notional", float))

    cashflow = Entity(name="Cashflow", grain=Grain.ATOMIC)
    cashflow.add_attribute(Attribute("cashflow_id", str))
    cashflow.add_attribute(Attribute("amount", float))
    cashflow.add_attribute(Attribute("date", str))

    topology.add_entity(trade)
    topology.add_entity(leg)
    topology.add_entity(cashflow)

    # Morphisms (REQ-LDM-02)
    trade_to_legs = Morphism(
        name="legs",
        source=trade,
        target=leg,
        cardinality=Cardinality.ONE_TO_MANY
    )

    leg_to_cashflows = Morphism(
        name="cashflows",
        source=leg,
        target=cashflow,
        cardinality=Cardinality.ONE_TO_MANY
    )

    topology.add_morphism(trade_to_legs)
    topology.add_morphism(leg_to_cashflows)

    return topology
```

### 5.2 POC Test Cases

```python
# POC Success Criteria Tests

def test_valid_path_trade_to_cashflows():
    """
    POC Success #1: Define Trade → Legs → Cashflows

    Validates: REQ-LDM-03 (valid path compilation)
    """
    topology = create_trading_topology()
    compiler = PathCompiler(topology)

    # Valid path
    path = compiler.compile("Trade.legs.cashflows")

    assert path.is_valid
    assert len(path.steps) == 2
    assert path.start_entity.name == "Trade"
    assert path.end_entity.name == "Cashflow"
    assert len(path.errors) == 0

def test_grain_mixing_rejection():
    """
    POC Success #2: Reject grain mixing (compile time)

    Example: sum(Trade.amount, Portfolio.total)

    Validates: REQ-TRV-02 (grain safety enforcement)
    """
    topology = Topology(name="MixedGrainTest")

    # Create entities with different grains
    trade = Entity(name="Trade", grain=Grain.ATOMIC)
    trade.add_attribute(Attribute("amount", float))

    portfolio = Entity(name="Portfolio", grain=Grain.AGGREGATE)
    portfolio.add_attribute(Attribute("total", float))

    topology.add_entity(trade)
    topology.add_entity(portfolio)

    # Attempt to create invalid morphism (ATOMIC → AGGREGATE without proper aggregation)
    invalid_morph = Morphism(
        name="invalid",
        source=trade,
        target=portfolio,
        cardinality=Cardinality.ONE_TO_ONE  # Wrong: should be N:1 for aggregation
    )

    # Validation should fail
    assert not invalid_morph.is_grain_preserving()

def test_lineage_emission():
    """
    POC Success #3: Emit lineage graph

    Validates: REQ-TRV-05 (lineage traceability)
    """
    topology = create_trading_topology()
    tracker = LineageTracker()

    # Simulate traversal: Trade-101 → Leg-A → Cashflow-1
    trade_entity = topology.entities["Trade"]
    leg_entity = topology.entities["Leg"]
    cashflow_entity = topology.entities["Cashflow"]

    trade_to_legs = topology.morphisms["legs"]
    leg_to_cashflows = topology.morphisms["cashflows"]

    # Record lineage
    tracker.record_traversal(trade_entity, leg_entity, trade_to_legs, "Trade-101", "Leg-A")
    tracker.record_traversal(leg_entity, cashflow_entity, leg_to_cashflows, "Leg-A", "Cashflow-1")

    lineage = tracker.get_lineage()

    assert len(lineage.edges) == 2
    assert lineage.edges[0].source.instance_id == "Trade-101"
    assert lineage.edges[1].target.instance_id == "Cashflow-1"

    # Generate Graphviz output
    dot = lineage.to_graphviz()
    assert "Trade_Trade-101" in dot
    assert "Cashflow_Cashflow-1" in dot
```

---

## 6. Implementation Roadmap (Week 1)

### Day 1-2: Core Structures (TDD)
- [ ] Implement `Entity` class with tests (REQ-LDM-06)
- [ ] Implement `Morphism` class with tests (REQ-LDM-02)
- [ ] Implement `Topology` class with tests (REQ-LDM-01)
- [ ] Test: Create trading topology

### Day 3-4: Path Compilation
- [ ] Implement `PathCompiler` with tests (REQ-LDM-03)
- [ ] Implement `GrainValidator` with tests (REQ-TRV-02)
- [ ] Test: Valid path `Trade.legs.cashflows`
- [ ] Test: Reject grain mixing

### Day 5: Lineage Tracking
- [ ] Implement `LineageTracker` with tests (REQ-TRV-05)
- [ ] Implement `LineageGraph.to_graphviz()`
- [ ] Test: Generate lineage graph

### Day 6: Integration & Demo
- [ ] Create demo script showing all 3 POC success criteria
- [ ] Generate visual lineage diagram
- [ ] Documentation & presentation

---

## 7. Requirements Traceability Matrix

| Requirement | Component | Status | Test Coverage |
|-------------|-----------|--------|---------------|
| REQ-LDM-01 | Topology | ✅ Ready | test_topology.py |
| REQ-LDM-02 | Morphism, Cardinality | ✅ Ready | test_morphism.py |
| REQ-LDM-03 | PathCompiler | ✅ Ready | test_path_compiler.py |
| REQ-LDM-06 | Entity, Grain | ✅ Ready | test_entity.py |
| REQ-TRV-02 | GrainValidator | ✅ Ready | test_grain_validation.py |
| REQ-TRV-05 | LineageTracker | ✅ Ready | test_lineage.py |

---

## 8. Project Structure

```
data_mapper.test02/
├── src/
│   └── cdme/                        # Category Theory Data Mapper Engine
│       ├── __init__.py
│       ├── topology.py              # Topology, Entity, Morphism (REQ-LDM-*)
│       ├── path.py                  # PathCompiler (REQ-LDM-03)
│       ├── grain.py                 # GrainValidator (REQ-TRV-02)
│       ├── lineage.py               # LineageTracker (REQ-TRV-05)
│       └── examples/
│           └── trading_domain.py    # POC example topology
│
├── tests/
│   ├── test_topology.py             # Validates: REQ-LDM-01
│   ├── test_entity.py               # Validates: REQ-LDM-06
│   ├── test_morphism.py             # Validates: REQ-LDM-02
│   ├── test_path_compiler.py        # Validates: REQ-LDM-03
│   ├── test_grain_validation.py     # Validates: REQ-TRV-02
│   ├── test_lineage.py              # Validates: REQ-TRV-05
│   └── test_poc_integration.py      # Week 1 success criteria
│
├── docs/
│   ├── requirements/
│   │   └── mapper_requirements.md   # Source requirements
│   ├── design/
│   │   ├── design_CT_01.md          # Theoretical foundation
│   │   ├── design_sql_01.md         # DA translation
│   │   └── POC_IMPLEMENTATION_DESIGN.md  # This document
│   └── lineage/
│       └── example_lineage.dot      # Generated lineage graphs
│
├── pyproject.toml                   # Python project config
├── pytest.ini                       # Pytest configuration
└── README.md                        # Project overview
```

---

## 9. Success Metrics

**POC will be considered successful when**:

1. ✅ **Valid Path Compilation**
   - Input: `"Trade.legs.cashflows"`
   - Output: `Path(is_valid=True, steps=[...], errors=[])`

2. ✅ **Grain Mixing Rejection**
   - Input: Attempt to mix ATOMIC and AGGREGATE grains
   - Output: Compilation error with clear message

3. ✅ **Lineage Graph Generation**
   - Input: Path traversal
   - Output: Graphviz DOT file showing: Trade-101 → Leg-A → Cashflow-1

4. ✅ **Test Coverage**
   - All core components: 100% coverage
   - Integration tests: Pass
   - Total coverage: ≥ 80%

---

## 10. Next Steps After POC

Once POC is complete, proceed to **Month 3 MVP** requirements:
- Physical binding (PDM Functor)
- Real data execution (not just topology)
- OpenLineage integration
- Regulatory report generation

---

**Design Agent Sign-Off**: ✅
**Ready for Code Stage**: Yes
**TDD Required**: Yes (RED → GREEN → REFACTOR)

🎨 **Design complete! Proceeding to Tasks Stage for work breakdown.**
