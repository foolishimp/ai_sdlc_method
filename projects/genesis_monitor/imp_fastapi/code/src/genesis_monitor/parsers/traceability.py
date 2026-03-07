# Implements: REQ-F-TRACE-001
"""Scan project files for REQ tag traceability (Implements/Validates tags)."""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

# Patterns for REQ key extraction
_IMPLEMENTS_RE = re.compile(r"#\s*Implements:\s*(REQ-[\w-]+(?:\s*,\s*REQ-[\w-]+)*)")
_VALIDATES_RE = re.compile(r"#\s*Validates:\s*(REQ-[\w-]+(?:\s*,\s*REQ-[\w-]+)*)")
_REQ_KEY_RE = re.compile(r"REQ-[\w-]+")

# Telemetry pattern: req="REQ-*" or req='REQ-*'  # Implements: REQ-F-LINEAGE-002
_TELEMETRY_RE = re.compile(r"""req=["'](REQ-[\w-]+)["']""")

# Spec heading pattern: ### REQ-F-* or ### REQ-NFR-*  # Implements: REQ-F-LINEAGE-004
_SPEC_HEADING_RE = re.compile(r"^###\s+(REQ-(?:F|NFR)-[\w-]+)")

# File extensions to scan
_CODE_EXTENSIONS = {".py", ".ts", ".js", ".java", ".scala", ".rs", ".go", ".sh"}
_TEST_PATTERNS = {"test_", "_test.", "tests/", "test/", "spec/"}

# Directories to skip
_SKIP_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "node_modules",
    ".tox", ".mypy_cache", ".pytest_cache", ".ai-workspace",
    ".claude", "dist", "build", "egg-info",
}


@dataclass
class ReqTagEntry:
    """A single REQ tag found in a file."""

    req_key: str
    file_path: str  # relative to project root
    line_number: int
    tag_type: str  # "implements" or "validates"


@dataclass
class TraceabilityReport:
    """Cross-referenced REQ key traceability across code and tests."""

    code_tags: list[ReqTagEntry] = field(default_factory=list)
    test_tags: list[ReqTagEntry] = field(default_factory=list)

    # Derived: REQ key → list of files
    code_coverage: dict[str, list[str]] = field(default_factory=dict)
    test_coverage: dict[str, list[str]] = field(default_factory=dict)

    # All unique REQ keys found
    all_req_keys: set[str] = field(default_factory=set)

    # Files scanned
    code_files_scanned: int = 0
    test_files_scanned: int = 0

    # --- new fields (REQ-F-LINEAGE-001..004) ---
    # REQ key → files where req= tag appears (REQ-F-LINEAGE-002)
    telemetry_coverage: dict[str, list[str]] = field(default_factory=dict)

    # REQ keys extracted from REQUIREMENTS.md headings (REQ-F-LINEAGE-004)
    spec_defined_keys: set[str] = field(default_factory=set)

    # In code|tests|telemetry but absent from spec (REQ-F-LINEAGE-003)
    orphan_keys: set[str] = field(default_factory=set)

    # In spec but absent from code AND tests AND telemetry (REQ-F-LINEAGE-003)
    uncovered_keys: set[str] = field(default_factory=set)

    # Count of .py files scanned for telemetry tags
    telemetry_files_scanned: int = 0


def _is_test_file(rel_path: str) -> bool:
    """Heuristic: is this file a test file? Uses path relative to project root."""
    parts = rel_path.lower()
    name = rel_path.rsplit("/", 1)[-1] if "/" in rel_path else rel_path
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or parts.startswith("tests/")
        or parts.startswith("test/")
        or parts.startswith("spec/")
        or "/tests/" in parts
        or "/test/" in parts
    )


def _should_skip_dir(dirname: str) -> bool:
    """Should this directory be skipped?"""
    return dirname in _SKIP_DIRS or dirname.startswith(".")


def _extract_req_tags(file_path: Path, project_root: Path) -> list[ReqTagEntry]:
    """Extract all REQ tags from a single file."""
    entries = []
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, UnicodeDecodeError):
        return entries

    rel_path = str(file_path.relative_to(project_root))

    for line_no, line in enumerate(text.splitlines(), 1):
        # Check Implements tags
        for match in _IMPLEMENTS_RE.finditer(line):
            for req_key in _REQ_KEY_RE.findall(match.group(1)):
                entries.append(ReqTagEntry(
                    req_key=req_key,
                    file_path=rel_path,
                    line_number=line_no,
                    tag_type="implements",
                ))
        # Check Validates tags
        for match in _VALIDATES_RE.finditer(line):
            for req_key in _REQ_KEY_RE.findall(match.group(1)):
                entries.append(ReqTagEntry(
                    req_key=req_key,
                    file_path=rel_path,
                    line_number=line_no,
                    tag_type="validates",
                ))

    return entries


def spec_inventory(project_root: Path) -> set[str]:
    """Parse REQUIREMENTS.md and return the set of formally defined REQ keys.

    Searches project_root/.ai-workspace/spec/REQUIREMENTS.md first, then
    project_root/specification/REQUIREMENTS.md. Returns empty set if neither found.
    # Implements: REQ-F-LINEAGE-004
    """
    candidates = [
        project_root / ".ai-workspace" / "spec" / "REQUIREMENTS.md",
        project_root / "specification" / "REQUIREMENTS.md",
    ]
    for path in candidates:
        if path.exists():
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                return set()
            keys: set[str] = set()
            for line in text.splitlines():
                m = _SPEC_HEADING_RE.match(line)
                if m:
                    keys.add(m.group(1))
            return keys
    return set()


def telemetry_scanner(project_root: Path) -> dict[str, list[str]]:
    """Scan .py source files for req="REQ-*" and req='REQ-*' patterns.

    Returns dict mapping REQ key -> sorted list of unique relative file paths.
    Files with no matching patterns produce no entries.
    # Implements: REQ-F-LINEAGE-002
    """
    result: dict[str, list[str]] = {}
    for dirpath_str, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if not _should_skip_dir(d)]
        dirpath = Path(dirpath_str)
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            file_path = dirpath / filename
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            rel_path = str(file_path.relative_to(project_root))
            for line in text.splitlines():
                for m in _TELEMETRY_RE.finditer(line):
                    req_key = m.group(1)
                    result.setdefault(req_key, [])
                    if rel_path not in result[req_key]:
                        result[req_key].append(rel_path)
    for key in result:
        result[key] = sorted(result[key])
    return result


def parse_traceability(project_root: Path) -> TraceabilityReport:
    """Scan project files for REQ key traceability tags.

    Walks the project directory tree looking for code files with
    `# Implements: REQ-*` tags and test files with `# Validates: REQ-*` tags.
    Returns a cross-referenced report.
    """
    report = TraceabilityReport()
    code_files = 0
    test_files = 0

    for dirpath_str, dirnames, filenames in os.walk(project_root):
        # Prune directories in-place
        dirnames[:] = [d for d in dirnames if not _should_skip_dir(d)]

        dirpath = Path(dirpath_str)
        for filename in filenames:
            file_path = dirpath / filename
            if file_path.suffix not in _CODE_EXTENSIONS:
                continue

            rel_path = str(file_path.relative_to(project_root))
            is_test = _is_test_file(rel_path)
            if is_test:
                test_files += 1
            else:
                code_files += 1

            tags = _extract_req_tags(file_path, project_root)
            for tag in tags:
                report.all_req_keys.add(tag.req_key)
                if tag.tag_type == "validates" or (tag.tag_type == "implements" and is_test):
                    report.test_tags.append(tag)
                    report.test_coverage.setdefault(tag.req_key, [])
                    if tag.file_path not in report.test_coverage[tag.req_key]:
                        report.test_coverage[tag.req_key].append(tag.file_path)
                else:
                    report.code_tags.append(tag)
                    report.code_coverage.setdefault(tag.req_key, [])
                    if tag.file_path not in report.code_coverage[tag.req_key]:
                        report.code_coverage[tag.req_key].append(tag.file_path)

    report.code_files_scanned = code_files
    report.test_files_scanned = test_files

    # Telemetry and spec inventory  # Implements: REQ-F-LINEAGE-002, REQ-F-LINEAGE-004
    report.telemetry_coverage = telemetry_scanner(project_root)
    report.spec_defined_keys = spec_inventory(project_root)
    report.telemetry_files_scanned = len(
        {f for files in report.telemetry_coverage.values() for f in files}
    )

    # Orphan and uncovered key detection  # Implements: REQ-F-LINEAGE-003
    # Only meaningful when a spec inventory exists (backward compat — LINEAGE-001 AC-5)
    if report.spec_defined_keys:
        downstream = (
            set(report.code_coverage)
            | set(report.test_coverage)
            | set(report.telemetry_coverage)
        )
        report.orphan_keys = downstream - report.spec_defined_keys
        report.uncovered_keys = report.spec_defined_keys - downstream

    return report
