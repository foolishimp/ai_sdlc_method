#!/usr/bin/env python3
"""
Codex AISDLC - Command Setup (Stub)

Registers Codex command presets/configs into the target project.
Currently a stub that reports intended actions to avoid destructive writes.

# Implements: REQ-F-CMD-001 (Codex CLI equivalents)
"""

from pathlib import Path
import argparse
import sys


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Register Codex AISDLC commands (stub)")
    parser.add_argument("--target", default=".", help="Target project directory")
    args = parser.parse_args(argv)

    target = Path(args.target).resolve()
    preset_src = Path(__file__).resolve().parent.parent / "project-template" / "codex"
    preset_dest = target / "codex"

    print("ℹ️  Stub mode: no files written.")
    print(f"Would install Codex command presets from: {preset_src}")
    print(f"To destination: {preset_dest}")
    print("TODO: copy presets and verify commands map to codex-sdlc-* console scripts.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
