#!/usr/bin/env python3
"""
Codex AISDLC - Workspace Setup (Stub)

Copies the shared .ai-workspace template into a target project and validates structure.
This mirrors the Claude setup but is currently a non-destructive stub for Codex.

# Implements: REQ-F-WORKSPACE-001, REQ-F-WORKSPACE-002, REQ-F-WORKSPACE-003
"""

from pathlib import Path
import argparse
import shutil
import sys


def copy_workspace(template_root: Path, target: Path, force: bool) -> bool:
    source = template_root / ".ai-workspace"
    dest = target / ".ai-workspace"
    if not source.exists():
        print(f"❌ Template missing: {source}")
        return False
    if dest.exists() and not force:
        print("⏭️  .ai-workspace already exists (use --force to overwrite)")
        return True
    if dest.exists() and force:
        shutil.rmtree(dest)
    shutil.copytree(source, dest)
    print(f"✅ Installed .ai-workspace to {dest}")
    return True


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Install .ai-workspace for Codex AISDLC")
    parser.add_argument("--target", default=".", help="Target project directory")
    parser.add_argument("--force", action="store_true", help="Overwrite existing workspace")
    args = parser.parse_args(argv)

    target = Path(args.target).resolve()
    template_root = Path(__file__).resolve().parent.parent / "project-template"

    print(f"🎯 Target: {target}")
    print(f"📦 Template root: {template_root}")

    ok = copy_workspace(template_root, target, args.force)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
