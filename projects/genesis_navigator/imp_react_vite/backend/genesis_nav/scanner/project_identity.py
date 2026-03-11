"""Project identity derivation: project_id computation and deduplication.

A project_id is the directory name. When two projects share the same directory
name, the id is disambiguated using the relative path from the scan root.
"""

# Implements: REQ-F-NAV-001
# Implements: REQ-BR-001
# Implements: REQ-NFR-ARCH-002

from __future__ import annotations

from pathlib import Path


def derive_project_id(project_path: Path, root: Path, seen_names: set[str]) -> str:
    """Return a stable, unique project_id for a discovered Genesis project.

    The default id is the directory name. If another project with the same
    name has already been registered (tracked via ``seen_names``), the id is
    disambiguated by prepending the relative path from ``root``.

    Args:
        project_path: Absolute path to the project directory.
        root: The root directory supplied to the scanner.
        seen_names: Mutable set of project_ids already assigned in this scan.
            Updated in-place with the chosen id.

    Returns:
        A unique string project_id for ``project_path``.
    """
    name = project_path.name
    if name not in seen_names:
        seen_names.add(name)
        return name

    # Disambiguate: use relative path from root, e.g. "subdir/foo"
    try:
        rel = project_path.relative_to(root)
    except ValueError:
        rel = project_path

    disambiguated = str(rel)
    seen_names.add(disambiguated)
    return disambiguated
