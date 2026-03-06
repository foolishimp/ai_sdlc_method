# Validates: REQ-ITER-003, REQ-CTX-001, REQ-CTX-002
"""Tests for genesis config_loader — YAML loading, $variable resolution, and context hierarchy."""

import pathlib
import textwrap

import pytest
import yaml

# Add package to path
import sys
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "code"))

from genesis.config_loader import (
    deep_merge,
    load_context_hierarchy,
    load_yaml,
    merge_contexts,
    resolve_checklist,
    resolve_variable,
    resolve_variables,
)
from genesis.models import ResolvedCheck


# ── deep_merge ────────────────────────────────────────────────────────────


class TestDeepMerge:

    def test_scalar_override(self):
        base = {"language": "python"}
        override = {"language": "typescript"}
        result = deep_merge(base, override)
        assert result["language"] == "typescript"

    def test_scalar_addition(self):
        base = {"a": 1}
        override = {"b": 2}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 2}

    def test_nested_dict_merged_not_replaced(self):
        base = {"tools": {"linter": {"command": "ruff"}, "runner": {"command": "pytest"}}}
        override = {"tools": {"runner": {"args": "-v"}}}
        result = deep_merge(base, override)
        # runner merged: both command and args present
        assert result["tools"]["runner"]["command"] == "pytest"
        assert result["tools"]["runner"]["args"] == "-v"
        # linter unchanged
        assert result["tools"]["linter"]["command"] == "ruff"

    def test_nested_scalar_override(self):
        base = {"thresholds": {"coverage": 0.80, "complexity": 10}}
        override = {"thresholds": {"coverage": 0.90}}
        result = deep_merge(base, override)
        assert result["thresholds"]["coverage"] == 0.90
        assert result["thresholds"]["complexity"] == 10

    def test_does_not_mutate_base(self):
        base = {"a": {"b": 1}}
        override = {"a": {"c": 2}}
        deep_merge(base, override)
        assert "c" not in base["a"]

    def test_does_not_mutate_override(self):
        base = {"a": {"b": 1}}
        override = {"a": {"c": 2}}
        deep_merge(base, override)
        assert "b" not in override["a"]

    def test_empty_base(self):
        override = {"x": 42}
        assert deep_merge({}, override) == {"x": 42}

    def test_empty_override(self):
        base = {"x": 42}
        assert deep_merge(base, {}) == {"x": 42}

    def test_override_replaces_scalar_with_dict(self):
        base = {"tools": "old_scalar"}
        override = {"tools": {"runner": "pytest"}}
        result = deep_merge(base, override)
        assert result["tools"] == {"runner": "pytest"}

    def test_override_replaces_dict_with_scalar(self):
        base = {"tools": {"runner": "pytest"}}
        override = {"tools": "none"}
        result = deep_merge(base, override)
        assert result["tools"] == "none"


# ── merge_contexts ─────────────────────────────────────────────────────────


class TestMergeContexts:

    def test_single_context(self):
        ctx = {"language": "python"}
        assert merge_contexts(ctx) == {"language": "python"}

    def test_no_contexts_returns_empty(self):
        assert merge_contexts() == {}

    def test_three_levels_last_wins(self):
        global_ctx = {"thresholds": {"coverage": 0.70}, "language": "python"}
        org_ctx = {"thresholds": {"coverage": 0.80}}
        project_ctx = {"thresholds": {"coverage": 0.95}}
        result = merge_contexts(global_ctx, org_ctx, project_ctx)
        assert result["thresholds"]["coverage"] == 0.95
        assert result["language"] == "python"  # from global, not overridden

    def test_deep_merge_across_levels(self):
        global_ctx = {"tools": {"linter": {"command": "ruff"}, "runner": {"command": "pytest"}}}
        project_ctx = {"tools": {"runner": {"args": "-v"}}}
        result = merge_contexts(global_ctx, project_ctx)
        assert result["tools"]["linter"]["command"] == "ruff"
        assert result["tools"]["runner"]["command"] == "pytest"
        assert result["tools"]["runner"]["args"] == "-v"

    def test_later_empty_dict_does_not_clobber(self):
        ctx1 = {"a": {"b": 1, "c": 2}}
        ctx2 = {"a": {}}
        result = merge_contexts(ctx1, ctx2)
        assert result["a"]["b"] == 1
        assert result["a"]["c"] == 2


# ── load_context_hierarchy ─────────────────────────────────────────────────


class TestLoadContextHierarchy:

    def _write_yaml(self, path: pathlib.Path, data: dict) -> pathlib.Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.dump(data))
        return path

    def test_single_file(self, tmp_path):
        f = self._write_yaml(tmp_path / "project.yml", {"language": "python"})
        result = load_context_hierarchy([f])
        assert result["language"] == "python"

    def test_missing_file_skipped_by_default(self, tmp_path):
        project = self._write_yaml(tmp_path / "project.yml", {"x": 1})
        result = load_context_hierarchy([tmp_path / "missing.yml", project])
        assert result == {"x": 1}

    def test_stop_on_missing_raises(self, tmp_path):
        import pytest
        with pytest.raises(FileNotFoundError):
            load_context_hierarchy([tmp_path / "missing.yml"], stop_on_missing=True)

    def test_three_level_hierarchy(self, tmp_path):
        global_f = self._write_yaml(tmp_path / "global.yml", {
            "thresholds": {"coverage": 0.70},
            "tools": {"runner": {"command": "pytest"}},
        })
        org_f = self._write_yaml(tmp_path / "org.yml", {
            "thresholds": {"coverage": 0.80},
        })
        project_f = self._write_yaml(tmp_path / "project.yml", {
            "thresholds": {"coverage": 0.95},
            "tools": {"runner": {"args": "-v"}},
        })
        result = load_context_hierarchy([global_f, org_f, project_f])
        assert result["thresholds"]["coverage"] == 0.95
        assert result["tools"]["runner"]["command"] == "pytest"  # from global
        assert result["tools"]["runner"]["args"] == "-v"         # from project

    def test_empty_file_list(self):
        result = load_context_hierarchy([])
        assert result == {}

    def test_all_files_missing_returns_empty(self, tmp_path):
        result = load_context_hierarchy([tmp_path / "a.yml", tmp_path / "b.yml"])
        assert result == {}

    def test_project_overrides_global_scalar(self, tmp_path):
        global_f = self._write_yaml(tmp_path / "global.yml", {"language": "python"})
        project_f = self._write_yaml(tmp_path / "project.yml", {"language": "typescript"})
        result = load_context_hierarchy([global_f, project_f])
        assert result["language"] == "typescript"


# ── resolve_variable ─────────────────────────────────────────────────────

class TestResolveVariable:

    def test_simple_key(self):
        constraints = {"tools": {"test_runner": {"command": "pytest"}}}
        assert resolve_variable("tools.test_runner.command", constraints) == "pytest"

    def test_nested_deep(self):
        constraints = {"a": {"b": {"c": {"d": "deep"}}}}
        assert resolve_variable("a.b.c.d", constraints) == "deep"

    def test_missing_key_returns_none(self):
        constraints = {"tools": {}}
        assert resolve_variable("tools.test_runner.command", constraints) is None

    def test_top_level_key(self):
        constraints = {"language": "python"}
        assert resolve_variable("language", constraints) == "python"

    def test_numeric_value_becomes_string(self):
        constraints = {"thresholds": {"coverage": 0.80}}
        assert resolve_variable("thresholds.coverage", constraints) == "0.8"

    def test_none_value_returns_none(self):
        constraints = {"tools": {"runner": {"command": None}}}
        assert resolve_variable("tools.runner.command", constraints) is None

    def test_bool_value(self):
        constraints = {"tools": {"checker": {"required": False}}}
        assert resolve_variable("tools.checker.required", constraints) == "False"


# ── resolve_variables ────────────────────────────────────────────────────

class TestResolveVariables:

    def test_single_var(self):
        constraints = {"tools": {"test_runner": {"command": "pytest"}}}
        resolved, unresolved = resolve_variables(
            "$tools.test_runner.command -v", constraints
        )
        assert resolved == "pytest -v"
        assert unresolved == []

    def test_multiple_vars(self):
        constraints = {
            "tools": {"test_runner": {"command": "pytest", "args": "-v --tb=short"}}
        }
        resolved, unresolved = resolve_variables(
            "$tools.test_runner.command $tools.test_runner.args", constraints
        )
        assert resolved == "pytest -v --tb=short"
        assert unresolved == []

    def test_unresolved_var(self):
        constraints = {}
        resolved, unresolved = resolve_variables(
            "$tools.test_runner.command -v", constraints
        )
        assert resolved == "$tools.test_runner.command -v"
        assert unresolved == ["tools.test_runner.command"]

    def test_mixed_resolved_and_unresolved(self):
        constraints = {"tools": {"linter": {"command": "ruff check"}}}
        resolved, unresolved = resolve_variables(
            "$tools.linter.command $tools.linter.nonexistent", constraints
        )
        assert resolved == "ruff check $tools.linter.nonexistent"
        assert "tools.linter.nonexistent" in unresolved

    def test_no_vars(self):
        resolved, unresolved = resolve_variables("plain text", {})
        assert resolved == "plain text"
        assert unresolved == []

    def test_var_in_criterion_text(self):
        constraints = {"thresholds": {"test_coverage_minimum": 0.80}}
        resolved, unresolved = resolve_variables(
            "Test coverage >= $thresholds.test_coverage_minimum", constraints
        )
        assert resolved == "Test coverage >= 0.8"
        assert unresolved == []


# ── resolve_checklist ────────────────────────────────────────────────────

class TestResolveChecklist:

    @pytest.fixture
    def sample_constraints(self):
        return {
            "tools": {
                "test_runner": {
                    "command": "pytest",
                    "args": "-v",
                    "pass_criterion": "exit code 0",
                },
                "linter": {
                    "command": "ruff check",
                    "args": ".",
                    "pass_criterion": "exit code 0, zero violations",
                },
                "type_checker": {
                    "command": "mypy",
                    "args": "--strict src/",
                    "pass_criterion": "exit code 0, zero errors",
                    "required": False,
                },
            },
            "thresholds": {"test_coverage_minimum": 0.80},
            "standards": {"style_guide": "PEP 8"},
        }

    @pytest.fixture
    def sample_checklist(self):
        return {
            "checklist": [
                {
                    "name": "tests_pass",
                    "type": "deterministic",
                    "functional_unit": "evaluate",
                    "criterion": "All tests pass",
                    "source": "default",
                    "required": True,
                    "command": "$tools.test_runner.command $tools.test_runner.args",
                    "pass_criterion": "$tools.test_runner.pass_criterion",
                },
                {
                    "name": "code_quality",
                    "type": "agent",
                    "functional_unit": "evaluate",
                    "criterion": "Code follows $standards.style_guide",
                    "source": "default",
                    "required": True,
                },
                {
                    "name": "type_check",
                    "type": "deterministic",
                    "functional_unit": "evaluate",
                    "criterion": "Type checker reports zero errors",
                    "source": "default",
                    "required": "$tools.type_checker.required",
                    "command": "$tools.type_checker.command $tools.type_checker.args",
                    "pass_criterion": "$tools.type_checker.pass_criterion",
                },
            ]
        }

    def test_resolves_deterministic_command(self, sample_checklist, sample_constraints):
        checks = resolve_checklist(sample_checklist, sample_constraints)
        tests_pass = checks[0]
        assert tests_pass.name == "tests_pass"
        assert tests_pass.command == "pytest -v"
        assert tests_pass.pass_criterion == "exit code 0"
        assert tests_pass.required is True
        assert tests_pass.unresolved == []

    def test_resolves_agent_criterion(self, sample_checklist, sample_constraints):
        checks = resolve_checklist(sample_checklist, sample_constraints)
        quality = checks[1]
        assert quality.name == "code_quality"
        assert quality.check_type == "agent"
        assert "PEP 8" in quality.criterion
        assert quality.command is None

    def test_resolves_required_as_variable(self, sample_checklist, sample_constraints):
        checks = resolve_checklist(sample_checklist, sample_constraints)
        type_check = checks[2]
        assert type_check.name == "type_check"
        assert type_check.required is False  # resolved from $tools.type_checker.required

    def test_unresolved_vars_tracked(self):
        checklist = {
            "checklist": [
                {
                    "name": "mystery",
                    "type": "deterministic",
                    "criterion": "check $nonexistent.thing",
                    "source": "default",
                    "required": True,
                    "command": "$tools.missing.command",
                }
            ]
        }
        checks = resolve_checklist(checklist, {})
        assert len(checks[0].unresolved) > 0
        assert "nonexistent.thing" in checks[0].unresolved

    def test_empty_checklist(self):
        checks = resolve_checklist({}, {})
        assert checks == []


# ── load_yaml ────────────────────────────────────────────────────────────

class TestLoadYaml:

    def test_loads_single_doc(self, tmp_path):
        f = tmp_path / "test.yml"
        f.write_text("name: test\nversion: 1.0\n")
        result = load_yaml(f)
        assert result["name"] == "test"
        assert result["version"] == 1.0

    def test_loads_multi_doc(self, tmp_path):
        f = tmp_path / "test.yml"
        f.write_text("---\nfoo: bar\n---\nbaz: qux\n")
        result = load_yaml(f)
        assert result["foo"] == "bar"
        assert result["baz"] == "qux"

    def test_loads_real_edge_config(self):
        """Load actual tdd.yml edge config."""
        edge_path = (
            pathlib.Path(__file__).parent.parent
            / "code/.claude-plugin/plugins/genesis/config/edge_params/tdd.yml"
        )
        if edge_path.exists():
            config = load_yaml(edge_path)
            assert "checklist" in config
            assert len(config["checklist"]) > 0

    def test_loads_real_constraints_template(self):
        """Load actual project_constraints_template.yml."""
        path = (
            pathlib.Path(__file__).parent.parent
            / "code/.claude-plugin/plugins/genesis/config/project_constraints_template.yml"
        )
        if path.exists():
            config = load_yaml(path)
            assert "tools" in config
            assert "thresholds" in config


# ── Integration: real edge config + real constraints ─────────────────────

class TestRealConfigResolution:

    @pytest.fixture
    def real_edge_config(self):
        path = (
            pathlib.Path(__file__).parent.parent
            / "code/.claude-plugin/plugins/genesis/config/edge_params/tdd.yml"
        )
        if not path.exists():
            pytest.skip("tdd.yml not found")
        return load_yaml(path)

    @pytest.fixture
    def real_constraints(self):
        path = (
            pathlib.Path(__file__).parent.parent
            / "code/.claude-plugin/plugins/genesis/config/project_constraints_template.yml"
        )
        if not path.exists():
            pytest.skip("project_constraints_template.yml not found")
        return load_yaml(path)

    def test_resolve_tdd_checklist(self, real_edge_config, real_constraints):
        checks = resolve_checklist(real_edge_config, real_constraints)
        assert len(checks) > 0

        # Find the tests_pass check
        tests_pass = next((c for c in checks if c.name == "tests_pass"), None)
        assert tests_pass is not None
        assert tests_pass.command == "pytest -v --tb=short"
        assert tests_pass.check_type == "deterministic"
        assert tests_pass.required is True

    def test_all_deterministic_checks_with_tools_have_commands(self, real_edge_config, real_constraints):
        checks = resolve_checklist(real_edge_config, real_constraints)
        for check in checks:
            # Traceability checks are deterministic but agent-evaluated (no shell command)
            if (
                check.check_type == "deterministic"
                and not check.unresolved
                and check.source != "traceability"
            ):
                assert check.command, f"{check.name} is deterministic but has no command"
