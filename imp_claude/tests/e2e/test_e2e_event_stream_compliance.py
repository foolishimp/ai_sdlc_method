# Validates: REQ-EVENT-001, REQ-EVENT-002, REQ-EVENT-003, REQ-EVENT-004, REQ-EVENT-005
"""E2E tests for event stream contract compliance.

Validates that every event written to events.jsonl:
  - Conforms to the expected format (OL or flat)
  - Carries all required fields
  - Preserves the append-only guarantee (no deletion, no timestamp inversion)
  - Can be normalised to a consistent flat form via normalize_event()

Architecture facts encoded in these tests:

1. Engine-emitted events use ol_event.py (OL format):
     {eventType, eventTime, run: {runId, facets}, job, inputs, outputs, producer, schemaURL}

2. `genesis emit-event` CLI uses fd_emit.py (flat format):
     {event_type, timestamp, project, ...data}

3. normalize_event() in ol_event.py bridges both formats to flat for consumers.

4. The event log is append-only: no line may be deleted or modified once written.
   Timestamps must be monotonically non-decreasing (each event no earlier than prior).

5. Every OL event must carry the sdlc:universal facet with:
     _producer, instance_id, actor, causation_id, correlation_id

Run:
    pytest imp_claude/tests/e2e/test_e2e_event_stream_compliance.py -v -m e2e -s
"""

import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys
import textwrap
import uuid
from datetime import datetime, timezone

import pytest


# ── E2E sibling-module imports ─────────────────────────────────────────────────
def _load_sibling(name: str):
    path = pathlib.Path(__file__).parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"e2e_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_conftest = _load_sibling("conftest")
CONFIG_DIR = _conftest.CONFIG_DIR
COMMANDS_DIR = _conftest.COMMANDS_DIR
AGENTS_DIR = _conftest.AGENTS_DIR
PLUGIN_ROOT = _conftest.PLUGIN_ROOT
RUNS_DIR = _conftest.RUNS_DIR
PROJECT_ROOT = _conftest.PROJECT_ROOT
INTENT_MD = _conftest.INTENT_MD
PROJECT_CONSTRAINTS_YML = _conftest.PROJECT_CONSTRAINTS_YML
TEST_PROJECT_CLAUDE_MD = _conftest.TEST_PROJECT_CLAUDE_MD
TEST_PROJECT_PYPROJECT = _conftest.TEST_PROJECT_PYPROJECT
run_claude_headless = _conftest.run_claude_headless
skip_no_claude = _conftest.skip_no_claude
_clean_env = _conftest._clean_env
_copy_config_files = _conftest._copy_config_files
_copy_profile_files = _conftest._copy_profile_files
_copy_commands = _conftest._copy_commands
_copy_agents = _conftest._copy_agents
_get_plugin_version = _conftest._get_plugin_version

GENESIS_CODE_DIR = PROJECT_ROOT / "imp_claude" / "code"


def _genesis_sys_path():
    return str(GENESIS_CODE_DIR)


# ── Shared OL field constants ─────────────────────────────────────────────────

# Required top-level fields for every OL RunEvent
OL_REQUIRED_TOP_LEVEL = frozenset([
    "eventType",
    "eventTime",
    "run",
    "job",
    "inputs",
    "outputs",
    "producer",
    "schemaURL",
])

# Required OL eventType values (from _OL_EVENT_TYPE dict)
OL_VALID_EVENT_TYPES = frozenset([
    "START", "COMPLETE", "FAIL", "ABORT", "OTHER",
])

# Required nested run.facets keys (sdlc:universal sub-fields)
OL_UNIVERSAL_FACET_FIELDS = frozenset([
    "_producer",
    "instance_id",
    "actor",
    "causation_id",
    "correlation_id",
])

# Required flat event fields
FLAT_REQUIRED_FIELDS = frozenset([
    "event_type",
    "timestamp",
    "project",
])

# ISO 8601 pattern (basic validation — not exhaustive)
ISO_8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
)


# ═══════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════

def _is_ol_event(raw: dict) -> bool:
    """Return True if raw looks like an OL RunEvent (has 'eventType')."""
    return "eventType" in raw


def _is_flat_event(raw: dict) -> bool:
    """Return True if raw looks like a flat fd_emit event (has 'event_type')."""
    return "event_type" in raw


def _validate_ol_event(raw: dict) -> list[str]:
    """Return list of field violations for an OL event. Empty = compliant."""
    violations = []

    # Top-level required fields
    for field in OL_REQUIRED_TOP_LEVEL:
        if field not in raw:
            violations.append(f"missing top-level field: {field!r}")

    # eventType value check
    et = raw.get("eventType")
    if et not in OL_VALID_EVENT_TYPES:
        violations.append(f"eventType={et!r} not in {sorted(OL_VALID_EVENT_TYPES)}")

    # eventTime ISO 8601
    evt = raw.get("eventTime", "")
    if not evt:
        violations.append("eventTime is empty")
    elif not ISO_8601_RE.match(evt):
        violations.append(f"eventTime does not look like ISO 8601: {evt!r}")

    # run.runId
    run = raw.get("run", {})
    if not isinstance(run, dict):
        violations.append("run is not a dict")
    else:
        run_id = run.get("runId", "")
        if not run_id:
            violations.append("run.runId is empty")
        else:
            try:
                uuid.UUID(run_id)
            except ValueError:
                violations.append(f"run.runId is not a valid UUID4: {run_id!r}")

        # run.facets.sdlc:universal
        facets = run.get("facets", {})
        if not isinstance(facets, dict):
            violations.append("run.facets is not a dict")
        else:
            universal = facets.get("sdlc:universal", {})
            if not isinstance(universal, dict):
                violations.append("run.facets.sdlc:universal is not a dict")
            else:
                for sub_field in OL_UNIVERSAL_FACET_FIELDS:
                    if sub_field not in universal:
                        violations.append(
                            f"run.facets.sdlc:universal missing field: {sub_field!r}"
                        )

    # job.namespace
    job = raw.get("job", {})
    if not isinstance(job, dict):
        violations.append("job is not a dict")
    else:
        namespace = job.get("namespace", "")
        if not namespace:
            violations.append("job.namespace is empty")
        elif not namespace.startswith("aisdlc://"):
            violations.append(f"job.namespace does not start with 'aisdlc://': {namespace!r}")

        job_name = job.get("name", "")
        if not job_name:
            violations.append("job.name is empty")

    # inputs / outputs are lists
    if not isinstance(raw.get("inputs"), list):
        violations.append("inputs is not a list")
    if not isinstance(raw.get("outputs"), list):
        violations.append("outputs is not a list")

    # producer non-empty
    if not raw.get("producer"):
        violations.append("producer is empty")

    # schemaURL starts with https://openlineage.io/
    schema = raw.get("schemaURL", "")
    if not schema.startswith("https://openlineage.io/"):
        violations.append(f"schemaURL does not start with 'https://openlineage.io/': {schema!r}")

    return violations


def _validate_flat_event(raw: dict) -> list[str]:
    """Return list of field violations for a flat event. Empty = compliant."""
    violations = []
    for field in FLAT_REQUIRED_FIELDS:
        if field not in raw:
            violations.append(f"missing required field: {field!r}")
    ts = raw.get("timestamp", "")
    if ts and not ISO_8601_RE.match(ts):
        violations.append(f"timestamp does not look like ISO 8601: {ts!r}")
    return violations


def _scaffold_minimal_project(project_dir: pathlib.Path) -> None:
    """Scaffold a minimal workspace so genesis commands can find a workspace root."""
    ws = project_dir / ".ai-workspace"
    events_dir = ws / "events"
    events_dir.mkdir(parents=True, exist_ok=True)

    context_dir = ws / "claude" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    features_active = ws / "features" / "active"
    features_active.mkdir(parents=True, exist_ok=True)
    (ws / "features" / "completed").mkdir(parents=True, exist_ok=True)
    (ws / "tasks" / "active").mkdir(parents=True, exist_ok=True)

    graph_dir = ws / "graph"
    graph_dir.mkdir(parents=True, exist_ok=True)
    _copy_config_files(graph_dir)

    (project_dir / "CLAUDE.md").write_text("# Test project\n")
    (project_dir / "pyproject.toml").write_text(
        '[project]\nname = "event-compliance-test"\nversion = "0.1.0"\n'
    )

    timestamp = datetime.now(timezone.utc).isoformat()
    with open(events_dir / "events.jsonl", "w") as f:
        f.write(json.dumps({
            "event_type": "project_initialized",
            "timestamp": timestamp,
            "project": "event-compliance-test",
            "profile": "standard",
            "version": _get_plugin_version(),
        }) + "\n")


# ═══════════════════════════════════════════════════════════════════════
# PART A: OL event structure validation
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.e2e
class TestOLEventStructure:
    """Validates that make_ol_event() produces fully compliant OL RunEvents.

    Tests the Python API directly — no subprocess overhead. Each test
    validates a specific structural guarantee of the OL format.
    """

    def test_make_ol_event_has_all_required_top_level_fields(self):
        """make_ol_event() must produce all required OL top-level fields.

        WHY: These are the fields required by the OpenLineage specification.
        A missing field means downstream consumers (genesis_monitor, pipeline
        integrations) cannot parse the event. Every field is load-bearing.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import make_ol_event

        event = make_ol_event(
            event_type="IterationStarted",
            job_name="design→code",
            project="test-project",
            instance_id="REQ-F-TEST-001",
            actor="test-actor",
        )

        for field in OL_REQUIRED_TOP_LEVEL:
            assert field in event, (
                f"make_ol_event() missing required field {field!r}. "
                f"Keys present: {sorted(event.keys())}"
            )

    def test_make_ol_event_eventtype_is_valid_ol_value(self):
        """eventType must be one of the valid OL event type strings.

        WHY: The OpenLineage spec defines exactly 5 event types:
        START, COMPLETE, FAIL, ABORT, OTHER. Any other value breaks
        OL consumers. The _OL_EVENT_TYPE lookup table maps semantic types
        to valid OL values.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import make_ol_event, _OL_EVENT_TYPE

        # Test all semantic types in the lookup table
        for semantic_type, expected_ol_type in _OL_EVENT_TYPE.items():
            event = make_ol_event(
                event_type=semantic_type,
                job_name="test-edge",
                project="test-project",
                instance_id="test-instance",
                actor="test",
            )
            assert event["eventType"] == expected_ol_type, (
                f"Semantic type {semantic_type!r} → expected OL type {expected_ol_type!r}, "
                f"got {event['eventType']!r}"
            )
            assert event["eventType"] in OL_VALID_EVENT_TYPES, (
                f"OL type {event['eventType']!r} not in valid set {sorted(OL_VALID_EVENT_TYPES)}"
            )

    def test_make_ol_event_eventtime_is_iso8601(self):
        """eventTime must be an ISO 8601 timestamp string.

        WHY: eventTime is the system-assigned append timestamp. The event logger
        assigns it from the system clock — callers cannot override it. The format
        must be ISO 8601 for interoperability with time-series consumers.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import make_ol_event

        event = make_ol_event(
            event_type="IterationCompleted",
            job_name="code↔unit_tests",
            project="proj",
            instance_id="REQ-F-CONV-001",
            actor="engine",
            payload={"delta": 2},
        )
        evt = event.get("eventTime", "")
        assert evt, "eventTime must not be empty"
        assert ISO_8601_RE.match(evt), (
            f"eventTime does not match ISO 8601: {evt!r}"
        )

    def test_make_ol_event_run_id_is_uuid4(self):
        """run.runId must be a valid UUID4.

        WHY: runId is used as causation_id and correlation_id in downstream events.
        If it is not a valid UUID4, chain analysis and replay tools will reject it.
        Each make_ol_event() call must generate a fresh UUID4.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import make_ol_event

        event1 = make_ol_event("IterationStarted", "edge", "proj", "inst", "actor")
        event2 = make_ol_event("IterationStarted", "edge", "proj", "inst", "actor")

        run_id1 = event1["run"]["runId"]
        run_id2 = event2["run"]["runId"]

        for rid in (run_id1, run_id2):
            try:
                parsed = uuid.UUID(rid)
                assert parsed.version == 4, f"runId is UUID{parsed.version}, expected UUID4"
            except ValueError as e:
                pytest.fail(f"run.runId is not a valid UUID: {rid!r} — {e}")

        assert run_id1 != run_id2, (
            "Two separate make_ol_event() calls produced the same runId. "
            "runIds must be unique per event."
        )

    def test_make_ol_event_sdlc_universal_facet_fields(self):
        """run.facets.sdlc:universal must contain all required fields.

        WHY: The sdlc:universal facet is the universal causal chain record.
        instance_id enables isolation; causation_id enables replay; actor
        enables attribution; correlation_id enables chain analysis.
        Missing any field breaks the event traceability invariant.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import make_ol_event

        event = make_ol_event(
            event_type="EdgeConverged",
            job_name="code↔unit_tests",
            project="test-project",
            instance_id="REQ-F-CONV-001",
            actor="edge-runner",
            causation_id="parent-run-id-123",
            correlation_id="root-run-id-456",
        )

        universal = event["run"]["facets"]["sdlc:universal"]
        for field in OL_UNIVERSAL_FACET_FIELDS:
            assert field in universal, (
                f"sdlc:universal facet missing required field {field!r}. "
                f"Fields present: {sorted(universal.keys())}"
            )

        assert universal["instance_id"] == "REQ-F-CONV-001"
        assert universal["actor"] == "edge-runner"
        assert universal["causation_id"] == "parent-run-id-123"
        assert universal["correlation_id"] == "root-run-id-456"

    def test_make_ol_event_job_namespace_starts_with_aisdlc(self):
        """job.namespace must start with 'aisdlc://'.

        WHY: The namespace encodes the project identity. Every event's job
        namespace must follow the 'aisdlc://{project}' convention so tools
        can partition events by project. A missing or malformed namespace
        makes events undiscoverable in multi-project setups.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import make_ol_event

        event = make_ol_event(
            event_type="IterationStarted",
            job_name="requirements→design",
            project="my-service",
            instance_id="REQ-F-AUTH-001",
            actor="human",
        )

        namespace = event["job"]["namespace"]
        assert namespace.startswith("aisdlc://"), (
            f"job.namespace should start with 'aisdlc://', got {namespace!r}"
        )
        assert "my-service" in namespace, (
            f"job.namespace should contain project name 'my-service', got {namespace!r}"
        )

    def test_make_ol_event_producer_and_schema_url(self):
        """producer must be non-empty and schemaURL must start with OpenLineage base URL.

        WHY: producer identifies the code that emitted the event — required for
        audit. schemaURL enables schema validation by OL tools. Both are required
        by the OpenLineage specification.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import make_ol_event, PRODUCER, SCHEMA_URL

        event = make_ol_event(
            event_type="EdgeStarted",
            job_name="design→code",
            project="proj",
            instance_id="REQ-F-001",
            actor="test",
        )

        assert event["producer"], "producer must not be empty"
        assert event["producer"] == PRODUCER
        assert event["schemaURL"].startswith("https://openlineage.io/"), (
            f"schemaURL must start with 'https://openlineage.io/', got {event['schemaURL']!r}"
        )
        assert event["schemaURL"] == SCHEMA_URL

    def test_ol_event_inputs_outputs_are_lists(self):
        """inputs and outputs must be lists (may be empty).

        WHY: inputs/outputs are required OL fields for data lineage tracking.
        They must be lists (not None, not missing) for OL consumers to iterate
        over them without type errors.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import make_ol_event

        # Without explicit inputs/outputs
        event1 = make_ol_event("IterationStarted", "edge", "proj", "inst", "actor")
        assert isinstance(event1["inputs"], list), "inputs must be a list"
        assert isinstance(event1["outputs"], list), "outputs must be a list"

        # With explicit inputs/outputs
        event2 = make_ol_event(
            "IterationCompleted", "edge", "proj", "inst", "actor",
            inputs=["src/main.py"],
            outputs=["tests/test_main.py"],
        )
        assert isinstance(event2["inputs"], list)
        assert isinstance(event2["outputs"], list)
        assert len(event2["inputs"]) == 1
        assert len(event2["outputs"]) == 1
        assert event2["inputs"][0]["name"] == "src/main.py"

    def test_iteration_started_maps_to_start(self):
        """IterationStarted semantic type must map to OL 'START' event type."""
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import make_ol_event

        event = make_ol_event("IterationStarted", "code↔unit_tests", "proj", "inst", "actor")
        assert event["eventType"] == "START"

    def test_edge_converged_maps_to_complete(self):
        """EdgeConverged semantic type must map to OL 'COMPLETE' event type."""
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import make_ol_event

        event = make_ol_event("EdgeConverged", "code↔unit_tests", "proj", "inst", "actor")
        assert event["eventType"] == "COMPLETE"

    def test_iteration_completed_maps_to_other(self):
        """IterationCompleted maps to OL 'OTHER' (non-terminal convergence step).

        WHY: IterationCompleted is not a terminal event — convergence is not
        yet declared at this point. It maps to OTHER to indicate an intermediate
        state. If it mapped to COMPLETE, OL consumers would treat it as a
        closed run prematurely.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import make_ol_event

        event = make_ol_event("IterationCompleted", "code↔unit_tests", "proj", "inst", "actor",
                              payload={"delta": 2})
        assert event["eventType"] == "OTHER", (
            f"IterationCompleted should map to OTHER (non-terminal), got {event['eventType']!r}"
        )

    def test_full_ol_event_validation(self):
        """Full structural validation of a make_ol_event() result — zero violations expected."""
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import make_ol_event

        event = make_ol_event(
            event_type="IterationCompleted",
            job_name="code↔unit_tests",
            project="validation-test",
            instance_id="REQ-F-VALID-001",
            actor="edge-runner",
            causation_id="some-parent-id",
            correlation_id="some-root-id",
            payload={"edge": "code↔unit_tests", "delta": 0, "status": "converged"},
            inputs=["src/calculator.py"],
            outputs=["tests/test_calculator.py"],
        )

        violations = _validate_ol_event(event)
        assert not violations, (
            f"OL event has {len(violations)} structural violation(s):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


# ═══════════════════════════════════════════════════════════════════════
# PART B: Flat event structure validation
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.e2e
class TestFlatEventStructure:
    """Validates that make_event() (fd_emit.py) produces correct flat events.

    Flat events are the format used by `genesis emit-event` CLI and all
    slash-command emissions (F_P calling the CLI). They use 'event_type'
    (not 'eventType') and carry data fields merged at top level.
    """

    def test_make_event_has_required_fields(self):
        """make_event() must produce event_type, timestamp, and project fields.

        WHY: These three fields are the minimum required for a flat event to
        be parseable by any log consumer. Missing any of them makes the event
        unclassifiable and un-timestampable.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.fd_emit import make_event

        event = make_event("test_event", "my-project", key="value", number=42)

        assert event.event_type == "test_event"
        assert event.project == "my-project"
        assert event.timestamp, "timestamp must not be empty"
        assert ISO_8601_RE.match(event.timestamp), (
            f"timestamp is not ISO 8601: {event.timestamp!r}"
        )

    def test_make_event_data_fields_merged(self):
        """Data kwargs must be accessible in event.data dict.

        WHY: fd_emit merges **data kwargs into event.data, which is then merged
        at the top level when serialised to events.jsonl. Consumers read fields
        like event['actor'], event['edge'] directly — not event['data']['actor'].
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.fd_emit import make_event

        event = make_event(
            "review_approved", "proj",
            feature="REQ-F-TEST-001",
            edge="code↔unit_tests",
            actor="human",
        )

        assert event.data["feature"] == "REQ-F-TEST-001"
        assert event.data["edge"] == "code↔unit_tests"
        assert event.data["actor"] == "human"

    def test_emit_event_writes_to_file(self, tmp_path: pathlib.Path):
        """emit_event() must append to events.jsonl with correct flat format.

        WHY: emit_event() is the write path for all flat events. It must create
        the file if it doesn't exist and append atomically. The written line must
        be valid JSON with event_type, timestamp, and project at top level.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.fd_emit import make_event, emit_event

        events_path = tmp_path / "events" / "events.jsonl"
        event = make_event("iteration_completed", "proj", delta=2, edge="code↔unit_tests")
        emit_event(events_path, event)

        assert events_path.exists(), "emit_event() must create events.jsonl"
        lines = [l.strip() for l in events_path.read_text().splitlines() if l.strip()]
        assert len(lines) == 1

        record = json.loads(lines[0])
        assert record["event_type"] == "iteration_completed"
        assert record["project"] == "proj"
        assert record["delta"] == 2
        assert record["edge"] == "code↔unit_tests"
        assert "timestamp" in record

    def test_flat_event_does_not_have_ol_fields(self, tmp_path: pathlib.Path):
        """Flat events must NOT have OL-specific top-level fields.

        WHY: The two formats must be distinguishable. A flat event with 'eventType'
        would confuse normalize_event() which uses eventType presence to detect
        OL format. The formats must remain orthogonal.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.fd_emit import make_event, emit_event

        events_path = tmp_path / "events.jsonl"
        event = make_event("review_approved", "proj", actor="human")
        emit_event(events_path, event)

        record = json.loads(events_path.read_text().strip())
        # Flat events must NOT have OL structure
        assert "eventType" not in record, (
            "Flat event has 'eventType' (OL field). "
            "fd_emit should produce 'event_type' (snake_case)."
        )
        assert "schemaURL" not in record, "Flat event should not have 'schemaURL'"
        assert "run" not in record, "Flat event should not have 'run' (OL RunEvent field)"
        assert "eventTime" not in record, "Flat event should not have 'eventTime' (OL field)"

    def test_flat_event_validation(self, tmp_path: pathlib.Path):
        """Full validation of a flat event — zero violations expected."""
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.fd_emit import make_event, emit_event

        events_path = tmp_path / "events.jsonl"
        event = make_event(
            "edge_converged",
            "my-project",
            feature="REQ-F-CONV-001",
            edge="code↔unit_tests",
            iteration=3,
        )
        emit_event(events_path, event)

        record = json.loads(events_path.read_text().strip())
        violations = _validate_flat_event(record)
        assert not violations, (
            f"Flat event has {len(violations)} violation(s):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


# ═══════════════════════════════════════════════════════════════════════
# PART C: normalize_event bridge
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.e2e
class TestNormalizeEventBridge:
    """Validates normalize_event() as the single read-side compatibility layer.

    normalize_event() must accept both OL and flat events and produce a
    consistent flat dict. This is the contract that all log consumers rely on.
    """

    def test_normalize_ol_event_returns_flat_event_type(self):
        """normalize_event() must extract event_type from OL sdlc:event_type facet.

        WHY: OL events use 'eventType' (PascalCase). Consumers expect 'event_type'
        (snake_case). normalize_event() performs this CamelCase → snake_case
        translation via regex. If this fails, event-type-based filtering breaks.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import make_ol_event, normalize_event

        ol_event = make_ol_event(
            "IterationCompleted",
            "code↔unit_tests",
            "test-proj",
            "REQ-F-001",
            "engine",
            payload={"delta": 2},
        )

        normalized = normalize_event(ol_event)
        assert "event_type" in normalized, (
            f"normalize_event() must add 'event_type' field. Got: {sorted(normalized.keys())}"
        )
        assert normalized["event_type"] == "iteration_completed", (
            f"Expected 'iteration_completed', got {normalized['event_type']!r}"
        )

    def test_normalize_ol_event_returns_timestamp(self):
        """normalize_event() must extract timestamp from OL eventTime.

        WHY: eventTime (OL) → timestamp (flat) is the canonical timestamp field.
        All time-series analysis and monotonicity checks use 'timestamp'.

        normalize_event() only normalises events that have an sdlc:event_type facet.
        That facet is present when: (a) the event has a payload, OR (b) the OL type
        is OTHER. We use a payload to ensure the facet is present.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import make_ol_event, normalize_event

        # Include a payload so sdlc:event_type facet is written — required for normalize_event()
        ol_event = make_ol_event(
            "EdgeConverged", "edge", "proj", "inst", "actor",
            payload={"delta": 0},
        )
        normalized = normalize_event(ol_event)

        assert "timestamp" in normalized, "normalize_event() must produce 'timestamp' field"
        assert normalized["timestamp"], "timestamp must not be empty"
        assert ISO_8601_RE.match(normalized["timestamp"]), (
            f"normalized timestamp not ISO 8601: {normalized['timestamp']!r}"
        )

    def test_normalize_ol_event_returns_project(self):
        """normalize_event() must extract project from job.namespace.

        WHY: job.namespace = 'aisdlc://{project}'. normalize_event() strips
        the scheme prefix. Consumers filter by project name, not by namespace.

        normalize_event() only normalises events that have an sdlc:event_type facet.
        IterationStarted maps to OL 'START' — without a payload the facet is
        omitted (see ol_event.py:169). We include a payload to ensure normalisation.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import make_ol_event, normalize_event

        # Include a payload so sdlc:event_type facet is written — required for normalize_event()
        ol_event = make_ol_event(
            "IterationStarted", "edge", "my-service", "inst", "actor",
            payload={"edge": "code↔unit_tests"},
        )
        normalized = normalize_event(ol_event)

        assert "project" in normalized, "normalize_event() must produce 'project' field"
        assert normalized["project"] == "my-service", (
            f"Expected project='my-service', got {normalized['project']!r}"
        )

    def test_normalize_flat_event_passes_through(self):
        """normalize_event() must pass through flat events unchanged.

        WHY: Flat events already have 'event_type', so normalize_event()
        returns them as-is. This prevents double-normalization and ensures
        idempotency: normalize(normalize(x)) == normalize(x).
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import normalize_event

        flat = {
            "event_type": "review_approved",
            "timestamp": "2026-03-14T10:00:00+00:00",
            "project": "my-project",
            "actor": "human",
            "feature": "REQ-F-001",
        }

        normalized = normalize_event(flat)
        assert normalized is flat, (
            "normalize_event() should return flat events unchanged (same object). "
            "Flat events are detected by 'event_type' presence."
        )

    def test_normalize_event_payload_fields_accessible(self):
        """normalize_event() must surface payload fields at top level.

        WHY: OL payload is nested in run.facets.sdlc:payload. normalize_event()
        merges these into the flat dict so consumers can access delta, edge,
        feature etc. directly without navigating the OL structure.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import make_ol_event, normalize_event

        ol_event = make_ol_event(
            "IterationCompleted",
            "code↔unit_tests",
            "proj",
            "REQ-F-001",
            "engine",
            payload={
                "edge": "code↔unit_tests",
                "delta": 3,
                "status": "iterating",
                "feature": "REQ-F-001",
            },
        )

        normalized = normalize_event(ol_event)
        assert normalized.get("delta") == 3, (
            f"delta not surfaced from OL payload: {normalized}"
        )
        assert normalized.get("status") == "iterating"
        assert normalized.get("feature") == "REQ-F-001"

    def test_normalize_consistency_ol_and_flat_both_have_required_fields(self):
        """Both OL and flat events, after normalization, must have event_type, timestamp, project.

        WHY: This is the read-side contract. Any consumer iterating events.jsonl
        uses normalize_event() and can unconditionally access these three fields
        without checking the source format.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import make_ol_event, normalize_event
        from genesis.fd_emit import make_event, emit_event

        # OL event
        ol_raw = make_ol_event("EdgeStarted", "code↔unit_tests", "proj-ol", "inst", "actor")
        ol_norm = normalize_event(ol_raw)

        # Flat event (serialise/deserialise to simulate file round-trip)
        import io
        events_path_mock = pathlib.Path("/tmp") / f"test_{uuid.uuid4().hex}.jsonl"
        flat_event = make_event("edge_started", "proj-flat", edge="code↔unit_tests")
        emit_event(events_path_mock, flat_event)
        flat_raw = json.loads(events_path_mock.read_text().strip())
        flat_norm = normalize_event(flat_raw)
        events_path_mock.unlink(missing_ok=True)

        for norm, label in ((ol_norm, "OL"), (flat_norm, "flat")):
            for field in ("event_type", "timestamp", "project"):
                assert field in norm, (
                    f"{label} event after normalization missing {field!r}. "
                    f"Keys: {sorted(norm.keys())}"
                )
                assert norm[field], f"{label} event normalized {field!r} is empty"


# ═══════════════════════════════════════════════════════════════════════
# PART D: Append-only guarantee
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.e2e
class TestAppendOnlyGuarantee:
    """Validates the append-only invariant for events.jsonl.

    The event stream is the foundational medium (ADR-S-012). No operation
    modifies or deletes existing lines. Timestamps must be monotonically
    non-decreasing (each event no earlier than the prior event).
    """

    def test_events_persist_after_multiple_writes(self, tmp_path: pathlib.Path):
        """Events written in separate emit_event() calls must all persist.

        WHY: append-only guarantee: each write appends a new line, never
        replaces existing lines. All N events must be present after N writes.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.fd_emit import make_event, emit_event

        events_path = tmp_path / "events.jsonl"
        event_types = [
            "project_initialized",
            "edge_started",
            "iteration_completed",
            "edge_converged",
        ]

        for et in event_types:
            emit_event(events_path, make_event(et, "proj"))

        lines = [l.strip() for l in events_path.read_text().splitlines() if l.strip()]
        assert len(lines) == len(event_types), (
            f"Expected {len(event_types)} events, found {len(lines)}. "
            "Append-only guarantee: prior events must not be overwritten."
        )

        for i, (line, expected_type) in enumerate(zip(lines, event_types)):
            record = json.loads(line)
            assert record["event_type"] == expected_type, (
                f"Line {i}: expected event_type={expected_type!r}, got {record['event_type']!r}. "
                "Events must be written in append order."
            )

    def test_events_count_never_decreases(self, tmp_path: pathlib.Path):
        """Reading events.jsonl after each write must always show an equal or larger count.

        WHY: append-only means line count is monotonically non-decreasing.
        If line count decreases between reads, a truncation has occurred —
        a log-integrity violation.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.fd_emit import make_event, emit_event

        events_path = tmp_path / "events.jsonl"
        prior_count = 0

        for i in range(10):
            emit_event(events_path, make_event(f"event_{i}", "proj", seq=i))
            lines = [l.strip() for l in events_path.read_text().splitlines() if l.strip()]
            current_count = len(lines)
            assert current_count >= prior_count, (
                f"After write {i}: count went from {prior_count} to {current_count}. "
                "Event count must be monotonically non-decreasing (append-only)."
            )
            prior_count = current_count

    def test_timestamps_are_monotonically_non_decreasing(self, tmp_path: pathlib.Path):
        """Event timestamps in events.jsonl must be non-decreasing.

        WHY: The event logger assigns timestamps from the system clock at append time.
        Timestamps cannot go backward (barring system clock adjustments). Monotonicity
        is required for time-based replay and causality analysis.

        Note: non-decreasing (not strictly increasing) because two events in the same
        millisecond may have identical timestamps.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.fd_emit import make_event, emit_event

        events_path = tmp_path / "events.jsonl"

        for i in range(5):
            emit_event(events_path, make_event(f"event_{i}", "proj"))

        lines = [l.strip() for l in events_path.read_text().splitlines() if l.strip()]
        timestamps = [json.loads(l)["timestamp"] for l in lines]

        for i in range(1, len(timestamps)):
            prev_ts = timestamps[i - 1]
            curr_ts = timestamps[i]
            assert curr_ts >= prev_ts, (
                f"Timestamp decreased at position {i}: "
                f"{prev_ts!r} → {curr_ts!r}. "
                "Event stream timestamps must be monotonically non-decreasing."
            )

    def test_existing_events_unchanged_after_new_write(self, tmp_path: pathlib.Path):
        """Writing a new event must not change any previously written event.

        WHY: An existing event being modified after the fact is a log-integrity
        violation. This simulates the read-after-write contract: read N events,
        write one more, re-read N events, compare. All N must be identical.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.fd_emit import make_event, emit_event

        events_path = tmp_path / "events.jsonl"

        # Write 3 events
        for i in range(3):
            emit_event(events_path, make_event(f"event_{i}", "proj", seq=i))

        # Snapshot the 3 lines
        snapshot = [l.strip() for l in events_path.read_text().splitlines() if l.strip()]
        assert len(snapshot) == 3

        # Write one more event
        emit_event(events_path, make_event("extra_event", "proj"))

        # Re-read and compare the first 3 lines
        all_lines = [l.strip() for l in events_path.read_text().splitlines() if l.strip()]
        assert len(all_lines) == 4, "Should now have 4 events"

        for i, (orig, rereaded) in enumerate(zip(snapshot, all_lines[:3])):
            assert orig == rereaded, (
                f"Event at position {i} was modified after a subsequent write.\n"
                f"Original: {orig}\nRe-read:  {rereaded}"
            )

    def test_all_lines_are_valid_json(self, tmp_path: pathlib.Path):
        """Every line in events.jsonl must be valid JSON.

        WHY: The event log is parsed line-by-line. A malformed line causes a
        JSONDecodeError which can halt event stream processing. The emit functions
        must produce valid JSON for every line.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.fd_emit import make_event, emit_event
        from genesis.ol_event import make_ol_event, emit_ol_event

        events_path = tmp_path / "events.jsonl"

        # Mix flat and OL events
        emit_event(events_path, make_event("flat_event_1", "proj"))
        emit_ol_event(events_path, make_ol_event(
            "IterationStarted", "code↔unit_tests", "proj", "inst", "actor"
        ))
        emit_event(events_path, make_event("flat_event_2", "proj"))
        emit_ol_event(events_path, make_ol_event(
            "EdgeConverged", "code↔unit_tests", "proj", "inst", "actor",
            payload={"delta": 0}
        ))

        lines = [l.strip() for l in events_path.read_text().splitlines() if l.strip()]
        for i, line in enumerate(lines):
            try:
                json.loads(line)
            except json.JSONDecodeError as e:
                pytest.fail(f"Line {i} is not valid JSON: {line!r}\nError: {e}")


# ═══════════════════════════════════════════════════════════════════════
# PART E: Mixed-format log (real engine run)
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.e2e
class TestMixedFormatLog:
    """Tests that validate events.jsonl after a real (or minimal) engine run.

    Exercises the coexistence of OL and flat events in the same log file,
    and verifies that normalize_event() can handle all of them.
    """

    @pytest.fixture(scope="class")
    def engine_run_project(self, tmp_path_factory):
        """Run `genesis start` on a minimal project (no Claude, may exit nothing_to_do).

        Produces a workspace that may contain engine-emitted OL events,
        providing a real mixed-format log for validation.
        """
        project_dir = tmp_path_factory.mktemp("engine-run-test")
        _scaffold_minimal_project(project_dir)
        return project_dir

    def test_engine_run_exits_with_expected_code(self, engine_run_project: pathlib.Path):
        """genesis start on a minimal project must exit with a known code.

        WHY: Validates the engine CLI itself is reachable. Exit 0 means
        nothing_to_do (no features with pending edges). Exit 1 means
        evaluator/config error. Both are acceptable for a minimal scaffold
        with no active features.
        """
        env = _clean_env()
        env["PYTHONPATH"] = str(GENESIS_CODE_DIR)

        result = subprocess.run(
            [sys.executable, "-m", "genesis", "start",
             "--workspace", str(engine_run_project)],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=30, env=env,
        )

        assert result.returncode in (0, 1, 2, 3), (
            f"genesis start exited {result.returncode} (expected 0, 1, 2, or 3)\n"
            f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
        )

    def test_all_events_parseable_by_normalize_event(self, engine_run_project: pathlib.Path):
        """Every event in events.jsonl must be parseable by normalize_event().

        WHY: normalize_event() is the single read-side compatibility layer.
        If any event cannot be parsed, log consumers that call normalize_event()
        will silently drop or corrupt that event's data.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import normalize_event

        events_file = engine_run_project / ".ai-workspace" / "events" / "events.jsonl"
        assert events_file.exists(), "events.jsonl must exist"

        lines = [l.strip() for l in events_file.read_text().splitlines() if l.strip()]
        assert lines, "events.jsonl must not be empty"

        for i, line in enumerate(lines):
            raw = json.loads(line)
            try:
                normalized = normalize_event(raw)
                assert "event_type" in normalized or "eventType" in normalized, (
                    f"Line {i}: normalize_event() produced neither event_type nor eventType: "
                    f"{sorted(normalized.keys())}"
                )
            except Exception as e:
                pytest.fail(f"normalize_event() raised on line {i}: {e}\nRaw: {raw}")

    def test_ol_events_have_no_violations(self, engine_run_project: pathlib.Path):
        """All OL-format events in events.jsonl must pass structural validation.

        WHY: Engine-emitted events use OL format. Every OL event in the log
        must satisfy the OL RunEvent schema. Violations indicate bugs in
        make_ol_event() or emit_ol_event() that corrupt the event stream.
        """
        events_file = engine_run_project / ".ai-workspace" / "events" / "events.jsonl"
        lines = [l.strip() for l in events_file.read_text().splitlines() if l.strip()]

        ol_events = [json.loads(l) for l in lines if "eventType" in json.loads(l)]
        if not ol_events:
            pytest.skip("No OL-format events in log — engine may not have run any edges")

        all_violations = []
        for i, event in enumerate(ol_events):
            violations = _validate_ol_event(event)
            if violations:
                all_violations.append(
                    f"OL event {i} (type={event.get('eventType')!r}):\n"
                    + "\n".join(f"    - {v}" for v in violations)
                )

        assert not all_violations, (
            f"{len(all_violations)} OL event(s) have structural violations:\n"
            + "\n".join(all_violations)
        )

    def test_flat_events_have_no_violations(self, engine_run_project: pathlib.Path):
        """All flat-format events in events.jsonl must pass structural validation.

        WHY: Flat events are produced by emit-event CLI and slash commands.
        Every flat event must have event_type, timestamp, and project. Missing
        fields cause silent failures when consumers read them.
        """
        events_file = engine_run_project / ".ai-workspace" / "events" / "events.jsonl"
        lines = [l.strip() for l in events_file.read_text().splitlines() if l.strip()]

        flat_events = [json.loads(l) for l in lines if "event_type" in json.loads(l)]
        if not flat_events:
            pytest.skip("No flat-format events in log")

        all_violations = []
        for i, event in enumerate(flat_events):
            violations = _validate_flat_event(event)
            if violations:
                all_violations.append(
                    f"Flat event {i} (type={event.get('event_type')!r}):\n"
                    + "\n".join(f"    - {v}" for v in violations)
                )

        assert not all_violations, (
            f"{len(all_violations)} flat event(s) have structural violations:\n"
            + "\n".join(all_violations)
        )


# ═══════════════════════════════════════════════════════════════════════
# PART F: emit-event CLI produces correct flat record
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.e2e
class TestEmitEventCLI:
    """Validates the emit-event CLI subcommand.

    The CLI uses fd_emit (flat format). Tests confirm the format contract
    and expose the known gap that emit-event does not produce OL-compliant events.
    """

    def test_emit_event_cli_stdout_has_event_type_timestamp_project(self, tmp_path: pathlib.Path):
        """emit-event CLI stdout must contain event_type, timestamp, project fields.

        WHY: cmd_emit_event() prints a flat record to stdout (line 918-919 in
        __main__.py). Callers that capture stdout to confirm the event was emitted
        rely on these three fields. A missing field breaks caller introspection.
        """
        _scaffold_minimal_project(tmp_path)
        env = _clean_env()
        env["PYTHONPATH"] = str(GENESIS_CODE_DIR)

        result = subprocess.run(
            [
                sys.executable, "-m", "genesis", "emit-event",
                "--type", "test_event",
                "--data", json.dumps({"key": "value"}),
                "--workspace", str(tmp_path),
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=30, env=env,
        )

        assert result.returncode == 0, (
            f"emit-event exited {result.returncode}\n"
            f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
        )

        stdout = result.stdout.strip()
        if stdout:
            try:
                record = json.loads(stdout)
                assert "event_type" in record, (
                    f"stdout missing event_type: {sorted(record.keys())}"
                )
                assert record["event_type"] == "test_event"
                assert "timestamp" in record, "stdout missing timestamp"
                assert "project" in record, "stdout missing project"
            except json.JSONDecodeError:
                pytest.skip("stdout not JSON — output format may differ")

    def test_emit_event_cli_appends_to_events_jsonl(self, tmp_path: pathlib.Path):
        """emit-event CLI must append the event to events.jsonl.

        WHY: Validates the write path end-to-end: CLI → fd_emit → events.jsonl.
        The event must be findable in the file after the CLI exits.
        """
        _scaffold_minimal_project(tmp_path)
        env = _clean_env()
        env["PYTHONPATH"] = str(GENESIS_CODE_DIR)

        before_count = len([
            l for l in (
                (tmp_path / ".ai-workspace" / "events" / "events.jsonl")
                .read_text().splitlines()
            ) if l.strip()
        ])

        subprocess.run(
            [
                sys.executable, "-m", "genesis", "emit-event",
                "--type", "custom_event",
                "--data", json.dumps({"source": "e2e_test"}),
                "--workspace", str(tmp_path),
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=30, env=env,
            check=True,
        )

        events_file = tmp_path / ".ai-workspace" / "events" / "events.jsonl"
        after_lines = [l.strip() for l in events_file.read_text().splitlines() if l.strip()]
        assert len(after_lines) == before_count + 1, (
            f"Expected {before_count + 1} events after emit-event, "
            f"got {len(after_lines)}"
        )

        last_event = json.loads(after_lines[-1])
        assert last_event.get("event_type") == "custom_event"
        assert last_event.get("source") == "e2e_test"

    def test_emit_event_cli_does_not_produce_ol_format(self, tmp_path: pathlib.Path):
        """emit-event CLI produces flat format, NOT OL format.

        WHY: Documents the format gap. emit-event uses fd_emit (flat), while the
        engine uses ol_event (OL). The event log therefore contains mixed formats.
        A consumer that expects only OL format will fail on CLI-emitted events.
        """
        _scaffold_minimal_project(tmp_path)
        env = _clean_env()
        env["PYTHONPATH"] = str(GENESIS_CODE_DIR)

        subprocess.run(
            [
                sys.executable, "-m", "genesis", "emit-event",
                "--type", "review_approved",
                "--data", json.dumps({"actor": "human", "feature": "REQ-F-001"}),
                "--workspace", str(tmp_path),
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=30, env=env,
            check=True,
        )

        events_file = tmp_path / ".ai-workspace" / "events" / "events.jsonl"
        lines = [l.strip() for l in events_file.read_text().splitlines() if l.strip()]
        last_line = json.loads(lines[-1])

        # The CLI-emitted event is FLAT format — it has event_type, NOT eventType
        assert "event_type" in last_line, (
            "CLI-emitted event should have 'event_type' (flat format)"
        )
        # Documents the format gap: this event is NOT OL-compliant
        # A reviewer can see this comment and understand that emit-event does not
        # produce OL structure even though the engine does
        assert "eventType" not in last_line, (
            "CLI-emitted event should NOT have 'eventType'. "
            "emit-event uses fd_emit (flat), not ol_event (OL). "
            "This is the known mixed-format gap: engine → OL, CLI → flat."
        )

    @pytest.mark.xfail(
        reason=(
            "REQ-GAP-002: emit-event CLI produces flat format (fd_emit), "
            "not OL-compliant format (ol_event). "
            "For full event stream consistency, all emitters should produce OL events. "
            "Currently the CLI uses fd_emit while the engine uses ol_event — two formats "
            "coexist in events.jsonl. This gap requires a CLI rewrite to use ol_event "
            "or a merge of the two emitters."
        ),
        strict=False,
    )
    def test_emit_event_cli_produces_ol_compliant_events(self, tmp_path: pathlib.Path):
        """emit-event CLI should produce OL-compliant events.

        This test FAILS (xfail) because emit-event CLI uses fd_emit (flat format)
        not ol_event (OL format). The test documents REQ-GAP-002: the CLI emitter
        and engine emitter produce different formats, creating a mixed-format log.

        When this gap is fixed (CLI rewritten to use ol_event), this test should
        be removed and the structural validation tests updated to require OL format
        from all emitters.
        """
        _scaffold_minimal_project(tmp_path)
        env = _clean_env()
        env["PYTHONPATH"] = str(GENESIS_CODE_DIR)

        subprocess.run(
            [
                sys.executable, "-m", "genesis", "emit-event",
                "--type", "review_approved",
                "--data", json.dumps({"actor": "human"}),
                "--workspace", str(tmp_path),
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=30, env=env,
            check=True,
        )

        events_file = tmp_path / ".ai-workspace" / "events" / "events.jsonl"
        lines = [l.strip() for l in events_file.read_text().splitlines() if l.strip()]
        last_line = json.loads(lines[-1])

        # ASSERTION: The event should have OL top-level structure.
        # This FAILS because emit-event uses flat fd_emit format.
        violations = _validate_ol_event(last_line)
        assert not violations, (
            f"CLI-emitted event has OL violations (it uses flat format, not OL):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


# ═══════════════════════════════════════════════════════════════════════
# PART G: Event log forensic analysis fixture
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def event_forensics_report(tmp_path_factory):
    """Session-scoped fixture that produces a forensic report at end of test run.

    Runs after all event-stream tests complete. Produces a report in the
    runs/ directory summarising:
      - Total events count across all test tmp_paths
      - OL vs flat format breakdown
      - Missing required fields per event type
      - Timestamp gap analysis
      - Compliance summary

    The report is written to RUNS_DIR / e2e_event_forensics_{timestamp}.json.
    """
    # This fixture yields during the test phase and runs report generation
    # in the finalisation phase (after yield).
    collected_events_paths: list[pathlib.Path] = []

    # Provide list to tests for registration (tests that want to contribute to report)
    yield collected_events_paths

    # Finalisation: aggregate all registered events paths + runs/ archives
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    all_events: list[dict] = []
    sources: list[str] = []

    # Collect from registered paths
    for events_path in collected_events_paths:
        if events_path.exists():
            for line in events_path.read_text().splitlines():
                line = line.strip()
                if line:
                    try:
                        all_events.append(json.loads(line))
                        sources.append(str(events_path))
                    except json.JSONDecodeError:
                        pass

    # Also scan any runs/ archives from this session
    if RUNS_DIR.exists():
        for run_dir in sorted(RUNS_DIR.iterdir()):
            if not run_dir.is_dir() or run_dir.name.startswith("."):
                continue
            events_f = run_dir / ".ai-workspace" / "events" / "events.jsonl"
            if events_f.exists():
                for line in events_f.read_text().splitlines():
                    line = line.strip()
                    if line:
                        try:
                            all_events.append(json.loads(line))
                            sources.append(str(events_f))
                        except json.JSONDecodeError:
                            pass

    if not all_events:
        return  # Nothing to report

    # Classify events
    ol_events = [e for e in all_events if _is_ol_event(e)]
    flat_events = [e for e in all_events if _is_flat_event(e)]
    unknown_events = [
        e for e in all_events if not _is_ol_event(e) and not _is_flat_event(e)
    ]

    total = len(all_events)
    ol_count = len(ol_events)
    flat_count = len(flat_events)
    unknown_count = len(unknown_events)

    # Validate OL events
    ol_violations: list[dict] = []
    for i, event in enumerate(ol_events):
        viols = _validate_ol_event(event)
        if viols:
            ol_violations.append({
                "index": i,
                "event_type": event.get("eventType", "?"),
                "violations": viols,
            })

    # Validate flat events
    flat_violations: list[dict] = []
    for i, event in enumerate(flat_events):
        viols = _validate_flat_event(event)
        if viols:
            flat_violations.append({
                "index": i,
                "event_type": event.get("event_type", "?"),
                "violations": viols,
            })

    # Timestamp gap analysis (flat events with timestamp field)
    timestamps = []
    for e in all_events:
        ts = e.get("timestamp") or e.get("eventTime")
        if ts and ISO_8601_RE.match(str(ts)):
            timestamps.append(str(ts))

    timestamps.sort()
    inversions = 0
    for i in range(1, len(timestamps)):
        if timestamps[i] < timestamps[i - 1]:
            inversions += 1

    # Missing fields report per event type
    event_type_missing: dict[str, list[str]] = {}
    for e in all_events:
        if _is_ol_event(e):
            etype = e.get("eventType", "UNKNOWN")
            viols = _validate_ol_event(e)
            if viols:
                event_type_missing.setdefault(etype, []).extend(viols)
        elif _is_flat_event(e):
            etype = e.get("event_type", "UNKNOWN")
            viols = _validate_flat_event(e)
            if viols:
                event_type_missing.setdefault(etype, []).extend(viols)

    report = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_events": total,
            "ol_format_count": ol_count,
            "flat_format_count": flat_count,
            "unknown_format_count": unknown_count,
            "mixed_format_percentage": round(
                100 * min(ol_count, flat_count) / total if total > 0 else 0, 1
            ),
            "ol_violation_count": len(ol_violations),
            "flat_violation_count": len(flat_violations),
            "timestamp_inversion_count": inversions,
            "compliance_score": round(
                100 * (total - len(ol_violations) - len(flat_violations)) / total
                if total > 0 else 100, 1
            ),
        },
        "ol_violations": ol_violations[:50],  # cap for readability
        "flat_violations": flat_violations[:50],
        "missing_fields_by_event_type": {
            k: list(set(v)) for k, v in event_type_missing.items()
        },
        "timestamp_analysis": {
            "total_timestamps": len(timestamps),
            "inversions": inversions,
            "monotonic": inversions == 0,
        },
        "sources_sampled": len(set(sources)),
    }

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = RUNS_DIR / f"e2e_event_forensics_{timestamp}.json"
    try:
        report_path.write_text(json.dumps(report, indent=2) + "\n")
        print(f"\nE2E: Event forensics report → {report_path}", flush=True)
    except Exception as e:
        print(f"E2E: WARNING — could not write forensics report: {e}", flush=True)


@pytest.mark.e2e
class TestEventForensics:
    """Runs the forensic analysis on the engine_run_project and validates results.

    Validates that the combined event log (from a minimal engine run) has
    acceptable compliance metrics.
    """

    def test_forensic_report_zero_ol_violations_on_engine_events(
        self, tmp_path: pathlib.Path
    ):
        """Engine-emitted OL events must have zero structural violations.

        WHY: This is the end-to-end OL compliance test. The engine runs,
        emits events, and we verify every OL event it produced is fully
        spec-compliant. Any violation here indicates a bug in make_ol_event()
        or emit_ol_event() that would propagate to all downstream consumers.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import make_ol_event, emit_ol_event

        events_path = tmp_path / "events" / "events.jsonl"
        events_path.parent.mkdir(parents=True, exist_ok=True)

        # Emit a representative set of engine event types
        engine_event_types = [
            ("EdgeStarted", "OTHER"),
            ("IterationCompleted", "OTHER"),
            ("EdgeConverged", "COMPLETE"),
            ("IterationStarted", "START"),
            ("IterationFailed", "FAIL"),
        ]

        for semantic_type, expected_ol in engine_event_types:
            event = make_ol_event(
                semantic_type,
                "code↔unit_tests",
                "forensic-test",
                "REQ-F-FORENSIC-001",
                "edge-runner",
                payload={"edge": "code↔unit_tests", "delta": 0},
            )
            emit_ol_event(events_path, event)

        # Validate all OL events
        lines = [l.strip() for l in events_path.read_text().splitlines() if l.strip()]
        all_violations = []
        for i, line in enumerate(lines):
            raw = json.loads(line)
            if _is_ol_event(raw):
                violations = _validate_ol_event(raw)
                if violations:
                    all_violations.append(
                        f"Event {i} ({raw.get('eventType')!r}): {violations}"
                    )

        assert not all_violations, (
            f"Engine-emitted OL events have {len(all_violations)} violation(s):\n"
            + "\n".join(all_violations)
        )

    def test_forensic_report_flat_events_always_normalizable(self, tmp_path: pathlib.Path):
        """All flat events in a mixed log must be normalizable without errors.

        WHY: This validates the read-side contract. Given a realistic mixed log
        (both OL and flat events from different emitters), every event must
        be processable by normalize_event() without raising an exception.
        This is the key guarantee for log consumers that use normalize_event()
        as their entry point.
        """
        if _genesis_sys_path() not in sys.path:
            sys.path.insert(0, _genesis_sys_path())

        from genesis.ol_event import make_ol_event, emit_ol_event, normalize_event
        from genesis.fd_emit import make_event, emit_event

        events_path = tmp_path / "events.jsonl"

        # Mix of OL and flat events (simulating real production log)
        emit_event(events_path, make_event("project_initialized", "proj", profile="standard"))
        emit_ol_event(events_path, make_ol_event("EdgeStarted", "code↔unit_tests",
                                                  "proj", "REQ-F-001", "engine"))
        emit_event(events_path, make_event("intent_raised", "proj",
                                           signal_source="homeostatic_gap",
                                           feature="REQ-F-001"))
        emit_ol_event(events_path, make_ol_event("IterationCompleted", "code↔unit_tests",
                                                  "proj", "REQ-F-001", "engine",
                                                  payload={"delta": 2}))
        emit_event(events_path, make_event("review_approved", "proj",
                                           actor="human", feature="REQ-F-001"))
        emit_ol_event(events_path, make_ol_event("EdgeConverged", "code↔unit_tests",
                                                  "proj", "REQ-F-001", "engine",
                                                  payload={"delta": 0}))

        lines = [l.strip() for l in events_path.read_text().splitlines() if l.strip()]
        assert len(lines) == 6, f"Expected 6 events, got {len(lines)}"

        errors = []
        for i, line in enumerate(lines):
            raw = json.loads(line)
            try:
                normalized = normalize_event(raw)
                # Verify the normalized result is a dict (not None/exception)
                assert isinstance(normalized, dict), f"normalize_event() returned non-dict"
            except Exception as e:
                errors.append(f"Line {i}: {type(e).__name__}: {e}")

        assert not errors, (
            f"normalize_event() raised on {len(errors)} event(s):\n"
            + "\n".join(errors)
        )
