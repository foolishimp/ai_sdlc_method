# Validates: REQ-TOOL-005, REQ-TOOL-009
"""Fixtures for Codex implementation tests."""

import pathlib
import json
import shutil

import pytest
import yaml

# Root paths
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
# Canonical specification root (nested layout)
SPEC_ROOT = PROJECT_ROOT / "specification"

# Codex implementation paths
IMP_CODEX = PROJECT_ROOT / "imp_codex"
# Compatibility mirror so legacy tests can keep using SPEC_DIR / "<doc>.md"
SPEC_DIR = IMP_CODEX / ".spec_compat"
DESIGN_DIR = IMP_CODEX / "design"
PLUGIN_ROOT = IMP_CODEX / "code"
CONFIG_DIR = PLUGIN_ROOT / "config"
EDGE_PARAMS_DIR = CONFIG_DIR / "edge_params"
PROFILES_DIR = CONFIG_DIR / "profiles"
COMMANDS_DIR = PLUGIN_ROOT / "commands"
AGENTS_DIR = PLUGIN_ROOT / "agents"


def _ensure_spec_compat() -> None:
    """Mirror nested specification docs into a flat compat directory.

    The repository now stores docs in `specification/{core,features,requirements}`.
    Most imp_codex tests still reference a flat `SPEC_DIR / <doc>.md` path.
    """
    SPEC_DIR.mkdir(parents=True, exist_ok=True)

    mapping = {
        SPEC_ROOT / "INTENT.md": SPEC_DIR / "INTENT.md",
        SPEC_ROOT / "core" / "AI_SDLC_ASSET_GRAPH_MODEL.md": SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md",
        SPEC_ROOT / "core" / "PROJECTIONS_AND_INVARIANTS.md": SPEC_DIR / "PROJECTIONS_AND_INVARIANTS.md",
        SPEC_ROOT / "requirements" / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md": SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md",
        SPEC_ROOT / "features" / "FEATURE_VECTORS.md": SPEC_DIR / "FEATURE_VECTORS.md",
    }

    for src, dst in mapping.items():
        if not src.exists():
            raise FileNotFoundError(f"Required spec document missing: {src}")
        shutil.copy2(src, dst)


_ensure_spec_compat()


def pytest_ignore_collect(collection_path, config):  # pragma: no cover
    """Prevent archived e2e artifacts from being collected as tests."""
    return "imp_codex/tests/e2e/runs/" in str(collection_path)



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
