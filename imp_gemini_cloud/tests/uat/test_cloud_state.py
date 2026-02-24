import pytest
from imp_gemini_cloud.code.internal.cloud_state import WorkspaceState, ProjectState

def test_detect_state_uninitialised():
    ws = WorkspaceState(tenant_id="t1", project_id="p1", db=None, mock_data={})
    assert ws.detect_state() == ProjectState.UNINITIALISED

def test_detect_state_stuck():
    mock = {
        "events": [
            {"event_type": "iteration_completed", "feature": "F1", "edge": "E1", "delta": 5},
            {"event_type": "iteration_completed", "feature": "F1", "edge": "E1", "delta": 5},
            {"event_type": "iteration_completed", "feature": "F1", "edge": "E1", "delta": 5}
        ]
    }
    ws = WorkspaceState(tenant_id="t1", project_id="p1", db=None, mock_data=mock)
    assert ws.detect_state() == ProjectState.STUCK

def test_detect_state_converged():
    mock = {
        "events": [{"event_type": "edge_converged"}],
        "features": [{"feature": "F1", "status": "converged"}]
    }
    ws = WorkspaceState(tenant_id="t1", project_id="p1", db=None, mock_data=mock)
    assert ws.detect_state() == ProjectState.ALL_CONVERGED
