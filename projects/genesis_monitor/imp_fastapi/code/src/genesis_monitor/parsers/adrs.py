# Implements: REQ-F-PARSE-007
"""Parse specification/adrs/ADR-S-*.md files into AdrEntry models."""

import re
from pathlib import Path

from genesis_monitor.models.core import AdrEntry

# Status badge colours
_STATUS_STYLE = {
    "accepted":    "background:#1b5e20;color:#a5d6a7",
    "proposed":    "background:#1a237e;color:#90caf9",
    "deprecated":  "background:#4a148c;color:#ce93d8",
    "superseded":  "background:#b71c1c;color:#ef9a9a",
    "retired":     "background:#37474f;color:#b0bec5",
    "draft":       "background:#e65100;color:#ffcc80",
}

_ADR_FILENAME_RE = re.compile(r"ADR-S-(\d+)-(.+)\.md$", re.IGNORECASE)


def parse_adrs(project_path: Path) -> list[AdrEntry]:
    """Scan specification/adrs/ for ADR-S-*.md files and return parsed entries."""
    adrs_dir = project_path / "specification" / "adrs"
    if not adrs_dir.is_dir():
        return []

    entries: list[AdrEntry] = []
    for md_path in sorted(adrs_dir.glob("ADR-S-*.md")):
        entry = _parse_one(md_path)
        if entry:
            entries.append(entry)

    return entries


def _parse_one(path: Path) -> AdrEntry | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    m = _ADR_FILENAME_RE.match(path.name)
    if not m:
        return None
    number = int(m.group(1))

    # Extract title from first H1
    title_m = re.search(r"^#\s+ADR-S-\d+[:\s—–-]+(.+)$", text, re.MULTILINE)
    title = title_m.group(1).strip() if title_m else path.stem

    # **Status**: Accepted / Proposed / Retired / Deprecated / Superseded
    status_m = re.search(r"\*\*Status\*\*\s*:\s*(.+)", text, re.IGNORECASE)
    raw_status = status_m.group(1).strip().rstrip(".") if status_m else ""
    # Normalise: take first word, lower-case
    status_word = raw_status.split()[0].lower() if raw_status else "unknown"
    # Handle "Retired — 2026-03-07" style
    status = status_word.rstrip(",;—–-")

    # **Date**: YYYY-MM-DD
    date_m = re.search(r"\*\*Date\*\*\s*:\s*(\S+)", text, re.IGNORECASE)
    date = date_m.group(1).strip() if date_m else ""

    # **Scope**: one-liner
    scope_m = re.search(r"\*\*Scope\*\*\s*:\s*(.+)", text, re.IGNORECASE)
    scope = scope_m.group(1).strip() if scope_m else ""

    # Summary: first paragraph after the "---" separator and header block, or first line of ## Context
    summary = _extract_summary(text)

    # Superseded-by note
    superseded_by_m = re.search(r"\*\*Superseded by\*\*\s*:\s*(.+)", text, re.IGNORECASE)
    superseded_by = superseded_by_m.group(1).strip() if superseded_by_m else None

    badge_style = _STATUS_STYLE.get(status, "background:#424242;color:#e0e0e0")

    return AdrEntry(
        number=number,
        adr_id=f"ADR-S-{number:03d}",
        title=title,
        status=status,
        date=date,
        scope=scope,
        summary=summary,
        path=str(path),
        superseded_by=superseded_by,
        badge_style=badge_style,
    )


def _extract_summary(text: str) -> str:
    """Pull first meaningful sentence from Context section, or first body paragraph."""
    # Try ## Context section
    ctx_m = re.search(r"##\s+Context\s*\n+(.*?)(?:\n##|\Z)", text, re.DOTALL)
    if ctx_m:
        para = ctx_m.group(1).strip()
        # First non-empty line
        first = next((l.strip() for l in para.splitlines() if l.strip()), "")
        if first:
            return first[:200]

    # Fall back: first paragraph after the header block (after first ---)
    parts = text.split("---", 1)
    if len(parts) > 1:
        body = parts[1].strip()
        lines = [l.strip() for l in body.splitlines() if l.strip() and not l.startswith("#")]
        if lines:
            return lines[0][:200]

    return ""
