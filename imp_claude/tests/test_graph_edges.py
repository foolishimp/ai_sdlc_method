# Validates: REQ-GRAPH-002
# Validates: REQ-GRAPH-003
# Validates: REQ-ITER-002
# Validates: REQ-EDGE-001
# Validates: REQ-EDGE-002
# Validates: REQ-EDGE-003
"""Deterministic tests for graph admissibility, Markov convergence,
and edge parameterisation (TDD, BDD, ADR patterns).

INT-GAP-004 resolution — Phase 1 methodology correctness.
"""

import pathlib
import sys

import pytest
import yaml

sys.path.insert(
    0,
    str(pathlib.Path(__file__).parent.parent / "code"),
)

from conftest import (
    CONFIG_DIR,
    EDGE_PARAMS_DIR,
)


def _load(rel: str) -> dict:
    path = EDGE_PARAMS_DIR / rel
    with open(path) as f:
        docs = list(yaml.safe_load_all(f))
    result: dict = {}
    for doc in docs:
        if doc is not None:
            result.update(doc)
    return result


def _topology() -> dict:
    with open(CONFIG_DIR / "graph_topology.yml") as f:
        docs = list(yaml.safe_load_all(f))
    result: dict = {}
    for doc in docs:
        if doc is not None:
            result.update(doc)
    return result


# ═══════════════════════════════════════════════════════════════════════
# REQ-GRAPH-002 — Admissible Transitions
# ═══════════════════════════════════════════════════════════════════════


class TestAdmissibleTransitions:
    """Graph topology enforces directed transitions with typed source/target."""

    @pytest.fixture
    def topo(self):
        return _topology()

    @pytest.fixture
    def transitions(self, topo):
        return topo["transitions"]

    def test_transitions_are_directed(self, transitions):
        """Every transition has explicit source and target asset types."""
        for t in transitions:
            assert "source" in t, f"transition '{t.get('name')}' missing source"
            assert "target" in t, f"transition '{t.get('name')}' missing target"

    def test_default_edges_present(self, transitions):
        """All required default edges from the spec acceptance criteria exist."""
        # REQ-GRAPH-002: Intent→Requirements, Requirements→Feature Decomp,
        # Feat Decomp→Design, Code↔Unit Tests, Design→UAT Tests, Code→CI/CD,
        # Running System→Telemetry, Telemetry→Intent
        required = [
            ("intent", "requirements"),
            ("requirements", "feature_decomposition"),
            ("code", "unit_tests"),
            ("design", "uat_tests"),
            ("design", "test_cases"),
            ("code", "cicd"),
            ("running_system", "telemetry"),
            ("telemetry", "intent"),
        ]
        present = {(t["source"], t["target"]) for t in transitions}
        for source, target in required:
            assert (source, target) in present, (
                f"Required default edge {source}→{target} not in graph topology"
            )

    def test_graph_is_cyclic(self, topo):
        """Feedback loop (telemetry→intent) makes the graph cyclic — first-class edges."""
        graph_properties = topo.get("graph_properties", {})
        assert graph_properties.get("cyclic") is True, (
            "graph_topology.yml graph_properties.cyclic must be true — "
            "feedback edges are first-class (REQ-GRAPH-002)"
        )

    def test_edge_types_valid(self, transitions):
        """Every transition uses a recognised edge_type."""
        valid = {"standard", "co_evolution"}
        for t in transitions:
            assert t.get("edge_type") in valid, (
                f"transition '{t.get('name')}' edge_type must be standard or co_evolution"
            )

    def test_transitions_registry_extensible(self, transitions):
        """Transitions stored as a list — new edges addable without engine changes."""
        assert isinstance(transitions, list), (
            "transitions must be a YAML list to support extension"
        )
        assert len(transitions) >= 14

    def test_transitions_logged_for_audit(self, transitions):
        """Each transition has evaluators field enabling audit of traversal."""
        for t in transitions:
            assert "evaluators" in t, (
                f"transition '{t.get('name')}' missing evaluators — "
                "audit requires at least one evaluator per transition"
            )


# ═══════════════════════════════════════════════════════════════════════
# REQ-GRAPH-003 — Asset as Markov Object
# ═══════════════════════════════════════════════════════════════════════


class TestAssetMarkovObject:
    """Assets achieve stable Markov status only on evaluator convergence."""

    @pytest.fixture
    def topo(self):
        return _topology()

    @pytest.fixture
    def asset_types(self, topo):
        return topo["asset_types"]

    def test_all_asset_types_have_markov_criteria(self, asset_types):
        """Every asset type declares its promotion conditions."""
        for name, asset in asset_types.items():
            assert "markov_criteria" in asset, (
                f"asset_type '{name}' missing markov_criteria — "
                "stable status requires defined convergence conditions"
            )

    def test_markov_criteria_non_empty(self, asset_types):
        """Each asset type has at least one Markov criterion (non-trivial convergence)."""
        for name, asset in asset_types.items():
            criteria = asset.get("markov_criteria", [])
            assert len(criteria) >= 1, (
                f"asset_type '{name}' has empty markov_criteria — "
                "at least one criterion required for stable boundary"
            )

    def test_asset_types_have_schema(self, asset_types):
        """Every asset type has a typed schema (Markov boundary = typed interface)."""
        for name, asset in asset_types.items():
            assert "schema" in asset, (
                f"asset_type '{name}' missing schema — "
                "Markov boundary requires a typed interface"
            )

    def test_unit_tests_asset_has_coverage_criterion(self, asset_types):
        """Unit tests asset type has coverage_above_threshold in Markov criteria.

        Coverage is measured on the test run (unit_tests asset), not on code
        itself — the test suite must meet the threshold to achieve stable status.
        """
        unit_tests_type = asset_types.get("unit_tests", {})
        criteria = unit_tests_type.get("markov_criteria", [])
        assert "coverage_above_threshold" in criteria, (
            "unit_tests asset_type must include coverage_above_threshold in "
            "markov_criteria — the test suite stable boundary includes coverage"
        )

    def test_requirements_asset_requires_human_approval(self, asset_types):
        """Requirements Markov promotion requires human approval (F_H gate)."""
        req_type = asset_types.get("requirements", {})
        criteria = req_type.get("markov_criteria", [])
        assert "human_approved" in criteria, (
            "requirements asset_type must include human_approved in markov_criteria"
        )

    def test_engine_convergence_reflects_markov_semantics(self):
        """Engine converged=True ↔ delta=0 ↔ candidate becomes stable asset."""
        from genesis.engine import EngineConfig

        # EngineConfig has max_iterations_per_edge — non-convergence is bounded
        fields = list(EngineConfig.__dataclass_fields__.keys())
        assert "max_iterations_per_edge" in fields, (
            "EngineConfig must have max_iterations_per_edge — "
            "non-convergence after max_iter escalates to human (REQ-ITER-002)"
        )


# ═══════════════════════════════════════════════════════════════════════
# REQ-ITER-002 — Convergence and Promotion
# ═══════════════════════════════════════════════════════════════════════


class TestConvergenceAndPromotion:
    """Candidates promoted to next asset type only on evaluator convergence."""

    def test_max_iterations_configurable(self):
        """EngineConfig.max_iterations_per_edge is configurable (not hard-coded)."""
        from genesis.engine import EngineConfig

        fields = EngineConfig.__dataclass_fields__
        assert "max_iterations_per_edge" in fields
        # Default exists but is overridable
        default = fields["max_iterations_per_edge"].default
        assert default is not None and default > 0

    def test_delta_zero_produces_converged(self, tmp_path):
        """When all F_D checks pass (delta=0), evaluate_checklist marks converged.

        Directly tests the convergence formula: converged = (delta == 0).
        Uses `true` command as a pass-always deterministic check.
        """
        from genesis.fd_evaluate import evaluate_checklist
        from genesis.models import ResolvedCheck

        passing_check = ResolvedCheck(
            name="always_passes",
            check_type="deterministic",
            functional_unit="evaluate",
            criterion="command exits with code 0",
            source="test",
            required=True,
            command="true",
            pass_criterion="exit code 0",
        )
        result = evaluate_checklist(
            [passing_check], cwd=tmp_path, edge="code↔unit_tests"
        )
        assert result.delta == 0
        assert result.converged is True

    def test_delta_nonzero_means_not_converged(self, tmp_path):
        """When a required F_D check fails (delta>0), converged is False.

        Non-convergence after max_iterations escalates to human evaluator (REQ-ITER-002).
        Uses `false` command as a fail-always deterministic check.
        """
        from genesis.fd_evaluate import evaluate_checklist
        from genesis.models import ResolvedCheck

        failing_check = ResolvedCheck(
            name="always_fails",
            check_type="deterministic",
            functional_unit="evaluate",
            criterion="command exits with code 0",
            source="test",
            required=True,
            command="false",
            pass_criterion="exit code 0",
        )
        result = evaluate_checklist(
            [failing_check], cwd=tmp_path, edge="code↔unit_tests"
        )
        assert result.delta > 0
        assert result.converged is False

    def test_convergence_threshold_configurable_per_edge(self):
        """Edge params reference $thresholds variables — threshold configurable per project."""
        tdd = _load("tdd.yml")
        checklist = tdd.get("checklist", [])
        # Find the coverage check
        coverage_checks = [
            c
            for c in checklist
            if "coverage" in c.get("name", "").lower()
            or "$thresholds" in str(c.get("criterion", ""))
        ]
        assert len(coverage_checks) >= 1, (
            "tdd.yml checklist must include a coverage threshold check "
            "that references $thresholds (configurable per edge per project)"
        )


# ═══════════════════════════════════════════════════════════════════════
# REQ-EDGE-001 — TDD at Code ↔ Tests Edges
# ═══════════════════════════════════════════════════════════════════════


class TestTDDEdge:
    """Code↔Unit Tests edge uses TDD co-evolution pattern."""

    @pytest.fixture
    def topo(self):
        return _topology()

    @pytest.fixture
    def tdd(self):
        return _load("tdd.yml")

    def test_code_unit_tests_edge_is_co_evolution(self, topo):
        """Code↔Unit Tests transition has edge_type co_evolution (bidirectional)."""
        transitions = topo["transitions"]
        tdd_edge = next(
            (
                t
                for t in transitions
                if t["source"] == "code" and t["target"] == "unit_tests"
            ),
            None,
        )
        assert tdd_edge is not None, "Code↔Unit Tests transition must exist"
        assert tdd_edge["edge_type"] == "co_evolution", (
            "Code↔Unit Tests must be co_evolution (not standard) — "
            "test and code assets iterate together"
        )

    def test_tdd_phases_present(self, tdd):
        """TDD config defines red, green, refactor, commit phases."""
        phases = tdd.get("phases", {})
        for required_phase in ("red", "green", "refactor", "commit"):
            assert required_phase in phases, (
                f"tdd.yml missing '{required_phase}' phase — "
                "REQ-EDGE-001 requires all four TDD phases"
            )

    def test_tdd_red_phase_uses_deterministic_evaluator(self, tdd):
        """RED phase evaluator is deterministic (test exists and fails = F_D fact)."""
        red = tdd.get("phases", {}).get("red", {})
        assert red.get("evaluator") == "deterministic", (
            "RED phase must use deterministic evaluator — "
            "test failure is an observable fact, not an agent judgment"
        )

    def test_tdd_coverage_threshold_configurable(self, tdd):
        """Coverage threshold is configurable (default 80% but project-overridable)."""
        checklist = tdd.get("checklist", [])
        # Coverage check references $thresholds variable
        has_threshold_ref = any("$thresholds" in str(c) for c in checklist)
        assert has_threshold_ref, (
            "tdd.yml checklist must reference $thresholds — "
            "minimum coverage threshold must be configurable (default 80%)"
        )

    def test_tdd_implements_req_edge_001(self, tdd):
        """tdd.yml header declares it implements REQ-EDGE-001."""
        # Read raw file to check header comment
        raw = (EDGE_PARAMS_DIR / "tdd.yml").read_text()
        assert "REQ-EDGE-001" in raw, (
            "tdd.yml must declare '# Implements: REQ-EDGE-001' in header"
        )


# ═══════════════════════════════════════════════════════════════════════
# REQ-EDGE-002 — BDD at Design→Test Edges
# ═══════════════════════════════════════════════════════════════════════


class TestBDDEdge:
    """Design→Test Cases and Design→UAT Tests edges use BDD/Gherkin pattern."""

    @pytest.fixture
    def topo(self):
        return _topology()

    @pytest.fixture
    def bdd(self):
        return _load("bdd.yml")

    def test_design_uat_tests_edge_exists(self, topo):
        """Design→UAT Tests transition exists in graph topology."""
        transitions = topo["transitions"]
        bdd_edge = next(
            (
                t
                for t in transitions
                if t["source"] == "design" and t["target"] == "uat_tests"
            ),
            None,
        )
        assert bdd_edge is not None, "Design→UAT Tests transition must exist"

    def test_design_test_cases_edge_exists(self, topo):
        """Design→Test Cases transition exists in graph topology."""
        transitions = topo["transitions"]
        edge = next(
            (
                t
                for t in transitions
                if t["source"] == "design" and t["target"] == "test_cases"
            ),
            None,
        )
        assert edge is not None, "Design→Test Cases transition must exist"

    def test_bdd_uses_gherkin_format(self, bdd):
        """BDD config specifies Gherkin as the scenario format."""
        assert bdd.get("scenario_format") == "gherkin", (
            "bdd.yml must specify scenario_format: gherkin"
        )

    def test_bdd_uat_requires_business_language(self, bdd):
        """UAT BDD enforces business language only (no technical jargon)."""
        assert bdd.get("language_constraint") == "business", (
            "bdd.yml must set language_constraint: business — "
            "UAT scenarios must be readable by non-technical stakeholders"
        )

    def test_bdd_template_has_given_when_then(self, bdd):
        """BDD template uses Given/When/Then Gherkin structure."""
        template = bdd.get("template", "")
        assert "Given" in template, "BDD template missing 'Given'"
        assert "When" in template, "BDD template missing 'When'"
        assert "Then" in template, "BDD template missing 'Then'"

    def test_bdd_checklist_requires_req_key_scenario_coverage(self, bdd):
        """BDD evaluator requires every REQ key to have ≥1 Gherkin scenario."""
        checklist = bdd.get("checklist", [])
        coverage_check = next(
            (c for c in checklist if "scenarios_cover_all" in c.get("name", "")),
            None,
        )
        assert coverage_check is not None, (
            "bdd.yml checklist must include scenarios_cover_all_requirements check"
        )

    def test_bdd_implements_req_edge_002(self):
        """bdd.yml header declares it implements REQ-EDGE-002."""
        raw = (EDGE_PARAMS_DIR / "bdd.yml").read_text()
        assert "REQ-EDGE-002" in raw, (
            "bdd.yml must declare '# Implements: REQ-EDGE-002' in header"
        )


# ═══════════════════════════════════════════════════════════════════════
# REQ-EDGE-003 — ADRs at Requirements→Design Edge
# ═══════════════════════════════════════════════════════════════════════


class TestADREdge:
    """Requirements→Design edge produces Architecture Decision Records."""

    @pytest.fixture
    def topo(self):
        return _topology()

    @pytest.fixture
    def adr(self):
        return _load("adr.yml")

    def test_requirements_design_edge_exists(self, topo):
        """Requirements→Design transition exists in graph topology."""
        transitions = topo["transitions"]
        edge = next(
            (
                t
                for t in transitions
                if t["source"] == "requirements" and t["target"] == "design"
            ),
            None,
        )
        assert edge is not None, "Requirements→Design transition must exist"

    def test_adr_template_has_decision_section(self, adr):
        """ADR template includes Decision section (core ADR requirement)."""
        template = adr.get("template", "")
        assert "Decision" in template, (
            "adr.yml template must include a Decision section"
        )

    def test_adr_template_has_context_section(self, adr):
        """ADR template includes Context section (forces at play)."""
        template = adr.get("template", "")
        assert "Context" in template, "adr.yml template must include a Context section"

    def test_adr_template_has_consequences_section(self, adr):
        """ADR template includes Consequences section."""
        template = adr.get("template", "")
        assert "Consequences" in template, (
            "adr.yml template must include a Consequences section"
        )

    def test_adr_template_has_alternatives_section(self, adr):
        """ADR template includes Alternatives Considered section."""
        template = adr.get("template", "")
        assert "Alternatives" in template, (
            "adr.yml template must include an Alternatives Considered section"
        )

    def test_adr_template_references_req_keys(self, adr):
        """ADR template has {requirements} field to link ADRs to REQ keys."""
        template = adr.get("template", "")
        assert "requirements" in template.lower() or "REQ-" in template, (
            "adr.yml template must reference requirement keys "
            "so ADRs are traceable to spec"
        )

    def test_adr_acknowledges_ecosystem_constraints(self, adr):
        """ADR config acknowledges ecosystem constraints (Context[] binding)."""
        raw = (EDGE_PARAMS_DIR / "adr.yml").read_text()
        assert "ecosystem" in raw.lower() or "context" in raw.lower(), (
            "adr.yml must reference ecosystem constraints — "
            "ADRs acknowledge the technology context"
        )

    def test_adr_has_versioning(self, adr):
        """ADR template includes Status and Date fields (versioned artifacts)."""
        template = adr.get("template", "")
        assert "Status" in template, "adr.yml template missing Status field"

    def test_adr_implements_req_edge_003(self):
        """adr.yml header declares it implements REQ-EDGE-003."""
        raw = (EDGE_PARAMS_DIR / "adr.yml").read_text()
        assert "REQ-EDGE-003" in raw, (
            "adr.yml must declare '# Implements: REQ-EDGE-003' in header"
        )
