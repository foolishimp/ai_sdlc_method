# Validates: REQ-F-NAMEDCOMP-001 (NC-005 — PLAN Edge Parameter Template)
# Reference: ADR-S-026 §4.3, specification/features/NAMEDCOMP_DESIGN_RECOMMENDATIONS.md §Phase 2B
"""Tests for the PLAN edge parameter template and the `extends` composition contract."""

import pathlib

import pytest
import yaml


PLUGIN_ROOT = pathlib.Path(__file__).parent.parent / "code" / ".claude-plugin" / "plugins" / "genesis"
PLAN_TEMPLATE = PLUGIN_ROOT / "config" / "named_compositions" / "plan.yml"
EDGE_PARAMS_DIR = PLUGIN_ROOT / "config" / "edge_params"


@pytest.fixture
def plan_template():
    with open(PLAN_TEMPLATE) as f:
        return yaml.safe_load(f)


# ─── P2B: Template file schema ───────────────────────────────────────────────

class TestPlanTemplateSchema:
    """plan.yml exists and has the correct structure."""

    def test_file_exists(self):
        assert PLAN_TEMPLATE.exists(), "config/named_compositions/plan.yml must exist"

    def test_is_template_flagged(self, plan_template):
        assert plan_template.get("_template") is True

    def test_has_name(self, plan_template):
        assert plan_template.get("_name") == "PLAN"

    def test_has_version(self, plan_template):
        assert plan_template.get("_version") == "v1"

    def test_has_description(self, plan_template):
        assert isinstance(plan_template.get("description"), str)

    def test_has_convergence_criteria(self, plan_template):
        assert isinstance(plan_template.get("convergence_criteria"), list)
        assert len(plan_template["convergence_criteria"]) > 0

    def test_has_internal_events(self, plan_template):
        assert isinstance(plan_template.get("internal_events"), list)
        assert len(plan_template["internal_events"]) > 0

    def test_has_output_type(self, plan_template):
        assert plan_template.get("output_type") == "work_order"

    def test_has_output_schema(self, plan_template):
        schema = plan_template.get("output_schema", {})
        assert "required_fields" in schema
        assert "optional_fields" in schema


class TestPlanTemplateConvergenceCriteria:
    """plan.yml convergence_criteria has all required checks."""

    @pytest.fixture
    def check_names(self, plan_template):
        return {c["check"] for c in plan_template["convergence_criteria"]}

    def test_work_order_produced_check(self, check_names):
        assert "work_order_produced" in check_names

    def test_units_evaluated_check(self, check_names):
        assert "units_evaluated" in check_names

    def test_dep_dag_acyclic_check(self, check_names):
        assert "dep_dag_acyclic" in check_names

    def test_ranked_units_present_check(self, check_names):
        assert "ranked_units_present" in check_names

    def test_deferred_units_documented_check(self, check_names):
        assert "deferred_units_documented" in check_names

    def test_work_order_coherence_agent_check(self, check_names):
        assert "work_order_coherence" in check_names

    def test_human_approval_check(self, check_names):
        assert "human_approval" in check_names

    def test_deterministic_checks_have_required_true(self, plan_template):
        for check in plan_template["convergence_criteria"]:
            if check.get("type") == "deterministic":
                assert check.get("required") is True, f"{check['check']} should be required"

    def test_human_approval_check_type(self, plan_template):
        human_check = next(
            c for c in plan_template["convergence_criteria"] if c["check"] == "human_approval"
        )
        assert human_check["type"] == "human"


class TestPlanTemplateInternalEvents:
    """plan.yml internal events are all present with required fields."""

    @pytest.fixture
    def event_names(self, plan_template):
        return {e["event"] for e in plan_template["internal_events"]}

    def test_plan_decomposed_event(self, event_names):
        assert "plan_decomposed" in event_names

    def test_plan_evaluated_event(self, event_names):
        assert "plan_evaluated" in event_names

    def test_plan_ordered_event(self, event_names):
        assert "plan_ordered" in event_names

    def test_plan_ranked_event(self, event_names):
        assert "plan_ranked" in event_names

    def test_each_event_has_when_and_payload(self, plan_template):
        for event in plan_template["internal_events"]:
            assert "when" in event, f"Event {event.get('event')} missing 'when'"
            assert "payload" in event, f"Event {event.get('event')} missing 'payload'"


class TestPlanTemplateOutputSchema:
    """plan.yml output_schema has the correct required and optional fields."""

    def test_units_in_required(self, plan_template):
        schema = plan_template["output_schema"]
        assert "units" in schema["required_fields"]

    def test_dep_dag_in_required(self, plan_template):
        schema = plan_template["output_schema"]
        assert "dep_dag" in schema["required_fields"]

    def test_build_order_in_required(self, plan_template):
        schema = plan_template["output_schema"]
        assert "build_order" in schema["required_fields"]

    def test_ranked_units_in_required(self, plan_template):
        schema = plan_template["output_schema"]
        assert "ranked_units" in schema["required_fields"]

    def test_deferred_units_in_optional(self, plan_template):
        schema = plan_template["output_schema"]
        assert "deferred_units" in schema["optional_fields"]


# ─── P2B: Template directory layout ──────────────────────────────────────────

class TestNamedCompositionsDirectory:
    """config/named_compositions/ directory exists as the template home."""

    def test_directory_exists(self):
        nc_dir = PLUGIN_ROOT / "config" / "named_compositions"
        assert nc_dir.is_dir(), "config/named_compositions/ directory must exist"

    def test_plan_template_is_in_directory(self):
        plan_path = PLUGIN_ROOT / "config" / "named_compositions" / "plan.yml"
        assert plan_path.exists()

    def test_no_non_template_files_at_library_level(self):
        """Library template files should not be referenced directly from graph_topology."""
        nc_dir = PLUGIN_ROOT / "config" / "named_compositions"
        for yml_file in nc_dir.glob("*.yml"):
            data = yaml.safe_load(yml_file.open())
            # All files in this dir should have _template: true
            assert data.get("_template") is True, (
                f"{yml_file.name} should have _template: true — "
                "template files must not be referenced directly in graph_topology"
            )
