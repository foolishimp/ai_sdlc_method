# Validates: REQ-SUPV-003, REQ-EVAL-001, REQ-EVAL-002, REQ-F-EVAL-001, ADR-S-026
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
    pytest imp_gemini/tests/e2e/test_e2e_homeostasis.py -v -m e2e -s
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
    run_gemini_headless,
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
    from src.converter import celsius_to_fahrenheit, fahrenheit_to_celsius

    # Validates: REQ-F-CONV-001
    def test_freezing_point():
        assert celsius_to_fahrenheit(0) == 32.0

    # Validates: REQ-F-CONV-001
    def test_boiling_point():
        assert celsius_to_fahrenheit(100) == 212.0
''')

# Unified Intent Vector with earlier edges pre-converged, code↔unit_tests pending
HOMEOSTASIS_INTENT_VECTOR_YML = textwrap.dedent("""
    id: "INTENT-CONV-001"
    source: "abiogenesis"
    parent_vector_id: ""
    resolution_level: "code"
    vector_type: "feature"
    profile: "standard"
    status: "iterating"
    created_at: "{timestamp}"
    updated_at: "{timestamp}"
    composition_expression:
      macro: "BUILD"
      bindings:
        unit_category: "module"
    trajectory:
      intent:
        status: converged
      requirements:
        status: converged
      design:
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
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # 1. Scaffolding (Unified Layout)
    for d in ["graph/edges", "profiles", "vectors/active", "events", "gemini_genesis", "spec"]:
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
    
    # 5. conftest for path
    (project_dir / "tests" / "conftest.py").write_text(textwrap.dedent("""
        import sys
        import pathlib
        sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
    """))
    
    # 6. Unified Intent Vector
    with open(ws / "vectors" / "active" / "INTENT-CONV-001.yml", "w") as f:
        f.write(HOMEOSTASIS_INTENT_VECTOR_YML.replace("{timestamp}", timestamp))
    
    # 7. Initial Event
    ev = {"event_type": "project_initialized", "timestamp": timestamp, "project": "temperature-converter"}
    with open(ws / "events" / "events.jsonl", "w") as f:
        f.write(json.dumps(ev) + "\n")
        
    # 8. Copy code directory for agentic discovery
    dest_code = project_dir / "code"
    shutil.copytree(IMP_GEMINI / "gemini_cli", dest_code, dirs_exist_ok=True)

    return project_dir

@pytest.fixture(scope="module")
def homeostasis_result(homeostasis_project_dir: pathlib.Path) -> pathlib.Path:
    """REAL E2E: Run Gemini CLI headless to fix the buggy code."""
    project_dir = homeostasis_project_dir
    
    # Prompt forcing evaluation-first protocol
    prompt = (
        "You are the AI SDLC methodology engine. Intent Vector 'INTENT-CONV-001' is in progress. "
        "The 'code' edge is converged but 'unit_tests' is pending. "
        "The current 'src/converter.py' has BUGS. "
        "PROTOCOL: \n"
        "1. You MUST first run 'pytest' to detect the failures in iteration 1. \n"
        "2. Record 'iteration_completed' with 'delta > 0' and 'status: failed'. \n"
        "3. Then FIX the formulas in 'src/converter.py' and re-run tests in iteration 2. \n"
        "4. Converge the 'code\u2194unit_tests' edge with 'delta: 0' and 'status: converged'.\n"
        "Respond with terminal commands only."
    )
    
    result = run_gemini_headless(project_dir, prompt)
    
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

    def test_multi_iteration_convergence(self, homeostasis_result: pathlib.Path):
        """The code\u2194unit_tests edge MUST take more than 1 iteration."""
        events = load_events(homeostasis_result)
        iterations = [e for e in events if e.get("event_type") == "iteration_completed" and "unit_tests" in e.get("edge", "")]
        assert len(iterations) > 1, f"Expected > 1 iteration for buggy code, found {len(iterations)}"

    def test_initial_delta_nonzero(self, homeostasis_result: pathlib.Path):
        """First iteration must have delta > 0 (RED phase)."""
        events = load_events(homeostasis_result)
        iterations = [e for e in events if e.get("event_type") == "iteration_completed" and "unit_tests" in e.get("edge", "")]
        assert iterations[0].get("delta", 0) > 0, "First iteration should have failed with delta > 0"

    def test_delta_decreases_to_zero(self, homeostasis_result: pathlib.Path):
        """Delta must eventually reach 0 (GREEN phase)."""
        events = load_events(homeostasis_result)
        iterations = [e for e in events if e.get("event_type") == "iteration_completed" and "unit_tests" in e.get("edge", "")]
        assert iterations[-1].get("delta") == 0, f"Final delta should be 0, found {iterations[-1].get('delta')}"

    def test_edge_converged_emitted(self, homeostasis_result: pathlib.Path):
        """An edge_converged event must be emitted when delta is 0."""
        events = load_events(homeostasis_result)
        converged = [e for e in events if e.get("event_type") == "edge_converged" and "unit_tests" in e.get("edge", "")]
        assert converged, "No edge_converged event found for unit_tests"

    def test_buggy_formulas_corrected(self, homeostasis_result: pathlib.Path):
        """The agent should have fixed the formulas in converter.py."""
        conv_file = homeostasis_result / "src" / "converter.py"
        content = conv_file.read_text()
        # The buggy formula was: c * 2 + 30
        assert "* 2 + 30" not in content, "Buggy formula still present in converter.py"
        assert "9/5" in content or "1.8" in content, "Correct formula not found in converter.py"
