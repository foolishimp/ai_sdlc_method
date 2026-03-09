# Implements: REQ-ITER-003 (Functor Encoding Tracking), REQ-CTX-001 (Context as Constraint Surface), REQ-CTX-002 (Context Hierarchy)
# Implements: REQ-GRAPH-001 (Asset Type Registry), REQ-GRAPH-002 (Admissible Transitions), REQ-GRAPH-003 (Asset as Markov Object)
# Implements: REQ-EDGE-001 (TDD at Code↔Tests Edges), REQ-EDGE-002 (BDD at Design→Test Edges), REQ-EDGE-003 (ADRs at Requirements→Design Edge)
# Implements: REQ-TOOL-008 (Context Snapshot), REQ-TOOL-013 (Output Directory Binding)
# Implements: REQ-UX-007 (Edge Zoom Management)
"""YAML loading, $variable resolution, and context hierarchy composition for edge configs and project constraints."""

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


# ═══════════════════════════════════════════════════════════════════════
# CONTEXT HIERARCHY — REQ-CTX-002
# ═══════════════════════════════════════════════════════════════════════
# Levels: global → organisation → team → project
# Later contexts override earlier; objects are deep-merged, scalars replaced.


def deep_merge(base: dict, override: dict) -> dict:
    """Deep-merge two dicts: scalars in override replace base; nested dicts are merged recursively.

    Returns a new dict — neither input is mutated.
    """
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def merge_contexts(*contexts: dict) -> dict:
    """Merge an ordered sequence of context dicts (global → project).

    Later entries override earlier ones. Objects are deep-merged; scalars replaced.
    Returns a new merged dict.
    """
    result: dict = {}
    for ctx in contexts:
        result = deep_merge(result, ctx)
    return result


def load_context_hierarchy(
    context_files: list[pathlib.Path],
    *,
    stop_on_missing: bool = False,
) -> dict:
    """Load and merge a hierarchy of context YAML files in order.

    Files are merged left-to-right (first file = lowest priority, last = highest).
    Missing files are silently skipped unless ``stop_on_missing=True``.

    Args:
        context_files: Ordered list of paths: [global, org, team, project, ...]
        stop_on_missing: If True, raise FileNotFoundError for missing files.

    Returns:
        Deep-merged dict of all found context files.
    """
    contexts: list[dict] = []
    for path in context_files:
        if not path.exists():
            if stop_on_missing:
                raise FileNotFoundError(f"Context file not found: {path}")
            continue
        contexts.append(load_yaml(path))
    return merge_contexts(*contexts)


def resolve_variable(ref: str, constraints: dict) -> Optional[str]:
    """Resolve a single $variable reference against constraints.

    ref: dotted path without the leading $, e.g. "tools.test_runner.command"
    Returns the resolved value as a string, or None if not found.
    """
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
    """Resolve all $variable references in a text string.

    Returns (resolved_text, list_of_unresolved_refs).
    """
    unresolved = []

    def _replace(match: re.Match) -> str:
        ref = match.group(1)
        value = resolve_variable(ref, constraints)
        if value is None:
            unresolved.append(ref)
            return match.group(0)  # leave original $ref
        return value

    resolved = _VAR_PATTERN.sub(_replace, text)
    return resolved, unresolved


def resolve_checklist(edge_config: dict, constraints: dict) -> list[ResolvedCheck]:
    """Resolve all $variables in an edge config's checklist.

    Returns a list of ResolvedCheck with concrete values.
    """
    checklist = edge_config.get("checklist", [])
    results = []

    for entry in checklist:
        all_unresolved = []

        # Resolve criterion
        criterion = entry.get("criterion", "")
        if isinstance(criterion, str):
            criterion, unr = resolve_variables(criterion, constraints)
            all_unresolved.extend(unr)

        # Resolve command (deterministic only)
        command = entry.get("command")
        if command and isinstance(command, str):
            command, unr = resolve_variables(command, constraints)
            all_unresolved.extend(unr)

        # Resolve pass_criterion
        pass_criterion = entry.get("pass_criterion")
        if pass_criterion and isinstance(pass_criterion, str):
            pass_criterion, unr = resolve_variables(pass_criterion, constraints)
            all_unresolved.extend(unr)

        # Resolve required (can be a $variable string like "$tools.type_checker.required")
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
