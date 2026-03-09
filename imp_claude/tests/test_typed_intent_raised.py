# Validates: REQ-F-NAMEDCOMP-001 (NC-003 — Typed gap.intent Output)
# Validates: REQ-INTENT-002 (Intent as Spec — typed gap.intent output)
# Reference: ADR-S-026 §3-4, specification/features/NAMEDCOMP_DESIGN_RECOMMENDATIONS.md §Phase 3
"""Tests for typed gap.intent output in intent_raised events.
Verifies that composition resolution is embedded correctly in the event schema
and that unresolvable gap types emit null with a known resolution status."""

import json
import pathlib
from typing import Optional

import pytest
import yaml

from genesis.config_loader import load_named_compositions, resolve_composition


PLUGIN_ROOT = pathlib.Path(__file__).parent.parent / "code" / ".claude-plugin" / "plugins" / "genesis"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def build_intent_raised_event(
    intent_id: str,
    gap_type: Optional[str],
    registry: dict,
    extra_bindings: Optional[dict] = None,
) -> dict:
    """Build an intent_raised event dict with composition resolution (ADR-S-026 §4)."""
    composition = None
    composition_resolution = None
    if gap_type is not None:
        composition, composition_resolution = resolve_composition(gap_type, registry, extra_bindings)

    return {
        "event_type": "intent_raised",
        "timestamp": "2026-03-09T00:00:00Z",
        "project": "test_project",
        "data": {
            "intent_id": intent_id,
            "trigger": "test trigger",
            "delta": "test delta",
            "signal_source": "gap",
            "gap_type": gap_type,
            "composition": composition,
            "composition_resolution": composition_resolution,
            "vector_type": "feature",
            "affected_req_keys": ["REQ-TEST-001"],
            "severity": "high",
        },
    }


@pytest.fixture
def registry():
    return load_named_compositions(PLUGIN_ROOT)


# ─── P3: Event schema — composition field present ────────────────────────────

class TestIntentRaisedWithComposition:
    """intent_raised events include composition field when gap_type is known."""

    def test_known_gap_type_has_composition(self, registry):
        event = build_intent_raised_event("INT-001", "missing_schema", registry)
        assert event["data"]["composition"] is not None

    def test_composition_has_macro_version_bindings(self, registry):
        event = build_intent_raised_event("INT-001", "missing_requirements", registry)
        comp = event["data"]["composition"]
        assert "macro" in comp
        assert "version" in comp
        assert "bindings" in comp

    def test_composition_resolution_is_resolved_for_known(self, registry):
        event = build_intent_raised_event("INT-001", "unknown_risk", registry)
        assert event["data"]["composition_resolution"] == "resolved"

    def test_missing_schema_composition_macro(self, registry):
        event = build_intent_raised_event("INT-001", "missing_schema", registry)
        assert event["data"]["composition"]["macro"] == "SCHEMA_DISCOVERY"

    def test_missing_requirements_composition_macro(self, registry):
        event = build_intent_raised_event("INT-001", "missing_requirements", registry)
        assert event["data"]["composition"]["macro"] == "PLAN"

    def test_unknown_risk_composition_macro(self, registry):
        event = build_intent_raised_event("INT-001", "unknown_risk", registry)
        assert event["data"]["composition"]["macro"] == "POC"

    def test_unknown_domain_composition_macro(self, registry):
        event = build_intent_raised_event("INT-001", "unknown_domain", registry)
        assert event["data"]["composition"]["macro"] == "DATA_DISCOVERY"


class TestIntentRaisedWithoutGapType:
    """intent_raised events without gap_type have null composition (backward compatible)."""

    def test_null_gap_type_has_null_composition(self, registry):
        event = build_intent_raised_event("INT-001", None, registry)
        assert event["data"]["composition"] is None

    def test_null_gap_type_has_null_resolution(self, registry):
        event = build_intent_raised_event("INT-001", None, registry)
        assert event["data"]["composition_resolution"] is None

    def test_pre_adr_s026_event_parses_correctly(self):
        """Events without composition/gap_type fields should parse without error."""
        old_format_event = {
            "event_type": "intent_raised",
            "timestamp": "2026-01-01T00:00:00Z",
            "project": "test_project",
            "data": {
                "intent_id": "INT-OLD-001",
                "signal_source": "gap",
                "severity": "high",
            },
        }
        # Should not raise when accessing optional fields with .get()
        comp = old_format_event["data"].get("composition")
        resolution = old_format_event["data"].get("composition_resolution")
        gap_type = old_format_event["data"].get("gap_type")
        assert comp is None
        assert resolution is None
        assert gap_type is None


class TestIntentRaisedNoDispatchEntry:
    """Unknown gap_types emit null composition with no_dispatch_entry status."""

    def test_unknown_gap_type_has_null_composition(self, registry):
        event = build_intent_raised_event("INT-001", "completely_unknown_gap", registry)
        assert event["data"]["composition"] is None

    def test_unknown_gap_type_resolution_is_no_dispatch_entry(self, registry):
        event = build_intent_raised_event("INT-001", "completely_unknown_gap", registry)
        assert event["data"]["composition_resolution"] == "no_dispatch_entry"


class TestIntentRaisedUnresolvable:
    """Placeholder macros (EVOLVE, CONSENSUS) emit unresolvable status."""

    def test_spec_drift_is_unresolvable(self, registry):
        """spec_drift maps to EVOLVE which is not yet defined as a composition."""
        event = build_intent_raised_event("INT-001", "spec_drift", registry)
        # EVOLVE is in dispatch but not in compositions list — unresolvable
        assert event["data"]["composition_resolution"] == "unresolvable"
        assert event["data"]["composition"]["macro"] == "EVOLVE"

    def test_unresolvable_composition_still_has_macro(self, registry):
        """Even unresolvable compositions have macro/version for audit purposes."""
        event = build_intent_raised_event("INT-001", "spec_drift", registry)
        comp = event["data"]["composition"]
        assert comp is not None
        assert "macro" in comp
        assert "version" in comp


class TestCallerBindingsInEvent:
    """Caller bindings in intent_raised events override defaults."""

    def test_extra_bindings_appear_in_event_composition(self, registry):
        event = build_intent_raised_event(
            "INT-001",
            "missing_requirements",
            registry,
            extra_bindings={"criteria": "arch_stability", "source_asset": "spec/requirements.md"},
        )
        bindings = event["data"]["composition"]["bindings"]
        assert bindings["criteria"] == "arch_stability"
        assert bindings["source_asset"] == "spec/requirements.md"

    def test_default_bindings_preserved_for_unspecified_fields(self, registry):
        event = build_intent_raised_event(
            "INT-001",
            "missing_requirements",
            registry,
            extra_bindings={"source_asset": "spec/requirements.md"},
        )
        bindings = event["data"]["composition"]["bindings"]
        assert bindings["unit_type"] == "capability"  # from default_bindings


# ─── P3: intentengine_config.yml has gap_type_dispatch section ───────────────

class TestIntentEngineConfigExtension:
    """intentengine_config.yml has the gap_type_dispatch section added in P3."""

    @pytest.fixture
    def intentengine_config(self):
        config_path = PLUGIN_ROOT / "config" / "intentengine_config.yml"
        with open(config_path) as f:
            return yaml.safe_load(f)

    def test_has_gap_type_dispatch_section(self, intentengine_config):
        assert "gap_type_dispatch" in intentengine_config

    def test_gap_type_dispatch_has_source(self, intentengine_config):
        dispatch = intentengine_config["gap_type_dispatch"]
        assert "source" in dispatch
        assert "named_compositions.yml" in dispatch["source"]

    def test_gap_type_dispatch_has_fallback(self, intentengine_config):
        dispatch = intentengine_config["gap_type_dispatch"]
        assert "fallback" in dispatch

    def test_gap_type_dispatch_has_event_schema_extension(self, intentengine_config):
        dispatch = intentengine_config["gap_type_dispatch"]
        schema_ext = dispatch.get("event_schema_extension", {})
        assert "gap_type" in schema_ext
        assert "composition" in schema_ext
        assert "composition_resolution" in schema_ext


# ─── P3: Event serialisation ─────────────────────────────────────────────────

class TestEventSerialisation:
    """intent_raised events with composition are JSON-serialisable."""

    def test_event_is_json_serialisable(self, registry):
        event = build_intent_raised_event("INT-001", "missing_design", registry)
        serialised = json.dumps(event)
        deserialised = json.loads(serialised)
        assert deserialised["data"]["composition"]["macro"] == "PLAN"

    def test_null_composition_is_json_serialisable(self, registry):
        event = build_intent_raised_event("INT-001", None, registry)
        serialised = json.dumps(event)
        deserialised = json.loads(serialised)
        assert deserialised["data"]["composition"] is None
