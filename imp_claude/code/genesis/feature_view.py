# Implements: REQ-TOOL-009 (Feature Views)
# Implements: REQ-FEAT-001 (Feature Vector Trajectories), REQ-TOOL-005 (Test Gap Analysis)
"""Feature view — cross-artifact REQ key tracer.

Generates per-feature status reports by scanning project artifacts for
REQ key tags at each SDLC stage. Provides the Python backing for the
/gen-trace command.

Tag formats scanned:
    Spec/Design:   REQ-F-AUTH-001          (direct mention)
    Code:          # Implements: REQ-F-AUTH-001
    Tests:         # Validates: REQ-F-AUTH-001
    Telemetry:     req="REQ-F-AUTH-001"    (structured log tag)
    UAT/BDD:       @REQ-F-AUTH-001         (Gherkin tag)
    Comment/doc:   REQ-F-AUTH-001          (bare mention)

The scan is intentionally broad — any file containing the REQ key in any
context is surfaced. False positives are acceptable; false negatives are not.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ═══════════════════════════════════════════════════════════════════════
# TAG PATTERNS
# ═══════════════════════════════════════════════════════════════════════

_REQ_KEY_PATTERN = re.compile(r"\bREQ-[A-Z]+(?:-[A-Z]+)*-\d+\b")

# Stage-specific tag patterns (ordered by specificity)
_TAG_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("implements", re.compile(r"Implements:\s*REQ-[A-Z]")),
    ("validates", re.compile(r"Validates:\s*REQ-[A-Z]")),
    ("telemetry", re.compile(r'req=["\']REQ-[A-Z]')),
    ("gherkin_tag", re.compile(r"@REQ-[A-Z]")),
]

# File extensions by stage category
_STAGE_EXTENSIONS: dict[str, set[str]] = {
    "spec": {".md", ".rst", ".txt"},
    "design": {".md", ".rst", ".txt", ".yml", ".yaml"},
    "code": {".py", ".js", ".ts", ".java", ".scala", ".go", ".rs", ".rb", ".kt", ".cs"},
    "tests": {
        ".py",
        ".js",
        ".ts",
        ".java",
        ".scala",
        ".go",
        ".rs",
        ".rb",
        ".kt",
        ".feature",
        ".gherkin",
    },
    "config": {".yml", ".yaml", ".json", ".toml", ".ini"},
}

# Directory patterns that indicate stage
_STAGE_DIR_HINTS: dict[str, list[str]] = {
    "spec": ["specification", "spec", "requirements"],
    "design": ["design", "adrs", "adr"],
    "code": ["src", "lib", "app", "code"],
    "tests": ["tests", "test", "spec"],
    "telemetry": ["telemetry", "metrics", "monitoring", "observability"],
}


# ═══════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class ArtifactMatch:
    """A single file that references a REQ key."""

    path: Path  # absolute path to the file
    rel_path: str  # relative to project root
    line_numbers: list[int]  # lines where the key appears
    tag_types: list[str]  # ["implements", "validates", "bare", ...]
    stage_hint: str  # inferred stage: spec/design/code/tests/telemetry/unknown


@dataclass
class FeatureView:
    """Cross-artifact view for a single REQ key."""

    req_key: str
    matches_by_stage: dict[str, list[ArtifactMatch]] = field(default_factory=dict)
    missing_stages: list[str] = field(default_factory=list)
    coverage: int = 0  # number of stages with at least one match
    total_stages: int = 0  # number of expected stages
    coverage_pct: float = 0.0

    def summary(self) -> str:
        """One-line coverage summary."""
        stages_present = sorted(self.matches_by_stage.keys())
        missing = sorted(self.missing_stages)
        return (
            f"{self.req_key}: {self.coverage}/{self.total_stages} stages tagged "
            f"[{', '.join(stages_present)}]"
            + (f" — MISSING: {', '.join(missing)}" if missing else "")
        )


# ═══════════════════════════════════════════════════════════════════════
# SCANNING
# ═══════════════════════════════════════════════════════════════════════

# Files/dirs to skip when scanning
_SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".venv",
    "venv",
    ".ai-workspace",
    "dist",
    "build",
    ".mypy_cache",
    ".tox",
}
_SKIP_EXTENSIONS = {".pyc", ".pyo", ".class", ".so", ".dylib", ".dll", ".exe"}


def _infer_stage(path: Path, project_root: Path) -> str:
    """Infer the SDLC stage of a file from its path."""
    try:
        rel = path.relative_to(project_root)
    except ValueError:
        rel = path

    parts = [p.lower() for p in rel.parts]
    suffix = path.suffix.lower()

    # Directory-based inference (most specific)
    for stage, hints in _STAGE_DIR_HINTS.items():
        for part in parts:
            if any(h in part for h in hints):
                # Refine: if directory says "tests" but file is .feature → uat
                if stage == "tests" and suffix in {".feature", ".gherkin"}:
                    return "uat"
                return stage

    # Extension-based fallback
    if suffix in _STAGE_EXTENSIONS["code"]:
        return "code"
    if suffix in {".feature", ".gherkin"}:
        return "uat"
    if suffix in {".md", ".rst", ".txt"}:
        return "spec"

    return "unknown"


def _classify_line_tag(line: str) -> list[str]:
    """Return tag types detected in a single line."""
    tags = []
    for tag_type, pattern in _TAG_PATTERNS:
        if pattern.search(line):
            tags.append(tag_type)
    if not tags:
        tags.append("bare")
    return tags


def scan_for_req_key(
    req_key: str,
    search_root: Path,
    project_root: Optional[Path] = None,
) -> list[ArtifactMatch]:
    """Scan all files under search_root for occurrences of req_key.

    Returns a list of ArtifactMatch objects, one per matching file.
    """
    if project_root is None:
        project_root = search_root

    # Build a simple literal+word-boundary pattern for the specific key
    key_re = re.compile(r"\b" + re.escape(req_key) + r"\b")
    matches: list[ArtifactMatch] = []

    for fpath in _iter_files(search_root):
        if fpath.suffix.lower() in _SKIP_EXTENSIONS:
            continue
        try:
            text = fpath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if not key_re.search(text):
            continue

        # Collect line numbers and tag types
        line_numbers: list[int] = []
        tag_types_set: set[str] = set()
        for lineno, line in enumerate(text.splitlines(), start=1):
            if key_re.search(line):
                line_numbers.append(lineno)
                for t in _classify_line_tag(line):
                    tag_types_set.add(t)

        if not line_numbers:
            continue

        try:
            rel = str(fpath.relative_to(project_root))
        except ValueError:
            rel = str(fpath)

        matches.append(
            ArtifactMatch(
                path=fpath,
                rel_path=rel,
                line_numbers=line_numbers,
                tag_types=sorted(tag_types_set),
                stage_hint=_infer_stage(fpath, project_root),
            )
        )

    return matches


def _iter_files(root: Path):
    """Yield all files under root, skipping hidden/irrelevant directories."""
    if not root.exists():
        return
    for item in root.iterdir():
        if item.name.startswith("."):
            continue
        if item.name in _SKIP_DIRS:
            continue
        if item.is_dir():
            yield from _iter_files(item)
        elif item.is_file():
            yield item


# ═══════════════════════════════════════════════════════════════════════
# FEATURE VIEW BUILDER
# ═══════════════════════════════════════════════════════════════════════

# The SDLC stages we expect every feature to appear in (ordered)
EXPECTED_STAGES = ["spec", "design", "code", "tests", "uat"]


def build_feature_view(
    req_key: str,
    project_root: Path,
    expected_stages: Optional[list[str]] = None,
) -> FeatureView:
    """Build a FeatureView for req_key by scanning the entire project_root.

    Args:
        req_key:         REQ key to trace (e.g., "REQ-F-AUTH-001")
        project_root:    Root of the project to scan
        expected_stages: Stages to check coverage against; defaults to EXPECTED_STAGES
    """
    if expected_stages is None:
        expected_stages = EXPECTED_STAGES

    all_matches = scan_for_req_key(req_key, project_root, project_root)

    # Group by stage
    by_stage: dict[str, list[ArtifactMatch]] = {}
    for m in all_matches:
        stage = m.stage_hint
        by_stage.setdefault(stage, []).append(m)

    # Determine missing stages
    missing = [s for s in expected_stages if s not in by_stage]
    covered = [s for s in expected_stages if s in by_stage]

    coverage = len(covered)
    total = len(expected_stages)

    return FeatureView(
        req_key=req_key,
        matches_by_stage=by_stage,
        missing_stages=missing,
        coverage=coverage,
        total_stages=total,
        coverage_pct=round(100.0 * coverage / total, 1) if total > 0 else 0.0,
    )


# ═══════════════════════════════════════════════════════════════════════
# MULTI-FEATURE VIEWS
# ═══════════════════════════════════════════════════════════════════════


def build_all_feature_views(
    req_keys: list[str],
    project_root: Path,
    expected_stages: Optional[list[str]] = None,
) -> dict[str, FeatureView]:
    """Build feature views for multiple REQ keys.

    Returns: {req_key: FeatureView}
    """
    return {
        key: build_feature_view(key, project_root, expected_stages) for key in req_keys
    }


def coverage_report(views: dict[str, FeatureView]) -> list[dict[str, Any]]:
    """Produce a coverage report across all feature views.

    Returns list of dicts sorted by coverage ascending (least covered first).
    """
    rows = []
    for req_key, view in views.items():
        rows.append(
            {
                "req_key": req_key,
                "coverage": view.coverage,
                "total_stages": view.total_stages,
                "coverage_pct": view.coverage_pct,
                "stages_present": sorted(view.matches_by_stage.keys()),
                "missing_stages": view.missing_stages,
                "summary": view.summary(),
            }
        )
    return sorted(rows, key=lambda r: r["coverage_pct"])
