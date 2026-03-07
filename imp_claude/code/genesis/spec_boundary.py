# Implements: REQ-TOOL-010 (Spec/Design Boundary Enforcement)
"""Spec/Design boundary checker — detects technology leakage in requirements.

Requirements documents (WHAT) must be technology-agnostic. This module
detects when specific technology names (Python, Django, Docker, AWS, etc.)
appear in requirements, which indicates specification debt — tech choices
that belong in design ADRs have leaked into the spec.

Technology leakage in requirements is harmful because:
- It locks the spec to one implementation before design decisions are made
- It prevents multiple design variants (same spec, different implementations)
- It conflates WHAT the system must do with HOW it does it

Usage:
    result = check_spec_boundary(req_path, TECH_KEYWORDS)
    if result.has_violations:
        for v in result.violations:
            print(f"  {v.line_number}: {v.matched_keyword!r} in: {v.line}")

Reference: Asset Graph Model §2.6 (Spec/Design Boundary), §2.7 (Multiple Implementations)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════
# DEFAULT TECHNOLOGY KEYWORD SETS
# ═══════════════════════════════════════════════════════════════════════

# Languages and runtimes that belong in design, not spec
TECH_LANGUAGES = {
    "python",
    "javascript",
    "typescript",
    "java",
    "scala",
    "kotlin",
    "go",
    "golang",
    "rust",
    "ruby",
    "php",
    "c#",
    "c++",
    "swift",
    "node.js",
    "nodejs",
    "jvm",
    "clr",
    ".net",
}

# Web frameworks
TECH_FRAMEWORKS = {
    "django",
    "flask",
    "fastapi",
    "spring",
    "spring boot",
    "rails",
    "express",
    "next.js",
    "nextjs",
    "nuxt",
    "angular",
    "react",
    "vue",
    "svelte",
    "htmx",
    "fastify",
    "gin",
    "echo",
    "fiber",
    "axum",
    "actix",
    "rocket",
    "play framework",
}

# Databases and storage
TECH_DATABASES = {
    "postgresql",
    "postgres",
    "mysql",
    "sqlite",
    "mongodb",
    "redis",
    "cassandra",
    "dynamodb",
    "firestore",
    "elasticsearch",
    "opensearch",
    "clickhouse",
    "snowflake",
    "bigquery",
    "redshift",
    "oracle",
}

# Infrastructure and cloud
TECH_INFRA = {
    "docker",
    "kubernetes",
    "k8s",
    "helm",
    "terraform",
    "ansible",
    "aws",
    "azure",
    "gcp",
    "google cloud",
    "lambda",
    "ec2",
    "s3",
    "cloudformation",
    "pulumi",
    "nomad",
    "consul",
}

# Build and package tools
TECH_BUILD = {
    "pip",
    "poetry",
    "pipenv",
    "conda",
    "npm",
    "yarn",
    "pnpm",
    "maven",
    "gradle",
    "sbt",
    "cargo",
    "bundler",
    "composer",
    "webpack",
    "vite",
    "esbuild",
    "rollup",
    "bazel",
}

# Test frameworks (acceptable in spec only as concepts, not named tools)
TECH_TEST_TOOLS = {
    "pytest",
    "jest",
    "junit",
    "rspec",
    "mocha",
    "jasmine",
    "playwright",
    "cypress",
    "selenium",
    "testcontainers",
}

# All tech keywords combined
TECH_KEYWORDS: frozenset[str] = frozenset(
    TECH_LANGUAGES
    | TECH_FRAMEWORKS
    | TECH_DATABASES
    | TECH_INFRA
    | TECH_BUILD
    | TECH_TEST_TOOLS
)

# Phrases that indicate acceptable spec-level technology mentions
# (e.g., "must support Python versions" may be acceptable)
_ACCEPTABLE_CONTEXTS = [
    r"must support",
    r"must integrate with",
    r"ecosystem.compatibility",
    r"technology-agnostic",
    r"not be tied to",
    r"independent of",
    r"regardless of",
]
_ACCEPTABLE_RE = re.compile("|".join(_ACCEPTABLE_CONTEXTS), re.IGNORECASE)


# Regex for whole-word matching (surrounded by non-word chars)
def _build_keyword_pattern(keywords: frozenset[str]) -> re.Pattern[str]:
    # Sort by length descending so longer phrases match first
    sorted_kws = sorted(keywords, key=len, reverse=True)
    escaped = [re.escape(kw) for kw in sorted_kws]
    return re.compile(r"(?<!\w)(" + "|".join(escaped) + r")(?!\w)", re.IGNORECASE)


_DEFAULT_PATTERN = _build_keyword_pattern(TECH_KEYWORDS)


# ═══════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class TechLeakageViolation:
    """A single technology keyword found in a requirements document."""

    file_path: str
    line_number: int
    line: str
    matched_keyword: str
    context_acceptable: bool  # True if line looks like an acceptable usage


@dataclass
class BoundaryCheckResult:
    """Result of checking spec/design boundary for a set of documents."""

    files_checked: int
    violations: list[TechLeakageViolation] = field(default_factory=list)
    acceptable: list[TechLeakageViolation] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    def summary(self) -> str:
        if not self.violations:
            return f"Spec boundary: clean ({self.files_checked} files checked)"
        kws = sorted({v.matched_keyword.lower() for v in self.violations})
        return (
            f"Spec boundary: {self.violation_count} technology leak(s) in {self.files_checked} file(s) "
            f"— keywords: {', '.join(kws)}"
        )


# ═══════════════════════════════════════════════════════════════════════
# SCANNING
# ═══════════════════════════════════════════════════════════════════════


def scan_tech_leakage(
    doc_path: Path,
    keyword_pattern: Optional[re.Pattern[str]] = None,
) -> list[TechLeakageViolation]:
    """Scan a requirements document for technology keyword leakage.

    Returns list of violations (keyword occurrences in context that
    indicate binding to a specific technology).
    """
    if keyword_pattern is None:
        keyword_pattern = _DEFAULT_PATTERN

    if not doc_path.exists():
        return []

    violations = []
    try:
        text = doc_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue

        # Skip comment-style headers or ADR references
        if stripped.startswith("#") and "ADR" in stripped:
            continue
        # Skip lines that are clearly in acceptable context
        if _ACCEPTABLE_RE.search(stripped):
            continue

        for match in keyword_pattern.finditer(stripped):
            keyword = match.group(0)
            # Check if surrounding context makes this acceptable
            acceptable = bool(_ACCEPTABLE_RE.search(stripped))
            v = TechLeakageViolation(
                file_path=str(doc_path),
                line_number=lineno,
                line=stripped[:200],
                matched_keyword=keyword,
                context_acceptable=acceptable,
            )
            violations.append(v)

    return violations


def check_spec_boundary(
    req_docs: list[Path],
    keyword_pattern: Optional[re.Pattern[str]] = None,
) -> BoundaryCheckResult:
    """Check multiple requirements documents for technology leakage.

    Returns a BoundaryCheckResult summarising all violations across all docs.
    """
    all_violations: list[TechLeakageViolation] = []
    all_acceptable: list[TechLeakageViolation] = []

    for doc_path in req_docs:
        raw_violations = scan_tech_leakage(doc_path, keyword_pattern)
        for v in raw_violations:
            if v.context_acceptable:
                all_acceptable.append(v)
            else:
                all_violations.append(v)

    return BoundaryCheckResult(
        files_checked=len(req_docs),
        violations=all_violations,
        acceptable=all_acceptable,
    )


# ═══════════════════════════════════════════════════════════════════════
# CUSTOM KEYWORD SETS
# ═══════════════════════════════════════════════════════════════════════


def build_custom_pattern(keywords: frozenset[str]) -> re.Pattern[str]:
    """Build a word-boundary regex pattern from a custom keyword set."""
    return _build_keyword_pattern(keywords)


def merge_keyword_sets(*sets: frozenset[str]) -> frozenset[str]:
    """Merge multiple keyword sets into one."""
    result: frozenset[str] = frozenset()
    for s in sets:
        result = result | s
    return result
