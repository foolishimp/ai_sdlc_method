# Implements: GENESIS_ENGINE_SPEC §5 (Configuration)
"""YAML loading and $variable resolution."""

import pathlib
import re
from typing import Optional

import yaml

from .models import ResolvedCheck

_VAR_PATTERN = re.compile(r"\$(\w+(?:\.\w+)*)")


def load_yaml(path: pathlib.Path) -> dict:
    """Load a YAML file, merging multiple documents into one dict."""
    with open(path) as f:
        docs = list(yaml.safe_load_all(f))
    result = {}
    for doc in docs:
        if doc is not None:
            result.update(doc)
    return result


def resolve_variable(ref: str, constraints: dict) -> Optional[str]:
    """Resolve a single $variable reference against constraints."""
    parts = ref.split(".")
    current = constraints
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    if current is None:
        return None
    return str(current)


def resolve_variables(text: str, constraints: dict) -> tuple[str, list[str]]:
    """Resolve all $variable references in a text string."""
    unresolved = []

    def _replace(match: re.Match) -> str:
        ref = match.group(1)
        value = resolve_variable(ref, constraints)
        if value is None:
            unresolved.append(ref)
            return match.group(0)
        return value

    resolved = _VAR_PATTERN.sub(_replace, text)
    return resolved, unresolved


def resolve_checklist(edge_config: dict, constraints: dict) -> list[ResolvedCheck]:
    """Resolve all $variables in an edge config's checklist."""
    checklist = edge_config.get("checklist", [])
    results = []

    for entry in checklist:
        all_unresolved = []

        criterion = entry.get("criterion", "")
        if isinstance(criterion, str):
            criterion, unr = resolve_variables(criterion, constraints)
            all_unresolved.extend(unr)

        command = entry.get("command")
        if command and isinstance(command, str):
            command, unr = resolve_variables(command, constraints)
            all_unresolved.extend(unr)

        pass_criterion = entry.get("pass_criterion")
        if pass_criterion and isinstance(pass_criterion, str):
            pass_criterion, unr = resolve_variables(pass_criterion, constraints)
            all_unresolved.extend(unr)

        required_raw = entry.get("required", True)
        if isinstance(required_raw, str):
            resolved_req, unr = resolve_variables(required_raw, constraints)
            all_unresolved.extend(unr)
            required = resolved_req.lower() not in ("false", "0", "no", "none")
        else:
            required = bool(required_raw)

        results.append(
            ResolvedCheck(
                name=entry.get("name", ""),
                check_type=entry.get("type", "agent"),
                functional_unit=entry.get("functional_unit", "evaluate"),
                criterion=criterion,
                source=entry.get("source", "default"),
                required=required,
                command=command,
                pass_criterion=pass_criterion,
                unresolved=all_unresolved,
            )
        )

    return results
