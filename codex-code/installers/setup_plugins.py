#!/usr/bin/env python3
"""
Codex AISDLC - Plugin Setup (Stub)

Installs/updates Codex AISDLC plugins listed in marketplace.json.
Currently reports planned actions; implementation to follow packaging.

# Implements: REQ-F-PLUGIN-001/002/003/004 (Codex delivery)
"""

from pathlib import Path
import argparse
import json
import sys


def load_marketplace(root: Path) -> list[dict]:
    marketplace_path = root / "marketplace.json"
    with marketplace_path.open() as f:
        data = json.load(f)
    return [p for p in data.get("plugins", []) if p.get("provider") == "openai"]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Install Codex AISDLC plugins (stub)")
    parser.add_argument("--root", default=".", help="Repository root containing marketplace.json")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    plugins = load_marketplace(root)
    print("ℹ️  Stub mode: no plugins installed.")
    print("Codex plugins detected in marketplace.json:")
    for p in plugins:
        print(f"- {p['name']} {p.get('version')} @ {p.get('path')}")
    print("TODO: pip install packages or copy local plugin assets for Codex runtime.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
