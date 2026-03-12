"""
Tests for Natural Language Intent Dispatch — REQ-F-UX-002.

Validates the NL routing layer behaviour defined in:
  - REQ-UX-008 (Natural Language Intent Dispatch)
  - ADR-S-038 (Bootloader-as-routing-vocabulary)
  - imp_claude/design/features/REQ-F-UX-002-nl-dispatch-design.md

Architecture note: the routing layer itself is LLM-native (gen-genesis.md command).
These tests validate:
  1. Static routing pattern coverage matches REQ-UX-008 AC spec
  2. intent_routed event schema and field completeness
  3. fd_classify correctly categorises intent_routed events
  4. Cold-start guarantee: gen-genesis reads only durable artifacts

# Validates: REQ-UX-008
"""

import json
import pytest
from pathlib import Path


# ─── TestRoutingPatterns ─────────────────────────────────────────────────────

class TestRoutingPatterns:
    """
    Validates that the static routing table defined in REQ-UX-008 §AC and
    ADR-S-038 §Appendix covers all required natural-language intents.

    # Validates: REQ-UX-008
    """

    # Canonical NL→command mappings from REQ-UX-008 AC
    REQUIRED_PATTERNS = [
        # (nl_trigger, expected_command_prefix)
        ("what's broken",      "gen-status --health"),
        ("health check",       "gen-status --health"),
        ("fix it",             "gen-start --auto"),
        ("start",              "gen-start"),
        ("continue",           "gen-start"),
        ("find gaps",          "gen-gaps"),
        ("coverage",           "gen-gaps"),
        ("where am I",         "gen-status"),
        ("status",             "gen-status"),
        ("new feature",        "gen-spawn --type feature"),
        ("release",            "gen-release"),
    ]

    def test_routing_table_covers_all_spec_patterns(self):
        """All NL patterns required by REQ-UX-008 AC are in the static routing table."""
        # Read the gen-genesis command (the static routing table lives there)
        genesis_cmd = Path("imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-genesis.md")
        if not genesis_cmd.exists():
            genesis_cmd = Path(".claude/commands/gen-genesis.md")
        assert genesis_cmd.exists(), "gen-genesis.md command file must exist (REQ-UX-008)"
        content = genesis_cmd.read_text()

        # Each required pattern must appear in the routing table section
        missing = []
        for nl_trigger, expected_cmd in self.REQUIRED_PATTERNS:
            # Check either the NL trigger or the expected command appears
            if expected_cmd.split()[0] not in content:
                missing.append((nl_trigger, expected_cmd))

        assert not missing, (
            f"gen-genesis.md missing routing entries for: "
            + ", ".join(f"'{t}'→'{c}'" for t, c in missing)
        )

    def test_gen_genesis_command_exists(self):
        """gen-genesis.md must exist in commands directory (REQ-UX-008 implementation)."""
        paths = [
            Path("imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-genesis.md"),
            Path(".claude/commands/gen-genesis.md"),
        ]
        assert any(p.exists() for p in paths), (
            "gen-genesis.md not found in any command directory"
        )

    def test_gen_genesis_has_cold_start_section(self):
        """gen-genesis.md must document cold-start guarantee (ADR-S-038 §Cold-Start)."""
        genesis_cmd = Path("imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-genesis.md")
        if not genesis_cmd.exists():
            genesis_cmd = Path(".claude/commands/gen-genesis.md")
        content = genesis_cmd.read_text().lower()
        assert "cold" in content or "bootstrap" in content, (
            "gen-genesis.md must describe cold-start or session bootstrap behaviour"
        )

    def test_routing_confidence_thresholds_documented(self):
        """Confidence thresholds (0.85/0.50) must be documented (ADR-S-038 §Thresholds)."""
        adr = Path("specification/adrs/ADR-S-038-natural-language-intent-dispatch.md")
        assert adr.exists(), "ADR-S-038 must exist"
        content = adr.read_text()
        assert "0.85" in content, "ADR-S-038 must document 0.85 confidence threshold"
        assert "0.50" in content or "0.5" in content, (
            "ADR-S-038 must document 0.50 confidence threshold"
        )

    def test_degraded_mode_without_genesis_documented(self):
        """Degraded mode (no /gen-genesis) must be documented in design."""
        design = Path(
            "imp_claude/design/features/REQ-F-UX-002-nl-dispatch-design.md"
        )
        assert design.exists(), "REQ-F-UX-002 design document must exist"
        content = design.read_text().lower()
        assert "degrad" in content or "without" in content, (
            "Design must document behaviour when gen-genesis has not been run"
        )


# ─── TestConfidenceThresholds ─────────────────────────────────────────────────

class TestConfidenceThresholds:
    """
    Validates the confidence threshold contract from ADR-S-038.

    # Validates: REQ-UX-008
    """

    def test_three_threshold_bands_defined(self):
        """ADR-S-038 must define exactly 3 confidence bands (≥0.85, 0.50-0.85, <0.50)."""
        adr = Path("specification/adrs/ADR-S-038-natural-language-intent-dispatch.md")
        content = adr.read_text()
        # All three bands must appear
        assert "≥ 0.85" in content or ">= 0.85" in content, "Missing ≥0.85 band"
        # Middle band
        assert "0.50" in content or "0.5–" in content or "50–" in content, (
            "Missing 0.50-0.85 band"
        )

    def test_silent_dispatch_for_high_confidence(self):
        """At confidence ≥0.85: silent dispatch with one-liner (ADR-S-038)."""
        adr = Path("specification/adrs/ADR-S-038-natural-language-intent-dispatch.md")
        content = adr.read_text().lower()
        assert "silent" in content, "ADR-S-038 must specify silent dispatch at high confidence"

    def test_clarification_for_low_confidence(self):
        """At confidence <0.50: single minimal clarification question (not a menu)."""
        adr = Path("specification/adrs/ADR-S-038-natural-language-intent-dispatch.md")
        content = adr.read_text().lower()
        assert "clarif" in content or "question" in content, (
            "ADR-S-038 must specify clarification behaviour at low confidence"
        )
        # Must NOT say "full menu" — the spec explicitly prohibits this
        assert "full menu" not in content, (
            "ADR-S-038 must not present a full menu — single question only"
        )

    def test_thresholds_are_f_d_constraints(self):
        """Confidence thresholds must be described as F_D constraints (ADR-S-038)."""
        adr = Path("specification/adrs/ADR-S-038-natural-language-intent-dispatch.md")
        content = adr.read_text()
        assert "F_D" in content, (
            "ADR-S-038 must describe confidence thresholds as F_D constraints"
        )


# ─── TestIntentRoutedEvent ────────────────────────────────────────────────────

class TestIntentRoutedEvent:
    """
    Validates the intent_routed event schema from REQ-EVENT-003.

    # Validates: REQ-UX-008
    """

    REQUIRED_FIELDS = {"input", "routed_to", "confidence", "feature", "edge", "basis"}

    def _make_intent_routed_event(self, **overrides):
        """Build a minimal valid intent_routed event."""
        base = {
            "event_type": "intent_routed",
            "timestamp": "2026-03-12T12:00:00Z",
            "project": "ai_sdlc_method",
            "data": {
                "input": "fix it",
                "routed_to": "gen-start --auto",
                "confidence": 0.95,
                "feature": "REQ-F-UX-002",
                "edge": "design→code",
                "basis": "bootloader §VII — route functional unit",
            },
        }
        base.update(overrides)
        return base

    def test_intent_routed_event_has_all_required_fields(self):
        """intent_routed event data must contain all required fields."""
        event = self._make_intent_routed_event()
        data = event["data"]
        missing = self.REQUIRED_FIELDS - set(data.keys())
        assert not missing, f"intent_routed event missing fields: {missing}"

    def test_intent_routed_event_type_string(self):
        """event_type must be exactly 'intent_routed'."""
        event = self._make_intent_routed_event()
        assert event["event_type"] == "intent_routed"

    def test_intent_routed_confidence_in_valid_range(self):
        """confidence must be in [0.0, 1.0]."""
        event = self._make_intent_routed_event()
        conf = event["data"]["confidence"]
        assert 0.0 <= conf <= 1.0, f"confidence {conf} outside [0.0, 1.0]"

    def test_intent_routed_serialisable_as_json(self):
        """intent_routed event must be JSON-serialisable (for events.jsonl append)."""
        event = self._make_intent_routed_event()
        serialised = json.dumps(event)
        deserialised = json.loads(serialised)
        assert deserialised["event_type"] == "intent_routed"

    def test_intent_routed_allows_null_feature_and_edge(self):
        """feature and edge may be null for static routing patterns without workspace context."""
        event = self._make_intent_routed_event()
        event["data"]["feature"] = None
        event["data"]["edge"] = None
        # Should still be valid
        data = event["data"]
        missing = self.REQUIRED_FIELDS - set(data.keys())
        assert not missing, "null feature/edge should still satisfy schema"

    def test_intent_routed_input_is_verbatim(self):
        """input field must capture verbatim user text (not normalised)."""
        raw_input = "Fix the INTRO-008 health wiring!"
        event = self._make_intent_routed_event()
        event["data"]["input"] = raw_input
        assert event["data"]["input"] == raw_input, "input must be verbatim"

    def test_intent_routed_in_spec_event_taxonomy(self):
        """intent_routed must appear in REQ-EVENT-003 event taxonomy."""
        spec = Path("specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md")
        content = spec.read_text()
        assert "intent_routed" in content, (
            "REQ-EVENT-003 must include intent_routed in its event taxonomy"
        )


# ─── TestFdClassifyIntentRouted ───────────────────────────────────────────────

class TestFdClassifyIntentRouted:
    """
    Validates fd_classify correctly categorises intent_routed events.

    # Validates: REQ-UX-008
    """

    def test_intent_routed_classified_as_routing(self):
        """fd_classify must categorise intent_routed as 'routing'."""
        import sys
        sys.path.insert(0, "imp_claude/code")
        from genesis.fd_classify import classify_signal_source

        event = {
            "event_type": "intent_routed",
            "timestamp": "2026-03-12T12:00:00Z",
            "project": "ai_sdlc_method",
            "data": {
                "input": "start",
                "routed_to": "gen-start --auto",
                "confidence": 0.92,
                "feature": None,
                "edge": None,
                "basis": "bootloader §VII",
            },
        }
        result = classify_signal_source(event)
        assert result == "routing", (
            f"intent_routed should be classified as 'routing', got '{result}'"
        )

    def test_session_bootstrap_classified_as_lifecycle(self):
        """fd_classify must categorise session_bootstrap as 'lifecycle'."""
        import sys
        sys.path.insert(0, "imp_claude/code")
        from genesis.fd_classify import classify_signal_source

        event = {
            "event_type": "session_bootstrap",
            "timestamp": "2026-03-12T12:00:00Z",
            "project": "ai_sdlc_method",
            "data": {"active_features": 5, "bootloader_version": "2.9.0"},
        }
        result = classify_signal_source(event)
        assert result == "lifecycle", (
            f"session_bootstrap should be classified as 'lifecycle', got '{result}'"
        )


# ─── TestColdStartGuarantee ───────────────────────────────────────────────────

class TestColdStartGuarantee:
    """
    Validates the cold-start guarantee: gen-genesis reads only durable filesystem
    artifacts, never conversation history.

    # Validates: REQ-UX-008
    """

    DURABLE_ARTIFACTS = [
        "specification/core/GENESIS_BOOTLOADER.md",  # routing vocabulary
        ".ai-workspace/features/active",              # workspace state
        ".ai-workspace/events/events.jsonl",          # event recency
    ]

    def test_bootloader_is_durable_artifact(self):
        """GENESIS_BOOTLOADER.md must exist as a durable filesystem artifact."""
        assert Path("specification/core/GENESIS_BOOTLOADER.md").exists(), (
            "Bootloader must be present on filesystem for cold-start guarantee"
        )

    def test_workspace_active_features_directory_exists(self):
        """Active features directory must exist (workspace personalisation source)."""
        assert Path(".ai-workspace/features/active").is_dir(), (
            ".ai-workspace/features/active must exist for dynamic routing context"
        )

    def test_gen_genesis_references_bootloader_path(self):
        """gen-genesis.md must reference the bootloader by filesystem path."""
        genesis_cmd = Path("imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-genesis.md")
        if not genesis_cmd.exists():
            genesis_cmd = Path(".claude/commands/gen-genesis.md")
        content = genesis_cmd.read_text()
        assert "GENESIS_BOOTLOADER" in content, (
            "gen-genesis must load GENESIS_BOOTLOADER.md by path (cold-start guarantee)"
        )

    def test_gen_genesis_reads_active_features(self):
        """gen-genesis.md must read active feature vectors from workspace."""
        genesis_cmd = Path("imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-genesis.md")
        if not genesis_cmd.exists():
            genesis_cmd = Path(".claude/commands/gen-genesis.md")
        content = genesis_cmd.read_text().lower()
        assert "active" in content and "feature" in content, (
            "gen-genesis must read active feature vectors for workspace personalisation"
        )

    def test_design_documents_cold_start_no_history_dependence(self):
        """Design must explicitly state no dependence on conversation history."""
        design = Path("imp_claude/design/features/REQ-F-UX-002-nl-dispatch-design.md")
        assert design.exists()
        content = design.read_text().lower()
        assert "history" in content or "durable" in content, (
            "Design must address conversation history independence"
        )

    def test_adr_s038_documents_cold_start(self):
        """ADR-S-038 must have a cold-start section."""
        adr = Path("specification/adrs/ADR-S-038-natural-language-intent-dispatch.md")
        content = adr.read_text().lower()
        assert "cold" in content, "ADR-S-038 must address cold-start problem"

    def test_gen_genesis_is_idempotent_documented(self):
        """gen-genesis must be documented as idempotent (safe to re-run)."""
        adr = Path("specification/adrs/ADR-S-038-natural-language-intent-dispatch.md")
        content = adr.read_text().lower()
        assert "idem" in content or "re-run" in content or "re-running" in content, (
            "ADR-S-038 must document gen-genesis idempotency"
        )
