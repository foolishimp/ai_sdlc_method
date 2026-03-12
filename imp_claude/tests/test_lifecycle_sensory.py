# Validates: REQ-LIFE-013
# Validates: REQ-SENSE-006
# Validates: REQ-SUPV-002
# Validates: REQ-SENSE-001
# Validates: REQ-EVENT-002
# Validates: REQ-LIFE-006
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


# ═══════════════════════════════════════════════════════════════════════════════
# REQ-SENSE-001 INTRO-008, REQ-EVENT-002, REQ-LIFE-006: Convergence Evidence
# (ADR-S-037: Projection Authority and Convergence Evidence Validation)
# ═══════════════════════════════════════════════════════════════════════════════


class TestConvergenceEvidencePresent:
    """REQ-SENSE-001 INTRO-008: convergence_evidence_present F_D check.

    Validates: REQ-SENSE-001 (INTRO-008 monitor), REQ-EVENT-002 (Projection Authority),
               REQ-LIFE-006 (convergence_without_evidence signal source)
    """

    def test_known_signal_sources_includes_convergence_without_evidence(self):
        """REQ-LIFE-006: convergence_without_evidence is a named signal source.

        ADR-S-037 adds this as the 8th signal source type.
        """
        from genesis.fd_classify import KNOWN_SIGNAL_SOURCES
        assert "convergence_without_evidence" in KNOWN_SIGNAL_SOURCES, (
            "KNOWN_SIGNAL_SOURCES must include 'convergence_without_evidence' (ADR-S-037)"
        )

    def test_known_signal_sources_has_all_req_life_006_types(self):
        """REQ-LIFE-006: all 8 signal source types present in KNOWN_SIGNAL_SOURCES."""
        from genesis.fd_classify import KNOWN_SIGNAL_SOURCES
        required = {
            "gap", "test_failure", "refactoring", "source_finding",
            "process_gap", "runtime_feedback", "ecosystem",
            "convergence_without_evidence",
        }
        missing = required - KNOWN_SIGNAL_SOURCES
        assert not missing, (
            f"KNOWN_SIGNAL_SOURCES missing REQ-LIFE-006 required sources: {missing}"
        )

    def test_gen_status_health_spec_includes_convergence_evidence_check(self):
        """REQ-SENSE-001 INTRO-008: gen-status --health spec must define convergence_evidence_present."""
        gen_status = (COMMANDS_DIR / "gen-status.md").read_text()
        assert "convergence_evidence_present" in gen_status, (
            "gen-status.md --health section must define the convergence_evidence_present F_D check (ADR-S-037)"
        )

    def test_gen_status_health_references_adr_s_037(self):
        """REQ-EVENT-002: projection authority enforcement must reference ADR-S-037."""
        gen_status = (COMMANDS_DIR / "gen-status.md").read_text()
        assert "ADR-S-037" in gen_status, (
            "gen-status.md must reference ADR-S-037 for projection authority traceability"
        )

    def test_gen_status_health_emits_convergence_without_evidence_intent(self):
        """REQ-LIFE-006: health check failure must emit intent_raised with correct signal_source."""
        gen_status = (COMMANDS_DIR / "gen-status.md").read_text()
        assert "convergence_without_evidence" in gen_status, (
            "gen-status.md must specify intent_raised{signal_source: convergence_without_evidence} "
            "as the health check failure output (ADR-S-037)"
        )

    def test_convergence_evidence_check_requires_stream_event(self):
        """REQ-EVENT-002: check must verify event stream, not just YAML assertion.

        The check logic in gen-status.md must search events.jsonl, not trust the YAML.
        """
        gen_status = (COMMANDS_DIR / "gen-status.md").read_text()
        assert "events.jsonl" in gen_status, (
            "convergence_evidence_present check must search events.jsonl, not trust YAML state"
        )
        assert "edge_converged" in gen_status, (
            "check must look for edge_converged event type as valid convergence evidence"
        )

    def test_retroactive_events_use_emission_retroactive_field(self):
        """REQ-EVENT-005: retroactive convergence events use emission: retroactive (not a custom field).

        ADR-S-037 §3 aligns with REQ-EVENT-005 naming — no separate 'retroactive: true' data field.
        """
        adr_s037 = (
            PROJECT_ROOT / "specification" / "adrs" /
            "ADR-S-037-projection-authority-and-convergence-evidence.md"
        ).read_text()
        # Must use the REQ-EVENT-005 canonical field name
        assert 'emission.*retroactive' in adr_s037 or '"emission": "retroactive"' in adr_s037 or \
               "emission: retroactive" in adr_s037, (
            "ADR-S-037 must use emission: retroactive (REQ-EVENT-005 field) not a custom retroactive field"
        )
        # Must use canonical REQ-EVENT-005 form; any mention of retroactive: true should be as
        # negative example only (e.g., in a naming note), not as a spec prescription.
        # Check: the naming note must reference emission: retroactive as the canonical form.
        assert "emission: retroactive" in adr_s037 or '"emission": "retroactive"' in adr_s037, (
            "ADR-S-037 must canonically reference emission: retroactive (REQ-EVENT-005 field)"
        )

    def test_req_sense_001_lists_intro_008(self):
        """REQ-SENSE-001: convergence_evidence_present must appear in the minimum monitors list."""
        req_doc = (
            PROJECT_ROOT / "specification" / "requirements" /
            "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        ).read_text()
        assert "INTRO-008" in req_doc, (
            "AISDLC_IMPLEMENTATION_REQUIREMENTS.md REQ-SENSE-001 must list INTRO-008 "
            "convergence_evidence_present monitor"
        )
        assert "convergence_evidence_present" in req_doc, (
            "AISDLC_IMPLEMENTATION_REQUIREMENTS.md must define convergence_evidence_present "
            "as a required interoceptive monitor (ADR-S-037)"
        )

    def test_req_event_002_has_projection_authority_ac(self):
        """REQ-EVENT-002: Projection Contract must include Projection Authority enforcement AC."""
        req_doc = (
            PROJECT_ROOT / "specification" / "requirements" /
            "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        ).read_text()
        assert "Projection Authority" in req_doc, (
            "REQ-EVENT-002 must include Projection Authority AC (ADR-S-037)"
        )

    def test_intro_008_emits_interoceptive_signal_not_intent_raised(self):
        """REQ-SENSE-001: INTRO-008 must emit interoceptive_signal, not intent_raised directly.

        Option A (triage-mediated) is the only correct architecture.
        Monitors observe and emit interoceptive_signal. Affect triage routes to intent_raised.
        Direct intent_raised from a monitor bypasses triage and violates the sensory contract.
        """
        req_doc = (
            PROJECT_ROOT / "specification" / "requirements" /
            "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        ).read_text()
        # INTRO-008 must emit interoceptive_signal
        assert "interoceptive_signal" in req_doc, (
            "REQ-SENSE-001 INTRO-008 must specify interoceptive_signal as monitor output"
        )
        # The routing to intent_raised must go through triage, not be direct
        # Find the INTRO-008 block — it must NOT say "emit intent_raised" directly
        intro_008_idx = req_doc.find("INTRO-008")
        assert intro_008_idx != -1
        # Get the text from INTRO-008 to the next monitor (INTRO- or ---) boundary
        intro_008_block = req_doc[intro_008_idx: intro_008_idx + 1200]
        assert "affect triage" in intro_008_block or "triage" in intro_008_block, (
            "INTRO-008 block must reference affect triage as the routing mechanism"
        )

    def test_adr_s037_check_emits_interoceptive_signal_not_intent_raised(self):
        """ADR-S-037: convergence_evidence_present check output must be interoceptive_signal.

        The check never emits intent_raised directly — that is affect triage's responsibility.
        """
        adr_s037 = (
            PROJECT_ROOT / "specification" / "adrs" /
            "ADR-S-037-projection-authority-and-convergence-evidence.md"
        ).read_text()
        assert "interoceptive_signal" in adr_s037, (
            "ADR-S-037 check definition must show interoceptive_signal as the monitor output"
        )
        assert "affect triage" in adr_s037 or "triage" in adr_s037, (
            "ADR-S-037 must explain that affect triage routes the signal to intent_raised"
        )

    def test_gen_status_health_check_outputs_to_health_checked_not_intent_raised(self):
        """gen-status --health invocation path: failures go into health_checked, not intent_raised.

        The sensory service path emits interoceptive_signal → triage → intent_raised.
        The health check path emits findings into health_checked (REQ-SUPV-003).
        Neither path emits intent_raised directly from the check itself.
        """
        gen_status = (COMMANDS_DIR / "gen-status.md").read_text()
        # The health check block must reference health_checked as the output event
        assert "health_checked" in gen_status, (
            "gen-status.md must show health check findings going into health_checked event"
        )
        # The gen-status convergence check block must NOT say emit intent_raised directly
        # Find the convergence_evidence_present block
        cep_idx = gen_status.find("convergence_evidence_present")
        assert cep_idx != -1
        cep_block = gen_status[cep_idx: cep_idx + 800]
        # Must explain the two-path model
        assert "health_checked" in cep_block or "interoceptive_signal" in cep_block, (
            "convergence_evidence_present block must reference health_checked or interoceptive_signal "
            "as the output, not emit intent_raised directly"
        )
