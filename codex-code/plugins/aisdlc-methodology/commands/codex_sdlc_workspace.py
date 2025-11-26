#!/usr/bin/env python3
"""
codex-sdlc-workspace

Validates the .ai-workspace structure and optionally installs it from the Codex template.
Safe by default (reports issues). Use --fix to copy missing pieces.

Usage:
    python codex_sdlc_workspace.py [--root .] [--fix] [--force]

# Implements: REQ-F-WORKSPACE-001/002/003 (validation), REQ-NFR-CONTEXT-001
"""

from pathlib import Path
import argparse
import shutil
import sys


REQUIRED_PATHS = [
    Path(".ai-workspace/tasks/active/ACTIVE_TASKS.md"),
    Path(".ai-workspace/tasks/finished"),
    Path(".ai-workspace/tasks/templates") if False else None,  # placeholder if templates added
    Path(".ai-workspace/config"),
]


def validate(root: Path) -> list[str]:
    findings: list[str] = []
    for p in REQUIRED_PATHS:
        if p is None:
            continue
        target = root / p
        if not target.exists():
            findings.append(f"Missing: {p}")
    return findings


def install_template(root: Path, force: bool) -> bool:
    template_root = Path(__file__).resolve().parent.parent.parent / "project-template" / ".ai-workspace"
    dest = root / ".ai-workspace"
    if not template_root.exists():
        print(f"❌ Template missing at {template_root}")
        return False
    if dest.exists() and force:
        shutil.rmtree(dest)
    if not dest.exists():
        shutil.copytree(template_root, dest)
        print(f"✅ Installed .ai-workspace from template to {dest}")
    else:
        print("⏭️  .ai-workspace already exists (use --force to overwrite)")
    return True


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate (and optionally install) .ai-workspace for Codex AISDLC")
    parser.add_argument("--root", default=".", help="Repo root (default: current directory)")
    parser.add_argument("--fix", action="store_true", help="Install workspace if missing")
    parser.add_argument("--force", action="store_true", help="Overwrite existing workspace when used with --fix")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    print(f"🎯 Checking workspace at: {root}")
    findings = validate(root)

    if findings:
        print("⚠️  Workspace issues:")
        for f in findings:
            print(f"- {f}")
        if args.fix:
            ok = install_template(root, args.force)
            return 0 if ok else 1
        return 1

    print("✅ .ai-workspace structure looks OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
