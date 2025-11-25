#!/usr/bin/env python3
"""
Codex AISDLC - Traceability Validator (Stub)

Validates REQ-* tagging and presence of the traceability matrix.
Currently prints findings without modifying files.

# Implements: REQ-NFR-TRACE-001, REQ-NFR-CONTEXT-001
"""

from pathlib import Path
import argparse
import sys


def check_files(root: Path) -> list[str]:
    findings: list[str] = []
    matrix = root / "docs" / "TRACEABILITY_MATRIX.md"
    if not matrix.exists():
        findings.append("TRACEABILITY_MATRIX.md missing")
    tasks = root / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"
    if not tasks.exists():
        findings.append("ACTIVE_TASKS.md missing")
    return findings


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate REQ tagging and traceability (stub)")
    parser.add_argument("--root", default=".", help="Repository root")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    findings = check_files(root)

    if findings:
        print("⚠️  Traceability issues:")
        for f in findings:
            print(f"- {f}")
        print("TODO: implement REQ tag scan and matrix regeneration.")
        return 1

    print("✅ Basic traceability files present. Detailed checks not yet implemented.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
