import pytest
from pathlib import Path
from gemini_cloud.engine.iterate import CloudIterateEngine
from gemini_cloud.functors.f_vertex import VertexFunctor
from gemini_cloud.engine.models import Outcome

def test_iterate_with_guardrail_failure(tmp_path):
    project_root = tmp_path
    (project_root / "gemini_cloud").mkdir()
    (project_root / ".ai-workspace" / "context").mkdir(parents=True)
    
    functors = {"F_P": VertexFunctor("test-project")}
    engine = CloudIterateEngine(functors, project_root)
    
    asset_path = project_root / "test.py"
    # No REQ tags, but it's pre-flight check that we test here
    # Edge with 'design' requires 'upstream_converged'
    
    result = engine.run(
        asset_path=asset_path,
        feature="F1",
        edge="requirements→design",
        context={"upstream_converged": False}
    )
    
    assert result.converged is False
    assert any(gr.name == "upstream_dependency" and not gr.passed for gr in result.guardrail_results)
    assert result.delta == -1

def test_iterate_with_tagging_guardrail_failure(tmp_path):
    project_root = tmp_path
    (project_root / "gemini_cloud").mkdir()
    (project_root / ".ai-workspace" / "context").mkdir(parents=True)
    
    functors = {"F_P": VertexFunctor("test-project")}
    engine = CloudIterateEngine(functors, project_root)
    
    asset_path = project_root / "test.py"
    asset_path.write_text("print('hello')") # Missing REQ tags
    
    result = engine.run(
        asset_path=asset_path,
        feature="F1",
        edge="design→code",
        context={"upstream_converged": True, "mock": True}
    )
    
    # VertexFunctor simulation will add the tag, so it should PASS the guardrail eventually
    # Wait, the guardrail check in CloudIterateEngine happens AFTER the functor.
    # VertexFunctor simulation adds '# Implements: REQ-F1-001'
    
    assert any(gr.name == "tagging_discipline" and gr.passed for gr in result.guardrail_results)
    assert "Implements: REQ-F1-001" in asset_path.read_text()

def test_iterate_convergence(tmp_path):
    project_root = tmp_path
    (project_root / "gemini_cloud").mkdir()
    (project_root / ".ai-workspace" / "context").mkdir(parents=True)
    
    functors = {"F_P": VertexFunctor("test-project")}
    engine = CloudIterateEngine(functors, project_root)
    
    asset_path = project_root / "test.py"
    asset_path.write_text("# Implements: REQ-F1-001\nprint('hello')")
    
    result = engine.run(
        asset_path=asset_path,
        feature="F1",
        edge="design→code",
        context={"upstream_converged": True, "mock": True}
    )
    
    assert result.converged is True
    assert result.delta == 0
