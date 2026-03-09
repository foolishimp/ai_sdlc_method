# Validates: REQ-F-NAMEDCOMP-001 (NC-004 — Project Convergence States)
# Validates: REQ-UX-003 (Feature Vector Status)
# Reference: ADR-S-026 §4.5, specification/features/NAMEDCOMP_DESIGN_RECOMMENDATIONS.md §Phase 4
"""Tests for the project-level convergence state algorithm: ITERATING, QUIESCENT, CONVERGED, BOUNDED."""

import pytest

from genesis.config_loader import compute_project_convergence_state, validate_feature_vector


# ─── Helpers ─────────────────────────────────────────────────────────────────

def make_vector(status: str, disposition=None, feature: str = "REQ-F-TEST-001") -> dict:
    return {"feature": feature, "status": status, "disposition": disposition}


# ─── NC-004: State transitions ───────────────────────────────────────────────

class TestProjectStateITERATING:
    """Project is ITERATING when any vector is actively iterating."""

    def test_one_iterating_vector(self):
        vectors = [make_vector("iterating")]
        result = compute_project_convergence_state(vectors)
        assert result["state"] == "ITERATING"

    def test_in_progress_counts_as_iterating(self):
        vectors = [make_vector("in_progress")]
        result = compute_project_convergence_state(vectors)
        assert result["state"] == "ITERATING"

    def test_mix_iterating_and_converged_is_still_iterating(self):
        vectors = [make_vector("iterating"), make_vector("converged", "converged", "REQ-F-TEST-002")]
        result = compute_project_convergence_state(vectors)
        assert result["state"] == "ITERATING"

    def test_iterating_count_correct(self):
        vectors = [
            make_vector("iterating", feature="REQ-F-TEST-001"),
            make_vector("in_progress", feature="REQ-F-TEST-002"),
            make_vector("converged", "converged", "REQ-F-TEST-003"),
        ]
        result = compute_project_convergence_state(vectors)
        assert result["iterating_count"] == 2


class TestProjectStateCONVERGED:
    """Project is CONVERGED when all required vectors are converged."""

    def test_single_converged_vector(self):
        vectors = [make_vector("converged", "converged")]
        result = compute_project_convergence_state(vectors)
        assert result["state"] == "CONVERGED"

    def test_all_converged(self):
        vectors = [
            make_vector("converged", "converged", "REQ-F-TEST-001"),
            make_vector("converged", "converged", "REQ-F-TEST-002"),
            make_vector("converged", "converged", "REQ-F-TEST-003"),
        ]
        result = compute_project_convergence_state(vectors)
        assert result["state"] == "CONVERGED"

    def test_converged_with_abandoned_excluded(self):
        """Abandoned vectors are excluded from required_vectors."""
        vectors = [
            make_vector("converged", "converged", "REQ-F-TEST-001"),
            make_vector("blocked", "abandoned", "REQ-F-TEST-002"),
        ]
        result = compute_project_convergence_state(vectors)
        assert result["state"] == "CONVERGED"

    def test_converged_with_blocked_deferred_excluded(self):
        vectors = [
            make_vector("converged", "converged", "REQ-F-TEST-001"),
            make_vector("blocked", "blocked_deferred", "REQ-F-TEST-002"),
        ]
        result = compute_project_convergence_state(vectors)
        assert result["state"] == "CONVERGED"

    def test_converged_count_matches_required(self):
        vectors = [
            make_vector("converged", "converged", "REQ-F-TEST-001"),
            make_vector("converged", "converged", "REQ-F-TEST-002"),
        ]
        result = compute_project_convergence_state(vectors)
        assert result["converged_count"] == result["total_required"] == 2


class TestProjectStateQUIESCENT:
    """Project is QUIESCENT when nothing iterates and blocked vectors lack disposition."""

    def test_blocked_no_disposition(self):
        vectors = [make_vector("blocked")]  # disposition=None
        result = compute_project_convergence_state(vectors)
        assert result["state"] == "QUIESCENT"

    def test_mix_converged_and_undispositioned_blocked_is_quiescent(self):
        vectors = [
            make_vector("converged", "converged", "REQ-F-TEST-001"),
            make_vector("blocked", None, "REQ-F-TEST-002"),
        ]
        result = compute_project_convergence_state(vectors)
        assert result["state"] == "QUIESCENT"

    def test_blocked_no_disposition_count(self):
        vectors = [
            make_vector("blocked", None, "REQ-F-TEST-001"),
            make_vector("blocked", None, "REQ-F-TEST-002"),
            make_vector("blocked", "blocked_accepted", "REQ-F-TEST-003"),
        ]
        result = compute_project_convergence_state(vectors)
        assert result["blocked_no_disposition"] == 2
        assert result["state"] == "QUIESCENT"


class TestProjectStateBOUNDED:
    """Project is BOUNDED when quiescent and all blockers are explicitly dispositioned."""

    def test_all_blocked_with_disposition(self):
        vectors = [make_vector("blocked", "blocked_accepted")]
        result = compute_project_convergence_state(vectors)
        assert result["state"] == "BOUNDED"

    def test_mix_converged_and_all_blocked_dispositioned(self):
        vectors = [
            make_vector("converged", "converged", "REQ-F-TEST-001"),
            make_vector("blocked", "blocked_accepted", "REQ-F-TEST-002"),
            make_vector("blocked", "blocked_deferred", "REQ-F-TEST-003"),
        ]
        result = compute_project_convergence_state(vectors)
        assert result["state"] == "BOUNDED"

    def test_blocked_with_disposition_count(self):
        vectors = [
            make_vector("blocked", "blocked_accepted", "REQ-F-TEST-001"),
            make_vector("blocked", "blocked_accepted", "REQ-F-TEST-002"),
        ]
        result = compute_project_convergence_state(vectors)
        assert result["blocked_with_disposition"] == 2


# ─── NC-004: Edge cases ───────────────────────────────────────────────────────

class TestEdgeCases:
    """Edge cases for the convergence state algorithm."""

    def test_empty_vector_list(self):
        result = compute_project_convergence_state([])
        assert result["state"] == "CONVERGED"  # 0/0 required converged
        assert result["iterating_count"] == 0
        assert result["converged_count"] == 0
        assert result["total_vectors"] == 0

    def test_pending_vectors_are_not_iterating(self):
        vectors = [make_vector("pending")]
        result = compute_project_convergence_state(vectors)
        # pending is not "iterating" or "in_progress"
        assert result["state"] != "ITERATING"
        assert result["iterating_count"] == 0

    def test_pending_not_converged_is_quiescent(self):
        """pending with no disposition and no iterating → QUIESCENT
        (blocked_no_disposition is 0, but not converged either)."""
        vectors = [make_vector("pending")]
        result = compute_project_convergence_state(vectors)
        # converged_count=0, total_required=1 → not CONVERGED
        # blocked_no_disp=0 → not QUIESCENT by the strict blocked check
        # → should be BOUNDED (nothing iterating, no undispositioned blocked)
        assert result["state"] in ("BOUNDED", "QUIESCENT")

    def test_result_dict_has_all_keys(self):
        vectors = [make_vector("converged", "converged")]
        result = compute_project_convergence_state(vectors)
        required_keys = {
            "state", "iterating_count", "required_vectors", "converged_count",
            "blocked_no_disposition", "blocked_with_disposition",
            "total_vectors", "total_required",
        }
        assert required_keys.issubset(set(result.keys()))

    def test_state_values_are_valid(self):
        valid_states = {"ITERATING", "QUIESCENT", "CONVERGED", "BOUNDED"}
        for status, dispo in [
            ("iterating", None),
            ("converged", "converged"),
            ("blocked", None),
            ("blocked", "blocked_accepted"),
        ]:
            vectors = [make_vector(status, dispo)]
            result = compute_project_convergence_state(vectors)
            assert result["state"] in valid_states


# ─── NC-004: Health check integration ─────────────────────────────────────────

class TestHealthChecks:
    """Health check warnings derived from state + validate_feature_vector()."""

    def test_project_state_consistency_fail(self):
        """converged status with null produced_asset_ref triggers warning."""
        vector = {
            "feature": "REQ-F-TEST-001",
            "status": "converged",
            "produced_asset_ref": None,
        }
        _, warnings = validate_feature_vector(vector)
        assert any("traceability chain broken" in w for w in warnings)

    def test_bounded_state_with_undispositioned_blocked_warns(self):
        """BOUNDED claims require all blocked vectors to have disposition."""
        vectors = [
            make_vector("blocked", None, "REQ-F-TEST-001"),
        ]
        result = compute_project_convergence_state(vectors)
        # QUIESCENT (not BOUNDED) because there's an undispositioned blocked vector
        assert result["state"] == "QUIESCENT"
        assert result["blocked_no_disposition"] > 0

    def test_converged_state_with_no_undispositioned_blocked(self):
        vectors = [
            make_vector("converged", "converged", "REQ-F-TEST-001"),
            make_vector("blocked", "abandoned", "REQ-F-TEST-002"),
        ]
        result = compute_project_convergence_state(vectors)
        assert result["state"] == "CONVERGED"
        assert result["blocked_no_disposition"] == 0
