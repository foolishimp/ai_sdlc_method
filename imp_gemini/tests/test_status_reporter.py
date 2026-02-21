# Validates: REQ-F-BOOT-003
import pytest
from imp_gemini.code.status import main
from imp_gemini.code.internal.state_machine import StateManager, ProjectState
from unittest.mock import patch, MagicMock

def test_status_output_in_progress(capsys):
    # Arrange
    with patch('imp_gemini.code.status.StateManager') as MockMgr:
        instance = MockMgr.return_value
        instance.get_current_state.return_value = ProjectState.IN_PROGRESS
        instance.get_active_features.return_value = [
            {
                "feature": "REQ-F-TEST-001",
                "trajectory": {
                    "requirements": {"status": "converged"},
                    "design": {"status": "iterating"},
                    "code": {"status": "pending"},
                    "unit_tests": {"status": "pending"}
                }
            }
        ]
        
        # Act
        main()
        
        # Assert
        captured = capsys.readouterr()
        assert "State: IN_PROGRESS" in captured.out
        assert "REQ-F-TEST-001" in captured.out
        assert "req ✓" in captured.out
        assert "design ●" in captured.out
        assert "code ○" in captured.out
