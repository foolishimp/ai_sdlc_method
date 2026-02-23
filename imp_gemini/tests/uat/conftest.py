# Validates: REQ-TOOL-005, REQ-UX-001
import json
import pathlib
import shutil
import textwrap
from datetime import datetime, timezone
import pytest
import yaml

# Path Constants
PROJECT_ROOT = pathlib.Path("/Users/jim/src/apps/ai_sdlc_method")
IMP_GEMINI = PROJECT_ROOT / "imp_gemini"
PLUGIN_ROOT = IMP_GEMINI / "code"
CONFIG_DIR = PLUGIN_ROOT / "config"
EDGE_PARAMS_DIR = CONFIG_DIR / "edge_params"
PROFILES_DIR = CONFIG_DIR / "profiles"
COMMANDS_DIR = PLUGIN_ROOT / "commands"
AGENTS_DIR = PLUGIN_ROOT / "agents"

def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()

def make_event(event_type: str, **kwargs) -> dict:
    ev = {"event_type": event_type, "timestamp": _ts()}
    ev.update(kwargs)
    return ev

def write_events(events_file: pathlib.Path, events: list[dict]) -> None:
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

def write_intent(workspace: pathlib.Path, content: str | None = None) -> pathlib.Path:
    spec_dir = workspace / ".ai-workspace" / "spec"
    spec_dir.mkdir(parents=True, exist_ok=True)
    path = spec_dir / "INTENT.md"
    path.write_text(content or textwrap.dedent("""
        # Intent: Test Application
        Problem statement for UAT.
    """))
    return path

def write_project_constraints(ws_dir: pathlib.Path) -> pathlib.Path:
    ctx_dir = ws_dir / "gemini_genesis"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    path = ctx_dir / "project_constraints.yml"
    path.write_text(textwrap.dedent("""
        project:
          name: "uat-test-project"
          version: "0.1.0"
          default_profile: standard
          mode: interactive
          valence: medium
    """))
    return path

@pytest.fixture
def initialized_workspace(tmp_path: pathlib.Path) -> pathlib.Path:
    ws = tmp_path / ".ai-workspace"
    for d in [
        ws / "graph", ws / "profiles",
        ws / "features" / "active", ws / "events",
        ws / "gemini_genesis", ws / "spec",
    ]:
        d.mkdir(parents=True, exist_ok=True)

    copy_configs(ws)
    write_intent(tmp_path)
    write_project_constraints(ws)
    write_events(ws / "events" / "events.jsonl", [
        make_event("project_initialized", project="uat-test-project"),
    ])
    return tmp_path

@pytest.fixture
def in_progress_workspace(tmp_path: pathlib.Path) -> pathlib.Path:
    ws = tmp_path / ".ai-workspace"
    for d in [
        ws / "graph", ws / "profiles",
        ws / "features" / "active", ws / "events",
        ws / "gemini_genesis", ws / "spec",
    ]:
        d.mkdir(parents=True, exist_ok=True)

    copy_configs(ws)
    write_intent(tmp_path)
    write_project_constraints(ws)

    write_feature_vector(
        ws / "features" / "active", "REQ-F-ALPHA-001",
        status="in_progress",
        trajectory={
            "requirements": {"status": "converged"},
            "design": {"status": "iterating", "iteration": 2, "delta": 1},
        },
    )

    events = [
        make_event("project_initialized", project="uat-test-project"),
        make_event("edge_converged", feature="REQ-F-ALPHA-001", edge="intent→requirements"),
        make_event("iteration_completed", feature="REQ-F-ALPHA-001", edge="requirements→design", iteration=2, delta=1),
    ]
    write_events(ws / "events" / "events.jsonl", events)
    return tmp_path

@pytest.fixture
def graph_topology():
    with open(CONFIG_DIR / "graph_topology.yml") as f:
        return yaml.safe_load(f)

@pytest.fixture
def all_edge_configs():
    configs = {}
    for path in EDGE_PARAMS_DIR.glob("*.yml"):
        with open(path) as f:
            configs[path.stem] = yaml.safe_load(f)
    return configs

@pytest.fixture
def all_profiles():
    profiles = {}
    for path in PROFILES_DIR.glob("*.yml"):
        with open(path) as f:
            profiles[path.stem] = yaml.safe_load(f)
    return profiles

@pytest.fixture
def sensory_monitors():
    with open(CONFIG_DIR / "sensory_monitors.yml") as f:
        return yaml.safe_load(f)

@pytest.fixture
def affect_triage():
    with open(CONFIG_DIR / "affect_triage.yml") as f:
        return yaml.safe_load(f)

@pytest.fixture
def agent_roles():
    with open(CONFIG_DIR / "agent_roles.yml") as f:
        return yaml.safe_load(f)
