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
    SIX_LEVEL_HIERARCHY,
    build_six_level_paths,
    deep_merge,
    generate_context_manifest,
    load_context_hierarchy,
    load_context_sources,
    load_six_level_context,
    load_yaml,
    merge_contexts,
    resolve_checklist,
    resolve_variable,
    resolve_variables,
    write_context_manifest,
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


# ── SIX_LEVEL_HIERARCHY constant ──────────────────────────────────────────


class TestSixLevelHierarchyConstant:
    """T-COMPLY-002: ADR-S-022 §2 — canonical 6-level sequence."""

    def test_has_six_levels(self):
        assert len(SIX_LEVEL_HIERARCHY) == 6

    def test_level_order(self):
        assert SIX_LEVEL_HIERARCHY == (
            "methodology", "org", "policy", "domain", "prior", "project"
        )

    def test_methodology_is_first(self):
        assert SIX_LEVEL_HIERARCHY[0] == "methodology"

    def test_project_is_last(self):
        assert SIX_LEVEL_HIERARCHY[-1] == "project"


# ── build_six_level_paths ────────────────────────────────────────────────


class TestBuildSixLevelPaths:
    """T-COMPLY-002: path list builder for workspace context directories."""

    def test_returns_seven_paths_by_default(self, tmp_path):
        """6 scope dirs + 1 project_constraints.yml = 7 paths."""
        paths = build_six_level_paths(tmp_path)
        assert len(paths) == 7

    def test_returns_six_paths_without_constraints(self, tmp_path):
        paths = build_six_level_paths(tmp_path, include_project_constraints=False)
        assert len(paths) == 6

    def test_path_order_matches_hierarchy(self, tmp_path):
        paths = build_six_level_paths(tmp_path, include_project_constraints=False)
        for i, level in enumerate(SIX_LEVEL_HIERARCHY):
            assert level in str(paths[i]), f"Level {level!r} not in path[{i}]: {paths[i]}"

    def test_methodology_is_first(self, tmp_path):
        paths = build_six_level_paths(tmp_path, include_project_constraints=False)
        assert "methodology" in str(paths[0])

    def test_project_is_last_scope(self, tmp_path):
        paths = build_six_level_paths(tmp_path, include_project_constraints=False)
        assert "project" in str(paths[-1])

    def test_project_constraints_appended_last(self, tmp_path):
        paths = build_six_level_paths(tmp_path)
        assert "project_constraints.yml" in str(paths[-1])

    def test_custom_filename(self, tmp_path):
        paths = build_six_level_paths(tmp_path, filename="override.yml", include_project_constraints=False)
        assert all("override.yml" in str(p) for p in paths)

    def test_paths_inside_workspace_context(self, tmp_path):
        paths = build_six_level_paths(tmp_path, include_project_constraints=False)
        for p in paths:
            assert str(p).startswith(str(tmp_path))
            assert ".ai-workspace/context" in str(p)


# ── load_six_level_context ────────────────────────────────────────────────


class TestLoadSixLevelContext:
    """T-COMPLY-002: 6-level context loads + merges correctly."""

    def _write_level(self, base: pathlib.Path, level: str, data: dict) -> None:
        scope_dir = base / ".ai-workspace" / "context" / level
        scope_dir.mkdir(parents=True, exist_ok=True)
        (scope_dir / "context.yml").write_text(__import__("yaml").dump(data))

    def test_returns_empty_dict_when_no_files_exist(self, tmp_path):
        result = load_six_level_context(tmp_path)
        assert result == {}

    def test_methodology_is_lowest_priority(self, tmp_path):
        self._write_level(tmp_path, "methodology", {"threshold": 0.50})
        self._write_level(tmp_path, "project", {"threshold": 0.95})
        result = load_six_level_context(tmp_path)
        assert result["threshold"] == 0.95

    def test_project_overrides_all_earlier_levels(self, tmp_path):
        for level in ("methodology", "org", "policy", "domain", "prior"):
            self._write_level(tmp_path, level, {"owner": level})
        self._write_level(tmp_path, "project", {"owner": "project"})
        result = load_six_level_context(tmp_path)
        assert result["owner"] == "project"

    def test_deep_merge_across_six_levels(self, tmp_path):
        self._write_level(tmp_path, "methodology", {"tools": {"runner": {"command": "pytest"}}})
        self._write_level(tmp_path, "org", {"tools": {"linter": {"command": "ruff"}}})
        self._write_level(tmp_path, "project", {"tools": {"runner": {"args": "-v"}}})
        result = load_six_level_context(tmp_path)
        assert result["tools"]["runner"]["command"] == "pytest"   # from methodology
        assert result["tools"]["runner"]["args"] == "-v"          # from project
        assert result["tools"]["linter"]["command"] == "ruff"     # from org

    def test_missing_levels_silently_skipped(self, tmp_path):
        # Only write methodology and project
        self._write_level(tmp_path, "methodology", {"base": True})
        self._write_level(tmp_path, "project", {"local": True})
        result = load_six_level_context(tmp_path)
        assert result["base"] is True
        assert result["local"] is True

    def test_prior_level_overrides_domain(self, tmp_path):
        self._write_level(tmp_path, "domain", {"db_version": "pg14"})
        self._write_level(tmp_path, "prior", {"db_version": "pg15"})
        result = load_six_level_context(tmp_path)
        assert result["db_version"] == "pg15"

    def test_project_constraints_yml_overrides_project_scope(self, tmp_path):
        """Legacy project_constraints.yml is the final override layer."""
        self._write_level(tmp_path, "project", {"coverage": 0.80})
        constraints_path = tmp_path / ".ai-workspace" / "context" / "project_constraints.yml"
        constraints_path.write_text(__import__("yaml").dump({"coverage": 0.95}))
        result = load_six_level_context(tmp_path)
        assert result["coverage"] == 0.95

    def test_old_four_level_comment_replaced(self):
        """T-COMPLY-002: verify the old 4-level hierarchy comment is gone from config_loader."""
        import pathlib
        src = pathlib.Path(__file__).parent.parent / "code" / "genesis" / "config_loader.py"
        text = src.read_text()
        assert "global → organisation → team → project" not in text, (
            "Old 4-level hierarchy comment must be replaced with 6-level (ADR-S-022)"
        )


# ── generate_context_manifest ─────────────────────────────────────────────


class TestGenerateContextManifest:
    """T-COMPLY-002: SHA-256 manifest for static lineage reproducibility."""

    def _write_file(self, path: pathlib.Path, content: str) -> pathlib.Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def test_present_files_have_sha256(self, tmp_path):
        f = self._write_file(tmp_path / "a.yml", "key: value\n")
        manifest = generate_context_manifest([f])
        assert str(f) in manifest["files"]
        assert manifest["files"][str(f)] is not None
        assert len(manifest["files"][str(f)]) == 64  # hex sha256

    def test_missing_files_have_null_hash(self, tmp_path):
        missing = tmp_path / "nonexistent.yml"
        manifest = generate_context_manifest([missing])
        assert manifest["files"][str(missing)] is None

    def test_aggregate_hash_is_deterministic(self, tmp_path):
        f = self._write_file(tmp_path / "ctx.yml", "x: 1\n")
        m1 = generate_context_manifest([f])
        m2 = generate_context_manifest([f])
        assert m1["aggregate_hash"] == m2["aggregate_hash"]

    def test_aggregate_hash_changes_on_content_change(self, tmp_path):
        f = tmp_path / "ctx.yml"
        f.write_text("x: 1\n")
        m1 = generate_context_manifest([f])
        f.write_text("x: 2\n")
        m2 = generate_context_manifest([f])
        assert m1["aggregate_hash"] != m2["aggregate_hash"]

    def test_aggregate_hash_prefixed_sha256(self, tmp_path):
        f = self._write_file(tmp_path / "ctx.yml", "y: 42\n")
        manifest = generate_context_manifest([f])
        assert manifest["aggregate_hash"].startswith("sha256:")

    def test_file_count_includes_missing(self, tmp_path):
        present = self._write_file(tmp_path / "a.yml", "a: 1\n")
        missing = tmp_path / "b.yml"
        manifest = generate_context_manifest([present, missing])
        assert manifest["file_count"] == 2

    def test_present_count_excludes_missing(self, tmp_path):
        present = self._write_file(tmp_path / "a.yml", "a: 1\n")
        missing = tmp_path / "b.yml"
        manifest = generate_context_manifest([present, missing])
        assert manifest["present_count"] == 1

    def test_empty_list_produces_zero_counts(self):
        manifest = generate_context_manifest([])
        assert manifest["file_count"] == 0
        assert manifest["present_count"] == 0
        assert "sha256:" in manifest["aggregate_hash"]


# ── write_context_manifest ────────────────────────────────────────────────


class TestWriteContextManifest:

    def test_writes_yaml_file(self, tmp_path):
        manifest = {"files": {}, "aggregate_hash": "sha256:abc", "file_count": 0, "present_count": 0}
        out = tmp_path / "context_manifest.yml"
        write_context_manifest(manifest, out)
        assert out.exists()

    def test_creates_parent_dirs(self, tmp_path):
        manifest = {"files": {}, "aggregate_hash": "sha256:abc", "file_count": 0, "present_count": 0}
        out = tmp_path / "deep" / "nested" / "context_manifest.yml"
        write_context_manifest(manifest, out)
        assert out.exists()

    def test_written_content_is_readable_yaml(self, tmp_path):
        import yaml as _yaml
        manifest = {"aggregate_hash": "sha256:xyz", "file_count": 1, "present_count": 1, "files": {"f.yml": "abc"}}
        out = tmp_path / "manifest.yml"
        write_context_manifest(manifest, out)
        loaded = _yaml.safe_load(out.read_text())
        assert loaded["aggregate_hash"] == "sha256:xyz"
        assert loaded["file_count"] == 1


# ── load_context_sources ──────────────────────────────────────────────────


class TestLoadContextSources:

    def test_returns_empty_list_when_no_context_sources(self, tmp_path):
        vector = {"feature": "REQ-F-001"}
        assert load_context_sources(vector, tmp_path) == []

    def test_resolves_relative_paths(self, tmp_path):
        vector = {"context_sources": ["context/domain/context.yml"]}
        paths = load_context_sources(vector, tmp_path)
        assert len(paths) == 1
        assert paths[0] == tmp_path / "context/domain/context.yml"

    def test_multiple_sources(self, tmp_path):
        vector = {"context_sources": ["a.yml", "b/c.yml"]}
        paths = load_context_sources(vector, tmp_path)
        assert len(paths) == 2

    def test_non_string_entries_skipped(self, tmp_path):
        vector = {"context_sources": ["valid.yml", 42, None]}
        paths = load_context_sources(vector, tmp_path)
        assert len(paths) == 1

    def test_returned_paths_are_absolute(self, tmp_path):
        vector = {"context_sources": ["ctx/domain.yml"]}
        paths = load_context_sources(vector, tmp_path)
        assert paths[0].is_absolute()
