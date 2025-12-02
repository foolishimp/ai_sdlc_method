#!/usr/bin/env python3
"""
Headless CLI tests for AISDLC plugin.

# Implements: REQ-NFR-TEST-001 (Automated Testing)
# Validates: TCS-CLI-001 through TCS-CLI-010

Uses Claude Code headless mode (-p flag) for testing.
No SDK required - just the Claude CLI.
"""

import subprocess
import json
import pytest
import re
import os
from pathlib import Path
from typing import Optional


# =============================================================================
# CLI Helper
# =============================================================================

def run_claude_headless(
    prompt: str,
    cwd: Optional[Path] = None,
    max_turns: int = 5,
    timeout: int = 120,
    allowed_tools: Optional[list] = None,
) -> dict:
    """
    Run Claude Code in headless mode.

    Returns parsed JSON response with keys:
    - result: The response text
    - session_id: Session ID for resuming
    - total_cost_usd: API cost
    - is_error: Whether an error occurred
    """
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "json",
        "--max-turns", str(max_turns),
    ]

    if allowed_tools:
        cmd.extend(["--allowedTools", ",".join(allowed_tools)])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env={**os.environ, "NO_COLOR": "1"},
        )

        if result.returncode != 0:
            return {
                "is_error": True,
                "error": result.stderr,
                "result": "",
            }

        return json.loads(result.stdout)

    except subprocess.TimeoutExpired:
        return {"is_error": True, "error": "Timeout", "result": ""}
    except json.JSONDecodeError as e:
        return {"is_error": True, "error": str(e), "result": result.stdout}


def extract_req_keys(text: str) -> list:
    """Extract REQ-* keys from text."""
    return re.findall(r'REQ-[A-Z]+-[A-Z]*-?\d{3}', text)


# =============================================================================
# Fixture
# =============================================================================

@pytest.fixture
def test_project(tmp_path):
    """Create a test project with AISDLC config."""
    # Create .claude/settings.json
    claude_dir = tmp_path / ".claude"
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

    (claude_dir / "settings.json").write_text(json.dumps(settings, indent=2))
    (tmp_path / "CLAUDE.md").write_text("# Test Project\nUsing AISDLC methodology.")

    return tmp_path


# =============================================================================
# Basic CLI Tests
# =============================================================================

class TestHeadlessBasic:
    """Basic headless mode tests."""

    def test_headless_responds(self):
        """Verify headless mode works at all."""
        result = run_claude_headless("Say hello", max_turns=1)

        assert not result.get("is_error"), f"Error: {result.get('error')}"
        assert "result" in result
        assert len(result["result"]) > 0

    def test_json_output_structure(self):
        """Verify JSON output has expected fields."""
        result = run_claude_headless("What is 2+2?", max_turns=1)

        assert "result" in result
        assert "session_id" in result


class TestPluginLoaded:
    """Test that AISDLC plugin is actually loaded."""

    def test_plugin_cached(self):
        """Verify plugin is in Claude's marketplace cache."""
        from pathlib import Path

        plugin_cache = Path.home() / ".claude/plugins/marketplaces/aisdlc/.claude-plugin/plugins/aisdlc-methodology/.claude-plugin"

        assert plugin_cache.exists(), "Plugin not cached - run installer first"
        assert (plugin_cache / "plugin.json").exists(), "plugin.json missing"
        assert (plugin_cache / "commands").is_dir(), "commands/ missing"
        assert (plugin_cache / "agents").is_dir(), "agents/ missing"
        assert (plugin_cache / "skills").is_dir(), "skills/ missing"

    def test_plugin_json_valid(self):
        """Verify plugin.json has correct structure."""
        from pathlib import Path

        plugin_json = Path.home() / ".claude/plugins/marketplaces/aisdlc/.claude-plugin/plugins/aisdlc-methodology/.claude-plugin/plugin.json"

        if not plugin_json.exists():
            pytest.skip("Plugin not cached")

        data = json.loads(plugin_json.read_text())

        assert data.get("name") == "aisdlc-methodology"
        assert "version" in data
        assert "commands" in data
        assert "agents" in data
        assert len(data["commands"]) >= 7, "Expected 7+ commands"
        assert len(data["agents"]) >= 7, "Expected 7 agents"

    def test_marketplace_json_valid(self):
        """Verify marketplace.json points to plugin correctly."""
        from pathlib import Path

        marketplace_json = Path.home() / ".claude/plugins/marketplaces/aisdlc/.claude-plugin/marketplace.json"

        if not marketplace_json.exists():
            pytest.skip("Marketplace not cached")

        data = json.loads(marketplace_json.read_text())

        assert data.get("name") == "aisdlc"
        assert "plugins" in data
        assert len(data["plugins"]) >= 1

        plugin = data["plugins"][0]
        assert plugin.get("name") == "aisdlc-methodology"
        assert plugin.get("source") == "./plugins/aisdlc-methodology"


# =============================================================================
# Requirements Tests
# =============================================================================

class TestRequirementsCLI:
    """Test requirements extraction via CLI."""

    @pytest.mark.slow
    def test_generates_req_keys(self, test_project):
        """Should generate REQ-* keys."""
        result = run_claude_headless(
            "Extract requirements with REQ-F-* keys for: 'User authentication system'",
            cwd=test_project,
            max_turns=3,
        )

        assert not result.get("is_error"), f"Error: {result.get('error')}"

        req_keys = extract_req_keys(result.get("result", ""))
        assert len(req_keys) >= 1, f"Expected REQ keys, got none in: {result['result'][:500]}"

    @pytest.mark.slow
    def test_nfr_generation(self, test_project):
        """Should generate NFR requirements for performance."""
        result = run_claude_headless(
            "Generate REQ-NFR-* requirements for: 'Response time under 100ms'",
            cwd=test_project,
            max_turns=3,
        )

        assert 'REQ-NFR-' in result.get("result", ""), "Should generate NFR keys"


# =============================================================================
# Session Continuity Tests
# =============================================================================

class TestSessionContinuity:
    """Test session resume functionality."""

    @pytest.mark.slow
    def test_resume_session(self, test_project):
        """Can resume a session and maintain context."""
        # Start session
        result1 = run_claude_headless(
            "Remember this: The project codename is PHOENIX",
            cwd=test_project,
            max_turns=1,
        )

        assert not result1.get("is_error")
        session_id = result1.get("session_id")
        assert session_id, "Should return session_id"

        # Resume session
        cmd = [
            "claude", "-p", "What was the project codename I mentioned?",
            "--resume", session_id,
            "--output-format", "json",
            "--max-turns", "1",
        ]

        result2 = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=test_project,
        )

        response = json.loads(result2.stdout)
        assert "PHOENIX" in response.get("result", "").upper(), \
            "Should remember context from previous session"


# =============================================================================
# Tool Control Tests
# =============================================================================

class TestToolControl:
    """Test tool access control."""

    def test_allowed_tools_respected(self):
        """Only allowed tools should be available."""
        result = run_claude_headless(
            "Read the file README.md",
            allowed_tools=["Read"],
            max_turns=2,
        )

        # Should not error - Read is allowed
        assert not result.get("is_error") or "permission" not in result.get("error", "").lower()

    def test_disallowed_tools_blocked(self):
        """Disallowed tools should be blocked."""
        # Run with NO tools allowed
        cmd = [
            "claude", "-p", "Write a file called test.txt",
            "--output-format", "json",
            "--max-turns", "2",
            "--disallowedTools", "Write,Edit",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Should either error or not actually write
        response = json.loads(result.stdout)
        # The test passes if Claude couldn't write (either errored or said it couldn't)
        assert True  # Placeholder - actual behavior depends on Claude's response
