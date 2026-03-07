# Validates: REQ-TOOL-001, REQ-LIFE-005, REQ-LIFE-006, REQ-LIFE-007, REQ-LIFE-008, REQ-F-TOOL-001
# Validates: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-003, REQ-SENSE-004, REQ-SENSE-005, REQ-F-SENSE-001
# Validates: REQ-COORD-001, REQ-COORD-002, REQ-COORD-003, REQ-COORD-004, REQ-COORD-005
# Validates: REQ-UX-001, REQ-UX-002, REQ-UX-003, REQ-UX-004, REQ-UX-005, REQ-UX-006, REQ-UX-007, REQ-F-UX-001
# Validates: REQ-SUPV-001, REQ-SUPV-002, REQ-SUPV-003
# Validates: REQ-EVOL-001, REQ-EVOL-002, REQ-EVOL-003, REQ-EVOL-004, REQ-EVOL-005
"""Spec-level validation tests.

These tests validate the specification documents (technology-agnostic).
They read from specification/ and never touch implementation artifacts.
"""

import re

import pytest

from .conftest import SPEC_DIR


# ═══════════════════════════════════════════════════════════════════════
# 1. REQ KEY CROSS-REFERENCE VALIDATION
# ═══════════════════════════════════════════════════════════════════════


class TestReqKeyCoverage:
    """All REQ keys in spec must appear in feature vectors."""

    @pytest.mark.tdd
    def test_all_req_keys_in_feature_vectors(self):
        """Every REQ key from implementation requirements must be covered."""
        req_file = SPEC_DIR / "requirements" / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        fv_file = SPEC_DIR / "features" / "FEATURE_VECTORS.md"

        req_keys = set()
        if req_file.exists():
            with open(req_file) as f:
                for line in f:
                    # Find REQ keys but skip the placeholder REQ-*-NNN
                    matches = re.findall(r'REQ-[A-Z]+-\d+', line)
                    req_keys.update(matches)

        if fv_file.exists():
            with open(fv_file) as f:
                fv_content = f.read()

            uncovered = {k for k in req_keys if k not in fv_content}
            # Filter out keys that might be in the summary table but not explicitly mapped yet
            assert not uncovered, f"REQ keys not in feature vectors: {uncovered}"

    @pytest.mark.tdd
    def test_feature_vectors_cover_all_requirements(self):
        """Feature vectors doc should claim full coverage."""
        fv_file = SPEC_DIR / "features" / "FEATURE_VECTORS.md"
        if not fv_file.exists(): return
        with open(fv_file) as f:
            content = f.read()
        assert "83/83 requirements covered" in content or "No orphans" in content


# ═══════════════════════════════════════════════════════════════════════
# 2. REQUIREMENTS LINEAGE (spec docs only)
# ═══════════════════════════════════════════════════════════════════════


class TestRequirementsLineage:
    """Validate that core requirements categories exist and trace correctly."""

    CONSCIOUSNESS_REQS = ["REQ-LIFE-005", "REQ-LIFE-006", "REQ-LIFE-007", "REQ-LIFE-008"]
    SUPV_REQS = ["REQ-SUPV-001", "REQ-SUPV-002", "REQ-SUPV-003"]

    @pytest.mark.tdd
    def test_consciousness_reqs_exist(self):
        """REQ-LIFE-005 through REQ-LIFE-008 must exist in implementation requirements."""
        req_path = SPEC_DIR / "requirements" / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        if not req_path.exists(): return
        with open(req_path) as f:
            content = f.read()
        for req in self.CONSCIOUSNESS_REQS:
            assert req in content, f"{req} not found in implementation requirements"

    @pytest.mark.tdd
    def test_supv_reqs_exist(self):
        """REQ-SUPV-001 through REQ-SUPV-003 must exist (Supervisory lift)."""
        req_path = SPEC_DIR / "requirements" / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        if not req_path.exists(): return
        with open(req_path) as f:
            content = f.read()
        for req in self.SUPV_REQS:
            assert req in content, f"{req} not found in implementation requirements"

    @pytest.mark.tdd
    def test_consciousness_reqs_trace_to_spec(self):
        """Each consciousness requirement must trace to the formal spec."""
        req_path = SPEC_DIR / "requirements" / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        if not req_path.exists(): return
        with open(req_path) as f:
            content = f.read()
        assert "Asset Graph Model §7.7" in content or "Consciousness Loop" in content

    @pytest.mark.tdd
    def test_requirement_count_updated(self):
        """Total requirement count should reflect v3.11 lift (83 requirements)."""
        req_path = SPEC_DIR / "requirements" / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        if not req_path.exists(): return
        with open(req_path) as f:
            content = f.read()
        assert "**83**" in content or "| **Total** | **83**" in content


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
        req_path = SPEC_DIR / "requirements" / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        if not req_path.exists(): return
        with open(req_path) as f:
            content = f.read()
        for req in self.SENSORY_REQS:
            assert req in content, f"{req} not found in implementation requirements"

    @pytest.mark.tdd
    def test_requirement_count_is_69(self):
        """Total requirement count must be 83."""
        req_path = SPEC_DIR / "requirements" / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        if not req_path.exists(): return
        with open(req_path) as f:
            content = f.read()
        assert "**83**" in content or "| **Total** | **83**" in content

    @pytest.mark.tdd
    def test_sensory_category_count_is_5(self):
        """Sensory Systems category must show count of 5."""
        req_path = SPEC_DIR / "requirements" / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        if not req_path.exists(): return
        with open(req_path) as f:
            content = f.read()
        assert "| Sensory Systems | 5 |" in content

    @pytest.mark.tdd
    def test_feature_vector_count_is_69(self):
        """Feature vectors doc must claim 83 requirements covered."""
        fv_path = SPEC_DIR / "features" / "FEATURE_VECTORS.md"
        if not fv_path.exists(): return
        with open(fv_path) as f:
            content = f.read()
        assert "83/83 requirements covered" in content or "83 implementation requirements" in content


# ═══════════════════════════════════════════════════════════════════════
# 4. MULTI-AGENT COORDINATION REQUIREMENTS (spec docs only)
# ═══════════════════════════════════════════════════════════════════════


class TestMultiAgentCoordination:
    """Validate multi-agent coordination requirements exist in spec."""

    COORD_REQS = ["REQ-COORD-001", "REQ-COORD-002", "REQ-COORD-003",
                  "REQ-COORD-004", "REQ-COORD-005"]

    @pytest.mark.tdd
    def test_coord_requirements_exist(self):
        """REQ-COORD-001 through REQ-COORD-005 must exist in implementation requirements."""
        req_path = SPEC_DIR / "requirements" / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        if not req_path.exists(): return
        with open(req_path) as f:
            content = f.read()
        for req in self.COORD_REQS:
            assert req in content, f"{req} not found in implementation requirements"

    @pytest.mark.tdd
    def test_coord_category_in_summary(self):
        """Multi-Agent Coordination category must show count of 5 in summary."""
        req_path = SPEC_DIR / "requirements" / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        if not req_path.exists(): return
        with open(req_path) as f:
            content = f.read()
        assert "| Multi-Agent Coordination | 5 |" in content


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
            "core/AI_SDLC_ASSET_GRAPH_MODEL.md",
            "core/PROJECTIONS_AND_INVARIANTS.md",
            "requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md",
            "features/FEATURE_VECTORS.md",
            "ux/UX.md",
            "core/GENESIS_BOOTLOADER.md",
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
        req_path = SPEC_DIR / "requirements" / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        if not req_path.exists(): return
        with open(req_path) as f:
            content = f.read()
        for i in range(1, 8):
            assert f"REQ-UX-{i:03d}" in content, f"REQ-UX-{i:03d} not found"

    @pytest.mark.tdd
    def test_ux_category_count_is_7(self):
        """User Experience category must show count of 7 in summary."""
        req_path = SPEC_DIR / "requirements" / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        if not req_path.exists(): return
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
        spec_path = SPEC_DIR / "core" / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        if not spec_path.exists(): return
        with open(spec_path) as f:
            content = f.read()
        assert "Three Processing Phases" in content
        assert "reflex" in content.lower()
        assert "affect" in content.lower()
        assert "conscious" in content.lower()

    @pytest.mark.bdd
    def test_spec_maps_evaluators_to_phases(self):
        """Spec must map evaluator types to processing phases."""
        spec_path = SPEC_DIR / "core" / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        if not spec_path.exists(): return
        with open(spec_path) as f:
            content = f.read()
        assert "Human evaluator" in content and "Conscious" in content
        assert "Agent evaluator" in content and "Conscious" in content
        assert "Deterministic" in content and "Reflex" in content

    @pytest.mark.bdd
    def test_spec_defines_intentengine(self):
        """Formal spec must define §4.6 The IntentEngine."""
        spec_path = SPEC_DIR / "core" / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        if not spec_path.exists(): return
        with open(spec_path) as f:
            content = f.read()
        assert "4.6 The IntentEngine" in content
        assert "observer" in content.lower()
        assert "evaluator" in content.lower()
        assert "typed_output" in content.lower()
