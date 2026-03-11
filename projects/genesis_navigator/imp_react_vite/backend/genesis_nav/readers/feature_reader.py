"""Reader for Genesis workspace feature vectors.

Reads all ``.yaml``/``.yml`` files from the ``active`` and ``completed``
feature directories inside a workspace.  Malformed YAML files are included
in the result with ``status: "error"`` so callers can still reason about the
full feature set.  All operations are read-only (REQ-NFR-ARCH-002).
"""

# Implements: REQ-F-STAT-001
# Implements: REQ-F-STAT-003
# Implements: REQ-NFR-ARCH-002

from __future__ import annotations

import os
from pathlib import Path

import yaml

_AI_WORKSPACE = ".ai-workspace"
_ACTIVE_REL = f"{_AI_WORKSPACE}/features/active"
_COMPLETED_REL = f"{_AI_WORKSPACE}/features/completed"


def read_features(workspace_path: Path) -> list[dict]:
    """Read all feature vectors from the workspace.

    Scans ``.ai-workspace/features/active/`` and
    ``.ai-workspace/features/completed/`` (non-recursively) for ``.yaml``
    and ``.yml`` files.  Each file is parsed as YAML.  Files that cannot be
    parsed are represented as::

        {"feature_id": <filename-without-extension>, "status": "error",
         "error": <str>}

    Args:
        workspace_path: Absolute path to the Genesis project root.

    Returns:
        List of feature dicts in directory-scan order (active first, then
        completed).  Empty list if neither directory exists.
    """
    features: list[dict] = []
    for rel in (_ACTIVE_REL, _COMPLETED_REL):
        directory = workspace_path / rel
        if not directory.is_dir():
            continue
        try:
            entries = sorted(os.scandir(directory), key=lambda e: e.name)
        except PermissionError:
            continue
        for entry in entries:
            if not entry.is_file():
                continue
            if not entry.name.endswith((".yml", ".yaml")):
                continue
            stem = Path(entry.name).stem
            try:
                with open(entry.path, encoding="utf-8") as fh:
                    data = yaml.safe_load(fh)
                if not isinstance(data, dict):
                    data = {}
                # Unwrap nested `feature:` block (canonical Genesis YAML format)
                if "feature" in data and isinstance(data["feature"], dict):
                    inner = dict(data["feature"])
                    # Merge remaining top-level keys (trajectory, constraints, etc.)
                    for k, v in data.items():
                        if k != "feature":
                            inner.setdefault(k, v)
                    data = inner
                # Normalise id → feature_id
                if "feature_id" not in data:
                    data["feature_id"] = data.pop("id", stem)
                features.append(data)
            except Exception as exc:  # noqa: BLE001
                features.append(
                    {
                        "feature_id": stem,
                        "status": "error",
                        "error": str(exc),
                    }
                )
    return features
