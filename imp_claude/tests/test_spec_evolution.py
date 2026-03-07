# Validates: REQ-EVOL-001 (Workspace Vectors Are Trajectory-Only)
# Validates: REQ-EVOL-DATA-001 (Forbidden Workspace Keys)
# Validates: REQ-EVOL-NFR-002 (Spec Hash Verification)
"""Tests for REQ-F-EVOL-001 Phase 1 implementation (ADR-030).

Covers EVOL-U1 (workspace schema enforcement) and EVOL-U3 (spec hash verification):
  - WorkspaceSchemaViolation raised on forbidden fields
  - All 5 forbidden keys trigger the exception
  - verify_spec_hashes() detects drift when spec file modified
  - verify_spec_hashes() clean path (no drift)
  - verify_genesis_compliance() includes spec_hash_consistency check
  - load_feature_vector() enforces schema at read time
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from genesis.contracts import WorkspaceSchemaViolation
from genesis.workspace_state import (
    FORBIDDEN_WORKSPACE_KEYS,
    load_feature_vector,
    verify_genesis_compliance,
    verify_spec_hashes,
)
from genesis.workspace_gradient import DELTA_SPEC_DRIFT


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_workspace(tmp_path: Path) -> Path:
    """Create a minimal .ai-workspace directory."""
    ws = tmp_path / ".ai-workspace"
    (ws / "events").mkdir(parents=True)
    (ws / "features" / "active").mkdir(parents=True)
    return tmp_path


def _write_spec_modified_event(
    workspace: Path,
    file_path: str,
    new_hash: str,
    timestamp: str = "2026-03-07T12:00:00Z",
) -> None:
    events_file = workspace / ".ai-workspace" / "events" / "events.jsonl"
    event = {
        "event_type": "spec_modified",
        "timestamp": timestamp,
        "project": "test",
        "data": {
            "file": file_path,
            "new_hash": new_hash,
            "summary": "test spec change",
        },
    }
    with open(events_file, "a") as f:
        f.write(json.dumps(event) + "\n")


def _sha256(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


# ── EVOL-U1: WorkspaceSchemaViolation ────────────────────────────────────────


class TestWorkspaceSchemaViolationException:
    def test_workspace_schema_violation_raised_on_forbidden_field(self, tmp_path):
        """WorkspaceSchemaViolation raised when 'satisfies' is present in workspace YAML."""
        vector_path = tmp_path / "REQ-F-TEST-001.yml"
        vector_path.write_text(yaml.dump({
            "feature": "REQ-F-TEST-001",
            "status": "iterating",
            "satisfies": ["REQ-TEST-001"],  # forbidden — belongs in spec
        }))

        with pytest.raises(WorkspaceSchemaViolation) as exc_info:
            load_feature_vector(vector_path)

        assert "satisfies" in str(exc_info.value)
        assert str(vector_path) in str(exc_info.value)

    def test_workspace_schema_violation_lists_field_name(self, tmp_path):
        """Exception message contains the exact offending field name."""
        vector_path = tmp_path / "REQ-F-TEST-001.yml"
        vector_path.write_text(yaml.dump({
            "feature": "REQ-F-TEST-001",
            "status": "iterating",
            "success_criteria": ["all tests pass"],  # forbidden
        }))

        with pytest.raises(WorkspaceSchemaViolation) as exc_info:
            load_feature_vector(vector_path)

        assert exc_info.value.field == "success_criteria"

    def test_workspace_schema_violation_all_forbidden_keys(self, tmp_path):
        """All 5 forbidden keys trigger WorkspaceSchemaViolation."""
        expected_keys = {"satisfies", "success_criteria", "dependencies", "what_converges", "phase"}
        assert expected_keys == FORBIDDEN_WORKSPACE_KEYS

        for key in FORBIDDEN_WORKSPACE_KEYS:
            vector_path = tmp_path / f"REQ-F-TEST-{key}.yml"
            vector_path.write_text(yaml.dump({
                "feature": "REQ-F-TEST-001",
                "status": "pending",
                key: "some value",
            }))

            with pytest.raises(WorkspaceSchemaViolation) as exc_info:
                load_feature_vector(vector_path)

            assert exc_info.value.field == key, f"Expected field={key!r}, got {exc_info.value.field!r}"

    def test_load_feature_vector_clean_passes(self, tmp_path):
        """A well-formed workspace YAML with no forbidden fields loads without error."""
        vector_path = tmp_path / "REQ-F-TEST-001.yml"
        data = {
            "feature": "REQ-F-TEST-001",
            "status": "iterating",
            "title": "Test feature",
            "trajectory": {"design": {"status": "converged"}},
        }
        vector_path.write_text(yaml.dump(data))

        result = load_feature_vector(vector_path)
        assert result["feature"] == "REQ-F-TEST-001"
        assert result["status"] == "iterating"


# ── EVOL-U3: Spec Hash Verification ──────────────────────────────────────────


class TestVerifySpecHashes:
    def test_spec_hash_verify_clean(self, tmp_path):
        """No drift reported when spec file matches the last spec_modified event hash."""
        workspace = _make_workspace(tmp_path)

        # Create a spec file
        spec_file = tmp_path / "specification" / "core" / "TEST.md"
        spec_file.parent.mkdir(parents=True)
        content = b"# Test Spec\n\nSome content here.\n"
        spec_file.write_bytes(content)

        # Record the correct hash in the event log
        file_path = "specification/core/TEST.md"
        _write_spec_modified_event(workspace, file_path, _sha256(content))

        drift = verify_spec_hashes(workspace)
        assert drift == [], f"Expected no drift, got: {drift}"

    def test_spec_hash_verify_detects_drift(self, tmp_path):
        """SPEC_DRIFT reported when spec file has been modified after the last event."""
        workspace = _make_workspace(tmp_path)

        # Create a spec file
        spec_file = tmp_path / "specification" / "core" / "TEST.md"
        spec_file.parent.mkdir(parents=True)
        original_content = b"# Test Spec\n\nOriginal content.\n"
        spec_file.write_bytes(original_content)

        # Record the hash of the ORIGINAL content
        file_path = "specification/core/TEST.md"
        _write_spec_modified_event(workspace, file_path, _sha256(original_content))

        # Now modify the file without recording a new event → drift
        spec_file.write_bytes(b"# Test Spec\n\nModified content - undocumented change.\n")

        drift = verify_spec_hashes(workspace)
        assert len(drift) == 1
        assert drift[0]["file"] == file_path
        assert drift[0]["expected_hash"] == _sha256(original_content)
        assert drift[0]["actual_hash"] != drift[0]["expected_hash"]

    def test_spec_hash_verify_no_events_returns_empty(self, tmp_path):
        """If no spec_modified events exist, no drift is reported (nothing tracked yet)."""
        workspace = _make_workspace(tmp_path)
        # Events file is empty — no spec_modified events

        drift = verify_spec_hashes(workspace)
        assert drift == []

    def test_spec_hash_verify_missing_file_is_drift(self, tmp_path):
        """A spec file referenced in the event log but deleted on disk is reported as drift."""
        workspace = _make_workspace(tmp_path)

        # Record an event for a file that doesn't exist
        file_path = "specification/core/DELETED.md"
        _write_spec_modified_event(workspace, file_path, "sha256:abc123")

        drift = verify_spec_hashes(workspace)
        assert len(drift) == 1
        assert drift[0]["actual_hash"] == "FILE_MISSING"


# ── EVOL-U3 + Health Checks: spec_hash_consistency ───────────────────────────


class TestHealthCheckSpecHashConsistency:
    def test_health_check_includes_spec_hash_consistency(self, tmp_path):
        """verify_genesis_compliance() includes a 'spec_hash_consistency' result."""
        workspace = _make_workspace(tmp_path)
        # Minimal CLAUDE.md to avoid bootloader check failure interfering
        (tmp_path / "CLAUDE.md").write_text("<!-- GENESIS_BOOTLOADER_START -->\n")

        compliance = verify_genesis_compliance(workspace)
        check_names = {r["name"] for r in compliance["results"]}
        assert "spec_hash_consistency" in check_names, (
            f"Expected 'spec_hash_consistency' in health check results. Got: {check_names}"
        )

    def test_health_check_spec_hash_consistency_passes_when_clean(self, tmp_path):
        """spec_hash_consistency passes when no drift exists."""
        workspace = _make_workspace(tmp_path)
        (tmp_path / "CLAUDE.md").write_text("<!-- GENESIS_BOOTLOADER_START -->\n")

        # No spec_modified events → nothing to drift from → pass
        compliance = verify_genesis_compliance(workspace)
        hash_check = next(r for r in compliance["results"] if r["name"] == "spec_hash_consistency")
        assert hash_check["status"] == "pass"

    def test_health_check_spec_hash_consistency_warns_on_drift(self, tmp_path):
        """spec_hash_consistency reports 'warn' when drift exists."""
        workspace = _make_workspace(tmp_path)
        (tmp_path / "CLAUDE.md").write_text("<!-- GENESIS_BOOTLOADER_START -->\n")

        # Create spec file and record hash
        spec_file = tmp_path / "specification" / "core" / "TEST.md"
        spec_file.parent.mkdir(parents=True)
        original = b"Original content.\n"
        spec_file.write_bytes(original)
        _write_spec_modified_event(
            workspace, "specification/core/TEST.md", _sha256(original)
        )

        # Modify the file without recording a new event
        spec_file.write_bytes(b"Modified content - undocumented.\n")

        compliance = verify_genesis_compliance(workspace)
        hash_check = next(r for r in compliance["results"] if r["name"] == "spec_hash_consistency")
        assert hash_check["status"] == "warn"
        assert "SPEC_DRIFT" in hash_check["description"]


# ── workspace_gradient: SPEC_DRIFT constant ───────────────────────────────────


class TestSpecDriftConstant:
    def test_delta_spec_drift_defined(self):
        """DELTA_SPEC_DRIFT is defined in workspace_gradient module."""
        assert DELTA_SPEC_DRIFT == "SPEC_DRIFT"
