# Validates: REQ-SUPV-001
import pytest
from pathlib import Path
from gemini_cli.engine.guardrails import GuardrailEngine
from gemini_cli.engine.iterate import IterateEngine
from gemini_cli.engine.models import Outcome, FunctorResult

def test_dependency_guardrail_block():
    # Arrange
    constraints = {}
    engine = GuardrailEngine(constraints)
    
    # Act: 'design' edge with 'upstream_converged=False'
    context = {"edge": "design→code", "upstream_converged": False}
    results = engine.validate_pre_flight("design→code", context)
    
    # Assert
    assert len(results) == 1
    assert results[0].passed is False
    assert "upstream asset is stable" in results[0].message

def test_security_guardrail_block():
    # Arrange
    constraints = {"classification": "confidential"}
    engine = GuardrailEngine(constraints)
    
    # Act: Confidential project without security scanner
    context = {"edge": "code↔unit_tests", "security_scanner_enabled": False}
    results = engine.validate_pre_flight("code↔unit_tests", context)
    
    # Assert
    assert len(results) == 1
    assert results[0].passed is False
    assert "security scanning" in results[0].message

def test_iterate_engine_aborts_on_guardrail(tmp_path):
    # Arrange
    constraints = {"classification": "confidential"}
    engine = IterateEngine(functors=[], constraints=constraints)
    
    asset = tmp_path / "asset.txt"
    asset.write_text("content")
    
    # Act: Context violates confidential security rule
    context = {"edge": "code↔unit_tests", "security_scanner_enabled": False}
    report = engine.run(asset, context)
    
    # Assert
    assert report.delta == -1
    assert any(not g.passed for g in report.guardrail_results)
