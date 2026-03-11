"""Gap Analysis Engine — traceability layer scanner for Genesis projects.

Computes three-layer gap coverage between spec REQ keys and their annotations
in code, tests, and telemetry.  All operations are pure read-only
(REQ-NFR-ARCH-002).
"""

# Implements: REQ-F-GAP-001
# Implements: REQ-F-GAP-002
# Implements: REQ-F-GAP-003
# Implements: REQ-F-GAP-004
# Implements: REQ-F-API-003
# Implements: REQ-NFR-ARCH-002

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_REQ_KEY_RE = re.compile(r"REQ-[A-Z][A-Z-]*[A-Z]-\d+")
_CODE_TAG_RE = re.compile(r"#\s*Implements:\s*(REQ-[A-Z][A-Z-]*[A-Z]-\d+)")
_TEST_TAG_RE = re.compile(r"#\s*Validates:\s*(REQ-[A-Z][A-Z-]*[A-Z]-\d+)")
_TELEM_TAG_RE = re.compile(r'req=["\'](REQ-[A-Z][A-Z-]*[A-Z]-\d+)')

# ---------------------------------------------------------------------------
# Directory pruning constants
# ---------------------------------------------------------------------------

_PRUNE: frozenset[str] = frozenset({".git", "node_modules", "__pycache__", ".venv"})
_EXCLUDE_CODE: frozenset[str] = _PRUNE | frozenset({"tests", "test"})
_TEXT_SUFFIXES: frozenset[str] = frozenset(
    {".py", ".md", ".yml", ".yaml", ".txt", ".js", ".ts", ".jsx", ".tsx", ".json"}
)
_TEST_DIR_NAMES: frozenset[str] = frozenset({"tests", "test"})


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _is_text_file(path: Path) -> bool:
    return path.suffix in _TEXT_SUFFIXES


def _read_text(path: Path) -> str:
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def _walk_files(root: Path, prune: frozenset[str]) -> list[Path]:
    """Walk *root* recursively, pruning *prune* directories, returning all files."""
    results: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in prune]
        current = Path(dirpath)
        for fname in filenames:
            results.append(current / fname)
    return results


# ---------------------------------------------------------------------------
# Public extraction functions
# ---------------------------------------------------------------------------


def extract_spec_req_keys(project_path: Path) -> set[str]:
    """Return all REQ-* keys defined in specification/requirements/REQUIREMENTS.md.

    Returns an empty set if the file does not exist.

    Args:
        project_path: Root of the Genesis project.

    Returns:
        Set of REQ key strings found in the requirements document.
    """
    req_file = project_path / "specification" / "requirements" / "REQUIREMENTS.md"
    if not req_file.exists():
        return set()
    return set(_REQ_KEY_RE.findall(_read_text(req_file)))


def extract_code_req_keys(project_path: Path) -> dict[str, list[str]]:
    """Return a mapping of REQ key → file paths where ``# Implements: REQ-*`` appears.

    Source files are all files under *project_path* except ``tests/``, ``.git/``,
    ``node_modules/``, and other pruned directories.

    Args:
        project_path: Root of the Genesis project.

    Returns:
        Dict mapping each found REQ key to a list of relative file paths.
    """
    result: dict[str, list[str]] = {}
    for fpath in _walk_files(project_path, _EXCLUDE_CODE):
        if not _is_text_file(fpath):
            continue
        text = _read_text(fpath)
        for match in _CODE_TAG_RE.finditer(text):
            key = match.group(1)
            rel = str(fpath.relative_to(project_path))
            result.setdefault(key, [])
            if rel not in result[key]:
                result[key].append(rel)
    return result


def extract_test_req_keys(project_path: Path) -> dict[str, list[str]]:
    """Return a mapping of REQ key → file paths where ``# Validates: REQ-*`` appears.

    Only files inside ``tests/`` or ``test/`` directories, or files whose name
    starts with ``test_`` or ends with ``_test.py``, are scanned.

    Args:
        project_path: Root of the Genesis project.

    Returns:
        Dict mapping each found REQ key to a list of relative file paths.
    """
    result: dict[str, list[str]] = {}
    for fpath in _walk_files(project_path, _PRUNE):
        if not _is_text_file(fpath):
            continue
        # Determine whether this looks like a test file
        parts = set(fpath.parts)
        in_test_dir = bool(parts & _TEST_DIR_NAMES)
        name = fpath.name
        is_test_file = in_test_dir or name.startswith("test_") or name.endswith("_test.py")
        if not is_test_file:
            continue
        text = _read_text(fpath)
        for match in _TEST_TAG_RE.finditer(text):
            key = match.group(1)
            rel = str(fpath.relative_to(project_path))
            result.setdefault(key, [])
            if rel not in result[key]:
                result[key].append(rel)
    return result


def extract_telemetry_req_keys(project_path: Path) -> dict[str, list[str]]:
    """Return a mapping of REQ key → file paths where ``req="REQ-*"`` appears.

    All text files under *project_path* are scanned (standard prune dirs excluded).

    Args:
        project_path: Root of the Genesis project.

    Returns:
        Dict mapping each found REQ key to a list of relative file paths.
    """
    result: dict[str, list[str]] = {}
    for fpath in _walk_files(project_path, _PRUNE):
        if not _is_text_file(fpath):
            continue
        text = _read_text(fpath)
        for match in _TELEM_TAG_RE.finditer(text):
            key = match.group(1)
            rel = str(fpath.relative_to(project_path))
            result.setdefault(key, [])
            if rel not in result[key]:
                result[key].append(rel)
    return result


# ---------------------------------------------------------------------------
# Gap computation
# ---------------------------------------------------------------------------


def compute_gap_layer(
    spec_keys: set[str],
    tagged_keys: dict[str, list[str]],
    gap_type: str,
) -> dict:
    """Compute coverage and gaps for one traceability layer.

    Args:
        spec_keys: All REQ keys defined in the specification.
        tagged_keys: REQ keys found in the relevant source artifacts, mapped to file paths.
        gap_type: Label for gaps in this layer (e.g. ``"CODE_GAP"``).

    Returns:
        Dict with keys ``gap_count`` (int), ``coverage_pct`` (float), ``gaps`` (list).
    """
    covered = spec_keys & set(tagged_keys.keys())
    uncovered = spec_keys - covered

    gaps = [
        {
            "req_key": key,
            "gap_type": gap_type,
            "files": [],
            "suggested_command": None,
        }
        for key in sorted(uncovered)
    ]

    coverage_pct = (len(covered) / len(spec_keys) * 100.0) if spec_keys else 100.0
    return {
        "gap_count": len(gaps),
        "coverage_pct": round(coverage_pct, 1),
        "gaps": gaps,
    }


def compute_health_signal(layer1_gap_count: int, layer2_gap_count: int) -> str:
    """Derive a traffic-light health signal from layer 1 and layer 2 gap counts.

    Args:
        layer1_gap_count: Number of uncovered REQ keys in layer 1 (code tags).
        layer2_gap_count: Number of uncovered REQ keys in layer 2 (test tags).

    Returns:
        ``"GREEN"`` (0 combined gaps), ``"AMBER"`` (1–5), or ``"RED"`` (>5).
    """
    total = layer1_gap_count + layer2_gap_count
    if total == 0:
        return "GREEN"
    if total <= 5:
        return "AMBER"
    return "RED"


def analyze_gaps(project_path: Path) -> dict:
    """Run the full three-layer gap analysis for a Genesis project.

    Args:
        project_path: Root of the Genesis project directory.

    Returns:
        Dict conforming to the :class:`~genesis_nav.models.schemas.GapReport` schema.
    """
    spec_keys = extract_spec_req_keys(project_path)
    code_keys = extract_code_req_keys(project_path)
    test_keys = extract_test_req_keys(project_path)
    telem_keys = extract_telemetry_req_keys(project_path)

    layer1 = compute_gap_layer(spec_keys, code_keys, "CODE_GAP")
    layer2 = compute_gap_layer(spec_keys, test_keys, "TEST_GAP")
    layer3 = compute_gap_layer(spec_keys, telem_keys, "TELEMETRY_GAP")

    return {
        "project_id": project_path.name,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "health_signal": compute_health_signal(layer1["gap_count"], layer2["gap_count"]),
        "layer_1": layer1,
        "layer_2": layer2,
        "layer_3": layer3,
    }
