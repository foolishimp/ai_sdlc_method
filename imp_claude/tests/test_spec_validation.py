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
        """Total requirement count should reflect additions (was 35, now 39, now 43, now 44, now 49, now 54, now 55, now 58, now 59, now 60, now 62, now 63, now 64, now 68, now 69)."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        assert "**69**" in content or "| **Total** | **69**" in content

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
        """Total requirement count must be 69."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        assert "**69**" in content or "| **Total** | **69**" in content

    @pytest.mark.tdd
    def test_sensory_category_count_is_6(self):
        """Sensory Systems category must show count of 6."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        assert "| Sensory Systems | 6 |" in content

    @pytest.mark.tdd
    def test_feature_vector_count_is_69(self):
        """Feature vectors doc must claim 69 requirements covered."""
        fv_path = SPEC_DIR / "FEATURE_VECTORS.md"
        with open(fv_path) as f:
            content = f.read()
        assert "69/69 requirements covered" in content or "69 implementation requirements" in content

    @pytest.mark.tdd
    def test_sense_feature_vector_has_7_reqs(self):
        """REQ-F-SENSE-001 must list 7 requirements in feature vectors summary (6 SENSE + SUPV-003)."""
        fv_path = SPEC_DIR / "FEATURE_VECTORS.md"
        with open(fv_path) as f:
            content = f.read()
        assert "REQ-SENSE-006" in content
        assert "| REQ-F-SENSE-001 | 7 |" in content

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
        # Affect is a valence vector emitted by ANY evaluator, not an evaluator assignment
        assert "Affect is not an evaluator type" in content

    @pytest.mark.bdd
    def test_spec_defines_affect_as_valence(self):
        """Spec §4.3 must define affect as valence vector on gap findings."""
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
        assert "autonomic nervous system" in content.lower()

    @pytest.mark.bdd
    def test_spec_states_each_phase_enables_next(self):
        """Spec must state that each phase enables the next."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Each phase enables the next" in content

    @pytest.mark.bdd
    def test_living_system_references_three_phases(self):
        """Living system section must reference all three processing phases."""
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
    def test_spec_defines_review_boundary_invariant(self):
        """Spec §4.5.4 must define the Review Boundary Invariant."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Review Boundary Invariant" in content

    @pytest.mark.bdd
    def test_spec_defines_autonomous_sensing(self):
        """Spec §4.5.4 must define autonomous sensing with human-approved changes."""
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
    def test_spec_defines_review_boundary_separation(self):
        """Spec §4.5.4 must separate autonomous sensing from human-approved changes."""
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
    def test_spec_defines_sensory_pipeline(self):
        """Spec §4.5.3 must define the sensory processing pipeline."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "INTEROCEPTION" in content or "interoception" in content.lower()
        assert "EXTEROCEPTION" in content or "exteroception" in content.lower()

    @pytest.mark.bdd
    def test_conscious_system_defines_properties(self):
        """Conscious system section must define operational properties."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Conscious but not Living" in content
        assert "concurrent" in content.lower() or "vector lifecycles" in content

    @pytest.mark.bdd
    def test_spec_defines_context_sources(self):
        """AI_SDLC_ASSET_GRAPH_MODEL.md must mention context sources in §2.8."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Context sources" in content
        assert "URI references" in content or "uri" in content.lower()
