# Validates: REQ-TOOL-005, REQ-TOOL-009
"""Fixtures for Claude Code implementation tests."""

import pathlib
import json

import pytest
import yaml

# Root paths
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
SPEC_DIR = PROJECT_ROOT / "specification"

# Claude implementation paths
IMP_CLAUDE = PROJECT_ROOT / "imp_claude"
DESIGN_DIR = IMP_CLAUDE / "design"
PLUGIN_ROOT = IMP_CLAUDE / "code/.claude-plugin/plugins/genesis"
CONFIG_DIR = PLUGIN_ROOT / "config"
EDGE_PARAMS_DIR = CONFIG_DIR / "edge_params"
PROFILES_DIR = CONFIG_DIR / "profiles"
COMMANDS_DIR = PLUGIN_ROOT / "commands"
AGENTS_DIR = PLUGIN_ROOT / "agents"
GENISIS_PKG = IMP_CLAUDE / "code" / "genesis"



def load_yaml(path: pathlib.Path) -> dict:
    """Load a YAML file, returning parsed dict. Merges multiple documents."""
    with open(path) as f:
        docs = list(yaml.safe_load_all(f))
    result = {}
    for doc in docs:
        if doc is not None:
            result.update(doc)
    return result


@pytest.fixture
def graph_topology():
    return load_yaml(CONFIG_DIR / "graph_topology.yml")


@pytest.fixture
def evaluator_defaults():
    return load_yaml(CONFIG_DIR / "evaluator_defaults.yml")


@pytest.fixture
def feature_vector_template():
    return load_yaml(CONFIG_DIR / "feature_vector_template.yml")


@pytest.fixture
def project_constraints_template():
    return load_yaml(CONFIG_DIR / "project_constraints_template.yml")


@pytest.fixture
def plugin_json():
    with open(PLUGIN_ROOT / "plugin.json") as f:
        return json.load(f)


@pytest.fixture
def all_edge_configs():
    """Load all edge param YAML files."""
    configs = {}
    for path in sorted(EDGE_PARAMS_DIR.glob("*.yml")):
        configs[path.stem] = load_yaml(path)
    return configs


@pytest.fixture
def all_profiles():
    """Load all projection profile YAML files."""
    profiles = {}
    for path in sorted(PROFILES_DIR.glob("*.yml")):
        profiles[path.stem] = load_yaml(path)
    return profiles


@pytest.fixture
def all_commands():
    """List all command markdown files."""
    return sorted(COMMANDS_DIR.glob("*.md"))


# ── Shared test helpers ──────────────────────────────────────────────────
# Used by test_functor_uat.py and test_functor_complex.py

def scaffold_green_project(tmp_path):
    """Scaffold a project that passes all deterministic checks."""
    import textwrap
    src = tmp_path / "src"
    src.mkdir()
    (src / "__init__.py").write_text("")
    (src / "auth.py").write_text(textwrap.dedent("""\
        # Implements: REQ-F-AUTH-001
        def login(user: str, password: str) -> bool:
            return user == "admin" and password == "secret"
    """))

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_auth.py").write_text(textwrap.dedent("""\
        # Validates: REQ-F-AUTH-001
        from src.auth import login

        def test_login_success():
            assert login("admin", "secret") is True

        def test_login_failure():
            assert login("admin", "wrong") is False
    """))

    (tmp_path / "pyproject.toml").write_text(textwrap.dedent("""\
        [tool.pytest.ini_options]
        pythonpath = ["."]
    """))
    return tmp_path


def green_constraints():
    return {
        "tools": {
            "test_runner": {
                "command": "python -m pytest",
                "args": "tests/ -v --tb=short",
                "pass_criterion": "exit code 0",
            },
            "linter": {
                "command": "python -m py_compile",
                "args": "src/auth.py",
                "pass_criterion": "exit code 0",
            },
            "formatter": {
                "command": "true",
                "args": "",
                "pass_criterion": "exit code 0",
            },
            "coverage": {
                "command": "python -m pytest",
                "args": "tests/ --co -q",
                "pass_criterion": "exit code 0",
            },
            "type_checker": {
                "command": "true",
                "args": "",
                "pass_criterion": "exit code 0, zero errors",
                "required": False,
            },
            "syntax_checker": {
                "command": "python -m py_compile",
                "args": "",
                "pass_criterion": "exit code 0",
            },
        },
        "thresholds": {
            "test_coverage_minimum": 0.80,
            "max_function_lines": 50,
        },
        "standards": {
            "style_guide": "PEP 8",
            "docstrings": "recommended",
            "type_hints": "recommended",
            "test_structure": "AAA",
        },
    }


def scaffold_broken_project(tmp_path):
    """Scaffold a project with a failing test."""
    import textwrap
    src = tmp_path / "src"
    src.mkdir()
    (src / "__init__.py").write_text("")
    (src / "calc.py").write_text(textwrap.dedent("""\
        # Implements: REQ-F-CALC-001
        def add(a, b):
            return a - b  # BUG: subtraction instead of addition
    """))

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_calc.py").write_text(textwrap.dedent("""\
        # Validates: REQ-F-CALC-001
        from src.calc import add

        def test_add():
            assert add(2, 3) == 5  # will FAIL
    """))

    (tmp_path / "pyproject.toml").write_text(textwrap.dedent("""\
        [tool.pytest.ini_options]
        pythonpath = ["."]
    """))
    return tmp_path


def red_constraints():
    return {
        "tools": {
            "test_runner": {
                "command": "python -m pytest",
                "args": "tests/ -v --tb=short",
                "pass_criterion": "exit code 0",
            },
            "linter": {
                "command": "python -m py_compile",
                "args": "src/calc.py",
                "pass_criterion": "exit code 0",
            },
            "formatter": {
                "command": "true",
                "args": "",
                "pass_criterion": "exit code 0",
            },
            "coverage": {
                "command": "true",
                "args": "",
                "pass_criterion": "exit code 0",
            },
            "type_checker": {
                "command": "true",
                "args": "",
                "pass_criterion": "exit code 0",
                "required": False,
            },
        },
        "thresholds": {"test_coverage_minimum": 0.80},
        "standards": {"style_guide": "PEP 8"},
    }


def make_engine_config(workspace_path, constraints, graph_topology=None):
    """Build an EngineConfig pointing at the real plugin configs."""
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "code"))
    from genesis.engine import EngineConfig
    from genesis.config_loader import load_yaml as _load_yaml
    return EngineConfig(
        project_name="test_project",
        workspace_path=workspace_path,
        edge_params_dir=EDGE_PARAMS_DIR,
        profiles_dir=PROFILES_DIR,
        constraints=constraints,
        graph_topology=graph_topology or _load_yaml(CONFIG_DIR / "graph_topology.yml"),
        model="sonnet",
        max_iterations_per_edge=3,
        claude_timeout=5,
    )


def events_path(workspace):
    return workspace / ".ai-workspace" / "events" / "events.jsonl"


def read_events(workspace):
    ep = events_path(workspace)
    if not ep.exists():
        return []
    return [json.loads(l) for l in ep.read_text().strip().split("\n") if l.strip()]


@pytest.fixture
def spec_req_keys():
    """Extract all REQ keys from implementation requirements doc."""
    import re
    req_file = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
    keys = set()
    with open(req_file) as f:
        for line in f:
            keys.update(re.findall(r'REQ-[A-Z]+-\d+', line))
    return keys


@pytest.fixture
def feature_vector_req_keys():
    """Extract all REQ-F-* keys from feature vectors doc."""
    import re
    fv_file = SPEC_DIR / "FEATURE_VECTORS.md"
    keys = set()
    with open(fv_file) as f:
        for line in f:
            keys.update(re.findall(r'REQ-F-[A-Z]+-\d+', line))
    return keys
