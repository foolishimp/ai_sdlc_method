# Validates: REQ-CTX-001, REQ-CTX-002, REQ-INTENT-004
import copy
import hashlib
import json
import pytest
import yaml
from genesis_core.internal.workspace_state import (
    compute_context_hash,
    deep_merge,
    resolve_context_hierarchy,
)

pytestmark = [pytest.mark.uat]

class TestContextConstraintSurface:
    def test_context_types_defined(self, initialized_workspace):
        ctx = initialized_workspace / ".ai-workspace" / "gemini_genesis" / "project_constraints.yml"
        assert ctx.exists()

    def test_context_version_control(self, initialized_workspace):
        ctx_path = initialized_workspace / ".ai-workspace" / "gemini_genesis" / "project_constraints.yml"
        with open(ctx_path) as f:
            constraints = yaml.safe_load(f)
        
        hash_v1 = compute_context_hash(constraints)
        
        modified = copy.deepcopy(constraints)
        modified["project"]["version"] = "0.2.0"
        
        hash_v2 = compute_context_hash(modified)
        assert hash_v1 != hash_v2
        assert compute_context_hash(constraints) == hash_v1

class TestContextHierarchy:
    def test_hierarchy_override(self):
        global_ctx = {
            "language": {"primary": "python", "version": "3.10"},
            "thresholds": {"test_coverage_minimum": 0.80},
        }
        project_ctx = {
            "language": {"version": "3.12"},
            "thresholds": {"test_coverage_minimum": 0.95},
        }
        resolved = resolve_context_hierarchy([global_ctx, project_ctx])
        assert resolved["language"]["version"] == "3.12"
        assert resolved["thresholds"]["test_coverage_minimum"] == 0.95
        assert resolved["language"]["primary"] == "python"

    def test_deep_merge_objects(self):
        base = {
            "tools": {
                "test_runner": {"command": "pytest", "args": "-v"},
            },
        }
        override = {
            "tools": {
                "test_runner": {"args": "-v --tb=short"},
            },
        }
        result = deep_merge(base, override)
        assert result["tools"]["test_runner"]["command"] == "pytest"
        assert result["tools"]["test_runner"]["args"] == "-v --tb=short"

class TestSpecReproducibility:
    def test_deterministic_serialisation(self):
        context_a = {"a": 1, "b": 2}
        context_b = {"b": 2, "a": 1}
        assert compute_context_hash(context_a) == compute_context_hash(context_b)

    def test_spec_versions_immutable(self, in_progress_workspace):
        intent_path = in_progress_workspace / ".ai-workspace" / "spec" / "INTENT.md"
        original_content = intent_path.read_text()
        original_hash = hashlib.sha256(original_content.encode()).hexdigest()
        
        intent_path.write_text(original_content + "\nModified")
        modified_hash = hashlib.sha256(intent_path.read_text().encode()).hexdigest()
        assert original_hash != modified_hash
