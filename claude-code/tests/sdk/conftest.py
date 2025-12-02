#!/usr/bin/env python3
"""
Pytest configuration for Claude Agent SDK tests.

# Implements: REQ-NFR-TEST-001 (Automated Testing)
"""

import pytest
import asyncio
from pathlib import Path

# Test project directory
TEST_PROJECT = Path(__file__).parent / "test-project"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_project(tmp_path_factory):
    """Create a temporary test project with AISDLC plugin."""
    project = tmp_path_factory.mktemp("test-project")

    # Create .claude/settings.json to load plugin
    claude_dir = project / ".claude"
    claude_dir.mkdir()

    settings = {
        "extraKnownMarketplaces": {
            "aisdlc": {
                "source": {
                    "source": "github",
                    "repo": "foolishimp/ai_sdlc_method"
                }
            }
        },
        "enabledPlugins": {
            "aisdlc-methodology@aisdlc": True
        }
    }

    import json
    (claude_dir / "settings.json").write_text(json.dumps(settings, indent=2))

    # Create minimal CLAUDE.md
    (project / "CLAUDE.md").write_text("# Test Project\nUsing AISDLC methodology.")

    return project


@pytest.fixture
def aisdlc_options(test_project):
    """Configure Claude Agent SDK options for AISDLC testing."""
    from claude_agent_sdk import ClaudeAgentOptions

    return ClaudeAgentOptions(
        cwd=str(test_project),
        allowed_tools=["Read", "Write", "Bash", "Grep", "Glob"],
        permission_mode="acceptEdits",
        max_turns=10,
    )
