# Implements: REQ-TOOL-003 (Workflow Commands), REQ-EVAL-002 (Evaluator Composition)
# Validates: REQ-TOOL-003, REQ-EVAL-002
"""Tests for genesis check-tags subcommand (F_D tag coverage evaluator)."""

import json
import sys
from pathlib import Path

import pytest

# Add genesis to path for direct import
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from genesis.__main__ import cmd_check_tags


class _Args:
    """Minimal argparse namespace stub."""
    def __init__(self, tag_type, path, exclude=None):
        self.type = tag_type
        self.path = str(path)
        self.exclude = exclude or ["__init__.py", "__pycache__"]


class TestCheckTagsImplements:
    """req_tags_in_code: every .py file must have Implements: REQ-*"""

    def test_all_tagged_returns_zero(self, tmp_path, capsys):
        (tmp_path / "a.py").write_text("# Implements: REQ-F-FOO-001\npass\n")
        (tmp_path / "b.py").write_text("# Implements: REQ-F-BAR-001\npass\n")
        rc = cmd_check_tags(_Args("implements", tmp_path))
        assert rc == 0

    def test_one_untagged_returns_one(self, tmp_path, capsys):
        (tmp_path / "tagged.py").write_text("# Implements: REQ-F-FOO-001\n")
        (tmp_path / "untagged.py").write_text("def foo(): pass\n")
        rc = cmd_check_tags(_Args("implements", tmp_path))
        assert rc == 1

    def test_three_untagged_returns_three(self, tmp_path):
        for i in range(3):
            (tmp_path / f"missing{i}.py").write_text("def foo(): pass\n")
        rc = cmd_check_tags(_Args("implements", tmp_path))
        assert rc == 3

    def test_output_is_valid_json(self, tmp_path, capsys):
        (tmp_path / "a.py").write_text("# Implements: REQ-F-FOO-001\n")
        cmd_check_tags(_Args("implements", tmp_path))
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["check"] == "req_tags_implements"
        assert data["total_files"] == 1
        assert data["tagged"] == 1
        assert data["untagged"] == 0

    def test_untagged_files_listed_in_output(self, tmp_path, capsys):
        (tmp_path / "missing.py").write_text("def foo(): pass\n")
        cmd_check_tags(_Args("implements", tmp_path))
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["untagged"] == 1
        assert any("missing.py" in f for f in data["untagged_files"])

    def test_init_py_excluded_by_default(self, tmp_path):
        (tmp_path / "__init__.py").write_text("# no tag here\n")
        (tmp_path / "real.py").write_text("# Implements: REQ-F-FOO-001\n")
        rc = cmd_check_tags(_Args("implements", tmp_path))
        assert rc == 0  # __init__.py not counted

    def test_pycache_excluded(self, tmp_path):
        cache = tmp_path / "__pycache__"
        cache.mkdir()
        (cache / "compiled.py").write_text("# no tag\n")
        (tmp_path / "real.py").write_text("# Implements: REQ-F-FOO-001\n")
        rc = cmd_check_tags(_Args("implements", tmp_path))
        assert rc == 0

    def test_nonexistent_path_returns_one(self, tmp_path):
        rc = cmd_check_tags(_Args("implements", tmp_path / "does_not_exist"))
        assert rc == 1

    def test_empty_directory_returns_zero(self, tmp_path):
        rc = cmd_check_tags(_Args("implements", tmp_path))
        assert rc == 0  # no files → no violations

    def test_recursive_scan(self, tmp_path):
        sub = tmp_path / "subpkg"
        sub.mkdir()
        (sub / "mod.py").write_text("def x(): pass\n")  # no tag
        (tmp_path / "top.py").write_text("# Implements: REQ-F-FOO-001\n")
        rc = cmd_check_tags(_Args("implements", tmp_path))
        assert rc == 1  # sub/mod.py is untagged


class TestCheckTagsValidates:
    """req_tags_in_tests: every test .py file must have Validates: REQ-*"""

    def test_all_tagged_returns_zero(self, tmp_path):
        (tmp_path / "test_foo.py").write_text("# Validates: REQ-F-FOO-001\n")
        rc = cmd_check_tags(_Args("validates", tmp_path))
        assert rc == 0

    def test_missing_validates_tag_fails(self, tmp_path):
        (tmp_path / "test_foo.py").write_text("def test_foo(): pass\n")
        rc = cmd_check_tags(_Args("validates", tmp_path))
        assert rc == 1

    def test_implements_tag_does_not_satisfy_validates_check(self, tmp_path):
        # Implements: alone is not enough for a validates check
        (tmp_path / "test_foo.py").write_text("# Implements: REQ-F-FOO-001\n")
        rc = cmd_check_tags(_Args("validates", tmp_path))
        assert rc == 1

    def test_output_check_field(self, tmp_path, capsys):
        (tmp_path / "test_foo.py").write_text("# Validates: REQ-F-FOO-001\n")
        cmd_check_tags(_Args("validates", tmp_path))
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["check"] == "req_tags_validates"
        assert data["pattern"] == "Validates: REQ-"


class TestCheckTagsCLI:
    """Integration: check-tags callable via python -m genesis."""

    def test_genesis_module_exposes_check_tags(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "genesis", "check-tags", "--help"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).parent.parent / "code"),
        )
        assert result.returncode == 0
        assert "implements" in result.stdout or "implements" in result.stderr

    def test_real_genesis_source_is_fully_tagged(self):
        """Dogfood: the genesis engine source itself must be fully tagged."""
        genesis_src = Path(__file__).parent.parent / "code" / "genesis"
        rc = cmd_check_tags(_Args("implements", genesis_src))
        assert rc == 0, f"{rc} genesis source files are missing Implements: tags"

    def test_real_test_files_are_fully_tagged(self):
        """Dogfood: developer-written test files must carry Validates: tags."""
        tests_dir = Path(__file__).parent
        # Exclude generated e2e run artifacts and uat fixtures
        args = _Args("validates", tests_dir,
                     exclude=["__init__.py", "__pycache__", "e2e/runs", "uat"])
        rc = cmd_check_tags(args)
        assert rc == 0, f"{rc} test files are missing Validates: tags"
