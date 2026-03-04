# Runs the UAT BDD scenarios and pipes the resulting events to a live Phoenix instance.
import os
import time
import pytest
from pathlib import Path
import threading

from gemini_cli.engine.sensory import SensoryService
from gemini_cli.engine.otlp_relay import OTLPRelay

def run():
    # 1. Setup a persistent test workspace so the Relay can tail it
    test_ws = Path("/tmp/sdlc-bdd-phoenix/.ai-workspace")
    if test_ws.exists():
        import shutil
        shutil.rmtree(test_ws.parent)
    
    (test_ws / "events").mkdir(parents=True)
    
    print("[BDD-Phoenix] Starting OTLP Relay...")
    relay = OTLPRelay(test_ws, collector_endpoint="http://localhost:6006/v1/traces")
    relay.start()
    time.sleep(1) # Let it initialize
    
    # 2. Run the BDD tests, overriding the tmp_path fixture to use our persistent one
    print("[BDD-Phoenix] Running UAT BDD Tests...")
    
    # We use a pytest hook to override the bdd_workspace and core_workspace fixtures
    class WorkspaceOverridePlugin:
        @pytest.fixture(autouse=True)
        def override_workspace(self, monkeypatch):
            # We patch the tests to use our live relay path instead of tmp_path
            monkeypatch.setattr("imp_gemini.tests.uat.test_observability_bdd.bdd_workspace", lambda *args: test_ws)
            monkeypatch.setattr("imp_gemini.tests.uat.test_core_methodology_bdd.core_workspace", lambda *args: test_ws)
            monkeypatch.setattr("imp_gemini.tests.uat.test_graph_engine_bdd.graph_workspace", lambda *args: test_ws)
    
    # Run the tests. We skip the observability test that mocks the tracer, 
    # because we want to use the REAL tracer here.
    exit_code = pytest.main([
        "imp_gemini/tests/uat/test_core_methodology_bdd.py",
        "imp_gemini/tests/uat/test_graph_engine_bdd.py",
        "-v"
    ])
    
    print(f"\n[BDD-Phoenix] Tests completed with exit code: {exit_code}")
    print("[BDD-Phoenix] Waiting 5s for Relay to flush to Phoenix...")
    time.sleep(5)
    relay.stop()
    
    print("\n" + "="*60)
    print(" View the BDD Test execution in Phoenix:")
    print(" 1. Open http://localhost:6006")
    print(" 2. Look for Trace names starting with 'edge_converged:' or 'feature_spawned:'")
    print(" 3. Filter by 'sdlc.feature_id == REQ-F-TDD-001' to see the TDD cycle.")
    print("="*60)

if __name__ == "__main__":
    run()
