# Validates: REQ-F-EVOL-001
# Validates: REQ-UX-006
# Validates: REQ-EVOL-003
# Validates: REQ-EVOL-005
"""
Tests for Consciousness Loop Stage 2+3.

Stage 2: Affect Triage — /gen-gaps emits feature_proposal events + writes PROP-NNN.yml
Stage 3: Human Gate — /gen-review-proposal approve/dismiss path

Tests cover:
  - ol_event.py: FeatureProposed / FeatureApproved / FeatureDismissed event types
  - Review queue YAML file structure (PROP-NNN.yml schema)
  - Proposal lifecycle: draft → approved → spec_modified
  - Proposal lifecycle: draft → dismissed → archived
"""

import json
import yaml
import pytest
from pathlib import Path


# ── OL event type mappings ────────────────────────────────────────────


class TestConsciousnessLoopOLEventTypes:
    """Validates that consciousness loop events map to correct OL event types."""

    def test_feature_proposed_maps_to_other(self):
        """FeatureProposed is an OTHER event — proposal is not terminal."""
        from genesis.ol_event import _OL_EVENT_TYPE

        assert "FeatureProposed" in _OL_EVENT_TYPE
        assert _OL_EVENT_TYPE["FeatureProposed"] == "OTHER"

    def test_feature_approved_maps_to_complete(self):
        """FeatureApproved is COMPLETE — human inflates workspace trajectory."""
        from genesis.ol_event import _OL_EVENT_TYPE

        assert "FeatureApproved" in _OL_EVENT_TYPE
        assert _OL_EVENT_TYPE["FeatureApproved"] == "COMPLETE"

    def test_feature_dismissed_maps_to_other(self):
        """FeatureDismissed is OTHER — dismissal is an archival action."""
        from genesis.ol_event import _OL_EVENT_TYPE

        assert "FeatureDismissed" in _OL_EVENT_TYPE
        assert _OL_EVENT_TYPE["FeatureDismissed"] == "OTHER"


# ── feature_proposed() constructor ───────────────────────────────────


class TestFeatureProposedConstructor:
    """Validates: FeatureProposed OL event construction (Stage 2 output)."""

    def test_feature_proposed_returns_ol_event(self):
        """feature_proposed() returns a valid OL event dict."""
        from genesis.ol_event import feature_proposed

        ev = feature_proposed(
            project="test-project",
            instance_id="inst-001",
            actor="gap_analysis",
            feature="REQ-F-AUTH-002",
            description="Add tests for user password reset",
        )

        assert ev["eventType"] == "OTHER"
        assert "run" in ev
        assert "job" in ev
        assert ev["producer"].endswith("ai_sdlc_method")

    def test_feature_proposed_job_name_is_propose_prefixed(self):
        """Job name is PROPOSE:{feature} for routing visibility."""
        from genesis.ol_event import feature_proposed

        ev = feature_proposed(
            project="test-project",
            instance_id="inst-001",
            actor="gap_analysis",
            feature="REQ-F-AUTH-002",
            description="Add tests",
        )

        assert ev["job"]["name"] == "PROPOSE:REQ-F-AUTH-002"

    def test_feature_proposed_payload_contains_feature_and_description(self):
        """Payload carries feature key and description."""
        from genesis.ol_event import feature_proposed

        ev = feature_proposed(
            project="test-project",
            instance_id="inst-001",
            actor="gap_analysis",
            feature="REQ-F-AUTH-002",
            description="Add tests for password reset endpoint",
        )

        payload = ev["run"]["facets"]["sdlc:payload"]
        assert payload["feature"] == "REQ-F-AUTH-002"
        assert payload["description"] == "Add tests for password reset endpoint"

    def test_feature_proposed_has_event_type_facet(self):
        """OL event carries sdlc:event_type facet with semantic type."""
        from genesis.ol_event import feature_proposed

        ev = feature_proposed(
            project="test-project",
            instance_id="inst-001",
            actor="gap_analysis",
            feature="REQ-F-AUTH-002",
            description="desc",
        )

        assert ev["run"]["facets"]["sdlc:event_type"]["type"] == "FeatureProposed"

    def test_feature_proposed_namespace_uses_project(self):
        """Job namespace is aisdlc://{project}."""
        from genesis.ol_event import feature_proposed

        ev = feature_proposed(
            project="my-service",
            instance_id="inst-001",
            actor="gap_analysis",
            feature="REQ-F-X-001",
            description="desc",
        )

        assert ev["job"]["namespace"] == "aisdlc://my-service"

    def test_feature_proposed_root_event_self_referential(self):
        """Root event (no causation_id) is self-referential."""
        from genesis.ol_event import feature_proposed

        ev = feature_proposed(
            project="test",
            instance_id="inst-001",
            actor="gap_analysis",
            feature="REQ-F-001",
            description="desc",
        )

        run_id = ev["run"]["runId"]
        facets = ev["run"]["facets"]["sdlc:universal"]
        assert facets["causation_id"] == run_id
        assert facets["correlation_id"] == run_id


# ── feature_approved() constructor ───────────────────────────────────


class TestFeatureApprovedConstructor:
    """Validates: FeatureApproved OL event construction (Stage 3 approval path)."""

    def test_feature_approved_returns_complete_event(self):
        """feature_approved() produces a COMPLETE OL event."""
        from genesis.ol_event import feature_approved

        ev = feature_approved(
            project="test-project",
            instance_id="inst-001",
            actor="human",
            feature="REQ-F-AUTH-002",
        )

        assert ev["eventType"] == "COMPLETE"

    def test_feature_approved_job_name_is_approve_prefixed(self):
        """Job name is APPROVE:{feature}."""
        from genesis.ol_event import feature_approved

        ev = feature_approved(
            project="test-project",
            instance_id="inst-001",
            actor="human",
            feature="REQ-F-AUTH-002",
        )

        assert ev["job"]["name"] == "APPROVE:REQ-F-AUTH-002"

    def test_feature_approved_payload_contains_feature(self):
        """Payload carries the feature key that was approved."""
        from genesis.ol_event import feature_approved

        ev = feature_approved(
            project="test-project",
            instance_id="inst-001",
            actor="human",
            feature="REQ-F-AUTH-002",
        )

        payload = ev["run"]["facets"]["sdlc:payload"]
        assert payload["feature"] == "REQ-F-AUTH-002"

    def test_feature_approved_actor_is_human(self):
        """Actor field records who approved (human gate)."""
        from genesis.ol_event import feature_approved

        ev = feature_approved(
            project="test",
            instance_id="inst-001",
            actor="human",
            feature="REQ-F-001",
        )

        assert ev["run"]["facets"]["sdlc:universal"]["actor"] == "human"


# ── feature_dismissed() constructor ──────────────────────────────────


class TestFeatureDismissedConstructor:
    """Validates: FeatureDismissed OL event construction (Stage 3 dismissal path)."""

    def test_feature_dismissed_returns_other_event(self):
        """feature_dismissed() produces an OTHER OL event."""
        from genesis.ol_event import feature_dismissed

        ev = feature_dismissed(
            project="test-project",
            instance_id="inst-001",
            actor="human",
            feature="REQ-F-AUTH-002",
            reason="covered by REQ-F-AUTH-004",
        )

        assert ev["eventType"] == "OTHER"

    def test_feature_dismissed_job_name_is_dismiss_prefixed(self):
        """Job name is DISMISS:{feature}."""
        from genesis.ol_event import feature_dismissed

        ev = feature_dismissed(
            project="test-project",
            instance_id="inst-001",
            actor="human",
            feature="REQ-F-AUTH-002",
            reason="duplicate",
        )

        assert ev["job"]["name"] == "DISMISS:REQ-F-AUTH-002"

    def test_feature_dismissed_payload_contains_feature_and_reason(self):
        """Payload carries both the feature key and the dismissal reason."""
        from genesis.ol_event import feature_dismissed

        ev = feature_dismissed(
            project="test-project",
            instance_id="inst-001",
            actor="human",
            feature="REQ-F-AUTH-002",
            reason="covered by REQ-F-AUTH-004",
        )

        payload = ev["run"]["facets"]["sdlc:payload"]
        assert payload["feature"] == "REQ-F-AUTH-002"
        assert payload["reason"] == "covered by REQ-F-AUTH-004"

    def test_feature_dismissed_has_event_type_facet(self):
        """sdlc:event_type facet carries FeatureDismissed."""
        from genesis.ol_event import feature_dismissed

        ev = feature_dismissed(
            project="test",
            instance_id="inst-001",
            actor="human",
            feature="REQ-F-001",
            reason="not needed",
        )

        assert ev["run"]["facets"]["sdlc:event_type"]["type"] == "FeatureDismissed"


# ── emit + persist round-trip ─────────────────────────────────────────


class TestConsciousnessLoopEmit:
    """Validates consciousness loop events survive emit → load round-trip."""

    def test_feature_proposed_emit_round_trip(self, tmp_path):
        """FeatureProposed event written to JSONL can be read back."""
        from genesis.ol_event import feature_proposed, emit_ol_event

        events_path = tmp_path / "events.jsonl"
        ev = feature_proposed(
            project="test",
            instance_id="inst-001",
            actor="gap_analysis",
            feature="REQ-F-AUTH-002",
            description="Add tests for password reset",
        )
        emit_ol_event(events_path, ev)

        lines = events_path.read_text().strip().splitlines()
        assert len(lines) == 1
        loaded = json.loads(lines[0])
        assert loaded["eventType"] == "OTHER"
        assert loaded["job"]["name"] == "PROPOSE:REQ-F-AUTH-002"

    def test_feature_approved_emit_round_trip(self, tmp_path):
        """FeatureApproved event written to JSONL can be read back."""
        from genesis.ol_event import feature_approved, emit_ol_event

        events_path = tmp_path / "events.jsonl"
        ev = feature_approved(
            project="test",
            instance_id="inst-001",
            actor="human",
            feature="REQ-F-AUTH-002",
        )
        emit_ol_event(events_path, ev)

        lines = events_path.read_text().strip().splitlines()
        assert len(lines) == 1
        loaded = json.loads(lines[0])
        assert loaded["eventType"] == "COMPLETE"
        assert loaded["job"]["name"] == "APPROVE:REQ-F-AUTH-002"

    def test_feature_dismissed_emit_round_trip(self, tmp_path):
        """FeatureDismissed event written to JSONL can be read back."""
        from genesis.ol_event import feature_dismissed, emit_ol_event

        events_path = tmp_path / "events.jsonl"
        ev = feature_dismissed(
            project="test",
            instance_id="inst-001",
            actor="human",
            feature="REQ-F-AUTH-002",
            reason="duplicate",
        )
        emit_ol_event(events_path, ev)

        lines = events_path.read_text().strip().splitlines()
        assert len(lines) == 1
        loaded = json.loads(lines[0])
        assert loaded["eventType"] == "OTHER"
        assert loaded["job"]["name"] == "DISMISS:REQ-F-AUTH-002"

    def test_proposal_lifecycle_events_sequence(self, tmp_path):
        """Full proposal lifecycle: proposed → approved sequence emits 2 events."""
        from genesis.ol_event import feature_proposed, feature_approved, emit_ol_event

        events_path = tmp_path / "events.jsonl"
        causation_id = None

        ev_proposed = feature_proposed(
            project="test",
            instance_id="inst-001",
            actor="gap_analysis",
            feature="REQ-F-AUTH-002",
            description="Add tests for password reset",
        )
        causation_id = ev_proposed["run"]["runId"]
        emit_ol_event(events_path, ev_proposed)

        ev_approved = feature_approved(
            project="test",
            instance_id="inst-001",
            actor="human",
            feature="REQ-F-AUTH-002",
            causation_id=causation_id,
            correlation_id=causation_id,
        )
        emit_ol_event(events_path, ev_approved)

        lines = events_path.read_text().strip().splitlines()
        assert len(lines) == 2

        proposed = json.loads(lines[0])
        approved = json.loads(lines[1])
        assert proposed["eventType"] == "OTHER"
        assert approved["eventType"] == "COMPLETE"

        # Causal chain is preserved
        approved_causation = approved["run"]["facets"]["sdlc:universal"]["causation_id"]
        assert approved_causation == causation_id


# ── Review queue YAML file schema ─────────────────────────────────────


class TestReviewQueueYAMLSchema:
    """Validates: PROP-NNN.yml structure for the review queue (Stage 2 output)."""

    def _make_proposal_yaml(self, tmp_path, proposal_id="PROP-001") -> Path:
        """Write a minimal valid PROP-NNN.yml to tmp_path."""
        reviews_dir = tmp_path / ".ai-workspace" / "reviews" / "pending"
        reviews_dir.mkdir(parents=True)
        proposal_path = reviews_dir / f"{proposal_id}.yml"

        proposal = {
            "proposal_id": proposal_id,
            "intent_id": "INT-001",
            "status": "draft",
            "severity": "high",
            "created": "2026-03-07T00:00:00Z",
            "source": "gap_analysis",
            "title": "Add tests for REQ-F-AUTH-002",
            "description": "No tests validate the password reset flow.",
            "affected_req_keys": ["REQ-F-AUTH-002", "REQ-F-AUTH-003"],
            "suggested_vector": {
                "feature": "REQ-F-AUTH-005",
                "title": "Password reset test coverage",
                "vector_type": "feature",
                "profile": "standard",
                "requirements": ["REQ-F-AUTH-002", "REQ-F-AUTH-003"],
            },
            "review_instructions": (
                "Approve: /gen-review-proposal --approve PROP-001\n"
                "Dismiss: /gen-review-proposal --dismiss PROP-001 --reason \"...\""
            ),
        }

        with open(proposal_path, "w") as f:
            yaml.dump(proposal, f, default_flow_style=False)

        return proposal_path

    def test_proposal_yaml_has_required_fields(self, tmp_path):
        """PROP-NNN.yml contains all required Stage 2 fields."""
        path = self._make_proposal_yaml(tmp_path)
        with open(path) as f:
            data = yaml.safe_load(f)

        required = [
            "proposal_id", "intent_id", "status", "severity", "created",
            "source", "title", "description", "affected_req_keys",
            "suggested_vector",
        ]
        for field in required:
            assert field in data, f"Missing required field: {field}"

    def test_proposal_yaml_status_is_draft(self, tmp_path):
        """New proposals have status: draft."""
        path = self._make_proposal_yaml(tmp_path)
        with open(path) as f:
            data = yaml.safe_load(f)
        assert data["status"] == "draft"

    def test_proposal_yaml_suggested_vector_has_feature_id(self, tmp_path):
        """suggested_vector contains a feature ID for workspace inflation."""
        path = self._make_proposal_yaml(tmp_path)
        with open(path) as f:
            data = yaml.safe_load(f)

        sv = data["suggested_vector"]
        assert "feature" in sv
        assert sv["feature"].startswith("REQ-F-")

    def test_proposal_yaml_severity_values(self, tmp_path):
        """Severity is one of: high, medium, low."""
        path = self._make_proposal_yaml(tmp_path)
        with open(path) as f:
            data = yaml.safe_load(f)
        assert data["severity"] in ("high", "medium", "low")

    def test_proposal_yaml_affected_req_keys_is_list(self, tmp_path):
        """affected_req_keys is a non-empty list of REQ-* strings."""
        path = self._make_proposal_yaml(tmp_path)
        with open(path) as f:
            data = yaml.safe_load(f)

        keys = data["affected_req_keys"]
        assert isinstance(keys, list)
        assert len(keys) > 0
        for k in keys:
            assert k.startswith("REQ-"), f"Invalid REQ key: {k}"

    def test_proposal_yaml_proposal_id_matches_filename(self, tmp_path):
        """proposal_id in YAML matches the filename (PROP-NNN consistency)."""
        path = self._make_proposal_yaml(tmp_path, "PROP-042")
        with open(path) as f:
            data = yaml.safe_load(f)
        assert data["proposal_id"] == "PROP-042"
        assert path.stem == "PROP-042"

    def test_approved_proposal_yaml_schema(self, tmp_path):
        """Approved proposal YAML has additional approved_at + feature_id fields."""
        pending_dir = tmp_path / ".ai-workspace" / "reviews" / "pending"
        approved_dir = tmp_path / ".ai-workspace" / "reviews" / "approved"
        approved_dir.mkdir(parents=True)
        pending_dir.mkdir(parents=True)

        # Write approved proposal
        approved_proposal = {
            "proposal_id": "PROP-001",
            "intent_id": "INT-001",
            "status": "approved",
            "severity": "high",
            "created": "2026-03-07T00:00:00Z",
            "approved_at": "2026-03-07T01:00:00Z",
            "feature_id": "REQ-F-AUTH-005",
            "source": "gap_analysis",
            "title": "Add tests for REQ-F-AUTH-002",
            "description": "No tests validate the password reset flow.",
            "affected_req_keys": ["REQ-F-AUTH-002"],
            "suggested_vector": {
                "feature": "REQ-F-AUTH-005",
                "title": "Password reset test coverage",
                "vector_type": "feature",
                "profile": "standard",
                "requirements": ["REQ-F-AUTH-002"],
            },
        }

        approved_path = approved_dir / "PROP-001.yml"
        with open(approved_path, "w") as f:
            yaml.dump(approved_proposal, f)

        with open(approved_path) as f:
            data = yaml.safe_load(f)

        assert data["status"] == "approved"
        assert "approved_at" in data
        assert "feature_id" in data
        assert data["feature_id"] == "REQ-F-AUTH-005"

    def test_dismissed_proposal_yaml_schema(self, tmp_path):
        """Dismissed proposal YAML has dismissed_at + dismissed_reason fields."""
        dismissed_dir = tmp_path / ".ai-workspace" / "reviews" / "dismissed"
        dismissed_dir.mkdir(parents=True)

        dismissed_proposal = {
            "proposal_id": "PROP-002",
            "intent_id": "INT-002",
            "status": "dismissed",
            "severity": "medium",
            "created": "2026-03-07T00:00:00Z",
            "dismissed_at": "2026-03-07T01:30:00Z",
            "dismissed_reason": "covered by REQ-F-AUTH-004",
            "source": "gap_analysis",
            "title": "Telemetry for REQ-F-DB-001",
            "description": "No observability for database operations.",
            "affected_req_keys": ["REQ-F-DB-001"],
            "suggested_vector": {
                "feature": "REQ-F-DB-005",
                "title": "Database telemetry",
                "vector_type": "feature",
                "profile": "standard",
                "requirements": ["REQ-F-DB-001"],
            },
        }

        dismissed_path = dismissed_dir / "PROP-002.yml"
        with open(dismissed_path, "w") as f:
            yaml.dump(dismissed_proposal, f)

        with open(dismissed_path) as f:
            data = yaml.safe_load(f)

        assert data["status"] == "dismissed"
        assert "dismissed_at" in data
        assert "dismissed_reason" in data
        assert data["dismissed_reason"] == "covered by REQ-F-AUTH-004"


# ── Review queue directory structure ─────────────────────────────────


class TestReviewQueueDirectoryStructure:
    """Validates: review queue directory layout for Stage 2+3."""

    def test_pending_directory_contains_prop_files(self, tmp_path):
        """Pending proposals live in .ai-workspace/reviews/pending/PROP-*.yml."""
        pending_dir = tmp_path / ".ai-workspace" / "reviews" / "pending"
        pending_dir.mkdir(parents=True)

        for i in range(1, 4):
            prop = {"proposal_id": f"PROP-{i:03d}", "status": "draft", "title": f"Proposal {i}"}
            with open(pending_dir / f"PROP-{i:03d}.yml", "w") as f:
                yaml.dump(prop, f)

        pending_files = list(pending_dir.glob("PROP-*.yml"))
        assert len(pending_files) == 3

    def test_review_queue_paths_match_spec(self, tmp_path):
        """Review queue uses 3 subdirs: pending / approved / dismissed."""
        for subdir in ("pending", "approved", "dismissed"):
            d = tmp_path / ".ai-workspace" / "reviews" / subdir
            d.mkdir(parents=True)
            assert d.is_dir()

    def test_proposal_move_pending_to_approved(self, tmp_path):
        """Moving a proposal from pending to approved simulates Stage 3 approve."""
        pending_dir = tmp_path / ".ai-workspace" / "reviews" / "pending"
        approved_dir = tmp_path / ".ai-workspace" / "reviews" / "approved"
        pending_dir.mkdir(parents=True)
        approved_dir.mkdir(parents=True)

        src = pending_dir / "PROP-001.yml"
        proposal = {
            "proposal_id": "PROP-001",
            "status": "draft",
            "title": "Test proposal",
        }
        with open(src, "w") as f:
            yaml.dump(proposal, f)

        # Simulate approve: update status + move
        proposal["status"] = "approved"
        proposal["approved_at"] = "2026-03-07T02:00:00Z"
        proposal["feature_id"] = "REQ-F-TEST-001"

        dst = approved_dir / "PROP-001.yml"
        with open(dst, "w") as f:
            yaml.dump(proposal, f)
        src.unlink()

        assert not src.exists()
        assert dst.exists()

        with open(dst) as f:
            data = yaml.safe_load(f)
        assert data["status"] == "approved"
        assert data["feature_id"] == "REQ-F-TEST-001"


# ── SpecModified event (REQ-EVOL-004) ────────────────────────────────


class TestSpecModifiedEvent:
    """Validates: spec_modified OL event (REQ-EVOL-004, ADR-S-010)."""

    def test_spec_modified_maps_to_complete(self):
        """SpecModified maps to COMPLETE — a terminal spec-change event."""
        from genesis.ol_event import _OL_EVENT_TYPE

        assert "SpecModified" in _OL_EVENT_TYPE
        assert _OL_EVENT_TYPE["SpecModified"] == "COMPLETE"

    def test_spec_modified_returns_complete_event(self):
        """spec_modified() produces a COMPLETE OL event."""
        from genesis.ol_event import spec_modified

        ev = spec_modified(
            project="test",
            instance_id="inst-001",
            actor="human",
            file="specification/features/FEATURE_VECTORS.md",
            what_changed="Added REQ-F-AUTH-005 feature vector",
            previous_hash="sha256:aabbcc",
            new_hash="sha256:ddeeff",
            trigger_event_id="PROP-001",
            trigger_type="feature_proposal",
        )
        assert ev["eventType"] == "COMPLETE"

    def test_spec_modified_job_name_is_spec_modified_prefixed(self):
        """Job name is SPEC_MODIFIED:{file} for tracing."""
        from genesis.ol_event import spec_modified

        ev = spec_modified(
            project="test",
            instance_id="inst-001",
            actor="human",
            file="specification/features/FEATURE_VECTORS.md",
            what_changed="Added feature",
            previous_hash="sha256:aabb",
            new_hash="sha256:ccdd",
            trigger_event_id="PROP-001",
            trigger_type="feature_proposal",
        )
        assert ev["job"]["name"] == "SPEC_MODIFIED:specification/features/FEATURE_VECTORS.md"

    def test_spec_modified_payload_has_all_required_fields(self):
        """Payload carries file, hashes, trigger_event_id, trigger_type (REQ-EVOL-004)."""
        from genesis.ol_event import spec_modified

        ev = spec_modified(
            project="test",
            instance_id="inst-001",
            actor="human",
            file="specification/features/FEATURE_VECTORS.md",
            what_changed="Added REQ-F-AUTH-005",
            previous_hash="sha256:aabb",
            new_hash="sha256:ccdd",
            trigger_event_id="PROP-001",
            trigger_type="feature_proposal",
        )
        payload = ev["run"]["facets"]["sdlc:payload"]
        assert payload["file"] == "specification/features/FEATURE_VECTORS.md"
        assert payload["what_changed"] == "Added REQ-F-AUTH-005"
        assert payload["previous_hash"] == "sha256:aabb"
        assert payload["new_hash"] == "sha256:ccdd"
        assert payload["trigger_event_id"] == "PROP-001"
        assert payload["trigger_type"] == "feature_proposal"

    def test_spec_modified_manual_trigger(self):
        """Manual edits use trigger_event_id='manual' and trigger_type='manual'."""
        from genesis.ol_event import spec_modified

        ev = spec_modified(
            project="test",
            instance_id="inst-001",
            actor="human",
            file="specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md",
            what_changed="Corrected §4.1 iterate() signature",
            previous_hash="sha256:1111",
            new_hash="sha256:2222",
            trigger_event_id="manual",
            trigger_type="manual",
        )
        payload = ev["run"]["facets"]["sdlc:payload"]
        assert payload["trigger_event_id"] == "manual"
        assert payload["trigger_type"] == "manual"

    def test_spec_modified_approval_sequence(self, tmp_path):
        """Full approval sequence: feature_approved → spec_modified."""
        from genesis.ol_event import feature_approved, spec_modified, emit_ol_event

        events_path = tmp_path / "events.jsonl"

        ev_approved = feature_approved(
            project="test",
            instance_id="inst-001",
            actor="human",
            feature="REQ-F-AUTH-005",
        )
        approval_run_id = ev_approved["run"]["runId"]
        emit_ol_event(events_path, ev_approved)

        ev_spec = spec_modified(
            project="test",
            instance_id="inst-001",
            actor="human",
            file="specification/features/FEATURE_VECTORS.md",
            what_changed="Added REQ-F-AUTH-005 via PROP-001 approval",
            previous_hash="sha256:aabb",
            new_hash="sha256:ccdd",
            trigger_event_id="PROP-001",
            trigger_type="feature_proposal",
            causation_id=approval_run_id,
            correlation_id=approval_run_id,
        )
        emit_ol_event(events_path, ev_spec)

        lines = events_path.read_text().strip().splitlines()
        assert len(lines) == 2
        approved, modified = [json.loads(l) for l in lines]
        assert approved["eventType"] == "COMPLETE"
        assert modified["eventType"] == "COMPLETE"

        # Causal chain: spec_modified causation_id = feature_approved run_id
        causation = modified["run"]["facets"]["sdlc:universal"]["causation_id"]
        assert causation == approval_run_id
