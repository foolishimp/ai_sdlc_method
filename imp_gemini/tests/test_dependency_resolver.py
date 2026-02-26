# Validates: REQ-FEAT-002
import pytest
from gemini_cli.engine.state import DependencyResolver

def test_dependency_resolution():
    events = [
        {"event_type": "feature_spawned", "feature": "CHILD", "data": {"parent": "PARENT"}}
    ]
    resolver = DependencyResolver(events)
    
    # Blocked if PARENT not converged
    assert resolver.is_blocked("CHILD", converged_features=[]) == True
    
    # Not blocked if PARENT converged
    assert resolver.is_blocked("CHILD", converged_features=["PARENT"]) == False
    
    # Unknown features are not blocked
    assert resolver.is_blocked("OTHER", converged_features=[]) == False
