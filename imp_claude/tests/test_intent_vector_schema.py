# Validates: REQ-F-NAMEDCOMP-001 (NC-002 — Intent Vector Schema Extension)
# Validates: REQ-FEAT-001 (Feature Vector Trajectories)
# Reference: ADR-S-026 §4.2–4.5, specification/features/NAMEDCOMP_DESIGN_RECOMMENDATIONS.md §Phase 2A
"""Tests for intent vector envelope fields: source_kind, trigger_event, target_asset_type,
produced_asset_ref, disposition, disposition_rationale."""

import pathlib

import pytest
import yaml

from genesis.config_loader import validate_feature_vector


PLUGIN_ROOT = pathlib.Path(__file__).parent.parent / "code" / ".claude-plugin" / "plugins" / "genesis"
TEMPLATE_FILE = PLUGIN_ROOT / "config" / "feature_vector_template.yml"


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def raw_template():
    with open(TEMPLATE_FILE) as f:
        return yaml.safe_load(f)


@pytest.fixture
def minimal_vector():
    """Minimal feature vector — only required fields."""
    return {
        "feature": "REQ-F-TEST-001",
        "title": "Test feature",
        "status": "pending",
        "vector_type": "feature",
        "profile": "standard",
    }


@pytest.fixture
def converged_vector():
    return {
        "feature": "REQ-F-TEST-001",
        "title": "Test feature",
        "status": "converged",
        "vector_type": "feature",
        "profile": "standard",
        "produced_asset_ref": "imp_claude/code/genesis/test_module.py",
        "disposition": "converged",
    }


# ─── P2A: Template has new fields ────────────────────────────────────────────

class TestTemplateHasEnvelopeFields:
    """feature_vector_template.yml includes the intent vector envelope fields."""

    def test_template_has_source_kind(self, raw_template):
        assert "source_kind" in raw_template

    def test_template_has_trigger_event(self, raw_template):
        assert "trigger_event" in raw_template

    def test_template_has_target_asset_type(self, raw_template):
        assert "target_asset_type" in raw_template

    def test_template_has_produced_asset_ref(self, raw_template):
        assert "produced_asset_ref" in raw_template

    def test_template_has_disposition(self, raw_template):
        assert "disposition" in raw_template

    def test_template_has_disposition_rationale(self, raw_template):
        assert "disposition_rationale" in raw_template

    def test_source_kind_default_is_parent_spawn(self, raw_template):
        assert raw_template["source_kind"] == "parent_spawn"

    def test_trigger_event_default_is_null(self, raw_template):
        assert raw_template["trigger_event"] is None

    def test_produced_asset_ref_default_is_null(self, raw_template):
        assert raw_template["produced_asset_ref"] is None

    def test_disposition_default_is_null(self, raw_template):
        assert raw_template["disposition"] is None


# ─── P2A: validate_feature_vector() defaults ─────────────────────────────────

class TestValidateFeatureVectorDefaults:
    """validate_feature_vector() adds defaults for missing optional fields."""

    def test_adds_source_kind_default(self, minimal_vector):
        validated, _ = validate_feature_vector(minimal_vector)
        assert validated["source_kind"] == "parent_spawn"

    def test_adds_trigger_event_default(self, minimal_vector):
        validated, _ = validate_feature_vector(minimal_vector)
        assert validated["trigger_event"] is None

    def test_adds_target_asset_type_default(self, minimal_vector):
        validated, _ = validate_feature_vector(minimal_vector)
        assert validated["target_asset_type"] is None

    def test_adds_produced_asset_ref_default(self, minimal_vector):
        validated, _ = validate_feature_vector(minimal_vector)
        assert validated["produced_asset_ref"] is None

    def test_adds_disposition_default(self, minimal_vector):
        validated, _ = validate_feature_vector(minimal_vector)
        assert validated["disposition"] is None

    def test_adds_disposition_rationale_default(self, minimal_vector):
        validated, _ = validate_feature_vector(minimal_vector)
        assert validated["disposition_rationale"] is None

    def test_does_not_overwrite_existing_source_kind(self):
        vector = {
            "feature": "REQ-F-TEST-001",
            "status": "pending",
            "source_kind": "gap_observation",
        }
        validated, _ = validate_feature_vector(vector)
        assert validated["source_kind"] == "gap_observation"

    def test_does_not_overwrite_existing_produced_asset_ref(self):
        vector = {
            "feature": "REQ-F-TEST-001",
            "status": "converged",
            "produced_asset_ref": "path/to/asset.py",
            "disposition": "converged",
        }
        validated, _ = validate_feature_vector(vector)
        assert validated["produced_asset_ref"] == "path/to/asset.py"

    def test_does_not_mutate_original_dict(self, minimal_vector):
        original_keys = set(minimal_vector.keys())
        validate_feature_vector(minimal_vector)
        assert set(minimal_vector.keys()) == original_keys


# ─── P2A: Convergence consistency warnings ────────────────────────────────────

class TestConvergenceConsistency:
    """validate_feature_vector() warns on traceability violations."""

    def test_converged_with_null_produced_asset_ref_warns(self):
        vector = {
            "feature": "REQ-F-TEST-001",
            "status": "converged",
            "produced_asset_ref": None,
        }
        _, warnings = validate_feature_vector(vector)
        assert any("traceability chain broken" in w for w in warnings)

    def test_converged_with_asset_ref_no_warning(self, converged_vector):
        _, warnings = validate_feature_vector(converged_vector)
        traceability_warns = [w for w in warnings if "traceability chain broken" in w]
        assert len(traceability_warns) == 0

    def test_pending_with_null_ref_no_warning(self, minimal_vector):
        _, warnings = validate_feature_vector(minimal_vector)
        traceability_warns = [w for w in warnings if "traceability chain broken" in w]
        assert len(traceability_warns) == 0

    def test_blocked_disposition_without_rationale_warns(self):
        vector = {
            "feature": "REQ-F-TEST-001",
            "status": "blocked",
            "disposition": "blocked_accepted",
            "disposition_rationale": None,
        }
        _, warnings = validate_feature_vector(vector)
        assert any("disposition_rationale" in w for w in warnings)

    def test_blocked_disposition_with_rationale_no_warning(self):
        vector = {
            "feature": "REQ-F-TEST-001",
            "status": "blocked",
            "disposition": "blocked_accepted",
            "disposition_rationale": "Accepted as known limitation",
        }
        _, warnings = validate_feature_vector(vector)
        disposition_warns = [w for w in warnings if "disposition_rationale" in w]
        assert len(disposition_warns) == 0

    def test_null_disposition_no_rationale_warning(self, minimal_vector):
        _, warnings = validate_feature_vector(minimal_vector)
        disposition_warns = [w for w in warnings if "disposition_rationale" in w]
        assert len(disposition_warns) == 0


# ─── P2A: source_kind validation ─────────────────────────────────────────────

class TestSourceKindValidation:
    """validate_feature_vector() warns on invalid source_kind values."""

    @pytest.mark.parametrize("valid_kind", ["abiogenesis", "parent_spawn", "gap_observation"])
    def test_valid_source_kinds_no_warning(self, valid_kind):
        vector = {"feature": "REQ-F-TEST-001", "status": "pending", "source_kind": valid_kind}
        _, warnings = validate_feature_vector(vector)
        kind_warns = [w for w in warnings if "source_kind" in w]
        assert len(kind_warns) == 0

    def test_invalid_source_kind_warns(self):
        vector = {"feature": "REQ-F-TEST-001", "status": "pending", "source_kind": "unknown_kind"}
        _, warnings = validate_feature_vector(vector)
        assert any("source_kind" in w for w in warnings)

    def test_returns_corrected_vector_even_with_warnings(self):
        vector = {"feature": "REQ-F-TEST-001", "status": "pending", "source_kind": "unknown_kind"}
        validated, warnings = validate_feature_vector(vector)
        assert isinstance(validated, dict)
        assert isinstance(warnings, list)
        assert len(warnings) > 0


# ─── P2A: No warnings on clean vectors ───────────────────────────────────────

class TestCleanVectorNoWarnings:
    """Clean vectors produce no warnings."""

    def test_minimal_vector_no_warnings(self, minimal_vector):
        _, warnings = validate_feature_vector(minimal_vector)
        assert warnings == []

    def test_converged_vector_with_asset_ref_no_warnings(self, converged_vector):
        _, warnings = validate_feature_vector(converged_vector)
        assert warnings == []

    def test_abiogenesis_vector_no_warnings(self):
        vector = {
            "feature": "REQ-F-ROOT-001",
            "status": "converged",
            "source_kind": "abiogenesis",
            "trigger_event": None,
            "produced_asset_ref": "specification/INTENT.md",
            "disposition": "converged",
        }
        _, warnings = validate_feature_vector(vector)
        assert warnings == []
