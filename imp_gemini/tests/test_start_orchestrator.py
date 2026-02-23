# Validates: REQ-F-BOOT-002
import pytest
from imp_gemini.code.start import main
from imp_gemini.code.internal.state_machine import StateManager, ProjectState
from unittest.mock import patch, MagicMock

def test_start_delegates_to_init_when_uninitialised(capsys):
    # Arrange
    with patch('imp_gemini.code.start.StateManager') as MockMgr:
        instance = MockMgr.return_value
        instance.get_current_state.return_value = ProjectState.UNINITIALISED
        
        # Act
        main()
        
        # Assert
        captured = capsys.readouterr()
        assert "Starting Progressive Init..." in captured.out

def test_start_orchestrates_iteration_when_in_progress(capsys):
    # Arrange
    with patch('imp_gemini.code.start.StateManager') as MockMgr:
        instance = MockMgr.return_value
        instance.get_current_state.return_value = ProjectState.IN_PROGRESS
        instance.get_next_actionable_feature.return_value = {
            "feature": "REQ-F-AUTH-001",
            "title": "User authentication",
            "trajectory": {"requirements": {"status": "converged"}}
        }
        instance.get_next_edge.return_value = "requirements→design"
        
        # Act
        main()
        
        # Assert
        captured = capsys.readouterr()
        assert "Feature: REQ-F-AUTH-001 \"User authentication\"" in captured.out
        assert "Next Edge: requirements→design" in captured.out
        assert "Delegating to /gen-iterate --edge \"requirements→design\"" in captured.out
