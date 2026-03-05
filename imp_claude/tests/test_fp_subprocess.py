# Validates: REQ-ROBUST-001 (Actor Isolation), REQ-ROBUST-002 (Supervisor Pattern)
"""Tests for fp_subprocess — Claude transport adapter (env sanitization + run_claude_isolated).

fp_subprocess is a thin adapter over proc.run_bounded(). These tests cover:
  - clean_env(): Claude nesting guard removal
  - run_claude_isolated(): adapter contract (delegates to run_bounded)

Process kill and stall detection are tested in test_proc.py (the total-function primitive).
"""

import os
from unittest.mock import patch

import pytest

from genesis.fp_subprocess import (
    SubprocessResult,
    _NESTING_GUARD_VARS,
    clean_env,
    run_claude_isolated,
)
from genesis.proc import BoundedResult


# ── clean_env tests ───────────────────────────────────────────────────────────


class TestCleanEnv:
    """Validates: REQ-ROBUST-001 — environment sanitization."""

    def test_strips_nesting_guards(self):
        """Nesting guard vars are removed from the environment."""
        with patch.dict(
            os.environ,
            {"CLAUDECODE": "1", "CLAUDE_CODE_SSE_PORT": "9999", "OTHER": "keep"},
        ):
            env = clean_env()
            assert "CLAUDECODE" not in env
            assert "CLAUDE_CODE_SSE_PORT" not in env
            assert "CLAUDE_CODE_ENTRYPOINT" not in env
            assert env["OTHER"] == "keep"

    def test_preserves_other_vars(self):
        """Non-guard environment variables pass through unchanged."""
        with patch.dict(os.environ, {"PATH": "/usr/bin", "HOME": "/home/test"}, clear=True):
            env = clean_env()
            assert env["PATH"] == "/usr/bin"
            assert env["HOME"] == "/home/test"

    def test_missing_guards_no_error(self):
        """If nesting guards aren't set, clean_env succeeds silently."""
        with patch.dict(os.environ, {"PATH": "/usr/bin"}, clear=True):
            env = clean_env()
            assert "CLAUDECODE" not in env
            assert "PATH" in env

    def test_all_guard_vars_known(self):
        """The guard var set matches expected vars."""
        assert _NESTING_GUARD_VARS == frozenset(
            ["CLAUDECODE", "CLAUDE_CODE_SSE_PORT", "CLAUDE_CODE_ENTRYPOINT"]
        )


# ── run_claude_isolated tests ─────────────────────────────────────────────────


def _bounded(
    stdout="", stderr="", returncode=0,
    timed_out=False, stall_killed=False, wall_killed=False,
    duration_ms=10, pid=12345, error="",
) -> BoundedResult:
    """Helper: build a BoundedResult for patching run_bounded."""
    r = BoundedResult(
        stdout=stdout, stderr=stderr, returncode=returncode,
        timed_out=timed_out, stall_killed=stall_killed, wall_killed=wall_killed,
        duration_ms=duration_ms, pid=pid, error=error,
    )
    return r


class TestRunClaudeIsolated:
    """Validates: REQ-ROBUST-001, REQ-ROBUST-002.

    Patches proc.run_bounded — the total-function primitive — so tests are
    fast and deterministic without spawning real subprocesses.
    """

    @patch("genesis.fp_subprocess.run_bounded")
    def test_success(self, mock_run):
        """Successful call returns stdout and zero exit code."""
        mock_run.return_value = _bounded(stdout="hello world", returncode=0, pid=12345)

        result = run_claude_isolated(["claude", "-p", "hi"], timeout=10)

        assert isinstance(result, SubprocessResult)
        assert result.stdout == "hello world"
        assert result.returncode == 0
        assert result.timed_out is False
        assert result.stall_killed is False
        assert result.error == ""
        assert result.pid == 12345

    @patch("genesis.fp_subprocess.run_bounded")
    def test_nonzero_exit(self, mock_run):
        """Nonzero exit code is captured."""
        mock_run.return_value = _bounded(
            stderr="error output", returncode=1, error="Exit code 1"
        )

        result = run_claude_isolated(["claude", "-p", "hi"], timeout=10)

        assert result.returncode == 1
        assert result.timed_out is False
        assert result.stderr == "error output"

    @patch("genesis.fp_subprocess.run_bounded")
    def test_wall_timeout(self, mock_run):
        """Wall timeout is reflected in timed_out flag."""
        mock_run.return_value = _bounded(
            returncode=-1, timed_out=True, wall_killed=True,
            error="Wall timeout: 10s exceeded"
        )

        result = run_claude_isolated(["claude", "-p", "hi"], timeout=10)

        assert result.timed_out is True
        assert result.stall_killed is False

    @patch("genesis.fp_subprocess.run_bounded")
    def test_stall_killed(self, mock_run):
        """Stall kill is reflected in stall_killed flag."""
        mock_run.return_value = _bounded(
            returncode=-1, timed_out=True, stall_killed=True,
            error="Stall: no output for 30s"
        )

        result = run_claude_isolated(["claude", "--print", "hi"], timeout=120, stall_timeout=30)

        assert result.timed_out is True
        assert result.stall_killed is True

    @patch("genesis.fp_subprocess.run_bounded")
    def test_env_sanitized_by_default(self, mock_run):
        """By default, sanitized env is passed to run_bounded."""
        mock_run.return_value = _bounded()

        with patch.dict(os.environ, {"CLAUDECODE": "1"}):
            run_claude_isolated(["claude"], timeout=10)

        _, kwargs = mock_run.call_args
        assert kwargs["env"] is not None
        assert "CLAUDECODE" not in kwargs["env"]

    @patch("genesis.fp_subprocess.run_bounded")
    def test_env_not_sanitized_when_disabled(self, mock_run):
        """When sanitize_env=False, env=None is passed (inherit)."""
        mock_run.return_value = _bounded()

        run_claude_isolated(["claude"], timeout=10, sanitize_env=False)

        _, kwargs = mock_run.call_args
        assert kwargs["env"] is None

    @patch("genesis.fp_subprocess.run_bounded")
    def test_timeout_forwarded(self, mock_run):
        """timeout and stall_timeout are forwarded to run_bounded."""
        mock_run.return_value = _bounded()

        run_claude_isolated(["claude"], timeout=45, stall_timeout=20)

        _, kwargs = mock_run.call_args
        assert kwargs["wall_timeout"] == 45.0
        assert kwargs["stall_timeout"] == 20.0
