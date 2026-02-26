# Validates: REQ-ROBUST-001 (Actor Isolation), REQ-ROBUST-002 (Supervisor Pattern)
"""Tests for fp_subprocess — isolated F_P process manager."""

import os
import subprocess
import time
from unittest.mock import MagicMock, patch

import pytest

from genisis.fp_subprocess import (
    SubprocessResult,
    _NESTING_GUARD_VARS,
    _kill_process_group,
    clean_env,
    run_claude_isolated,
)


# ── clean_env tests ──────────────────────────────────────────────────


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


# ── run_claude_isolated tests ────────────────────────────────────────


class TestRunClaudeIsolated:
    """Validates: REQ-ROBUST-001, REQ-ROBUST-002."""

    @patch("genisis.fp_subprocess.subprocess.Popen")
    def test_success(self, mock_popen_cls):
        """Successful subprocess returns stdout and zero exit code."""
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        mock_proc.communicate.return_value = ("hello world", "")
        mock_proc.returncode = 0
        mock_proc.poll.return_value = 0
        mock_popen_cls.return_value = mock_proc

        result = run_claude_isolated(["echo", "hello"], timeout=10)

        assert isinstance(result, SubprocessResult)
        assert result.stdout == "hello world"
        assert result.returncode == 0
        assert result.timed_out is False
        assert result.stall_killed is False
        assert result.error == ""
        assert result.pid == 12345
        assert result.duration_ms >= 0

    @patch("genisis.fp_subprocess.subprocess.Popen")
    def test_nonzero_exit(self, mock_popen_cls):
        """Nonzero exit code is captured with error message."""
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        mock_proc.communicate.return_value = ("", "error output")
        mock_proc.returncode = 1
        mock_proc.poll.return_value = 1
        mock_popen_cls.return_value = mock_proc

        result = run_claude_isolated(["false"], timeout=10)

        assert result.returncode == 1
        assert result.timed_out is False
        assert "Exited with code 1" in result.error
        assert result.stderr == "error output"

    @patch("genisis.fp_subprocess.subprocess.Popen")
    def test_os_error(self, mock_popen_cls):
        """OSError on Popen returns error result without crashing."""
        mock_popen_cls.side_effect = OSError("No such file")

        result = run_claude_isolated(["nonexistent_binary"], timeout=10)

        assert result.returncode == -1
        assert "Failed to start subprocess" in result.error
        assert result.duration_ms >= 0

    @patch("genisis.fp_subprocess.subprocess.Popen")
    def test_timeout_kills_process(self, mock_popen_cls):
        """Wall timeout triggers process group kill and sets timed_out."""
        mock_proc = MagicMock()
        mock_proc.pid = 12345

        # Simulate a hanging process: poll returns None initially, then 0 after kill
        poll_results = [None] * 100 + [0]
        mock_proc.poll.side_effect = poll_results

        # communicate blocks, then returns after kill
        def slow_communicate():
            time.sleep(0.5)
            return ("partial", "")

        mock_proc.communicate.side_effect = slow_communicate
        mock_proc.returncode = -9
        mock_popen_cls.return_value = mock_proc

        with patch("genisis.fp_subprocess._kill_process_group") as mock_kill:
            result = run_claude_isolated(
                ["sleep", "999"], timeout=1, stall_timeout=0
            )

        assert result.timed_out is True
        assert result.duration_ms > 0

    @patch("genisis.fp_subprocess.subprocess.Popen")
    def test_start_new_session(self, mock_popen_cls):
        """Popen called with start_new_session=True for process group isolation."""
        mock_proc = MagicMock()
        mock_proc.pid = 1
        mock_proc.communicate.return_value = ("", "")
        mock_proc.returncode = 0
        mock_proc.poll.return_value = 0
        mock_popen_cls.return_value = mock_proc

        run_claude_isolated(["echo"], timeout=10)

        call_kwargs = mock_popen_cls.call_args[1]
        assert call_kwargs["start_new_session"] is True

    @patch("genisis.fp_subprocess.subprocess.Popen")
    def test_env_sanitized_by_default(self, mock_popen_cls):
        """By default, environment is sanitized (nesting guards removed)."""
        mock_proc = MagicMock()
        mock_proc.pid = 1
        mock_proc.communicate.return_value = ("", "")
        mock_proc.returncode = 0
        mock_proc.poll.return_value = 0
        mock_popen_cls.return_value = mock_proc

        with patch.dict(os.environ, {"CLAUDECODE": "1"}):
            run_claude_isolated(["echo"], timeout=10)

        call_kwargs = mock_popen_cls.call_args[1]
        assert "CLAUDECODE" not in call_kwargs["env"]

    @patch("genisis.fp_subprocess.subprocess.Popen")
    def test_env_not_sanitized_when_disabled(self, mock_popen_cls):
        """When sanitize_env=False, environment is passed as None (inherit)."""
        mock_proc = MagicMock()
        mock_proc.pid = 1
        mock_proc.communicate.return_value = ("", "")
        mock_proc.returncode = 0
        mock_proc.poll.return_value = 0
        mock_popen_cls.return_value = mock_proc

        run_claude_isolated(["echo"], timeout=10, sanitize_env=False)

        call_kwargs = mock_popen_cls.call_args[1]
        assert call_kwargs["env"] is None


# ── _kill_process_group tests ────────────────────────────────────────


class TestKillProcessGroup:
    """Validates: REQ-ROBUST-001 — process tree cleanup."""

    def test_kill_terminates_process(self):
        """SIGTERM kills the process group; falls back to proc.kill()."""
        mock_proc = MagicMock()
        mock_proc.pid = 99999
        # Simulate process already gone
        mock_proc.poll.return_value = None

        with patch("genisis.fp_subprocess.os.getpgid", side_effect=ProcessLookupError):
            _kill_process_group(mock_proc)
            mock_proc.kill.assert_called_once()

    def test_kill_handles_already_dead(self):
        """If process is already dead, no error raised."""
        mock_proc = MagicMock()
        mock_proc.pid = 99999
        mock_proc.kill.side_effect = ProcessLookupError

        with patch("genisis.fp_subprocess.os.getpgid", side_effect=ProcessLookupError):
            # Should not raise
            _kill_process_group(mock_proc)
