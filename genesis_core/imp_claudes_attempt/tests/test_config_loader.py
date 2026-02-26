"""Tests for genesis_engine.config_loader — YAML loading and $variable resolution."""

import yaml

from genesis_engine.config_loader import (
    load_yaml,
    resolve_checklist,
    resolve_variable,
    resolve_variables,
)


def test_load_yaml_single_doc(tmp_path):
    path = tmp_path / "test.yml"
    path.write_text("key: value\n")
    result = load_yaml(path)
    assert result == {"key": "value"}


def test_load_yaml_multi_doc(tmp_path):
    path = tmp_path / "test.yml"
    path.write_text("a: 1\n---\nb: 2\n")
    result = load_yaml(path)
    assert result == {"a": 1, "b": 2}


def test_resolve_variable_simple():
    constraints = {"project": {"name": "test"}}
    assert resolve_variable("project.name", constraints) == "test"


def test_resolve_variable_missing():
    constraints = {"project": {"name": "test"}}
    assert resolve_variable("missing.key", constraints) is None


def test_resolve_variables_replaces():
    constraints = {"test": {"command": "pytest"}}
    text = "run $test.command here"
    resolved, unresolved = resolve_variables(text, constraints)
    assert resolved == "run pytest here"
    assert unresolved == []


def test_resolve_variables_tracks_unresolved():
    text = "run $missing.cmd"
    resolved, unresolved = resolve_variables(text, {})
    assert resolved == "run $missing.cmd"
    assert unresolved == ["missing.cmd"]


def test_resolve_checklist_deterministic(tmp_path):
    edge_config = {
        "checklist": [
            {
                "name": "lint",
                "type": "deterministic",
                "criterion": "code is clean",
                "command": "$test.command",
                "required": True,
            }
        ]
    }
    constraints = {"test": {"command": "ruff check ."}}
    checks = resolve_checklist(edge_config, constraints)
    assert len(checks) == 1
    assert checks[0].command == "ruff check ."
    assert checks[0].unresolved == []


def test_resolve_checklist_unresolved_var():
    edge_config = {
        "checklist": [
            {
                "name": "test",
                "type": "deterministic",
                "criterion": "tests pass",
                "command": "$undefined.var",
                "required": True,
            }
        ]
    }
    checks = resolve_checklist(edge_config, {})
    assert len(checks) == 1
    assert checks[0].unresolved == ["undefined.var"]
