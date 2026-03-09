# Implements: REQ-ITER-003 (Functor Encoding Tracking), REQ-CTX-001 (Context as Constraint Surface), REQ-CTX-002 (Context Hierarchy)
# Implements: REQ-GRAPH-001 (Asset Type Registry), REQ-GRAPH-002 (Admissible Transitions), REQ-GRAPH-003 (Asset as Markov Object)
# Implements: REQ-EDGE-001 (TDD at Code↔Tests Edges), REQ-EDGE-002 (BDD at Design→Test Edges), REQ-EDGE-003 (ADRs at Requirements→Design Edge)
# Implements: REQ-TOOL-008 (Context Snapshot), REQ-TOOL-013 (Output Directory Binding)
# Implements: REQ-UX-007 (Edge Zoom Management)
# Implements: REQ-F-NAMEDCOMP-001 (Named Composition Library — load_named_compositions, resolve_composition, validate_feature_vector)
"""YAML loading, $variable resolution, and context hierarchy composition for edge configs and project constraints."""

import pathlib
import re
from typing import Optional, Any

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
# CONTEXT HIERARCHY — REQ-CTX-002 (ADR-S-022)
# ═══════════════════════════════════════════════════════════════════════
# 6-level lineage DAG (lowest → highest priority):
#   methodology → org → policy → domain → prior → project
# Later contexts override earlier; objects are deep-merged, scalars replaced.
# See ADR-S-022 §2 for canonical sequence definition.


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

    The canonical 6-level order is: methodology → org → policy → domain → prior → project
    Use :func:`build_six_level_paths` to build the path list for a workspace.

    Args:
        context_files: Ordered list of paths (lowest → highest priority)
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


# Canonical 6-level hierarchy names (ADR-S-022 §2)
SIX_LEVEL_HIERARCHY: tuple[str, ...] = (
    "methodology",
    "org",
    "policy",
    "domain",
    "prior",
    "project",
)


def build_six_level_paths(
    workspace_root: pathlib.Path,
    *,
    context_dir: str = ".ai-workspace/context",
    filename: str = "context.yml",
    include_project_constraints: bool = True,
) -> list[pathlib.Path]:
    """Build the canonical 6-level path list for a workspace.

    Returns paths in merge order (methodology=lowest, project=highest):
        {workspace_root}/{context_dir}/{level}/{filename}

    If ``include_project_constraints=True`` (default), the legacy
    ``project_constraints.yml`` is appended as a final override — this
    ensures backwards compatibility with existing workspaces.

    Args:
        workspace_root: Project root directory.
        context_dir: Relative path to the context directory (default: ``.ai-workspace/context``).
        filename: Context file name within each scope directory (default: ``context.yml``).
        include_project_constraints: Whether to append ``project_constraints.yml`` as top-level override.

    Returns:
        Ordered list of paths — methodology first, project last.
    """
    base = workspace_root / context_dir
    paths = [base / level / filename for level in SIX_LEVEL_HIERARCHY]
    if include_project_constraints:
        paths.append(base / "project_constraints.yml")
    return paths


def load_six_level_context(
    workspace_root: pathlib.Path,
    *,
    context_dir: str = ".ai-workspace/context",
    filename: str = "context.yml",
    include_project_constraints: bool = True,
    stop_on_missing: bool = False,
) -> dict:
    """Load and merge the 6-level context hierarchy for a workspace.

    Convenience wrapper around :func:`build_six_level_paths` +
    :func:`load_context_hierarchy`.  All 6 scope directories are probed;
    missing files are silently skipped (override ``stop_on_missing`` to change).

    Returns:
        Deep-merged context dict (methodology=lowest priority, project=highest).
    """
    paths = build_six_level_paths(
        workspace_root,
        context_dir=context_dir,
        filename=filename,
        include_project_constraints=include_project_constraints,
    )
    return load_context_hierarchy(paths, stop_on_missing=stop_on_missing)


# ═══════════════════════════════════════════════════════════════════════
# CONTEXT MANIFEST — ADR-S-022 §2 (Reproducibility / Static Lineage)
# ═══════════════════════════════════════════════════════════════════════

import hashlib


def _sha256_file(path: pathlib.Path) -> str:
    """Return the hex SHA-256 digest of a file's contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_context_manifest(
    context_files: list[pathlib.Path],
) -> dict[str, Any]:
    """Generate a context manifest for reproducibility (ADR-S-022 §2).

    Scans the provided paths, hashes each existing file, then computes an
    aggregate hash over the sorted ``{path: sha256}`` mapping.

    Args:
        context_files: The context paths that were (or should be) loaded.
            Missing files are recorded as ``null`` hash.

    Returns:
        Dict with keys:
        - ``files``: ``{relative_or_absolute_str: sha256_hex | null}``
        - ``aggregate_hash``: sha256 of sorted ``path:hash`` pairs (present files only)
        - ``file_count``: total paths in the manifest
        - ``present_count``: number of files actually found
    """
    file_entries: dict[str, Optional[str]] = {}
    for path in sorted(context_files, key=str):
        if path.exists():
            file_entries[str(path)] = _sha256_file(path)
        else:
            file_entries[str(path)] = None

    # Aggregate hash: sha256 of all present entries joined as "path:hash\n"
    present_pairs = sorted(
        f"{p}:{h}" for p, h in file_entries.items() if h is not None
    )
    agg = hashlib.sha256("\n".join(present_pairs).encode()).hexdigest()

    return {
        "files": file_entries,
        "aggregate_hash": f"sha256:{agg}",
        "file_count": len(file_entries),
        "present_count": sum(1 for h in file_entries.values() if h is not None),
    }


def write_context_manifest(
    manifest: dict[str, Any],
    output_path: pathlib.Path,
) -> None:
    """Write a context manifest dict to a YAML file.

    Creates parent directories if they do not exist.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=True)


def load_context_sources(
    feature_vector: dict[str, Any],
    workspace_root: pathlib.Path,
) -> list[pathlib.Path]:
    """Resolve additional context paths declared in a feature vector's ``context_sources`` field.

    The ``context_sources`` field is a list of relative paths (relative to
    ``workspace_root``) or scope references like ``"context/domain/context.yml"``.
    Unresolvable entries are silently skipped.

    Returns:
        List of resolved absolute paths (existing or not — caller decides how to handle missing).
    """
    sources = feature_vector.get("context_sources", [])
    if not sources:
        return []
    resolved = []
    for src in sources:
        if isinstance(src, str):
            p = workspace_root / src
            resolved.append(p)
    return resolved


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


# ═══════════════════════════════════════════════════════════════════════
# NAMED COMPOSITION LIBRARY — REQ-F-NAMEDCOMP-001
# ═══════════════════════════════════════════════════════════════════════
# Implements ADR-S-026: typed composition expressions in intent_raised events.

# Sentinel for a gap_type with no dispatch entry
_NO_DISPATCH_ENTRY = "no_dispatch_entry"

# Default intent vector envelope fields (ADR-S-026 §4.2–4.5)
_INTENT_VECTOR_DEFAULTS: dict[str, Any] = {
    "source_kind": "parent_spawn",
    "trigger_event": None,
    "target_asset_type": None,
    "produced_asset_ref": None,
    "disposition": None,
    "disposition_rationale": None,
}


def load_named_compositions(
    plugin_root: pathlib.Path,
    workspace_root: Optional[pathlib.Path] = None,
) -> dict:
    """Load the named composition library, merging library and project-local entries.

    Library file: ``{plugin_root}/config/named_compositions.yml``
    Project-local directory: ``{workspace_root}/.ai-workspace/named_compositions/``

    Project-local entries shadow library entries by ``{name, version}`` key.
    Returns the merged registry dict with ``compositions`` list and ``gap_type_dispatch`` map.

    Emits: named_compositions_loaded (caller's responsibility — this is a pure loader).
    """
    library_path = plugin_root / "config" / "named_compositions.yml"
    library: dict = {}
    if library_path.exists():
        library = load_yaml(library_path)

    # Start with library compositions indexed by (name, version)
    comp_index: dict[tuple[str, str], dict] = {}
    for comp in library.get("compositions", []):
        key = (comp.get("name", ""), comp.get("version", "v1"))
        comp_index[key] = comp

    local_count = 0
    # Merge project-local overrides
    if workspace_root is not None:
        local_dir = workspace_root / ".ai-workspace" / "named_compositions"
        if local_dir.is_dir():
            for local_file in sorted(local_dir.glob("*.yml")):
                local_data = load_yaml(local_file)
                for comp in local_data.get("compositions", local_data.get("entries", [])):
                    key = (comp.get("name", ""), comp.get("version", "v1"))
                    comp_index[key] = comp  # shadow library entry
                    local_count += 1

    merged_compositions = list(comp_index.values())

    # Merge gap_type_dispatch: project-local entries shadow library entries by gap_type key
    merged_dispatch: dict[str, dict] = dict(library.get("gap_type_dispatch", {}))
    if workspace_root is not None:
        local_dispatch_file = workspace_root / ".ai-workspace" / "named_compositions" / "gap_type_dispatch.yml"
        if local_dispatch_file.exists():
            local_dispatch = load_yaml(local_dispatch_file)
            merged_dispatch.update(local_dispatch.get("gap_type_dispatch", {}))

    return {
        "version": library.get("version", "1.0"),
        "scope": library.get("scope", "library"),
        "compositions": merged_compositions,
        "gap_type_dispatch": merged_dispatch,
        "_library_count": len(list(library.get("compositions", []))),
        "_project_local_count": local_count,
    }


def resolve_composition(
    gap_type: str,
    registry: dict,
    extra_bindings: Optional[dict] = None,
) -> tuple[Optional[dict], str]:
    """Resolve a gap_type to a named composition expression.

    Uses the ``gap_type_dispatch`` table from the registry.
    Caller bindings (``extra_bindings``) merge over dispatch default_bindings.

    Returns:
        (composition_dict, resolution_status) where resolution_status is one of:
        - "resolved" — dispatch entry found, composition expression returned
        - "unresolvable" — entry found but macro not in compositions list
        - "no_dispatch_entry" — gap_type not in dispatch table
    """
    dispatch = registry.get("gap_type_dispatch", {})
    if gap_type not in dispatch:
        return None, _NO_DISPATCH_ENTRY

    entry = dispatch[gap_type]
    macro_name = entry.get("macro", "")
    version = entry.get("version", "v1")

    # Check macro exists in compositions list
    compositions = registry.get("compositions", [])
    comp = next(
        (c for c in compositions if c.get("name") == macro_name and c.get("version") == version),
        None,
    )
    if comp is None:
        # Entry in dispatch table but macro not defined (e.g. EVOLVE, CONSENSUS placeholders)
        bindings = dict(entry.get("default_bindings", {}))
        if extra_bindings:
            bindings.update(extra_bindings)
        return {
            "macro": macro_name,
            "version": version,
            "bindings": bindings,
        }, "unresolvable"

    # Build composition expression
    bindings = dict(entry.get("default_bindings", {}))
    if extra_bindings:
        bindings.update(extra_bindings)

    return {
        "macro": macro_name,
        "version": version,
        "bindings": bindings,
    }, "resolved"


def validate_feature_vector(vector: dict) -> tuple[dict, list[str]]:
    """Apply intent vector envelope defaults and validate convergence consistency.

    Mutates a copy of ``vector`` to add missing optional fields (ADR-S-026 §4.2–4.5).
    Returns ``(validated_vector, list_of_warnings)``.

    Warnings (non-blocking):
    - Convergence claimed without produced_asset_ref (traceability chain broken)
    - Non-null disposition without disposition_rationale
    - source_kind not in allowed values
    """
    result = dict(vector)
    warnings: list[str] = []

    # Apply defaults for missing intent vector envelope fields
    for field, default in _INTENT_VECTOR_DEFAULTS.items():
        if field not in result:
            result[field] = default

    # Validate convergence consistency
    status = result.get("status", "")
    produced = result.get("produced_asset_ref")
    if status == "converged" and produced is None:
        feature_id = result.get("feature", "unknown")
        warnings.append(
            f"{feature_id}: status=converged but produced_asset_ref is null — traceability chain broken"
        )

    # Validate disposition consistency
    disposition = result.get("disposition")
    rationale = result.get("disposition_rationale")
    if disposition is not None and disposition not in ("converged", None) and not rationale:
        feature_id = result.get("feature", "unknown")
        warnings.append(
            f"{feature_id}: disposition={disposition!r} requires disposition_rationale"
        )

    # Validate source_kind values
    allowed_source_kinds = {"abiogenesis", "parent_spawn", "gap_observation"}
    source_kind = result.get("source_kind", "parent_spawn")
    if source_kind not in allowed_source_kinds:
        feature_id = result.get("feature", "unknown")
        warnings.append(
            f"{feature_id}: source_kind={source_kind!r} not in {sorted(allowed_source_kinds)}"
        )

    return result, warnings


def compute_project_convergence_state(vectors: list[dict]) -> dict:
    """Compute the project convergence state from a list of feature vectors.

    Implements NC-004 three-state algorithm (ADR-S-026 §4.5, gen-status §Project Convergence State).

    Returns a dict with:
    - ``state``: "ITERATING" | "QUIESCENT" | "CONVERGED" | "BOUNDED"
    - ``iterating_count``: int
    - ``required_vectors``: list of vectors not dispositioned as blocked_deferred or abandoned
    - ``converged_count``: int (within required_vectors)
    - ``blocked_no_disposition``: int
    - ``blocked_with_disposition``: int
    """
    active_statuses = {"iterating", "in_progress"}
    excluded_dispositions = {"blocked_deferred", "abandoned"}

    iterating_count = sum(1 for v in vectors if v.get("status") in active_statuses)
    required_vectors = [v for v in vectors if v.get("disposition") not in excluded_dispositions]
    converged_count = sum(1 for v in required_vectors if v.get("status") == "converged")
    blocked_no_disp = sum(
        1 for v in vectors
        if v.get("status") == "blocked" and v.get("disposition") is None
    )
    blocked_with_disp = sum(
        1 for v in vectors
        if v.get("status") == "blocked" and v.get("disposition") is not None
    )

    if iterating_count > 0:
        state = "ITERATING"
    elif converged_count == len(required_vectors):
        state = "CONVERGED"
    elif blocked_no_disp > 0:
        state = "QUIESCENT"
    else:
        state = "BOUNDED"

    return {
        "state": state,
        "iterating_count": iterating_count,
        "required_vectors": required_vectors,
        "converged_count": converged_count,
        "blocked_no_disposition": blocked_no_disp,
        "blocked_with_disposition": blocked_with_disp,
        "total_vectors": len(vectors),
        "total_required": len(required_vectors),
    }
