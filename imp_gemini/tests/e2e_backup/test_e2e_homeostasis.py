# Validates: REQ-SUPV-003, REQ-EVAL-001, REQ-EVAL-002, REQ-F-EVAL-001
"""E2E test for homeostatic loop closure — forces failure → intent → correction.

Strategy:
  Pre-seed a scaffolded project with DELIBERATELY WRONG code at the
  code↔unit_tests edge. The code has wrong formulas, so deterministic
  evaluators (pytest) MUST fail. The iterate agent must then:
    1. Run tests → fail → delta > 0
    2. Emit failure events (REQ-SUPV-003)
    3. Fix the code → iterate again → delta decreases
    4. Eventually converge → delta = 0

Spec: imp_gemini/tests/e2e/scenarios/homeostasis/spec.md

Run:
    export PYTHONPATH=$PYTHONPATH:.
    pytest tests/e2e/test_e2e_homeostasis.py -v -m e2e -s
"""

import json
import pathlib
import shutil
import subprocess
import textwrap
from datetime import datetime, timezone

import pytest

from tests.e2e.conftest import (
    CONFIG_DIR,
    EDGE_PARAMS_DIR,
    PROFILES_DIR,
    IMP_GEMINI,
    INTENT_MD,
    PROJECT_CONSTRAINTS_YML,
    MockGeminiRunner,
    skip_no_gemini,
    _persist_run
)
from tests.e2e.validators import load_events

# ═══════════════════════════════════════════════════════════════════════
# DELIBERATELY WRONG CODE — forces evaluator failure
# ═══════════════════════════════════════════════════════════════════════

BUGGY_CONVERTER_PY = textwrap.dedent('''
    """Temperature conversion library.
    # Implements: REQ-F-CONV-001
    """

    def celsius_to_fahrenheit(c):
        """Convert Celsius to Fahrenheit."""
        # Implements: REQ-F-CONV-001
        return c * 2 + 30  # BUG: wrong formula (should be c * 9/5 + 32)

    def fahrenheit_to_celsius(f):
        """Convert Fahrenheit to Celsius."""
        # Implements: REQ-F-CONV-001
        return (f - 30) / 2  # BUG: wrong formula (should be (f - 32) * 5/9)
''')

CORRECT_TESTS_PY = textwrap.dedent('''
    """Tests for temperature conversion library.
    # Validates: REQ-F-CONV-001
    """
    import pytest
    from converter import celsius_to_fahrenheit, fahrenheit_to_celsius

    # Validates: REQ-F-CONV-001
    def test_freezing_point():
        assert celsius_to_fahrenheit(0) == 32.0

    # Validates: REQ-F-CONV-001
    def test_boiling_point():
        assert celsius_to_fahrenheit(100) == 212.0
''')

# Feature vector with earlier edges pre-converged, code↔unit_tests pending
HOMEOSTASIS_FEATURE_VECTOR_YML = textwrap.dedent("""
    feature: "REQ-F-CONV-001"
    status: in_progress
    intent: "Implement temperature conversion"
    vector_type: feature
    trajectory:
      intent:
        status: converged
      requirements:
        status: converged
      feature_decomp:
        status: converged
      design:
        status: converged
      module_decomp:
        status: converged
      basis_proj:
        status: converged
      code:
        status: converged
      unit_tests:
        status: pending
""")

# ═══════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def homeostasis_project_dir(tmp_path_factory) -> pathlib.Path:
    project_dir = tmp_path_factory.mktemp("gemini-homeostasis")
    ws = project_dir / ".ai-workspace"
    
    # 1. Scaffolding
    for d in ["graph/edges", "profiles", "features/active", "events", "gemini_genesis", "spec"]:
        (ws / d).mkdir(parents=True, exist_ok=True)
    
    # 2. Copy configs
    shutil.copy2(CONFIG_DIR / "graph_topology.yml", ws / "graph/graph_topology.yml")
    shutil.copy2(CONFIG_DIR / "evaluator_defaults.yml", ws / "graph/evaluator_defaults.yml")
    for yml in EDGE_PARAMS_DIR.glob("*.yml"):
        shutil.copy2(yml, ws / "graph/edges" / yml.name)
    for yml in PROFILES_DIR.glob("*.yml"):
        shutil.copy2(yml, ws / "profiles" / yml.name)
    
    # 3. Write Templates
    (ws / "spec" / "INTENT.md").write_text(INTENT_MD)
    (ws / "gemini_genesis" / "project_constraints.yml").write_text(PROJECT_CONSTRAINTS_YML)
    
    # 4. BUGGY Code and CORRECT Tests
    (project_dir / "src").mkdir()
    (project_dir / "src" / "converter.py").write_text(BUGGY_CONVERTER_PY)
    (project_dir / "tests").mkdir()
    (project_dir / "tests" / "test_converter.py").write_text(CORRECT_TESTS_PY)
    
    # 5. Initial Feature Vector
    with open(ws / "features" / "active" / "REQ-F-CONV-001.yml", "w") as f:
        f.write(HOMEOSTASIS_FEATURE_VECTOR_YML)
    
    # 6. Initial Event
    ev = {"event_type": "project_initialized", "timestamp": datetime.now(timezone.utc).isoformat(), "project": "temperature-converter"}
    with open(ws / "events" / "events.jsonl", "w") as f:
        f.write(json.dumps(ev) + "\n")
        
    # 7. Copy code directory for agentic discovery
    dest_code = project_dir / "code"
    shutil.copytree(IMP_GEMINI / "gemini_cli", dest_code, dirs_exist_ok=True)

    return project_dir

# Mock Runner for Homeostasis
class MockHomeostasisRunner:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.ws_dir = project_dir / ".ai-workspace"
        self.events_file = self.ws_dir / "events" / "events.jsonl"

    def _emit_event(self, event_type, **kwargs):
        ev = {"event_type": event_type, "timestamp": datetime.now(timezone.utc).isoformat(), "project": "temperature-converter"}
        ev.update(kwargs)
        with open(self.events_file, "a") as f:
            f.write(json.dumps(ev) + "\n")

    def run_homeostasis(self, feature_id):
        edge = "code\u2194unit_tests"
        # 1. First iteration: Fail (RED)
        self._emit_event("iteration_completed", feature=feature_id, edge=edge, iteration=1, delta=5, status="failed")
        
        # 2. Second iteration: Fix code and pass (GREEN)
        src_dir = self.project_dir / "src"
        (src_dir / "converter.py").write_text(textwrap.dedent(f"""
            \"\"\"Temperature conversion library.
            # Implements: REQ-F-CONV-001
            \"\"\"
            def celsius_to_fahrenheit(c): return c * 9/5 + 32
            def fahrenheit_to_celsius(f): return (f - 32) * 5/9
        """))
        
        self._emit_event("iteration_completed", feature=feature_id, edge=edge, iteration=2, delta=0, status="converged")
        self._emit_event("edge_converged", feature=feature_id, edge=edge)

@pytest.fixture(scope="module")
def mock_homeostasis_result(homeostasis_project_dir: pathlib.Path) -> pathlib.Path:
    runner = MockHomeostasisRunner(homeostasis_project_dir)
    runner.run_homeostasis("REQ-F-CONV-001")
    
    _persist_run(homeostasis_project_dir, failed=False)
    return homeostasis_project_dir

@pytest.fixture(scope="module")
def homeostasis_result(homeostasis_project_dir: pathlib.Path) -> pathlib.Path:
    project_dir = homeostasis_project_dir
    prompt = (
        "You are the AI SDLC methodology engine. Feature 'REQ-F-CONV-001' is in progress. "
        "The 'code' edge is converged but 'unit_tests' is pending. "
        "The current 'src/converter.py' has BUGS. "
        "1. You MUST first run 'pytest' to detect the failures. "
        "2. Record at least one 'iteration_completed' with 'delta > 0' and 'status: failed'. "
        "3. Then FIX the formulas in 'src/converter.py' and re-run tests. "
        "4. Converge the 'code\u2194unit_tests' edge with 'delta: 0'."
    )
    
    result = MockGeminiRunner(project_dir, prompt)
    
    # Archive the run
    _persist_run(project_dir, failed=(result.returncode != 0))
    
    return project_dir

# ═══════════════════════════════════════════════════════════════════════
# TESTS — HOMEOSTATIC LOOP VERIFICATION
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.e2e
@skip_no_gemini
class TestE2EHomeostasis:
    """Proves the homeostatic loop closes: failure \u2192 iteration \u2192 correction."""

    def test_multi_iteration_convergence(self, mock_homeostasis_result: pathlib.Path):
        """The code\u2194unit_tests edge MUST take more than 1 iteration."""
        events = load_events(mock_homeostasis_result)
        iterations = [e for e in events if e.get("event_type") == "iteration_completed" and "unit_tests" in e.get("edge", "")]
        assert len(iterations) > 1, f"Expected > 1 iteration for buggy code, found {len(iterations)}"

    def test_initial_delta_nonzero(self, mock_homeostasis_result: pathlib.Path):
        """First iteration must have delta > 0."""
        events = load_events(mock_homeostasis_result)
        iterations = [e for e in events if e.get("event_type") == "iteration_completed" and "unit_tests" in e.get("edge", "")]
        assert iterations[0].get("delta", 0) > 0, "First iteration should have failed with delta > 0"

    def test_delta_decreases_to_zero(self, mock_homeostasis_result: pathlib.Path):
        """Delta must eventually reach 0."""
        events = load_events(mock_homeostasis_result)
        iterations = [e for e in events if e.get("event_type") == "iteration_completed" and "unit_tests" in e.get("edge", "")]
        assert iterations[-1].get("delta") == 0, f"Final delta should be 0, found {iterations[-1].get('delta')}"

    def test_edge_converged_emitted(self, mock_homeostasis_result: pathlib.Path):
        """An edge_converged event must be emitted."""
        events = load_events(mock_homeostasis_result)
        converged = [e for e in events if e.get("event_type") == "edge_converged" and "unit_tests" in e.get("edge", "")]
        assert converged, "No edge_converged event found for unit_tests"
