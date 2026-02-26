# Validates: REQ-TOOL-001, REQ-TOOL-002, REQ-TOOL-009
import pytest
from genesis_core.internal.workspace_state import compute_feature_view, compute_aggregated_view

pytestmark = [pytest.mark.uat]

class TestDeveloperWorkspace:
    def test_workspace_directories(self, initialized_workspace):
        ws = initialized_workspace / ".ai-workspace"
        required = ["graph", "features/active", "events", "profiles"]
        for d in required:
            assert (ws / d).exists()

class TestFeatureViews:
    def test_per_req_feature_view(self, in_progress_workspace):
        view = compute_feature_view(in_progress_workspace / ".ai-workspace", "REQ-F-ALPHA-001")
        assert view["feature"] == "REQ-F-ALPHA-001"
        assert view["status"] == "in_progress"
        assert "requirements" in view["edges"]
        assert view["edges"]["requirements"]["status"] == "converged"

    def test_aggregated_feature_view(self, in_progress_workspace):
        agg = compute_aggregated_view(in_progress_workspace / ".ai-workspace")
        assert agg["total"] == 1
        assert agg["in_progress"] == 1
        assert agg["edges_total"] > 0
