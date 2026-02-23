# Validates: REQ-TOOL-001, REQ-TOOL-010, REQ-LIFE-005, REQ-LIFE-006, REQ-LIFE-007, REQ-LIFE-008
# Validates: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-003, REQ-SENSE-004, REQ-SENSE-005
# Validates: REQ-COORD-001, REQ-COORD-002, REQ-COORD-003, REQ-COORD-004, REQ-COORD-005
# Validates: REQ-SUPV-001, REQ-SUPV-002
"""Spec-level validation tests.

These tests validate the specification documents (technology-agnostic).
They read from specification/ and never touch implementation artifacts.
"""

import re

import pytest

from conftest import SPEC_DIR


# ═══════════════════════════════════════════════════════════════════════
# 1. REQ KEY CROSS-REFERENCE VALIDATION
# ═══════════════════════════════════════════════════════════════════════


class TestReqKeyCoverage:
    """All REQ keys in spec must appear in feature vectors."""

    @pytest.mark.tdd
    def test_all_req_keys_in_feature_vectors(self):
        """Every REQ key from implementation requirements must be covered."""
        req_file = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        fv_file = SPEC_DIR / "FEATURE_VECTORS.md"

        req_keys = set()
        with open(req_file) as f:
            for line in f:
                req_keys.update(re.findall(r'REQ-[A-Z]+-\d+', line))

        with open(fv_file) as f:
            fv_content = f.read()

        uncovered = {k for k in req_keys if k not in fv_content}
        assert not uncovered, f"REQ keys not in feature vectors: {uncovered}"

    @pytest.mark.tdd
    def test_feature_vectors_cover_all_requirements(self):
        """Feature vectors doc should claim full coverage."""
        fv_file = SPEC_DIR / "FEATURE_VECTORS.md"
        with open(fv_file) as f:
            content = f.read()
        assert "58/58 requirements covered" in content or "No orphans" in content


# ═══════════════════════════════════════════════════════════════════════
# 2. REQUIREMENTS LINEAGE (spec docs only)
# ═══════════════════════════════════════════════════════════════════════


class TestRequirementsLineage:
    """Validate that consciousness loop requirements exist and trace correctly."""

    CONSCIOUSNESS_REQS = ["REQ-LIFE-005", "REQ-LIFE-006", "REQ-LIFE-007", "REQ-LIFE-008"]

    @pytest.mark.tdd
    def test_consciousness_reqs_exist(self):
        """REQ-LIFE-005 through REQ-LIFE-008 must exist in implementation requirements."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        for req in self.CONSCIOUSNESS_REQS:
            assert req in content, f"{req} not found in implementation requirements"

    @pytest.mark.tdd
    def test_consciousness_reqs_trace_to_spec(self):
        """Each consciousness requirement must trace to the formal spec."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        assert "Asset Graph Model §7.7" in content

    @pytest.mark.tdd
    def test_requirement_count_updated(self):
        """Total requirement count should reflect additions (was 35, now 39, now 43, now 44, now 49, now 54, now 55, now 58, now 59, now 60, now 62, now 63, now 64, now 68)."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        assert "**68**" in content or "| **Total** | **68**" in content

    @pytest.mark.bdd
    def test_consciousness_loop_reqs_exist_in_spec(self):
        """REQ-LIFE-005 through REQ-LIFE-008 must exist in implementation requirements (lineage check)."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        for req in ["REQ-LIFE-005", "REQ-LIFE-006", "REQ-LIFE-007", "REQ-LIFE-008"]:
            assert req in content, f"{req} missing from implementation requirements"


# ═══════════════════════════════════════════════════════════════════════
# 3. SENSORY REQUIREMENTS (spec docs only)
# ═══════════════════════════════════════════════════════════════════════


class TestSensoryRequirements:
    """Validate that sensory system requirements are complete and correctly counted."""

    SENSORY_REQS = ["REQ-SENSE-001", "REQ-SENSE-002", "REQ-SENSE-003",
                    "REQ-SENSE-004", "REQ-SENSE-005"]

    @pytest.mark.tdd
    def test_all_sensory_reqs_exist(self):
        """All 5 sensory requirements must exist in implementation requirements."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        for req in self.SENSORY_REQS:
            assert req in content, f"{req} not found in implementation requirements"

    @pytest.mark.tdd
    def test_requirement_count_is_68(self):
        """Total requirement count must be 68."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        assert "**68**" in content or "| **Total** | **68**" in content

    @pytest.mark.tdd
    def test_sensory_category_count_is_5(self):
        """Sensory Systems category must show count of 5."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        assert "| Sensory Systems | 5 |" in content

    @pytest.mark.tdd
    def test_feature_vector_count_is_68(self):
        """Feature vectors doc must claim 68 requirements covered."""
        fv_path = SPEC_DIR / "FEATURE_VECTORS.md"
        with open(fv_path) as f:
            content = f.read()
        assert "68/68 requirements covered" in content or "68 implementation requirements" in content

    @pytest.mark.tdd
    def test_sense_feature_vector_has_6_reqs(self):
        """REQ-F-SENSE-001 must list 6 requirements in feature vectors summary (5 SENSE + SUPV-003)."""
        fv_path = SPEC_DIR / "FEATURE_VECTORS.md"
        with open(fv_path) as f:
            content = f.read()
        assert "REQ-SENSE-005" in content
        assert "| REQ-F-SENSE-001 | 6 |" in content

    @pytest.mark.tdd
    def test_req_sense_005_in_coverage_table(self):
        """REQ-SENSE-005 must appear in the coverage check table."""
        fv_path = SPEC_DIR / "FEATURE_VECTORS.md"
        with open(fv_path) as f:
            content = f.read()
        assert "| REQ-SENSE-005 | REQ-F-SENSE-001 |" in content

    @pytest.mark.bdd
    def test_req_sense_005_exists(self):
        """REQ-SENSE-005 must exist in implementation requirements."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        assert "REQ-SENSE-005" in content

    @pytest.mark.bdd
    def test_req_sense_005_defines_review_boundary(self):
        """REQ-SENSE-005 must define the review boundary concept."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        idx = content.find("### REQ-SENSE-005")
        assert idx > 0, "REQ-SENSE-005 section heading not found"
        section = content[idx:idx + 1000]
        assert "Review Boundary" in section
        assert "tool interface" in section

    @pytest.mark.bdd
    def test_feature_vector_references_req_sense_005(self):
        """REQ-F-SENSE-001 must reference REQ-SENSE-005."""
        fv_path = SPEC_DIR / "FEATURE_VECTORS.md"
        with open(fv_path) as f:
            content = f.read()
        assert "REQ-SENSE-005" in content


# ═══════════════════════════════════════════════════════════════════════
# 4. MULTI-AGENT COORDINATION REQUIREMENTS (spec docs only)
# ═══════════════════════════════════════════════════════════════════════


class TestMultiAgentCoordination:
    """Validate multi-agent coordination requirements exist in spec.

    NOTE — Design-stage coverage only (Phase 1a):
    These tests verify that spec documents define the coordination
    requirements correctly. Implementation-specific tests (ADR validation,
    design doc checks) are in imp_claude/tests/.
    """

    COORD_REQS = ["REQ-COORD-001", "REQ-COORD-002", "REQ-COORD-003",
                  "REQ-COORD-004", "REQ-COORD-005"]

    @pytest.mark.tdd
    def test_coord_requirements_exist(self):
        """REQ-COORD-001 through REQ-COORD-005 must exist in implementation requirements."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        for req in self.COORD_REQS:
            assert req in content, f"{req} not found in implementation requirements"

    @pytest.mark.tdd
    def test_coord_category_in_summary(self):
        """Multi-Agent Coordination category must show count of 5 in summary."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        assert "| Multi-Agent Coordination | 5 |" in content

    @pytest.mark.tdd
    def test_coord_category_in_categories_list(self):
        """COORD must be in the categories list."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        assert "COORD" in content

    @pytest.mark.tdd
    def test_coord_feature_vector_exists(self):
        """REQ-F-COORD-001 must exist in feature vectors doc."""
        fv_path = SPEC_DIR / "FEATURE_VECTORS.md"
        with open(fv_path) as f:
            content = f.read()
        assert "REQ-F-COORD-001" in content

    @pytest.mark.tdd
    def test_coord_reqs_in_coverage_table(self):
        """All COORD requirements must appear in feature vectors coverage table."""
        fv_path = SPEC_DIR / "FEATURE_VECTORS.md"
        with open(fv_path) as f:
            content = f.read()
        for req in self.COORD_REQS:
            assert f"| {req} | REQ-F-COORD-001 |" in content, \
                f"{req} missing from coverage table"


# ═══════════════════════════════════════════════════════════════════════
# 5. SPEC DOCUMENT EXISTENCE
# ═══════════════════════════════════════════════════════════════════════


class TestSpecDocumentExistence:
    """All specification documents must exist."""

    @pytest.mark.tdd
    def test_spec_documents_exist(self):
        """All specification documents must exist."""
        expected = [
            "INTENT.md",
            "AI_SDLC_ASSET_GRAPH_MODEL.md",
            "PROJECTIONS_AND_INVARIANTS.md",
            "AISDLC_IMPLEMENTATION_REQUIREMENTS.md",
            "FEATURE_VECTORS.md",
        ]
        for doc in expected:
            assert (SPEC_DIR / doc).exists(), f"missing spec document: {doc}"


# ═══════════════════════════════════════════════════════════════════════
# 6. UX REQUIREMENTS (spec docs only)
# ═══════════════════════════════════════════════════════════════════════


class TestUXRequirements:
    """Validate UX requirements exist in spec."""

    @pytest.mark.tdd
    def test_ux_requirements_exist(self):
        """REQ-UX-001 through REQ-UX-007 must exist in implementation requirements."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        for i in range(1, 8):
            assert f"REQ-UX-{i:03d}" in content, f"REQ-UX-{i:03d} not found"

    @pytest.mark.tdd
    def test_ux_category_count_is_7(self):
        """User Experience category must show count of 7 in summary."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        assert "| User Experience | 7 |" in content


# ═══════════════════════════════════════════════════════════════════════
# 7. FORMAL SPEC CONTENT VALIDATION
# ═══════════════════════════════════════════════════════════════════════


class TestFormalSpecContent:
    """Validate formal spec content for processing phases, consciousness loop, sensory service."""

    @pytest.mark.bdd
    def test_spec_defines_three_processing_phases(self):
        """Formal spec must define §4.3 Three Processing Phases."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Three Processing Phases" in content
        assert "reflex" in content.lower()
        assert "affect" in content.lower()
        assert "conscious" in content.lower()

    @pytest.mark.bdd
    def test_spec_maps_evaluators_to_phases(self):
        """Spec must map evaluator types to processing phases."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Human evaluator" in content and "Conscious" in content
        assert "Agent evaluator" in content and "Conscious" in content
        assert "Deterministic" in content and "Reflex" in content

    @pytest.mark.bdd
    def test_spec_defines_affect_phase(self):
        """Spec §4.3 must define the affect (limbic) processing phase."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Affect (limbic)" in content
        assert "Limbic system" in content
        assert "signal classification" in content.lower() or "Signal triage" in content

    @pytest.mark.bdd
    def test_spec_labels_hooks_as_reflex(self):
        """Spec §7.8 must label protocol hooks as reflex arc."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "reflex arc" in content.lower()
        assert "autonomic nervous system" in content.lower()

    @pytest.mark.bdd
    def test_spec_states_each_phase_enables_next(self):
        """Spec must state that each phase enables the next."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Each phase enables the next" in content

    @pytest.mark.bdd
    def test_living_system_table_has_three_nervous_system_layers(self):
        """Living system table (§7.7.6) must have autonomic, limbic, and frontal cortex."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Autonomic nervous system" in content
        assert "Limbic system" in content
        assert "Frontal cortex" in content

    @pytest.mark.bdd
    def test_spec_defines_consciousness_loop(self):
        """Formal spec must define the consciousness loop."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "consciousness loop" in content.lower() or "Consciousness Loop" in content
        assert "intent_raised" in content

    @pytest.mark.bdd
    def test_spec_defines_sensory_service_architecture(self):
        """Spec §4.5.4 must define Sensory Service Architecture."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "4.5.4 Sensory Service Architecture" in content

    @pytest.mark.bdd
    def test_spec_defines_long_running_service_model(self):
        """Spec §4.5.4 must define the sensory service as a long-running service."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "long-running service" in content

    @pytest.mark.bdd
    def test_spec_defines_review_boundary(self):
        """Spec §4.5.4 must define the review boundary."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "review boundary" in content.lower() or "REVIEW BOUNDARY" in content

    @pytest.mark.bdd
    def test_spec_defines_two_event_categories(self):
        """Spec §4.5.4 must define sensor/evaluate vs change-approval event categories."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Sensor/evaluate events" in content
        assert "Change-approval events" in content

    @pytest.mark.bdd
    def test_spec_defines_draft_only_autonomy(self):
        """Spec §4.5.4 must state that homeostatic responses are draft proposals only."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "draft proposals only" in content.lower() or "draft proposals" in content

    @pytest.mark.bdd
    def test_spec_defines_monitor_telemetry_separation(self):
        """Spec §4.5.4 must clarify that the monitor rides the telemetry."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "monitor rides the telemetry" in content.lower() or "genesis_monitor" in content

    @pytest.mark.bdd
    def test_living_system_table_shows_service_hosted(self):
        """Living system table must show interoception/exteroception as service-hosted."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "service-hosted" in content.lower()

    @pytest.mark.bdd
    def test_spec_defines_context_sources(self):
        """AI_SDLC_ASSET_GRAPH_MODEL.md must mention context sources in §2.8."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Context sources" in content
        assert "URI references" in content or "uri" in content.lower()
