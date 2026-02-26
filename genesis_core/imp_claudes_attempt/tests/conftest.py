"""Test configuration for genesis_core/imp_claudes_attempt."""

import sys
from pathlib import Path

import pytest

# Add code/ to sys.path so genesis_engine is importable
CODE_DIR = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(CODE_DIR))

SPEC_DIR = Path(__file__).parent.parent.parent / "specification"
DESIGN_DIR = Path(__file__).parent.parent / "design"


@pytest.fixture
def tmp_workspace(tmp_path):
    """Create a minimal workspace structure for tests."""
    ws = tmp_path / ".ai-workspace"
    (ws / "events").mkdir(parents=True)
    (ws / "features" / "active").mkdir(parents=True)
    (ws / "graph").mkdir(parents=True)
    (ws / "profiles").mkdir(parents=True)
    (ws / "context").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def constraints():
    """Minimal constraints dict."""
    return {
        "project": {"name": "test-project", "language": "python"},
        "test": {"command": "echo ok", "threshold": "0.70"},
    }
