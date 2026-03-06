# Validates: REQ-TOOL-010 (Spec/Design Boundary Enforcement)
"""Tests for spec_boundary.py — technology leakage detection."""

from pathlib import Path

import pytest

from genesis.spec_boundary import (
    BoundaryCheckResult,
    TechLeakageViolation,
    TECH_KEYWORDS,
    build_custom_pattern,
    check_spec_boundary,
    scan_tech_leakage,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def write_req_doc(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


# ── scan_tech_leakage ─────────────────────────────────────────────────────────


class TestScanTechLeakage:
    def test_detects_python_mention(self, tmp_path: Path) -> None:
        doc = write_req_doc(tmp_path / "req.md", "The system shall be implemented in Python.\n")
        violations = scan_tech_leakage(doc)
        assert len(violations) >= 1
        assert any(v.matched_keyword.lower() == "python" for v in violations)

    def test_detects_django(self, tmp_path: Path) -> None:
        doc = write_req_doc(tmp_path / "req.md", "Use Django for the web framework.\n")
        violations = scan_tech_leakage(doc)
        assert any(v.matched_keyword.lower() == "django" for v in violations)

    def test_detects_docker(self, tmp_path: Path) -> None:
        doc = write_req_doc(tmp_path / "req.md", "Deploy via Docker containers.\n")
        violations = scan_tech_leakage(doc)
        assert any(v.matched_keyword.lower() == "docker" for v in violations)

    def test_clean_doc_has_no_violations(self, tmp_path: Path) -> None:
        doc = write_req_doc(
            tmp_path / "req.md",
            "The system shall authenticate users using a token-based mechanism.\n"
            "REQ-F-AUTH-001: User authentication must support multi-factor verification.\n",
        )
        violations = scan_tech_leakage(doc)
        assert violations == []

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert scan_tech_leakage(tmp_path / "no_file.md") == []

    def test_returns_line_number(self, tmp_path: Path) -> None:
        doc = write_req_doc(
            tmp_path / "req.md",
            "Line 1\nLine 2\nThe system must use PostgreSQL.\n",
        )
        violations = scan_tech_leakage(doc)
        assert len(violations) >= 1
        v = next(v for v in violations if "postgresql" in v.matched_keyword.lower())
        assert v.line_number == 3

    def test_acceptable_context_not_flagged(self, tmp_path: Path) -> None:
        doc = write_req_doc(
            tmp_path / "req.md",
            "The system must support Python versions >= 3.10.\n",
        )
        violations = scan_tech_leakage(doc)
        # "must support" context → acceptable
        real_violations = [v for v in violations if not v.context_acceptable]
        assert len(real_violations) == 0

    def test_multiple_keywords_on_one_line(self, tmp_path: Path) -> None:
        doc = write_req_doc(tmp_path / "req.md", "Use Python with Django and PostgreSQL.\n")
        violations = scan_tech_leakage(doc)
        keywords = {v.matched_keyword.lower() for v in violations}
        assert "python" in keywords
        assert "django" in keywords
        assert "postgresql" in keywords

    def test_case_insensitive_matching(self, tmp_path: Path) -> None:
        doc = write_req_doc(tmp_path / "req.md", "Use PYTHON for this module.\n")
        violations = scan_tech_leakage(doc)
        assert len(violations) >= 1

    def test_partial_word_not_matched(self, tmp_path: Path) -> None:
        # "rust" should not match "trust", "robust"
        doc = write_req_doc(
            tmp_path / "req.md",
            "The system must be robust and trustworthy.\n",
        )
        violations = scan_tech_leakage(doc)
        rust_violations = [v for v in violations if v.matched_keyword.lower() == "rust"]
        assert rust_violations == []


# ── check_spec_boundary ───────────────────────────────────────────────────────


class TestCheckSpecBoundary:
    def test_clean_docs_no_violations(self, tmp_path: Path) -> None:
        doc = write_req_doc(
            tmp_path / "requirements.md",
            "REQ-F-AUTH-001: Users shall be authenticated via a token mechanism.\n"
            "REQ-NFR-PERF-001: The system shall respond within 200ms at p99.\n",
        )
        result = check_spec_boundary([doc])
        assert not result.has_violations
        assert result.violation_count == 0

    def test_detects_violations_across_multiple_files(self, tmp_path: Path) -> None:
        doc1 = write_req_doc(tmp_path / "req1.md", "Use Python for processing.\n")
        doc2 = write_req_doc(tmp_path / "req2.md", "Deploy to AWS Lambda.\n")
        result = check_spec_boundary([doc1, doc2])
        assert result.has_violations
        assert result.files_checked == 2

    def test_files_checked_count(self, tmp_path: Path) -> None:
        docs = [
            write_req_doc(tmp_path / f"req{i}.md", "Tech-agnostic content.\n")
            for i in range(3)
        ]
        result = check_spec_boundary(docs)
        assert result.files_checked == 3

    def test_empty_doc_list(self) -> None:
        result = check_spec_boundary([])
        assert not result.has_violations
        assert result.files_checked == 0

    def test_summary_clean(self, tmp_path: Path) -> None:
        doc = write_req_doc(tmp_path / "req.md", "Clean requirements.\n")
        result = check_spec_boundary([doc])
        summary = result.summary()
        assert "clean" in summary.lower()

    def test_summary_with_violations(self, tmp_path: Path) -> None:
        doc = write_req_doc(tmp_path / "req.md", "Use Django REST framework.\n")
        result = check_spec_boundary([doc])
        summary = result.summary()
        assert "django" in summary.lower()

    def test_custom_keyword_pattern(self, tmp_path: Path) -> None:
        # Custom pattern matching only "mytech"
        pattern = build_custom_pattern(frozenset(["mytech"]))
        doc = write_req_doc(tmp_path / "req.md", "The system shall use mytech API.\n")
        result = check_spec_boundary([doc], keyword_pattern=pattern)
        assert result.has_violations

    def test_custom_pattern_does_not_match_defaults(self, tmp_path: Path) -> None:
        # Custom pattern with only "mytech" → "Python" not matched
        pattern = build_custom_pattern(frozenset(["mytech"]))
        doc = write_req_doc(tmp_path / "req.md", "Use Python here.\n")
        result = check_spec_boundary([doc], keyword_pattern=pattern)
        assert not result.has_violations


# ── TECH_KEYWORDS integrity ───────────────────────────────────────────────────


class TestTechKeywords:
    def test_keywords_not_empty(self) -> None:
        assert len(TECH_KEYWORDS) > 20

    def test_common_tech_present(self) -> None:
        lower_kws = {k.lower() for k in TECH_KEYWORDS}
        for expected in ["python", "docker", "kubernetes", "postgresql", "react"]:
            assert expected in lower_kws, f"Expected '{expected}' in TECH_KEYWORDS"
