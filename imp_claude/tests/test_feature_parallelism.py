# Validates: REQ-COORD-004 (Markov-Aligned Parallelism)
"""Tests for feature_parallelism.py — inner product computation and agent routing."""

import pytest

from genesis.feature_parallelism import (
    compute_inner_product,
    compute_parallelism_matrix,
    find_orthogonal_groups,
    get_parallelism_advice,
    is_orthogonal,
    route_features_to_agents,
    shared_modules,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def feature_module_map():
    """Minimal feature → module mapping for tests."""
    return {
        "REQ-F-AUTH-001": ["auth.py", "models.py", "utils.py"],
        "REQ-F-API-001":  ["api.py",  "models.py"],
        "REQ-F-CLI-001":  ["cli.py",  "commands.py"],
        "REQ-F-ADMIN-001": ["admin.py", "models.py", "utils.py"],
        "REQ-F-EXPORT-001": ["export.py", "cli.py"],
    }


# ── compute_inner_product ─────────────────────────────────────────────────────


class TestComputeInnerProduct:
    def test_shared_one_module(self, feature_module_map: dict) -> None:
        # AUTH and API share models.py
        assert compute_inner_product("REQ-F-AUTH-001", "REQ-F-API-001", feature_module_map) == 1

    def test_shared_two_modules(self, feature_module_map: dict) -> None:
        # AUTH and ADMIN share models.py + utils.py
        assert compute_inner_product("REQ-F-AUTH-001", "REQ-F-ADMIN-001", feature_module_map) == 2

    def test_orthogonal_features(self, feature_module_map: dict) -> None:
        # AUTH and CLI share nothing
        assert compute_inner_product("REQ-F-AUTH-001", "REQ-F-CLI-001", feature_module_map) == 0

    def test_symmetric(self, feature_module_map: dict) -> None:
        # inner_product is symmetric
        assert (
            compute_inner_product("REQ-F-AUTH-001", "REQ-F-API-001", feature_module_map)
            == compute_inner_product("REQ-F-API-001", "REQ-F-AUTH-001", feature_module_map)
        )

    def test_feature_not_in_map_returns_zero(self, feature_module_map: dict) -> None:
        assert compute_inner_product("REQ-F-UNKNOWN", "REQ-F-AUTH-001", feature_module_map) == 0

    def test_both_absent_returns_zero(self) -> None:
        assert compute_inner_product("A", "B", {}) == 0

    def test_self_product_equals_module_count(self, feature_module_map: dict) -> None:
        # A feature's inner product with itself = its module count
        assert compute_inner_product("REQ-F-AUTH-001", "REQ-F-AUTH-001", feature_module_map) == 3


# ── is_orthogonal ─────────────────────────────────────────────────────────────


class TestIsOrthogonal:
    def test_orthogonal_features(self, feature_module_map: dict) -> None:
        assert is_orthogonal("REQ-F-AUTH-001", "REQ-F-CLI-001", feature_module_map)

    def test_non_orthogonal_features(self, feature_module_map: dict) -> None:
        assert not is_orthogonal("REQ-F-AUTH-001", "REQ-F-API-001", feature_module_map)

    def test_absent_feature_is_orthogonal(self, feature_module_map: dict) -> None:
        assert is_orthogonal("REQ-F-ABSENT", "REQ-F-AUTH-001", feature_module_map)


# ── shared_modules ────────────────────────────────────────────────────────────


class TestSharedModules:
    def test_returns_shared_modules(self, feature_module_map: dict) -> None:
        result = shared_modules("REQ-F-AUTH-001", "REQ-F-API-001", feature_module_map)
        assert result == ["models.py"]

    def test_multiple_shared_modules_sorted(self, feature_module_map: dict) -> None:
        result = shared_modules("REQ-F-AUTH-001", "REQ-F-ADMIN-001", feature_module_map)
        assert result == ["models.py", "utils.py"]

    def test_empty_when_orthogonal(self, feature_module_map: dict) -> None:
        assert shared_modules("REQ-F-AUTH-001", "REQ-F-CLI-001", feature_module_map) == []


# ── compute_parallelism_matrix ────────────────────────────────────────────────


class TestComputeParallelismMatrix:
    def test_returns_upper_triangle(self, feature_module_map: dict) -> None:
        features = ["REQ-F-AUTH-001", "REQ-F-API-001", "REQ-F-CLI-001"]
        matrix = compute_parallelism_matrix(features, feature_module_map)
        assert len(matrix) == 3  # n*(n-1)/2 = 3*2/2

    def test_auth_api_inner_product(self, feature_module_map: dict) -> None:
        features = ["REQ-F-AUTH-001", "REQ-F-API-001"]
        matrix = compute_parallelism_matrix(features, feature_module_map)
        assert matrix[("REQ-F-AUTH-001", "REQ-F-API-001")] == 1

    def test_orthogonal_pair_zero(self, feature_module_map: dict) -> None:
        features = ["REQ-F-AUTH-001", "REQ-F-CLI-001"]
        matrix = compute_parallelism_matrix(features, feature_module_map)
        assert matrix[("REQ-F-AUTH-001", "REQ-F-CLI-001")] == 0

    def test_empty_features_returns_empty(self) -> None:
        assert compute_parallelism_matrix([], {}) == {}


# ── find_orthogonal_groups ────────────────────────────────────────────────────


class TestFindOrthogonalGroups:
    def test_all_orthogonal_in_one_group(self) -> None:
        fmap = {
            "A": ["mod1.py"],
            "B": ["mod2.py"],
            "C": ["mod3.py"],
        }
        groups = find_orthogonal_groups(["A", "B", "C"], fmap)
        # All are orthogonal → one group
        assert len(groups) == 1
        assert sorted(groups[0]) == ["A", "B", "C"]

    def test_non_orthogonal_features_split_across_groups(self, feature_module_map: dict) -> None:
        # AUTH and API share models.py — cannot be in same parallel group
        groups = find_orthogonal_groups(["REQ-F-AUTH-001", "REQ-F-API-001"], feature_module_map)
        # Must be in different groups
        assert len(groups) == 2

    def test_groups_cover_all_features(self, feature_module_map: dict) -> None:
        features = list(feature_module_map.keys())
        groups = find_orthogonal_groups(features, feature_module_map)
        all_assigned = [f for group in groups for f in group]
        assert sorted(all_assigned) == sorted(features)

    def test_empty_features_returns_empty(self) -> None:
        assert find_orthogonal_groups([], {}) == []

    def test_single_feature_single_group(self) -> None:
        groups = find_orthogonal_groups(["A"], {"A": ["mod1.py"]})
        assert groups == [["A"]]


# ── get_parallelism_advice ────────────────────────────────────────────────────


class TestGetParallelismAdvice:
    def test_returns_advice_for_all_pairs(self, feature_module_map: dict) -> None:
        features = ["REQ-F-AUTH-001", "REQ-F-API-001", "REQ-F-CLI-001"]
        advice = get_parallelism_advice(features, feature_module_map)
        assert len(advice) == 3  # 3*2/2

    def test_orthogonal_pair_is_parallel_safe(self, feature_module_map: dict) -> None:
        advice = get_parallelism_advice(["REQ-F-AUTH-001", "REQ-F-CLI-001"], feature_module_map)
        assert len(advice) == 1
        assert advice[0]["advice"] == "parallel_safe"
        assert advice[0]["is_orthogonal"] is True
        assert "shared_modules" not in advice[0]

    def test_shared_pair_sequential_recommended(self, feature_module_map: dict) -> None:
        advice = get_parallelism_advice(["REQ-F-AUTH-001", "REQ-F-API-001"], feature_module_map)
        assert advice[0]["advice"] == "sequential_recommended"
        assert advice[0]["shared_modules"] == ["models.py"]
        assert advice[0]["inner_product"] == 1


# ── route_features_to_agents ──────────────────────────────────────────────────


class TestRouteFeaturesToAgents:
    def test_orthogonal_features_assigned_to_separate_agents(self) -> None:
        fmap = {"A": ["mod1.py"], "B": ["mod2.py"], "C": ["mod3.py"]}
        result = route_features_to_agents(["A", "B", "C"], ["agent-1", "agent-2"], fmap)
        # No warnings — all orthogonal
        assert result["warnings"] == []

    def test_all_features_assigned(self, feature_module_map: dict) -> None:
        features = list(feature_module_map.keys())
        result = route_features_to_agents(features, ["agent-1", "agent-2"], feature_module_map)
        assigned = [f for agent_feats in result["assignments"].values() for f in agent_feats]
        assert sorted(assigned) == sorted(features)

    def test_non_orthogonal_assignment_emits_warning(self, feature_module_map: dict) -> None:
        # Assign AUTH (shares models.py with API) and API to single agent
        fmap = {
            "REQ-F-AUTH-001": ["models.py"],
            "REQ-F-API-001": ["models.py"],
        }
        result = route_features_to_agents(
            ["REQ-F-AUTH-001", "REQ-F-API-001"], ["agent-1"], fmap
        )
        # One agent → both assigned → sharing modules → warning
        assert len(result["warnings"]) == 1
        w = result["warnings"][0]
        assert w["agent_id"] == "agent-1"
        assert "models.py" in w["shared_modules"]

    def test_empty_agents_returns_empty_assignments(self, feature_module_map: dict) -> None:
        result = route_features_to_agents(
            list(feature_module_map.keys()), [], feature_module_map
        )
        assert result["assignments"] == {}

    def test_empty_features_returns_empty_assignments(self, feature_module_map: dict) -> None:
        result = route_features_to_agents([], ["agent-1"], feature_module_map)
        assert result["assignments"]["agent-1"] == []

    def test_round_robin_with_more_groups_than_agents(self) -> None:
        # 3 groups, 2 agents → round-robin
        fmap = {"A": ["m1"], "B": ["m2"], "C": ["m3"]}  # all orthogonal → 1 group
        result = route_features_to_agents(["A", "B", "C"], ["ag1", "ag2"], fmap)
        all_assigned = sorted(
            [f for fs in result["assignments"].values() for f in fs]
        )
        assert all_assigned == ["A", "B", "C"]
