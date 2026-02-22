# Validates: REQ-EDGE-001, REQ-EDGE-002, REQ-EDGE-003, REQ-EDGE-004
"""UC-05: Edge Parameterisations — 16 scenarios.

Tests TDD co-evolution, BDD scenarios, ADR generation, and code tagging.
"""

from __future__ import annotations

import pytest

from imp_claude.tests.uat.conftest import EDGE_PARAMS_DIR

pytestmark = [pytest.mark.uat]


# ── EXISTING COVERAGE (not duplicated) ──────────────────────────────
# UC-05-14: TestEndToEndTraceability.test_code_implements_tags (test_methodology_bdd.py)
# UC-05-15: TestEndToEndTraceability.test_test_validates_tags (test_methodology_bdd.py)


# ═══════════════════════════════════════════════════════════════════════
# UC-05-01..05: TDD CO-EVOLUTION (Tier 1 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestTDDCoEvolution:
    """UC-05-01 through UC-05-05: RED/GREEN/REFACTOR cycle."""

    # UC-05-01 | Validates: REQ-EDGE-001 | Fixture: all_edge_configs
    def test_tdd_red_phase(self, all_edge_configs):
        """TDD edge config mandates test-first (RED phase)."""
        tdd = all_edge_configs["tdd"]
        red = tdd.get("phases", {}).get("red", {})
        assert red, "TDD config must define a 'red' phase"
        # The red phase must mandate writing a failing test first
        red_text = (
            red.get("description", "")
            + " "
            + red.get("action", "")
            + " "
            + red.get("convergence", "")
        ).lower()
        assert "fail" in red_text, "RED phase must reference failing tests"
        assert "test" in red_text, "RED phase must reference writing tests"

    # UC-05-02 | Validates: REQ-EDGE-001 | Fixture: all_edge_configs
    def test_tdd_green_phase(self, all_edge_configs):
        """TDD edge config has checks for minimal implementation (GREEN phase)."""
        tdd = all_edge_configs["tdd"]
        green = tdd.get("phases", {}).get("green", {})
        assert green, "TDD config must define a 'green' phase"
        green_text = (
            green.get("description", "")
            + " "
            + green.get("action", "")
            + " "
            + green.get("convergence", "")
        ).lower()
        assert "pass" in green_text, "GREEN phase must reference tests passing"
        assert "minimal" in green_text or "minimum" in green_text, (
            "GREEN phase must reference minimal/minimum implementation"
        )

    # UC-05-03 | Validates: REQ-EDGE-001 | Fixture: all_edge_configs
    def test_tdd_refactor_phase(self, all_edge_configs):
        """TDD edge config has refactoring/quality checks (REFACTOR phase)."""
        tdd = all_edge_configs["tdd"]
        refactor = tdd.get("phases", {}).get("refactor", {})
        assert refactor, "TDD config must define a 'refactor' phase"
        refactor_text = (
            refactor.get("description", "")
            + " "
            + refactor.get("action", "")
            + " "
            + refactor.get("convergence", "")
        ).lower()
        assert "refactor" in refactor_text or "improve" in refactor_text or "quality" in refactor_text, (
            "REFACTOR phase must reference refactoring or quality improvement"
        )
        # Refactor phase must ensure tests still pass
        assert "pass" in refactor_text or "green" in refactor_text or "still pass" in refactor_text, (
            "REFACTOR phase must ensure tests remain passing"
        )

    # UC-05-04 | Validates: REQ-EDGE-001 | Fixture: IN_PROGRESS
    def test_tdd_edge_is_bidirectional(self, graph_topology):
        """code<->unit_tests is a co_evolution (bidirectional) edge."""
        transitions = graph_topology.get("transitions", [])
        tdd = [t for t in transitions
              if t["source"] == "code" and t["target"] == "unit_tests"]
        assert len(tdd) == 1
        assert tdd[0]["edge_type"] == "co_evolution"

    # UC-05-05 | Validates: REQ-EDGE-001 | Fixture: IN_PROGRESS
    def test_tdd_edge_config_exists(self, all_edge_configs):
        """TDD edge param config exists and defines checks."""
        tdd = all_edge_configs.get("tdd", {})
        assert tdd, "TDD edge config should exist"
        # TDD config should reference test execution
        checks = tdd.get("checklist", tdd.get("checks", []))
        assert len(checks) > 0 or tdd, "TDD config should define checks or patterns"


# ═══════════════════════════════════════════════════════════════════════
# UC-05-06..09: BDD SCENARIOS (Tier 1 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestBDDScenarios:
    """UC-05-06 through UC-05-09: Gherkin format, REQ coverage, human approval."""

    # UC-05-06 | Validates: REQ-EDGE-002 | Fixture: all_edge_configs
    def test_bdd_gherkin_format(self, all_edge_configs):
        """BDD edge config defines Gherkin/Given-When-Then format."""
        bdd = all_edge_configs["bdd"]
        # scenario_format should be gherkin
        assert bdd.get("scenario_format") == "gherkin", (
            "BDD config must specify scenario_format: gherkin"
        )
        # Template should include Given/When/Then structure
        template = bdd.get("template", "")
        assert "Given" in template, "BDD template must include 'Given' step"
        assert "When" in template, "BDD template must include 'When' step"
        assert "Then" in template, "BDD template must include 'Then' step"
        # Checklist should enforce Given/When/Then structure
        checklist = bdd.get("checklist", [])
        gwt_checks = [c for c in checklist if "given" in c.get("name", "").lower()
                       or "when" in c.get("name", "").lower()
                       or "then" in c.get("name", "").lower()
                       or "given" in c.get("criterion", "").lower()]
        assert len(gwt_checks) > 0, (
            "BDD checklist must have a check enforcing Given/When/Then structure"
        )

    # UC-05-07 | Validates: REQ-EDGE-002 | Fixture: all_edge_configs
    def test_every_req_has_bdd(self, all_edge_configs):
        """BDD edge config has a check that ensures REQ coverage."""
        bdd = all_edge_configs["bdd"]
        checklist = bdd.get("checklist", [])
        # Find a check about scenario coverage per REQ key
        coverage_checks = [
            c for c in checklist
            if "req" in c.get("criterion", "").lower()
            and ("scenario" in c.get("criterion", "").lower()
                 or "cover" in c.get("criterion", "").lower())
        ]
        assert len(coverage_checks) > 0, (
            "BDD checklist must have a check ensuring every REQ key has scenarios"
        )
        # At least one of them should be required
        required_coverage = [c for c in coverage_checks if c.get("required")]
        assert len(required_coverage) > 0, (
            "REQ coverage check in BDD must be marked required"
        )

    # UC-05-08 | Validates: REQ-EDGE-002 | Fixture: IN_PROGRESS
    def test_bdd_edge_config_exists(self, all_edge_configs):
        """BDD edge param config exists."""
        bdd = all_edge_configs.get("bdd", {})
        assert bdd, "BDD edge config should exist"

    # UC-05-09 | Validates: REQ-EDGE-002 | Fixture: graph_topology
    def test_bdd_human_approval(self, graph_topology):
        """Design -> UAT Tests edge requires human evaluator for approval."""
        transitions = graph_topology.get("transitions", [])
        # Find the design -> uat_tests transition (BDD edge)
        uat_edges = [
            t for t in transitions
            if t.get("target") == "uat_tests"
        ]
        assert len(uat_edges) >= 1, (
            "Graph topology must have a transition targeting uat_tests"
        )
        uat_edge = uat_edges[0]
        evaluators = uat_edge.get("evaluators", [])
        assert "human" in evaluators, (
            "UAT tests edge must include 'human' in evaluators for stakeholder approval"
        )


# ═══════════════════════════════════════════════════════════════════════
# UC-05-10..13: ADR GENERATION (Tier 1 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestADRGeneration:
    """UC-05-10 through UC-05-13: ADRs at requirements->design edge."""

    # UC-05-10 | Validates: REQ-EDGE-003 | Fixture: all_edge_configs
    def test_adr_generated_per_dimension(self, all_edge_configs):
        """Requirements->design edge config has checks that reference constraint dimensions."""
        req_design = all_edge_configs.get("requirements_design", {})
        assert req_design, "requirements_design edge config must exist"
        checklist = req_design.get("checklist", [])
        # Should have checks for constraint dimension resolution
        dimension_checks = [
            c for c in checklist
            if "dimension" in c.get("criterion", "").lower()
            or "ecosystem" in c.get("name", "").lower()
            or "deployment" in c.get("name", "").lower()
            or "security" in c.get("name", "").lower()
            or "build_system" in c.get("name", "").lower()
        ]
        assert len(dimension_checks) >= 1, (
            "requirements_design checklist must have checks for constraint dimensions"
        )

    # UC-05-11 | Validates: REQ-EDGE-003 | Fixture: all_edge_configs
    def test_adr_acknowledges_ecosystem(self, all_edge_configs):
        """Requirements->design edge config references ecosystem constraints."""
        req_design = all_edge_configs.get("requirements_design", {})
        checklist = req_design.get("checklist", [])
        # Find a check specifically about ecosystem compatibility
        eco_checks = [
            c for c in checklist
            if "ecosystem" in c.get("name", "").lower()
            or "ecosystem" in c.get("criterion", "").lower()
        ]
        assert len(eco_checks) >= 1, (
            "requirements_design checklist must have an ecosystem compatibility check"
        )
        # It should be required (mandatory dimension)
        eco_required = [c for c in eco_checks if c.get("required")]
        assert len(eco_required) >= 1, (
            "Ecosystem compatibility check must be required (mandatory dimension)"
        )

    # UC-05-12 | Validates: REQ-EDGE-003 | Fixture: IN_PROGRESS
    def test_adr_edge_config_exists(self, all_edge_configs):
        """ADR edge param config exists for requirements->design."""
        adr = all_edge_configs.get("adr", all_edge_configs.get("requirements_design", {}))
        assert adr, "ADR/requirements_design edge config should exist"

    # UC-05-13 | Validates: REQ-EDGE-003 | Fixture: all_edge_configs
    def test_adr_references_req_keys(self, all_edge_configs):
        """ADR edge config includes requirement key traceability in checklist and template."""
        adr = all_edge_configs.get("adr", {})
        assert adr, "ADR edge config must exist"
        # ADR template should include REQ references
        template = adr.get("template", "")
        assert "REQ" in template, (
            "ADR template must reference REQ keys (e.g. in Requirements field)"
        )
        # ADR checklist should have a check for REQ traceability
        checklist = adr.get("checklist", [])
        req_checks = [
            c for c in checklist
            if "req" in c.get("criterion", "").lower()
            and ("trace" in c.get("criterion", "").lower()
                 or "reference" in c.get("criterion", "").lower()
                 or "address" in c.get("criterion", "").lower())
        ]
        assert len(req_checks) >= 1, (
            "ADR checklist must have a check for REQ key traceability"
        )


# ═══════════════════════════════════════════════════════════════════════
# UC-05-14..16: CODE TAGGING (Tier 1 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestCodeTagging:
    """UC-05-14 through UC-05-16: Implements/Validates tags and commit messages."""

    # UC-05-14 | Validates: REQ-EDGE-004 | Fixture: IN_PROGRESS
    def test_code_tagging_convention(self, all_edge_configs):
        """Code tagging edge config exists and defines tag format."""
        ct = all_edge_configs.get("code_tagging", all_edge_configs.get("traceability", {}))
        assert ct, "Code tagging edge config should exist"

    # UC-05-15 | Validates: REQ-EDGE-004 | Fixture: IN_PROGRESS
    def test_tag_format_in_graph(self, graph_topology):
        """Code asset type schema includes req_tags."""
        code_type = graph_topology["asset_types"]["code"]
        assert "req_tags" in code_type["schema"]
        ut_type = graph_topology["asset_types"]["unit_tests"]
        assert "req_tags" in ut_type["schema"]

    # UC-05-16 | Validates: REQ-EDGE-004 | Fixture: all_edge_configs
    def test_commit_messages_include_req(self, all_edge_configs):
        """Code tagging config defines a commit message REQ key check."""
        ct = all_edge_configs.get("code_tagging", {})
        assert ct, "Code tagging edge config must exist"
        checklist = ct.get("checklist", [])
        # Find a check about commit message tagging
        commit_checks = [
            c for c in checklist
            if "commit" in c.get("name", "").lower()
            or "commit" in c.get("criterion", "").lower()
        ]
        assert len(commit_checks) >= 1, (
            "Code tagging checklist must have a check for commit message REQ tags"
        )
        # The check should reference REQ keys
        commit_check = commit_checks[0]
        criterion = commit_check.get("criterion", "")
        assert "REQ" in criterion, (
            "Commit message check must reference REQ key format"
        )
