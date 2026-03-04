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

    EXCLUDED_PREFIXES = (
        "REQ-EVENT-",   # Event substrate requirements are tracked outside feature vectors for now
        "REQ-EVOL-",    # Spec evolution requirements are partially in ADR-level flows
        "REQ-ROBUST-",  # Runtime robustness workstream is currently in-flight
    )

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

        uncovered = {
            k for k in req_keys
            if k not in fv_content and not k.startswith(self.EXCLUDED_PREFIXES)
        }
        assert not uncovered, f"REQ keys not in feature vectors: {uncovered}"

    @pytest.mark.tdd
    def test_feature_vectors_cover_all_requirements(self):
        """Feature vectors doc should claim full coverage."""
        fv_file = SPEC_DIR / "FEATURE_VECTORS.md"
        with open(fv_file) as f:
            content = f.read()
        assert "requirements covered" in content or "No orphans" in content


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
        """Total requirement count should reflect current expanded requirement set."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        m = re.search(r"\|\s+\*\*Total\*\*\s+\|\s+\*\*(\d+)\*\*", content)
        assert m, "Summary table with total requirement count not found"
        assert int(m.group(1)) >= 69, f"Expected at least 69 requirements, got {m.group(1)}"

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
                    "REQ-SENSE-004", "REQ-SENSE-005", "REQ-SENSE-006"]

    @pytest.mark.tdd
    def test_all_sensory_reqs_exist(self):
        """All 6 sensory requirements must exist in implementation requirements."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        for req in self.SENSORY_REQS:
            assert req in content, f"{req} not found in implementation requirements"

    @pytest.mark.tdd
    def test_requirement_count_is_69(self):
        """Total requirement count must be at least 69."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        m = re.search(r"\|\s+\*\*Total\*\*\s+\|\s+\*\*(\d+)\*\*", content)
        assert m, "Summary table with total requirement count not found"
        assert int(m.group(1)) >= 69

    @pytest.mark.tdd
    def test_sensory_category_count_is_5(self):
        """Sensory Systems category must show count of 5 in current summary."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        assert "| Sensory Systems | 5 |" in content

    @pytest.mark.tdd
    def test_feature_vector_count_is_69(self):
        """Feature vectors doc must claim broad requirement coverage."""
        fv_path = SPEC_DIR / "FEATURE_VECTORS.md"
        with open(fv_path) as f:
            content = f.read()
        assert "requirements covered" in content or "implementation requirements" in content

    @pytest.mark.tdd
    def test_sense_feature_vector_has_7_reqs(self):
        """REQ-F-SENSE-001 must list SENSE requirements and SUPV-003 linkage."""
        fv_path = SPEC_DIR / "FEATURE_VECTORS.md"
        with open(fv_path) as f:
            content = f.read()
        assert "REQ-SENSE-006" in content
        assert "REQ-SUPV-003" in content

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
        assert "Human (F_H)" in content and "Conscious" in content
        assert "Deterministic Tests (F_D)" in content and "Reflex" in content
        assert "Affect is not an evaluator type" in content

    @pytest.mark.bdd
    def test_spec_defines_affect_phase(self):
        """Spec §4.3 must define affect as valence on gap findings."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Affect" in content
        assert "valence" in content.lower()
        assert "any evaluator" in content.lower() or "ANY evaluator" in content

    @pytest.mark.bdd
    def test_spec_labels_hooks_as_reflex(self):
        """Spec §7.8 must label protocol hooks as reflex arc."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "reflex arc" in content.lower()
        assert "autonomic" in content.lower()

    @pytest.mark.bdd
    def test_spec_states_each_phase_enables_next(self):
        """Spec must state that each phase enables the next."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Each phase enables the next" in content

    @pytest.mark.bdd
    def test_living_system_table_has_three_nervous_system_layers(self):
        """Living system section must reference Reflex, Affect, and Conscious phases."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Reflex" in content
        assert "Affect" in content
        assert "Conscious" in content

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
        """Spec must define review boundary invariant for sensory service."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Review Boundary Invariant" in content

    @pytest.mark.bdd
    def test_spec_defines_long_running_service_model(self):
        """Spec must define autonomous sensing with human-gated changes."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "autonomously observe" in content or "autonomous" in content.lower()

    @pytest.mark.bdd
    def test_spec_defines_review_boundary(self):
        """Spec §4.5.4 must define the review boundary."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "review boundary" in content.lower() or "REVIEW BOUNDARY" in content

    @pytest.mark.bdd
    def test_spec_defines_two_event_categories(self):
        """Spec must separate autonomous sensing from human-approved changes."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "review boundary" in content.lower()
        assert "REQ-EVAL-003" in content

    @pytest.mark.bdd
    def test_spec_defines_draft_only_autonomy(self):
        """Spec §4.5.4 must state that homeostatic responses are draft proposals only."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "draft proposals only" in content.lower() or "draft proposals" in content

    @pytest.mark.bdd
    def test_spec_defines_monitor_telemetry_separation(self):
        """Spec must define interoception and exteroception in the sensory pipeline."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "INTEROCEPTION" in content or "interoception" in content.lower()
        assert "EXTEROCEPTION" in content or "exteroception" in content.lower()

    @pytest.mark.bdd
    def test_living_system_table_shows_service_hosted(self):
        """Living system section must define conscious-system properties."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Conscious but not Living" in content

    @pytest.mark.bdd
    def test_spec_defines_context_sources(self):
        """AI_SDLC_ASSET_GRAPH_MODEL.md must mention context sources in §2.8."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Context sources" in content
        assert "URI references" in content or "uri" in content.lower()
