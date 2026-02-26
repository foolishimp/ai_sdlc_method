# Validates: REQ-CTX-001, REQ-CTX-002, REQ-INTENT-004
import pytest
from pathlib import Path
from gemini_cli.engine.config_loader import ConfigLoader

def test_hierarchical_loading(tmp_path, monkeypatch):
    loader = ConfigLoader(tmp_path)
    base = {"a": 1, "b": {"c": 2}}
    update = {"b": {"d": 3}, "e": 4}
    
    loader._deep_merge(base, update)
    assert base == {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}

def test_spec_hash_stability():
    loader = ConfigLoader(Path("."))
    loader.constraints = {"a": 1}
    
    h1 = loader.compute_spec_hash("intent v1")
    h2 = loader.compute_spec_hash("intent v1")
    h3 = loader.compute_spec_hash("intent v2")
    
    assert h1 == h2
    assert h1 != h3
