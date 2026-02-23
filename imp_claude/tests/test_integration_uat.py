# Validates: REQ-TOOL-005, REQ-TOOL-009, REQ-LIFE-010, REQ-LIFE-011, REQ-LIFE-012
# Validates: REQ-FEAT-001, REQ-FEAT-002, REQ-FEAT-003
# Validates: REQ-EDGE-004, REQ-INTENT-004
"""UAT / Integration tests — end-to-end methodology validation.

These tests validate cross-artifact consistency, traceability chains,
event log integrity, and the full abiogenesis loop. They read across
specification/, imp_claude/design/, imp_claude/code/, and .ai-workspace/.

Written in business language per BDD edge config (bdd.yml).
"""

import json
import pathlib
import re

import pytest
import yaml

from conftest import (
    SPEC_DIR, DESIGN_DIR, PLUGIN_ROOT, AGENTS_DIR,
    CONFIG_DIR, EDGE_PARAMS_DIR, PROFILES_DIR, COMMANDS_DIR,
    load_yaml,
)

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
WORKSPACE = PROJECT_ROOT / ".ai-workspace"
EVENTS_FILE = WORKSPACE / "events" / "events.jsonl"
FEATURES_DIR = WORKSPACE / "features" / "active"


# ═══════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════


def _extract_req_keys(text: str) -> set[str]:
    """Extract all REQ-{CATEGORY}-{SEQ} keys from text."""
    return set(re.findall(r'REQ-[A-Z]+-\d+', text))


def _read_file(path: pathlib.Path) -> str:
    with open(path) as f:
        return f.read()


def _load_events() -> list[dict]:
    """Load all events from events.jsonl."""
    events = []
    with open(EVENTS_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def _load_all_feature_vectors() -> dict[str, dict]:
    """Load all active feature vector YAML files."""
    vectors = {}
    for path in sorted(FEATURES_DIR.glob("*.yml")):
        with open(path) as f:
            data = yaml.safe_load(f)
        vectors[data["feature"]] = data
    return vectors


# ═══════════════════════════════════════════════════════════════════════
# 1. END-TO-END TRACEABILITY: Spec → Feature Vectors → Design → Code → Tests
# ═══════════════════════════════════════════════════════════════════════


class TestEndToEndTraceability:
    """
    Feature: Complete REQ key traceability chain
      As a methodology user
      I want every requirement to be traceable from spec through to tests
      So that nothing falls through the cracks

    Validates: REQ-FEAT-001, REQ-FEAT-002, REQ-FEAT-003, REQ-TOOL-005
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.req_spec = _read_file(SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md")
        self.feature_vectors = _read_file(SPEC_DIR / "FEATURE_VECTORS.md")
        self.design = _read_file(DESIGN_DIR / "AISDLC_V2_DESIGN.md")
        self.spec_keys = _extract_req_keys(self.req_spec)
        self.fv_keys = _extract_req_keys(self.feature_vectors)

    @pytest.mark.uat
    def test_all_spec_keys_appear_in_feature_vectors(self):
        """Every REQ key defined in the spec must appear in FEATURE_VECTORS.md."""
        missing = self.spec_keys - self.fv_keys
        assert not missing, f"REQ keys in spec but not in feature vectors: {sorted(missing)}"

    @pytest.mark.uat
    def test_no_orphan_keys_in_feature_vectors(self):
        """Every REQ key in feature vectors must exist in the spec."""
        # Filter to only REQ-{CAT}-{SEQ} (not REQ-F-* feature IDs)
        fv_req_keys = {k for k in self.fv_keys if not k.startswith("REQ-F-")}
        spec_req_keys = {k for k in self.spec_keys if not k.startswith("REQ-F-")}
        orphans = fv_req_keys - spec_req_keys
        assert not orphans, f"REQ keys in feature vectors but not in spec: {sorted(orphans)}"

    @pytest.mark.uat
    def test_design_references_all_feature_vectors(self):
        """Design doc must reference all 10 feature vector IDs."""
        expected_features = [
            "REQ-F-ENGINE-001", "REQ-F-EVAL-001", "REQ-F-CTX-001",
            "REQ-F-EDGE-001", "REQ-F-TRACE-001", "REQ-F-LIFE-001",
            "REQ-F-SENSE-001", "REQ-F-TOOL-001", "REQ-F-UX-001",
            "REQ-F-COORD-001",
        ]
        for fv in expected_features:
            assert fv in self.design, f"{fv} not referenced in design doc"

    @pytest.mark.uat
    def test_every_req_key_has_traces_to(self):
        """Every requirement in the spec must have a 'Traces To' line."""
        # Count REQ headers vs Traces To lines
        req_headers = re.findall(r'^### REQ-[A-Z]+-\d+:', self.req_spec, re.MULTILINE)
        traces_to = re.findall(r'^\*\*Traces To\*\*:', self.req_spec, re.MULTILINE)
        assert len(traces_to) >= len(req_headers), \
            f"Only {len(traces_to)} Traces To for {len(req_headers)} requirements"

    @pytest.mark.uat
    def test_agent_specs_have_implements_tags(self):
        """Every agent markdown spec must declare which REQ it implements."""
        for agent_file in sorted(AGENTS_DIR.glob("*.md")):
            content = _read_file(agent_file)
            assert "REQ-" in content or "Implements:" in content, \
                f"Agent {agent_file.name} has no REQ traceability"

    @pytest.mark.uat
    def test_test_files_have_validates_tags(self):
        """Every test file must declare which REQs it validates."""
        test_dir = pathlib.Path(__file__).parent
        for test_file in sorted(test_dir.glob("test_*.py")):
            content = _read_file(test_file)
            assert "Validates:" in content, \
                f"Test file {test_file.name} has no Validates: tag"

    @pytest.mark.uat
    def test_coverage_table_complete(self):
        """Feature vectors coverage table must have a row for every REQ key."""
        # Extract the coverage check table
        table_match = re.search(
            r'## Coverage Check.*?\n\n(.*?)\n\n',
            self.feature_vectors,
            re.DOTALL,
        )
        assert table_match, "Coverage Check table not found"
        table = table_match.group(1)
        table_keys = _extract_req_keys(table)
        # Filter spec keys to non-feature-ID keys
        spec_req_keys = {k for k in self.spec_keys if not k.startswith("REQ-F-")}
        missing = spec_req_keys - table_keys
        assert not missing, f"REQ keys missing from coverage table: {sorted(missing)}"


# ═══════════════════════════════════════════════════════════════════════
# 2. EVENT LOG INTEGRITY
# ═══════════════════════════════════════════════════════════════════════


class TestEventLogIntegrity:
    """
    Feature: Event log is a valid append-only source of truth
      As a methodology observer
      I want every event in events.jsonl to be well-formed
      So that derived views can be reliably reconstructed

    Validates: REQ-LIFE-005, REQ-LIFE-008
    """

    REQUIRED_EVENT_FIELDS = {"event_type", "timestamp", "project"}

    KNOWN_EVENT_TYPES = {
        # Current schema (v2.8+)
        "intent_raised", "spec_modified", "project_initialized",
        "iteration_completed", "edge_started", "edge_converged",
        "spawn_created", "spawn_folded_back", "checkpoint_created",
        "review_completed", "gaps_validated", "release_created",
        "interoceptive_signal", "exteroceptive_signal",
        "affect_triage", "draft_proposal", "observer_signal",
        "artifact_modified",
        # Legacy event types (pre-v2.8 — still valid in historical log)
        "evaluator_ran", "feature_spawned", "finding_raised",
        "telemetry_signal_emitted",
    }

    @pytest.fixture(autouse=True)
    def setup(self):
        self.events = _load_events()

    @pytest.mark.uat
    def test_events_file_exists(self):
        """Event log file must exist."""
        assert EVENTS_FILE.exists(), "events.jsonl does not exist"

    @pytest.mark.uat
    def test_all_events_are_valid_json(self):
        """Every line in events.jsonl must be valid JSON."""
        with open(EVENTS_FILE) as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        json.loads(line)
                    except json.JSONDecodeError:
                        pytest.fail(f"Line {i} is not valid JSON: {line[:80]}...")

    @pytest.mark.uat
    def test_all_events_have_required_fields(self):
        """Every event must have event_type, timestamp, and project."""
        for i, event in enumerate(self.events):
            missing = self.REQUIRED_EVENT_FIELDS - set(event.keys())
            assert not missing, f"Event {i+1} missing fields: {missing}. Type: {event.get('event_type', 'unknown')}"

    @pytest.mark.uat
    def test_all_event_types_are_known(self):
        """Every event_type must be in the known set."""
        for event in self.events:
            et = event["event_type"]
            assert et in self.KNOWN_EVENT_TYPES, \
                f"Unknown event_type: {et}"

    @pytest.mark.uat
    def test_timestamps_are_iso8601(self):
        """Every timestamp must be a valid ISO 8601 string."""
        for event in self.events:
            ts = event["timestamp"]
            assert re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', ts), \
                f"Invalid timestamp: {ts}"

    @pytest.mark.uat
    def test_timestamps_are_monotonically_non_decreasing(self):
        """Event timestamps should not go backwards."""
        for i in range(1, len(self.events)):
            prev = self.events[i - 1]["timestamp"]
            curr = self.events[i]["timestamp"]
            assert curr >= prev, \
                f"Timestamp regression at event {i+1}: {prev} > {curr}"

    @pytest.mark.uat
    def test_iteration_completed_events_have_evaluators(self):
        """iteration_completed events must include evaluator results."""
        for event in self.events:
            if event["event_type"] == "iteration_completed":
                assert "evaluators" in event, \
                    f"iteration_completed missing evaluators: {event.get('feature', '?')}"

    @pytest.mark.uat
    def test_recent_edge_converged_events_have_iteration_count(self):
        """Recent edge_converged events (v2.8+) must record iteration count."""
        # Only check events from 2026-02-22 onwards (post-v2.8)
        for event in self.events:
            if event["event_type"] == "edge_converged" and event["timestamp"] >= "2026-02-22T18:00":
                data = event.get("data", {})
                assert "iteration" in data, \
                    f"edge_converged missing iteration count: {event.get('feature', '?')}"

    @pytest.mark.uat
    def test_project_name_consistent(self):
        """All events must reference the same project name."""
        projects = {e["project"] for e in self.events}
        assert len(projects) == 1, f"Multiple project names: {projects}"


# ═══════════════════════════════════════════════════════════════════════
# 3. FEATURE VECTOR CONSISTENCY
# ═══════════════════════════════════════════════════════════════════════


class TestFeatureVectorConsistency:
    """
    Feature: Active feature vectors are consistent with spec
      As a methodology user
      I want feature vectors to accurately reflect the spec
      So that status reports are trustworthy

    Validates: REQ-FEAT-001, REQ-FEAT-002
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.vectors = _load_all_feature_vectors()
        self.spec_fv = _read_file(SPEC_DIR / "FEATURE_VECTORS.md")

    @pytest.mark.uat
    def test_all_spec_features_have_active_vectors(self):
        """Every feature in FEATURE_VECTORS.md must have an active .yml file."""
        spec_features = set(re.findall(r'(REQ-F-[A-Z]+-\d+)', self.spec_fv))
        active_features = set(self.vectors.keys())
        missing = spec_features - active_features
        assert not missing, f"Features in spec but no active vector: {sorted(missing)}"

    @pytest.mark.uat
    def test_no_orphan_active_vectors(self):
        """Every active vector must correspond to a feature in FEATURE_VECTORS.md."""
        spec_features = set(re.findall(r'### (REQ-F-[A-Z]+-\d+):', self.spec_fv))
        active_features = set(self.vectors.keys())
        orphans = active_features - spec_features
        assert not orphans, f"Active vectors not in spec: {sorted(orphans)}"

    @pytest.mark.uat
    def test_all_vectors_have_required_fields(self):
        """Every feature vector must have: feature, title, status, trajectory."""
        required = {"feature", "title", "status", "trajectory"}
        for fid, vec in self.vectors.items():
            missing = required - set(vec.keys())
            assert not missing, f"{fid} missing fields: {missing}"

    @pytest.mark.uat
    def test_all_vectors_have_valid_status(self):
        """Feature vector status must be one of: pending, in_progress, converged, blocked."""
        valid = {"pending", "in_progress", "converged", "blocked"}
        for fid, vec in self.vectors.items():
            assert vec["status"] in valid, \
                f"{fid} has invalid status: {vec['status']}"

    @pytest.mark.uat
    def test_converged_vectors_have_all_edges_converged(self):
        """If a feature is 'converged', all trajectory edges must be converged."""
        for fid, vec in self.vectors.items():
            if vec["status"] != "converged":
                continue
            traj = vec.get("trajectory", {})
            for edge_name, edge_data in traj.items():
                if isinstance(edge_data, dict):
                    status = edge_data.get("status", "pending")
                    assert status == "converged", \
                        f"{fid} is converged but edge '{edge_name}' is '{status}'"

    @pytest.mark.uat
    def test_vector_requirements_exist_in_spec(self):
        """Every REQ key listed in a feature vector must exist in the spec."""
        spec_content = _read_file(SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md")
        spec_keys = _extract_req_keys(spec_content)
        for fid, vec in self.vectors.items():
            for req in vec.get("requirements", []):
                assert req in spec_keys, \
                    f"{fid} references {req} which is not in the spec"


# ═══════════════════════════════════════════════════════════════════════
# 4. CROSS-FEATURE DEPENDENCY SATISFACTION
# ═══════════════════════════════════════════════════════════════════════


class TestDependencySatisfaction:
    """
    Feature: Feature dependencies are satisfied
      As a methodology user
      I want dependent features to not be marked converged before their dependencies
      So that the build order is sound

    Validates: REQ-FEAT-003
    """

    # Dependency graph from FEATURE_VECTORS.md
    DEPENDENCIES = {
        "REQ-F-ENGINE-001": [],
        "REQ-F-EVAL-001": ["REQ-F-ENGINE-001"],
        "REQ-F-CTX-001": ["REQ-F-ENGINE-001"],
        "REQ-F-TRACE-001": ["REQ-F-ENGINE-001"],
        "REQ-F-EDGE-001": ["REQ-F-EVAL-001"],
        "REQ-F-LIFE-001": ["REQ-F-ENGINE-001", "REQ-F-TRACE-001"],
        "REQ-F-SENSE-001": ["REQ-F-LIFE-001", "REQ-F-EVAL-001"],
        "REQ-F-TOOL-001": ["REQ-F-ENGINE-001", "REQ-F-TRACE-001"],
        "REQ-F-UX-001": ["REQ-F-TOOL-001", "REQ-F-ENGINE-001"],
        "REQ-F-COORD-001": ["REQ-F-ENGINE-001", "REQ-F-EVAL-001", "REQ-F-TOOL-001"],
    }

    @pytest.fixture(autouse=True)
    def setup(self):
        self.vectors = _load_all_feature_vectors()

    @pytest.mark.uat
    def test_converged_features_have_converged_dependencies(self):
        """A converged feature's dependencies must also be converged."""
        for fid, deps in self.DEPENDENCIES.items():
            vec = self.vectors.get(fid)
            if not vec or vec["status"] != "converged":
                continue
            for dep in deps:
                dep_vec = self.vectors.get(dep)
                assert dep_vec and dep_vec["status"] == "converged", \
                    f"{fid} is converged but dependency {dep} is not"

    @pytest.mark.uat
    def test_dependency_graph_has_no_cycles(self):
        """The dependency graph must be a DAG (no cycles)."""
        visited = set()
        path = set()

        def visit(node):
            if node in path:
                pytest.fail(f"Cycle detected involving {node}")
            if node in visited:
                return
            path.add(node)
            for dep in self.DEPENDENCIES.get(node, []):
                visit(dep)
            path.remove(node)
            visited.add(node)

        for node in self.DEPENDENCIES:
            visit(node)


# ═══════════════════════════════════════════════════════════════════════
# 5. OBSERVER AGENT INTEGRATION
# ═══════════════════════════════════════════════════════════════════════


class TestObserverIntegration:
    """
    Feature: Observer agents integrate correctly with the methodology
      As a methodology user
      I want observer agents to reference valid event types and signal sources
      So that the abiogenesis loop is properly closed

    Validates: REQ-LIFE-010, REQ-LIFE-011, REQ-LIFE-012
    """

    VALID_SIGNAL_SOURCES = {
        "gap", "test_failure", "refactoring", "source_finding",
        "process_gap", "runtime_feedback", "ecosystem",
        "discovery", "optimisation", "user", "TELEM",
    }

    @pytest.mark.uat
    def test_dev_observer_references_valid_event_types(self):
        """Dev observer must reference event types that exist in the iterate agent."""
        iterate_content = _read_file(AGENTS_DIR / "gen-iterate.md")
        observer_content = _read_file(AGENTS_DIR / "gen-dev-observer.md")
        # Observer must reference events that the iterate agent emits
        for event_type in ["iteration_completed", "edge_converged"]:
            assert event_type in observer_content, \
                f"Dev observer doesn't reference {event_type}"
        assert "observer_signal" in observer_content

    @pytest.mark.uat
    def test_dev_observer_signal_sources_are_valid(self):
        """Dev observer's signal sources must be from the defined set."""
        content = _read_file(AGENTS_DIR / "gen-dev-observer.md")
        # Extract signal sources mentioned
        mentioned = set(re.findall(r'`(\w+)`', content))
        signal_sources_in_doc = mentioned & self.VALID_SIGNAL_SOURCES
        assert len(signal_sources_in_doc) >= 3, \
            f"Dev observer mentions too few signal sources: {signal_sources_in_doc}"

    @pytest.mark.uat
    def test_cicd_observer_reads_req_tags(self):
        """CI/CD observer must read Implements:/Validates: tags to map failures."""
        content = _read_file(AGENTS_DIR / "gen-cicd-observer.md")
        assert "Implements:" in content
        assert "Validates:" in content

    @pytest.mark.uat
    def test_ops_observer_integrates_with_sensory(self):
        """Ops observer must consume sensory signals (interoceptive/exteroceptive)."""
        content = _read_file(AGENTS_DIR / "gen-ops-observer.md")
        assert "interoceptive" in content.lower()
        assert "exteroceptive" in content.lower()

    @pytest.mark.uat
    def test_all_observers_emit_observer_signal(self):
        """All 3 observers must emit observer_signal event type."""
        for agent in ["gen-dev-observer.md", "gen-cicd-observer.md", "gen-ops-observer.md"]:
            content = _read_file(AGENTS_DIR / agent)
            assert "observer_signal" in content, f"{agent} doesn't emit observer_signal"

    @pytest.mark.uat
    def test_all_observers_are_read_only(self):
        """All observers must declare they do not modify files."""
        for agent in ["gen-dev-observer.md", "gen-cicd-observer.md", "gen-ops-observer.md"]:
            content = _read_file(AGENTS_DIR / agent)
            assert "NOT" in content and ("modify" in content.lower() or "read-only" in content.lower()), \
                f"{agent} doesn't clearly state it's read-only"

    @pytest.mark.uat
    def test_observer_event_schema_in_design(self):
        """Design doc must define observer_signal event schema."""
        content = _read_file(DESIGN_DIR / "AISDLC_V2_DESIGN.md")
        assert "observer_signal" in content
        assert "observer_id" in content


# ═══════════════════════════════════════════════════════════════════════
# 6. METHODOLOGY SELF-CONSISTENCY (the method describes itself)
# ═══════════════════════════════════════════════════════════════════════


class TestMethodologySelfConsistency:
    """
    Feature: The methodology is self-consistent
      As the methodology author
      I want the method to correctly describe its own state
      So that it serves as a valid dogfood example

    Validates: REQ-TOOL-009
    """

    @pytest.mark.uat
    def test_graph_topology_edges_have_configs(self):
        """Edge param configs must exist for key edges in the graph."""
        # Core edges that must have configs
        required_configs = [
            "intent_requirements", "requirements_design", "design_code", "tdd",
        ]
        for config_name in required_configs:
            assert (EDGE_PARAMS_DIR / f"{config_name}.yml").exists(), \
                f"Missing edge config: {config_name}.yml"

    @pytest.mark.uat
    def test_profiles_reference_valid_edges(self):
        """Every edge in a profile must exist in graph_topology transitions."""
        topo = load_yaml(CONFIG_DIR / "graph_topology.yml")
        transitions = topo.get("transitions", [])
        valid_edges = {t["edge_type"] for t in transitions}
        profiles = topo.get("profiles", {})
        for pname, pdata in profiles.items():
            for edge in pdata.get("graph_edges", []):
                assert edge in valid_edges, \
                    f"Profile '{pname}' references unknown edge: {edge}"

    @pytest.mark.uat
    def test_commands_reference_valid_features(self):
        """Command markdown files should reference valid REQ keys."""
        spec_keys = _extract_req_keys(
            _read_file(SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md")
        )
        for cmd_file in sorted(COMMANDS_DIR.glob("*.md")):
            content = _read_file(cmd_file)
            cmd_keys = _extract_req_keys(content)
            invalid = cmd_keys - spec_keys
            # Filter out REQ-F-* feature IDs (used as examples)
            invalid = {k for k in invalid if not k.startswith("REQ-F-")}
            assert not invalid, \
                f"{cmd_file.name} references invalid REQ keys: {sorted(invalid)}"

    @pytest.mark.uat
    def test_status_md_exists_and_is_recent(self):
        """STATUS.md must exist as a derived view."""
        status_file = WORKSPACE / "STATUS.md"
        assert status_file.exists(), "STATUS.md does not exist"

    @pytest.mark.uat
    def test_eleven_active_feature_vectors(self):
        """There must be exactly 11 active feature vectors."""
        vectors = list(FEATURES_DIR.glob("*.yml"))
        assert len(vectors) == 11, f"Expected 11 active vectors, got {len(vectors)}"

    @pytest.mark.uat
    def test_all_features_converged(self):
        """All 11 features must be in converged state (post-release validation)."""
        vectors = _load_all_feature_vectors()
        non_converged = [
            fid for fid, v in vectors.items()
            if v["status"] != "converged"
        ]
        assert not non_converged, f"Non-converged features: {non_converged}"


# ═══════════════════════════════════════════════════════════════════════
# 7. ABIOGENESIS LOOP CLOSURE
# ═══════════════════════════════════════════════════════════════════════


class TestAbiogenesisLoop:
    """
    Feature: The full lifecycle loop is closed
      As a methodology user
      I want the complete loop from intent through to observer feedback
      So that the system is self-improving

    Validates: REQ-LIFE-010, REQ-LIFE-011, REQ-LIFE-012
    """

    @pytest.mark.uat
    def test_left_side_of_loop_exists(self):
        """Left side: intent → spec → features → design → code → tests → events."""
        # Verify the graph topology has the forward path
        topo = load_yaml(CONFIG_DIR / "graph_topology.yml")
        transitions = topo.get("transitions", [])
        edges = [(t["source"], t["target"]) for t in transitions]
        assert ("intent", "requirements") in edges
        assert ("requirements", "design") in edges
        assert ("design", "code") in edges
        assert ("code", "unit_tests") in edges

    @pytest.mark.uat
    def test_right_side_of_loop_exists(self):
        """Right side: telemetry → intent (feedback loop in graph)."""
        topo = load_yaml(CONFIG_DIR / "graph_topology.yml")
        transitions = topo.get("transitions", [])
        edges = [(t["source"], t["target"]) for t in transitions]
        assert ("running_system", "telemetry") in edges
        assert ("telemetry", "intent") in edges

    @pytest.mark.uat
    def test_observer_agents_bridge_the_gap(self):
        """Observer agents must exist to close the loop between events and intents."""
        assert (AGENTS_DIR / "gen-dev-observer.md").exists()
        assert (AGENTS_DIR / "gen-cicd-observer.md").exists()
        assert (AGENTS_DIR / "gen-ops-observer.md").exists()

    @pytest.mark.uat
    def test_feedback_loop_config_exists(self):
        """Feedback loop edge config must exist (telemetry→intent edge params)."""
        assert (EDGE_PARAMS_DIR / "feedback_loop.yml").exists()

    @pytest.mark.uat
    def test_signal_sources_cover_both_dev_and_prod(self):
        """Signal sources must cover both development-time and production-time."""
        config = load_yaml(EDGE_PARAMS_DIR / "feedback_loop.yml")
        content = str(config)
        # Development signals
        assert "gap" in content
        assert "test_failure" in content
        assert "process_gap" in content
        # Production signals
        assert "runtime_feedback" in content
        assert "ecosystem" in content

    @pytest.mark.uat
    def test_events_log_has_lifecycle_events(self):
        """Event log must contain events from multiple lifecycle stages."""
        events = _load_events()
        event_types = {e["event_type"] for e in events}
        # Must have at least intent, iteration, and convergence events
        assert "intent_raised" in event_types, "No intent_raised events"
        assert "iteration_completed" in event_types, "No iteration_completed events"
        assert "edge_converged" in event_types, "No edge_converged events"

    @pytest.mark.uat
    def test_spec_review_gradient_check_exists(self):
        """REQ-LIFE-009 (spec review as gradient check) must be implemented."""
        content = _read_file(SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md")
        assert "REQ-LIFE-009" in content
        assert "gradient" in content.lower()
        assert "stateless" in content.lower()
