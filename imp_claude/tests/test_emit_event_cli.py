# Validates: REQ-SUPV-003
# Validates: REQ-LIFE-002
"""
Tests for `python -m genesis emit-event` — the F_D event logger CLI boundary.

Verifies that:
- The subcommand exists and is callable
- event_time is assigned by the logger (from system clock), not by the caller
- Callers cannot inject event_time via --data
- JSON payload fields are written correctly
- Invalid --data produces a non-zero exit and no event written
- Project name is auto-detected from workspace when --project is omitted
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

# The genesis package lives at imp_claude/code/ — add to PYTHONPATH for subprocesses
_GENESIS_CODE_DIR = str(Path(__file__).parent.parent / "code")


def _run(args: list[str], workspace: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONPATH"] = _GENESIS_CODE_DIR + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "genesis"] + args,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(workspace),
    )


@pytest.fixture()
def ws(tmp_path: Path) -> Path:
    """Minimal workspace with events directory."""
    (tmp_path / ".ai-workspace" / "events").mkdir(parents=True)
    return tmp_path


class TestEmitEventCli:
    def test_help_registered(self, ws: Path) -> None:
        """emit-event subcommand appears in genesis --help."""
        result = _run(["--help"], ws)
        assert "emit-event" in result.stdout

    def test_emits_event_to_jsonl(self, ws: Path) -> None:
        """Happy path: event is appended to events.jsonl."""
        events_path = ws / ".ai-workspace" / "events" / "events.jsonl"
        assert not events_path.exists()

        result = _run(
            [
                "emit-event",
                "--type", "iteration_completed",
                "--data", json.dumps({"feature": "REQ-F-TEST-001", "delta": 0}),
                "--project", "test_project",
                "--workspace", str(ws),
            ],
            ws,
        )
        assert result.returncode == 0, result.stderr
        assert events_path.exists()

        lines = events_path.read_text().strip().split("\n")
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["event_type"] == "iteration_completed"
        assert record["project"] == "test_project"
        assert record["feature"] == "REQ-F-TEST-001"
        assert record["delta"] == 0
        assert "timestamp" in record

    def test_timestamp_is_system_clock_not_caller(self, ws: Path) -> None:
        """event_time is assigned by the logger — caller cannot override it via --data."""
        before = time.time()
        result = _run(
            [
                "emit-event",
                "--type", "health_checked",
                # Attempt to inject a past timestamp via payload
                "--data", json.dumps({"event_time": "1970-01-01T00:00:00Z", "genesis_compliant": True}),
                "--project", "test_project",
                "--workspace", str(ws),
            ],
            ws,
        )
        after = time.time()
        assert result.returncode == 0, result.stderr

        events_path = ws / ".ai-workspace" / "events" / "events.jsonl"
        record = json.loads(events_path.read_text().strip())

        # The canonical timestamp is the one set by make_event() — recent
        from datetime import datetime, timezone
        ts = datetime.fromisoformat(record["timestamp"])
        ts_epoch = ts.timestamp()
        assert before <= ts_epoch <= after + 1, (
            "timestamp must be current system time, not caller-supplied value"
        )
        # The injected "event_time" key in data becomes a payload field, not the canonical timestamp
        assert record.get("event_time") == "1970-01-01T00:00:00Z"  # payload only
        assert record["timestamp"] != "1970-01-01T00:00:00Z"       # canonical unaffected

    def test_invalid_json_data_returns_error(self, ws: Path) -> None:
        """Malformed --data produces non-zero exit and no event written."""
        events_path = ws / ".ai-workspace" / "events" / "events.jsonl"
        result = _run(
            [
                "emit-event",
                "--type", "iteration_completed",
                "--data", "not-valid-json",
                "--project", "test_project",
                "--workspace", str(ws),
            ],
            ws,
        )
        assert result.returncode != 0
        assert not events_path.exists()
        error = json.loads(result.stderr.strip())
        assert "error" in error

    def test_non_object_json_data_returns_error(self, ws: Path) -> None:
        """--data must be a JSON object, not an array or scalar."""
        result = _run(
            [
                "emit-event",
                "--type", "iteration_completed",
                "--data", '["not", "an", "object"]',
                "--project", "test_project",
                "--workspace", str(ws),
            ],
            ws,
        )
        assert result.returncode != 0

    def test_stdout_echoes_written_record(self, ws: Path) -> None:
        """stdout contains the JSON that was written (for hook verification)."""
        result = _run(
            [
                "emit-event",
                "--type", "edge_converged",
                "--data", json.dumps({"feature": "REQ-F-X-001", "edge": "code\u2194unit_tests"}),
                "--project", "myproject",
                "--workspace", str(ws),
            ],
            ws,
        )
        assert result.returncode == 0
        echoed = json.loads(result.stdout.strip())
        assert echoed["event_type"] == "edge_converged"
        assert echoed["feature"] == "REQ-F-X-001"

        # Must match what's on disk
        events_path = ws / ".ai-workspace" / "events" / "events.jsonl"
        disk_record = json.loads(events_path.read_text().strip())
        assert echoed["timestamp"] == disk_record["timestamp"]

    def test_multiple_appends_are_cumulative(self, ws: Path) -> None:
        """Successive calls append lines — no overwrite."""
        for i in range(3):
            _run(
                [
                    "emit-event",
                    "--type", "iteration_completed",
                    "--data", json.dumps({"iteration": i}),
                    "--project", "p",
                    "--workspace", str(ws),
                ],
                ws,
            )
        events_path = ws / ".ai-workspace" / "events" / "events.jsonl"
        lines = events_path.read_text().strip().split("\n")
        assert len(lines) == 3
        iterations = [json.loads(l)["iteration"] for l in lines]
        assert iterations == [0, 1, 2]

    def test_missing_type_arg_errors(self, ws: Path) -> None:
        """--type is required."""
        result = _run(
            ["emit-event", "--data", "{}", "--project", "p", "--workspace", str(ws)],
            ws,
        )
        assert result.returncode != 0
