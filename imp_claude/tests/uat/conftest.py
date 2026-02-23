# Validates: REQ-TOOL-005, REQ-UX-001
"""UAT fixture factories — 5 synthetic workspaces for scenario testing.

Each fixture uses tmp_path to create an isolated workspace.  Config files
are copied from the real plugin source so schema changes propagate
automatically.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import textwrap
from datetime import datetime, timezone

import pytest
import yaml

# ═══════════════════════════════════════════════════════════════════════
# PATH CONSTANTS (shared with imp_claude/tests/conftest.py)
# ═══════════════════════════════════════════════════════════════════════

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent
SPEC_DIR = PROJECT_ROOT / "specification"
IMP_CLAUDE = PROJECT_ROOT / "imp_claude"
PLUGIN_ROOT = (
    IMP_CLAUDE / "code" / ".claude-plugin" / "plugins"
    / "gen-methodology" / "v2"
)
CONFIG_DIR = PLUGIN_ROOT / "config"
EDGE_PARAMS_DIR = CONFIG_DIR / "edge_params"
PROFILES_DIR = CONFIG_DIR / "profiles"
COMMANDS_DIR = PLUGIN_ROOT / "commands"
AGENTS_DIR = PLUGIN_ROOT / "agents"


# ═══════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════

def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_event(event_type: str, **kwargs) -> dict:
    """Build a structured event dict with required fields."""
    ev = {"event_type": event_type, "timestamp": _ts()}
    ev.update(kwargs)
    return ev


def write_events(events_file: pathlib.Path, events: list[dict]) -> None:
    """Write a list of event dicts to events.jsonl."""
    events_file.parent.mkdir(parents=True, exist_ok=True)
    with open(events_file, "w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")


def write_feature_vector(
    features_dir: pathlib.Path,
    feature_id: str,
    *,
    status: str = "pending",
    profile: str = "standard",
    trajectory: dict | None = None,
    dependencies: list | None = None,
    extra: dict | None = None,
) -> pathlib.Path:
    """Write a feature vector YAML file."""
    features_dir.mkdir(parents=True, exist_ok=True)
    ts = _ts()
    data: dict = {
        "feature": feature_id,
        "title": f"Feature {feature_id}",
        "intent": "INT-001",
        "vector_type": "feature",
        "profile": profile,
        "status": status,
        "created": ts,
        "updated": ts,
        "trajectory": trajectory or {},
        "dependencies": dependencies or [],
    }
    if extra:
        data.update(extra)
    path = features_dir / f"{feature_id}.yml"
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
    return path


def copy_configs(ws_dir: pathlib.Path) -> None:
    """Copy graph topology, evaluator defaults, edge params, and profiles."""
    graph_dir = ws_dir / "graph"
    graph_dir.mkdir(parents=True, exist_ok=True)
    for name in ("graph_topology.yml", "evaluator_defaults.yml"):
        src = CONFIG_DIR / name
        if src.exists():
            shutil.copy2(src, graph_dir / name)

    edges_dir = graph_dir / "edges"
    edges_dir.mkdir(parents=True, exist_ok=True)
    for yml in EDGE_PARAMS_DIR.glob("*.yml"):
        shutil.copy2(yml, edges_dir / yml.name)

    profiles_dir = ws_dir / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    for yml in PROFILES_DIR.glob("*.yml"):
        shutil.copy2(yml, profiles_dir / yml.name)

    # Copy additional config files
    for name in ("sensory_monitors.yml", "affect_triage.yml", "agent_roles.yml"):
        src = CONFIG_DIR / name
        if src.exists():
            shutil.copy2(src, graph_dir / name)

    # Feature vector template
    fvt = CONFIG_DIR / "feature_vector_template.yml"
    if fvt.exists():
        feat_dir = ws_dir / "features"
        feat_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fvt, feat_dir / "feature_vector_template.yml")


def write_intent(workspace: pathlib.Path, content: str | None = None) -> pathlib.Path:
    """Write specification/INTENT.md."""
    spec_dir = workspace / "specification"
    spec_dir.mkdir(parents=True, exist_ok=True)
    path = spec_dir / "INTENT.md"
    path.write_text(content or textwrap.dedent("""\
        # Intent: Test Application

        ## Problem Statement

        Build a test application for UAT validation.

        ## Requirements

        ### REQ-F-ALPHA-001: Core Feature Alpha
        Acceptance criteria: system produces correct output.

        ### REQ-F-BETA-001: Core Feature Beta
        Acceptance criteria: all tests pass with coverage > 80%.

        ### REQ-F-GAMMA-001: Core Feature Gamma
        Acceptance criteria: basic functionality works.
    """))
    return path


def write_project_constraints(ws_dir: pathlib.Path) -> pathlib.Path:
    """Write project_constraints.yml in the context directory."""
    ctx_dir = ws_dir / "claude" / "context"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    path = ctx_dir / "project_constraints.yml"
    path.write_text(textwrap.dedent("""\
        ---
        project:
          name: "uat-test-project"
          version: "0.1.0"
          default_profile: standard

        language:
          primary: python
          version: "3.12"

        tools:
          test_runner:
            command: "pytest"
            args: "-v"
            pass_criterion: "exit code 0"

        thresholds:
          test_coverage_minimum: 0.80
          test_coverage_target: 1.00

        standards:
          style_guide: "PEP 8"
          req_tag_format:
            code: "Implements: REQ-*"
            tests: "Validates: REQ-*"

        constraint_dimensions:
          ecosystem_compatibility:
            language: "python"
            version: "3.12"
          deployment_target:
            platform: "library"
          security_model:
            authentication: "none"
          build_system:
            tool: "pip"
    """))
    return path


# ═══════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def clean_workspace(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture 1: CLEAN — empty project, no .ai-workspace.

    An empty directory with just pyproject.toml and src/.
    Represents a greenfield project before any methodology initialization.
    """
    (tmp_path / "pyproject.toml").write_text(textwrap.dedent("""\
        [project]
        name = "uat-test-project"
        version = "0.1.0"
        requires-python = ">=3.10"

        [tool.pytest.ini_options]
        testpaths = ["tests"]
    """))
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    return tmp_path


@pytest.fixture
def initialized_workspace(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture 2: INITIALIZED — freshly initialized, no features yet.

    Has .ai-workspace with configs, INTENT.md, and one project_initialized event.
    No feature vectors in features/active/.
    """
    ws = tmp_path / ".ai-workspace"

    # Directory structure
    for d in [
        ws / "graph",
        ws / "profiles",
        ws / "features" / "active",
        ws / "features" / "completed",
        ws / "events",
        ws / "tasks" / "active",
        ws / "agents",
        ws / "claude" / "context",
    ]:
        d.mkdir(parents=True, exist_ok=True)

    # Copy real configs
    copy_configs(ws)

    # Write intent
    write_intent(tmp_path)

    # Write project constraints
    write_project_constraints(ws)

    # Write project_initialized event
    write_events(ws / "events" / "events.jsonl", [
        make_event("project_initialized",
                   project="uat-test-project", profile="standard", version="2.8.0"),
    ])

    # pyproject.toml + src
    (tmp_path / "pyproject.toml").write_text(textwrap.dedent("""\
        [project]
        name = "uat-test-project"
        version = "0.1.0"
        requires-python = ">=3.10"
    """))
    (tmp_path / "src").mkdir(exist_ok=True)

    return tmp_path


@pytest.fixture
def in_progress_workspace(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture 3: IN_PROGRESS — 3 features at various stages.

    Feature A (REQ-F-ALPHA-001): converged intent→req, iterating req→design
    Feature B (REQ-F-BETA-001):  converged design→code, iterating code↔unit_tests (iter 3, delta=2)
    Feature C (REQ-F-GAMMA-001): just started, at intent→requirements (iter 1)
    """
    ws = tmp_path / ".ai-workspace"
    for d in [
        ws / "graph", ws / "profiles",
        ws / "features" / "active", ws / "features" / "completed",
        ws / "events", ws / "tasks" / "active",
        ws / "agents", ws / "claude" / "context",
    ]:
        d.mkdir(parents=True, exist_ok=True)

    copy_configs(ws)
    write_intent(tmp_path)
    write_project_constraints(ws)

    # Feature A — converged through intent→requirements, iterating requirements→design
    write_feature_vector(
        ws / "features" / "active", "REQ-F-ALPHA-001",
        status="in_progress",
        trajectory={
            "requirements": {"status": "converged"},
            "design": {"status": "iterating", "iteration": 2, "delta": 1},
        },
    )

    # Feature B — converged through design→code, iterating code↔unit_tests
    write_feature_vector(
        ws / "features" / "active", "REQ-F-BETA-001",
        status="in_progress",
        trajectory={
            "requirements": {"status": "converged"},
            "design": {"status": "converged"},
            "code": {"status": "iterating", "iteration": 3, "delta": 2},
            "unit_tests": {"status": "iterating", "iteration": 3, "delta": 2},
        },
    )

    # Feature C — just started
    write_feature_vector(
        ws / "features" / "active", "REQ-F-GAMMA-001",
        status="in_progress",
        trajectory={
            "requirements": {"status": "iterating", "iteration": 1, "delta": 3},
        },
    )

    # ~15 events for the trajectory
    events = [
        make_event("project_initialized",
                   project="uat-test-project", profile="standard", version="2.8.0"),
        # Feature A trajectory
        make_event("edge_started", feature="REQ-F-ALPHA-001", edge="intent→requirements"),
        make_event("iteration_completed", feature="REQ-F-ALPHA-001",
                   edge="intent→requirements", iteration=1, delta=2),
        make_event("iteration_completed", feature="REQ-F-ALPHA-001",
                   edge="intent→requirements", iteration=2, delta=0),
        make_event("edge_converged", feature="REQ-F-ALPHA-001", edge="intent→requirements"),
        make_event("edge_started", feature="REQ-F-ALPHA-001", edge="requirements→design"),
        make_event("iteration_completed", feature="REQ-F-ALPHA-001",
                   edge="requirements→design", iteration=1, delta=2),
        make_event("iteration_completed", feature="REQ-F-ALPHA-001",
                   edge="requirements→design", iteration=2, delta=1),
        # Feature B trajectory
        make_event("edge_started", feature="REQ-F-BETA-001", edge="intent→requirements"),
        make_event("edge_converged", feature="REQ-F-BETA-001", edge="intent→requirements"),
        make_event("edge_started", feature="REQ-F-BETA-001", edge="requirements→design"),
        make_event("edge_converged", feature="REQ-F-BETA-001", edge="requirements→design"),
        make_event("edge_started", feature="REQ-F-BETA-001", edge="design→code"),
        make_event("edge_converged", feature="REQ-F-BETA-001", edge="design→code"),
        make_event("edge_started", feature="REQ-F-BETA-001", edge="code↔unit_tests"),
        make_event("iteration_completed", feature="REQ-F-BETA-001",
                   edge="code↔unit_tests", iteration=1, delta=4),
        make_event("iteration_completed", feature="REQ-F-BETA-001",
                   edge="code↔unit_tests", iteration=2, delta=3),
        make_event("iteration_completed", feature="REQ-F-BETA-001",
                   edge="code↔unit_tests", iteration=3, delta=2),
        # Feature C trajectory
        make_event("edge_started", feature="REQ-F-GAMMA-001", edge="intent→requirements"),
        make_event("iteration_completed", feature="REQ-F-GAMMA-001",
                   edge="intent→requirements", iteration=1, delta=3),
    ]
    write_events(ws / "events" / "events.jsonl", events)

    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'uat-test-project'\n")
    (tmp_path / "src").mkdir(exist_ok=True)

    return tmp_path


@pytest.fixture
def converged_workspace(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture 4: CONVERGED — 2 features fully converged through all standard edges.

    Feature D (REQ-F-DELTA-001): all 4 standard edges converged
    Feature E (REQ-F-EPSILON-001): all 4 standard edges converged
    """
    ws = tmp_path / ".ai-workspace"
    for d in [
        ws / "graph", ws / "profiles",
        ws / "features" / "active", ws / "features" / "completed",
        ws / "events", ws / "tasks" / "active",
        ws / "agents", ws / "claude" / "context",
    ]:
        d.mkdir(parents=True, exist_ok=True)

    copy_configs(ws)
    write_intent(tmp_path)
    write_project_constraints(ws)

    edges = [
        "intent→requirements",
        "requirements→design",
        "design→code",
        "code↔unit_tests",
    ]

    for feat_id in ("REQ-F-DELTA-001", "REQ-F-EPSILON-001"):
        write_feature_vector(
            ws / "features" / "active", feat_id,
            status="converged",
            trajectory={
                "requirements": {"status": "converged"},
                "design": {"status": "converged"},
                "code": {"status": "converged"},
                "unit_tests": {"status": "converged"},
            },
        )

    events = [
        make_event("project_initialized",
                   project="uat-test-project", profile="standard", version="2.8.0"),
    ]
    for feat_id in ("REQ-F-DELTA-001", "REQ-F-EPSILON-001"):
        for edge in edges:
            events.append(make_event("edge_started", feature=feat_id, edge=edge))
            events.append(make_event("iteration_completed",
                                     feature=feat_id, edge=edge, iteration=1, delta=1))
            events.append(make_event("iteration_completed",
                                     feature=feat_id, edge=edge, iteration=2, delta=0))
            events.append(make_event("edge_converged", feature=feat_id, edge=edge))

    write_events(ws / "events" / "events.jsonl", events)

    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'uat-test-project'\n")
    (tmp_path / "src").mkdir(exist_ok=True)

    return tmp_path


@pytest.fixture
def stuck_workspace(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture 5: STUCK — features exhibiting stuck and blocked conditions.

    Feature X (REQ-F-STUCK-001):   delta=3 for 4 consecutive iterations on code↔unit_tests
    Feature Y (REQ-F-BLOCKED-001): depends on unconverged spawn REQ-F-SPIKE-001
    Feature Z (REQ-F-REVIEW-001):  pending human review on requirements→design
    """
    ws = tmp_path / ".ai-workspace"
    for d in [
        ws / "graph", ws / "profiles",
        ws / "features" / "active", ws / "features" / "completed",
        ws / "events", ws / "tasks" / "active",
        ws / "agents", ws / "claude" / "context",
    ]:
        d.mkdir(parents=True, exist_ok=True)

    copy_configs(ws)
    write_intent(tmp_path)
    write_project_constraints(ws)

    # Feature X — stuck (delta unchanged)
    write_feature_vector(
        ws / "features" / "active", "REQ-F-STUCK-001",
        status="in_progress",
        trajectory={
            "requirements": {"status": "converged"},
            "design": {"status": "converged"},
            "code": {"status": "iterating", "iteration": 5, "delta": 3},
            "unit_tests": {"status": "iterating", "iteration": 5, "delta": 3},
        },
    )

    # Feature Y — blocked on dependency
    write_feature_vector(
        ws / "features" / "active", "REQ-F-BLOCKED-001",
        status="in_progress",
        trajectory={
            "requirements": {"status": "converged"},
            "design": {"status": "blocked"},
        },
        dependencies=[{"feature": "REQ-F-SPIKE-001", "edge": "design"}],
    )

    # Feature Z — pending human review
    write_feature_vector(
        ws / "features" / "active", "REQ-F-REVIEW-001",
        status="in_progress",
        trajectory={
            "requirements": {"status": "converged"},
            "design": {"status": "pending_review"},
        },
    )

    # The unconverged spawn
    write_feature_vector(
        ws / "features" / "active", "REQ-F-SPIKE-001",
        status="in_progress",
        extra={"vector_type": "spike", "parent": {"feature": "REQ-F-BLOCKED-001"}},
        trajectory={
            "requirements": {"status": "iterating", "iteration": 1, "delta": 2},
        },
    )

    events = [
        make_event("project_initialized",
                   project="uat-test-project", profile="standard", version="2.8.0"),
        # Feature X — stuck iterations
        make_event("edge_started", feature="REQ-F-STUCK-001", edge="code↔unit_tests"),
        make_event("iteration_completed", feature="REQ-F-STUCK-001",
                   edge="code↔unit_tests", iteration=1, delta=4),
        make_event("iteration_completed", feature="REQ-F-STUCK-001",
                   edge="code↔unit_tests", iteration=2, delta=3),
        make_event("iteration_completed", feature="REQ-F-STUCK-001",
                   edge="code↔unit_tests", iteration=3, delta=3),
        make_event("iteration_completed", feature="REQ-F-STUCK-001",
                   edge="code↔unit_tests", iteration=4, delta=3),
        make_event("iteration_completed", feature="REQ-F-STUCK-001",
                   edge="code↔unit_tests", iteration=5, delta=3),
        # Feature Y — started but blocked
        make_event("edge_started", feature="REQ-F-BLOCKED-001", edge="requirements→design"),
        make_event("spawn_created", feature="REQ-F-BLOCKED-001",
                   spawn="REQ-F-SPIKE-001", reason="design dependency"),
        # Feature Z — iteration then awaiting review
        make_event("edge_started", feature="REQ-F-REVIEW-001", edge="requirements→design"),
        make_event("iteration_completed", feature="REQ-F-REVIEW-001",
                   edge="requirements→design", iteration=1, delta=0),
        # Note: no review_completed event — so it's pending human review
    ]
    write_events(ws / "events" / "events.jsonl", events)

    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'uat-test-project'\n")
    (tmp_path / "src").mkdir(exist_ok=True)

    return tmp_path


# ═══════════════════════════════════════════════════════════════════════
# COMMON FIXTURES
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture
def load_yaml():
    """Helper to load YAML files."""
    def _load(path: pathlib.Path) -> dict:
        with open(path) as f:
            docs = list(yaml.safe_load_all(f))
        result = {}
        for doc in docs:
            if doc is not None:
                result.update(doc)
        return result
    return _load


@pytest.fixture
def graph_topology():
    """Load the real graph topology config."""
    with open(CONFIG_DIR / "graph_topology.yml") as f:
        docs = list(yaml.safe_load_all(f))
    result = {}
    for doc in docs:
        if doc is not None:
            result.update(doc)
    return result


@pytest.fixture
def evaluator_defaults():
    """Load the real evaluator defaults config."""
    with open(CONFIG_DIR / "evaluator_defaults.yml") as f:
        docs = list(yaml.safe_load_all(f))
    result = {}
    for doc in docs:
        if doc is not None:
            result.update(doc)
    return result


@pytest.fixture
def all_profiles():
    """Load all projection profile YAML files."""
    profiles = {}
    for path in sorted(PROFILES_DIR.glob("*.yml")):
        with open(path) as f:
            profiles[path.stem] = yaml.safe_load(f)
    return profiles


@pytest.fixture
def all_edge_configs():
    """Load all edge param YAML files."""
    configs = {}
    for path in sorted(EDGE_PARAMS_DIR.glob("*.yml")):
        with open(path) as f:
            docs = list(yaml.safe_load_all(f))
        result = {}
        for doc in docs:
            if doc is not None:
                result.update(doc)
        configs[path.stem] = result
    return configs


@pytest.fixture
def sensory_monitors():
    """Load sensory monitors config."""
    with open(CONFIG_DIR / "sensory_monitors.yml") as f:
        docs = list(yaml.safe_load_all(f))
    result = {}
    for doc in docs:
        if doc is not None:
            result.update(doc)
    return result


@pytest.fixture
def affect_triage():
    """Load affect triage config."""
    with open(CONFIG_DIR / "affect_triage.yml") as f:
        docs = list(yaml.safe_load_all(f))
    result = {}
    for doc in docs:
        if doc is not None:
            result.update(doc)
    return result


@pytest.fixture
def agent_roles():
    """Load agent roles config."""
    with open(CONFIG_DIR / "agent_roles.yml") as f:
        docs = list(yaml.safe_load_all(f))
    result = {}
    for doc in docs:
        if doc is not None:
            result.update(doc)
    return result
