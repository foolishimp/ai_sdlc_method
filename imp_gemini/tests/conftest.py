# Validates: REQ-TOOL-005, REQ-TOOL-009
"""Fixtures for Gemini CLI implementation tests."""

import pathlib
import json

import pytest
import yaml

# Do not collect archived E2E run artifacts as active tests.
collect_ignore_glob = ["e2e/runs/*"]

# Root paths
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
SPEC_DIR = PROJECT_ROOT / "specification"

# Gemini implementation paths
IMP_GEMINI = PROJECT_ROOT / "imp_gemini"
DESIGN_DIR = IMP_GEMINI / "design"
PLUGIN_ROOT = IMP_GEMINI / "gemini_cli"
CONFIG_DIR = PLUGIN_ROOT / "config"
EDGE_PARAMS_DIR = CONFIG_DIR / "edge_params"
PROFILES_DIR = CONFIG_DIR / "profiles"
COMMANDS_DIR = PLUGIN_ROOT / "commands"
AGENTS_DIR = PLUGIN_ROOT / "agents"



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
