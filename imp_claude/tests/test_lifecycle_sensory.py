# Validates: REQ-LIFE-013
# Validates: REQ-SENSE-006
# Validates: REQ-SUPV-002
"""Tests for lifecycle gates, artifact observation, and constraint tolerances.

Covers:
  REQ-LIFE-013: Release readiness criteria (4-gate model)
  REQ-SENSE-006: Artifact write observation via PostToolUse hook
  REQ-SUPV-002: Constraint tolerances — every constraint has a measurable threshold
"""

import sys
import pathlib
import pytest

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
IMP_CLAUDE = PROJECT_ROOT / "imp_claude"
PLUGIN_ROOT = IMP_CLAUDE / "code" / ".claude-plugin" / "plugins" / "genesis"
CONFIG_DIR = PLUGIN_ROOT / "config"
EDGE_PARAMS_DIR = CONFIG_DIR / "edge_params"
COMMANDS_DIR = PLUGIN_ROOT / "commands"
HOOKS_DIR = PLUGIN_ROOT / "hooks"
GENESIS_PKG = IMP_CLAUDE / "code" / "genesis"

sys.path.insert(0, str(IMP_CLAUDE / "code"))


# ═══════════════════════════════════════════════════════════════════════════════
# REQ-LIFE-013: Release Readiness Criteria
# ═══════════════════════════════════════════════════════════════════════════════


class TestReleaseReadinessGates:
    """REQ-LIFE-013: Formal 4-gate release readiness model."""

    def test_gate1_fp_actor_result_missing_is_typed_exception(self):
        """Gate 1 — F_P invocation contract: missing fold-back raises typed exception.

        REQ-LIFE-013 Gate 1 requires: 'missing fold-back raises a typed exception,
        not a silent skip'. FpActorResultMissing must be a RuntimeError subclass
        distinct from the generic skip path.
        """
        from genesis.contracts import FpActorResultMissing

        assert issubclass(FpActorResultMissing, RuntimeError)
        # Must be distinct from the base class — not a re-export of RuntimeError
        assert FpActorResultMissing is not RuntimeError

    def test_gate1_fp_actor_result_missing_docstring_distinguishes_from_skip(self):
        """Gate 1: FpActorResultMissing docstring states it is NOT a silent skip."""
        from genesis.contracts import FpActorResultMissing

        doc = FpActorResultMissing.__doc__ or ""
        # Must articulate the distinction from a transparent skip
        assert any(
            phrase in doc.lower()
            for phrase in ["skip", "silent", "observable", "available"]
        ), f"FpActorResultMissing docstring should distinguish from silent skip: {doc}"

    def test_gate1_engine_catches_fp_actor_result_missing(self):
        """Gate 1: Engine catches FpActorResultMissing and emits FpFailure (not re-raises)."""
        engine_src = (GENESIS_PKG / "engine.py").read_text()
        assert "FpActorResultMissing" in engine_src, (
            "engine.py must import and handle FpActorResultMissing"
        )
        # Engine should catch it — look for except block
        assert "except FpActorResultMissing" in engine_src, (
            "engine.py must catch FpActorResultMissing to emit FpFailure"
        )

    def test_gate1_artifact_modified_in_event_taxonomy(self):
        """Gate 1 — event taxonomy conformance: artifact_modified is a known event type.

        REQ-LIFE-013 Gate 1 requires 'events conforming to the accepted event taxonomy'.
        """
        from genesis.fd_classify import classify_signal_source

        result = classify_signal_source({"event_type": "artifact_modified"})
        assert result != "unknown", (
            "artifact_modified must be a known event type in the taxonomy"
        )
        assert result == "artifact", (
            f"artifact_modified should map to 'artifact' signal class, got: {result}"
        )

    def test_gate1_fp_failure_in_event_taxonomy(self):
        """Gate 1: fp_failure is in the accepted event taxonomy."""
        from genesis.fd_classify import classify_signal_source

        result = classify_signal_source({"event_type": "fp_failure"})
        assert result == "failure", (
            f"fp_failure must map to 'failure' signal class, got: {result}"
        )

    def test_gate1_engine_events_conform_to_taxonomy(self):
        """Gate 1: Core engine event types are in the accepted event taxonomy."""
        from genesis.fd_classify import classify_signal_source

        unknown = []
        core_types = [
            "edge_started",
            "edge_converged",
            "iteration_completed",
            "fp_failure",
            "spawn_created",
        ]
        for et in core_types:
            result = classify_signal_source({"event_type": et})
            if result == "unknown":
                unknown.append(et)

        assert not unknown, (
            f"Core engine event types not in taxonomy: {unknown}"
        )

    def test_gate1_gen_release_has_readiness_validation_step(self):
        """Gate 1: gen-release command implements a release readiness validation step."""
        release_md = COMMANDS_DIR / "gen-release.md"
        assert release_md.exists(), "gen-release.md must exist"
        content = release_md.read_text()
        assert "Validate Release Readiness" in content, (
            "gen-release must have a 'Validate Release Readiness' step"
        )

    def test_gate_model_is_4_gate_ordered(self):
        """REQ-LIFE-013: Release model has 4 ordered gates.

        The spec defines: Gate 1 (runtime), Gate 2 (observability),
        Gate 3 (ecosystem), Gate 4 (assurance = Gates 2+3 both green).
        """
        spec_req = (
            PROJECT_ROOT
            / "specification"
            / "requirements"
            / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        )
        content = spec_req.read_text()
        # All 4 gates must be defined
        for n in range(1, 5):
            assert f"Gate {n}" in content, (
                f"REQ-LIFE-013 must define Gate {n}"
            )

    def test_gate4_requires_gates_2_and_3(self):
        """Gate 4 is the assurance gate — requires Gates 2 and 3."""
        spec_req = (
            PROJECT_ROOT
            / "specification"
            / "requirements"
            / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        )
        content = spec_req.read_text()
        # Gate 4 assurance description
        assert "Gate 4" in content
        # Gate 4 must reference 2 and 3
        gate4_idx = content.find("Gate 4")
        surrounding = content[gate4_idx: gate4_idx + 300]
        assert "2" in surrounding and "3" in surrounding, (
            "Gate 4 must reference Gates 2 and 3"
        )

    def test_bootstrap_principle_is_documented(self):
        """REQ-LIFE-013: Bootstrap principle (use Genesis on itself to build next version)."""
        spec_req = (
            PROJECT_ROOT
            / "specification"
            / "requirements"
            / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        )
        content = spec_req.read_text()
        # GCC model or bootstrap self-reference
        assert "bootstrap" in content.lower() or "GCC" in content, (
            "REQ-LIFE-013 must document the bootstrap principle (GCC model)"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# REQ-SENSE-006: Artifact Write Observation
# ═══════════════════════════════════════════════════════════════════════════════


class TestArtifactWriteObservation:
    """REQ-SENSE-006: PostToolUse hook observes artifact writes and emits events."""

    @pytest.fixture
    def hook_path(self):
        return HOOKS_DIR / "on-artifact-written.sh"

    @pytest.fixture
    def hook_content(self, hook_path):
        assert hook_path.exists(), "on-artifact-written.sh must exist"
        return hook_path.read_text()

    def test_hook_file_exists(self, hook_path):
        """Hook script must exist at the expected path."""
        assert hook_path.exists()

    def test_hook_declares_req_sense_006(self, hook_content):
        """Hook must declare it implements REQ-SENSE-006."""
        assert "REQ-SENSE-006" in hook_content, (
            "on-artifact-written.sh must declare 'Implements: REQ-SENSE-006'"
        )

    def test_hook_declares_req_tool_006(self, hook_content):
        """Hook also implements REQ-TOOL-006 (hooks as protocol enforcement)."""
        assert "REQ-TOOL-006" in hook_content

    def test_hook_fails_silently_on_error(self, hook_content):
        """Hook must never block — trap all errors and exit 0.

        REQ-SENSE-006: 'The hook fails silently on error (observation failure
        must not block construction)'.
        """
        assert "trap 'exit 0' ERR EXIT" in hook_content, (
            "Hook must trap all errors and exit 0 (never block writes)"
        )

    def test_hook_emits_artifact_modified_event(self, hook_content):
        """Hook emits an artifact_modified event for each detected write."""
        assert '"artifact_modified"' in hook_content or "'artifact_modified'" in hook_content, (
            "Hook must emit event_type artifact_modified"
        )

    def test_hook_emits_edge_started_on_first_write(self, hook_content):
        """First write to a new asset type in a session emits edge_started.

        REQ-SENSE-006: 'First write to a new asset type in a session emits
        edge_started with trigger artifact_write_detected'.
        """
        assert '"edge_started"' in hook_content or "'edge_started'" in hook_content, (
            "Hook must emit edge_started on first write to new asset type"
        )
        assert "artifact_write_detected" in hook_content, (
            "edge_started trigger must be 'artifact_write_detected'"
        )

    def test_hook_excludes_workspace_internals(self, hook_content):
        """Hook must exclude .ai-workspace/, .git/, and node_modules/.

        REQ-SENSE-006: 'Writes to non-artifact paths are excluded'.
        """
        assert ".ai-workspace/" in hook_content, (
            "Hook must explicitly exclude .ai-workspace/ paths"
        )
        assert ".git/" in hook_content, (
            "Hook must explicitly exclude .git/ paths"
        )

    def test_hook_excludes_infrastructure_files(self, hook_content):
        """Hook must exclude infrastructure files (CLAUDE.md, pyproject.toml, etc.)."""
        assert "CLAUDE.md" in hook_content, (
            "Hook must explicitly exclude CLAUDE.md"
        )

    def test_hook_is_multi_tenant_aware(self, hook_content):
        """Hook strips imp_<name>/ prefix for asset type mapping.

        REQ-SENSE-006: 'Multi-tenant aware: paths under imp_<name>/ mapped
        by subdirectory after tenant prefix'.
        """
        assert "imp_" in hook_content, (
            "Hook must handle imp_<name>/ multi-tenant prefix stripping"
        )

    def test_hook_artifact_modified_has_required_fields(self, hook_content):
        """artifact_modified event must include: timestamp, file_path, asset_type, tool."""
        required_fields = ["timestamp", "file_path", "asset_type", "tool"]
        for field in required_fields:
            assert f'"{field}"' in hook_content or "${field}" in hook_content or field in hook_content, (
                f"artifact_modified event must include field: {field}"
            )

    def test_artifact_modified_in_fd_classify_signal_map(self):
        """artifact_modified must be in fd_classify signal map.

        This ensures the event is processable by the IntentEngine pipeline.
        """
        fd_classify_src = (GENESIS_PKG / "fd_classify.py").read_text()
        assert '"artifact_modified"' in fd_classify_src, (
            "artifact_modified must be in fd_classify signal map for IntentEngine routing"
        )

    def test_hook_targets_posttooluse_trigger(self, hook_content):
        """Hook is designed for PostToolUse trigger (observation after every write)."""
        # The hook processes tool_name from hook input (PostToolUse data shape)
        assert "tool_name" in hook_content or "TOOL_NAME" in hook_content, (
            "Hook must read tool_name from PostToolUse hook input"
        )

    def test_hook_maps_asset_types_from_paths(self, hook_content):
        """Hook maps directory paths to methodology asset types."""
        # Check that known asset type categories are mapped
        expected_types = ["requirements", "design", "unit_tests", "code"]
        for asset_type in expected_types:
            assert asset_type in hook_content, (
                f"Hook must map paths to asset type: {asset_type}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# REQ-SUPV-002: Constraint Tolerances
# ═══════════════════════════════════════════════════════════════════════════════


class TestConstraintTolerances:
    """REQ-SUPV-002: Every constraint has a measurable tolerance — constraints are sensors."""

    def test_classify_tolerance_breach_within_bounds(self):
        """Tolerance within bounds → 'reflex.log' (system healthy, fire-and-forget).

        REQ-SUPV-002: 'within bounds (reflex.log)'.
        """
        from genesis.workspace_state import classify_tolerance_breach

        result = classify_tolerance_breach(0.50, threshold=0.80)
        assert result == "reflex.log", (
            f"observed <= threshold should return 'reflex.log', got: {result}"
        )

    def test_classify_tolerance_breach_at_boundary(self):
        """Tolerance exactly at threshold → still 'reflex.log' (boundary is inclusive)."""
        from genesis.workspace_state import classify_tolerance_breach

        result = classify_tolerance_breach(0.80, threshold=0.80)
        assert result == "reflex.log"

    def test_classify_tolerance_breach_drifting(self):
        """Tolerance drifting (> threshold but <= 2x) → 'specEventLog' (deferred intent).

        REQ-SUPV-002: 'drifting (specEventLog — optimization intent deferred)'.
        """
        from genesis.workspace_state import classify_tolerance_breach

        # 0.90 is > 0.80 (threshold) but <= 1.60 (2x threshold) → drifting
        result = classify_tolerance_breach(0.90, threshold=0.80)
        assert result == "specEventLog", (
            f"drifting (>threshold, <=2x) should return 'specEventLog', got: {result}"
        )

    def test_classify_tolerance_breach_escalate(self):
        """Tolerance far exceeded (> 2x threshold) → 'escalate' (corrective intent raised).

        REQ-SUPV-002: 'breached (escalate — corrective intent raised)'.
        """
        from genesis.workspace_state import classify_tolerance_breach

        # 2.0 is > 1.60 (2x 0.80) → escalate
        result = classify_tolerance_breach(2.0, threshold=0.80)
        assert result == "escalate", (
            f"severely exceeded should return 'escalate', got: {result}"
        )

    def test_classify_tolerance_breach_critical_severity_escalates_immediately(self):
        """Critical severity escalates immediately, even when drifting not far exceeded.

        REQ-SUPV-002: severity breach classification — critical overrides drifting.
        """
        from genesis.workspace_state import classify_tolerance_breach

        # 0.90 is drifting (not far exceeded), but critical severity → escalate immediately
        result = classify_tolerance_breach(0.90, threshold=0.80, severity="critical")
        assert result == "escalate", (
            f"critical severity should escalate immediately, got: {result}"
        )

    def test_classify_tolerance_breach_non_critical_does_not_escalate_at_drifting(self):
        """Non-critical severity at drifting level → specEventLog (not immediate escalate)."""
        from genesis.workspace_state import classify_tolerance_breach

        result = classify_tolerance_breach(0.90, threshold=0.80, severity="warning")
        assert result == "specEventLog", (
            f"non-critical drifting should defer to specEventLog, got: {result}"
        )

    def test_verify_genesis_compliance_includes_tolerance_check(self):
        """verify_genesis_compliance must include a tolerance check step (REQ-SUPV-002).

        The health check command is the primary surface for tolerance gap analysis.
        """
        ws_src = (GENESIS_PKG / "workspace_state.py").read_text()
        assert "tolerance_check" in ws_src, (
            "verify_genesis_compliance must include a 'tolerance_check' result"
        )
        assert "REQ-SUPV-002" in ws_src, (
            "workspace_state.py must reference REQ-SUPV-002 in tolerance check"
        )

    def test_tdd_edge_params_use_numeric_threshold_variable(self):
        """TDD edge params reference $thresholds.test_coverage_minimum (numeric, not qualitative).

        REQ-SUPV-002: 'edge config expresses constraints as measurable thresholds'.
        """
        tdd_path = EDGE_PARAMS_DIR / "tdd.yml"
        assert tdd_path.exists(), "tdd.yml must exist"
        content = tdd_path.read_text()
        assert "$thresholds.test_coverage_minimum" in content, (
            "TDD edge params must reference numeric $thresholds.test_coverage_minimum"
        )

    def test_project_constraints_template_has_numeric_thresholds(self):
        """project_constraints_template.yml must have numeric thresholds section.

        REQ-SUPV-002: 'Every constraint surface expresses constraints as measurable thresholds'.
        """
        template_path = CONFIG_DIR / "project_constraints_template.yml"
        assert template_path.exists()
        content = template_path.read_text()
        assert "thresholds:" in content, (
            "project_constraints_template.yml must have a thresholds section"
        )
        assert "test_coverage_minimum:" in content, (
            "thresholds section must include test_coverage_minimum with a numeric value"
        )
        # Must be a numeric value (0.80 not "80%")
        import re
        match = re.search(r"test_coverage_minimum:\s*([\d.]+)", content)
        assert match is not None, (
            "test_coverage_minimum must have a numeric value (e.g. 0.80, not a qualitative string)"
        )
        value = float(match.group(1))
        assert 0.0 < value <= 1.0, (
            f"test_coverage_minimum should be a fraction (0.0-1.0), got: {value}"
        )

    def test_constraint_without_tolerance_is_wish(self):
        """REQ-SUPV-002: A constraint without a declared tolerance is flagged by gap analysis.

        verify_genesis_compliance identifies 'wish' constraints (qualitative, no threshold).
        """
        ws_src = (GENESIS_PKG / "workspace_state.py").read_text()
        # The tolerance check must identify qualitative values as "wishes"
        assert "wish" in ws_src.lower() or "wishes" in ws_src.lower(), (
            "verify_genesis_compliance must identify wish constraints (no measurable threshold)"
        )

    def test_tolerance_breach_signal_map_complete(self):
        """classify_tolerance_breach produces all 3 signal types in REQ-SUPV-002."""
        from genesis.workspace_state import classify_tolerance_breach

        signals = {
            classify_tolerance_breach(0.50, 0.80),   # within bounds
            classify_tolerance_breach(0.90, 0.80),   # drifting
            classify_tolerance_breach(2.0, 0.80),    # escalate
        }
        expected = {"reflex.log", "specEventLog", "escalate"}
        assert signals == expected, (
            f"classify_tolerance_breach must produce all 3 signal types: {expected}, got: {signals}"
        )
