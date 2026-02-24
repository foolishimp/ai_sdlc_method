"""Compatibility package exposing ``imp_gemini/gemini_cli`` at repo root.

This lets imports such as ``gemini_cli.engine.state`` and module execution
``python -m gemini_cli.cli`` work without requiring callers to alter
PYTHONPATH to include ``imp_gemini`` explicitly.
"""

from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parent.parent / "imp_gemini" / "gemini_cli"
__path__ = [str(_PKG_ROOT)]

