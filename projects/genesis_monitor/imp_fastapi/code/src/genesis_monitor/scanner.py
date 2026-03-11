# Implements: REQ-F-DISC-001, REQ-F-DISC-003, REQ-F-CQRS-001, REQ-F-CQRS-002
"""Workspace discovery — scans root directories for .ai-workspace/ projects."""

import os
from pathlib import Path

PRUNE_DIRS = {".git", "node_modules", "__pycache__", ".venv", ".tox", ".mypy_cache"}


def scan_roots(roots: list[Path]) -> list[Path]:
    """Find all directories containing a .ai-workspace/ subdirectory."""
    projects: list[Path] = []

    for root in roots:
        root = root.expanduser().resolve()
        if not root.is_dir(): continue

        # Check root itself
        if (root / ".ai-workspace").is_dir():
            projects.append(root)

        for dirpath, dirnames, _filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in PRUNE_DIRS]

            if ".ai-workspace" in dirnames:
                projects.append(Path(dirpath))

    return sorted(list(set(projects)))


def build_workspace_hierarchy(paths: list[Path]) -> dict[Path, list[Path]]:
    """Build parent→direct-children map for a list of project paths.

    A path B is a direct child of A if:
    - B is a proper subdirectory of A
    - There is no other project path C that lies between A and B (i.e., no C
      such that B is a subdirectory of C and C is a subdirectory of A).

    Returns a dict mapping each path to its list of direct child paths.
    All paths in the input that have no children map to an empty list.
    """
    resolved = [p.resolve() for p in paths]
    parent_of: dict[Path, Path | None] = {p: None for p in resolved}

    for p in resolved:
        # Find the closest ancestor among all other paths
        best_ancestor: Path | None = None
        for candidate in resolved:
            if candidate == p:
                continue
            try:
                p.relative_to(candidate)  # raises if not a subpath
            except ValueError:
                continue
            # candidate is an ancestor of p; pick the deepest one
            if best_ancestor is None or len(candidate.parts) > len(best_ancestor.parts):
                best_ancestor = candidate
        parent_of[p] = best_ancestor

    children: dict[Path, list[Path]] = {p: [] for p in resolved}
    for child, parent in parent_of.items():
        if parent is not None:
            children[parent].append(child)

    return children
