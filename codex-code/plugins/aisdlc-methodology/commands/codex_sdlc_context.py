#!/usr/bin/env python3
"""
codex-sdlc-context

Loads key AISDLC references for Codex sessions and surfaces active tasks.
Non-destructive helper to align Codex with Claude context loading behavior.

Usage:
    python codex_sdlc_context.py [--root .]

# Implements: REQ-NFR-CONTEXT-001, REQ-NFR-TRACE-001 (reminders only)
"""

from pathlib import Path
import argparse
import sys


def read_head(path: Path, lines: int = 40) -> list[str]:
    if not path.exists():
        return [f"❌ Missing: {path}"]
    out: list[str] = []
    with path.open() as f:
        for i, line in enumerate(f):
            if i >= lines:
                break
            out.append(line.rstrip("\n"))
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Load AISDLC context for Codex sessions")
    parser.add_argument("--root", default=".", help="Repo root (default: current directory)")
    parser.add_argument("--preview-lines", type=int, default=40, help="Lines to preview from context files")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    preview = args.preview_lines

    codex_md = root / "CODEX.md"
    tasks_md = root / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"
    method_ref = root / "docs" / "requirements" / "AI_SDLC_REQUIREMENTS.md"
    impl_req = root / "docs" / "requirements" / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"

    print(f"🎯 Codex AISDLC context (root: {root})")
    print("\n== CODEX.md ==")
    print("\n".join(read_head(codex_md, preview)))

    print("\n== ACTIVE_TASKS.md ==")
    print("\n".join(read_head(tasks_md, preview)))

    print("\n== AI_SDLC_REQUIREMENTS.md ==")
    print("\n".join(read_head(method_ref, preview)))

    print("\n== AISDLC_IMPLEMENTATION_REQUIREMENTS.md ==")
    print("\n".join(read_head(impl_req, preview)))

    print("\n✅ Context load complete (non-destructive).")
    print("Reminder: tag work with REQ-* and update ACTIVE_TASKS before coding.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
