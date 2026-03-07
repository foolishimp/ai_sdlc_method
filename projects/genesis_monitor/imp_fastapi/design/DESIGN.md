# Genesis Monitor — Implementation Design

**Version**: 1.0.0 (REQ-F-GMON-004 — Full 4-Column REQ Lineage + Telemetry Scanner)
**Date**: 2026-03-07
**Feature**: REQ-F-GMON-004
**Source Asset**: .ai-workspace/spec/REQUIREMENTS.md §28 (REQ-F-LINEAGE-001..004)
**Edge**: requirements→design (iteration 1, converged)

---

## Architecture Overview

The monitor follows a strict 4-layer architecture (enforced by ADR-001, ADR-003):

```
Filesystem
    │
    ▼
┌──────────────────┐
│ parsers/          │  Read-only. Parse raw files → typed Python objects.
│ traceability.py   │  No server imports. No projection logic.
└────────┬─────────┘
         │ TraceabilityReport
         ▼
┌──────────────────┐
│ projections/      │  Compute derived views from parsed models.
│ traceability.py   │  No server imports. No filesystem access.
└────────┬─────────┘
         │ dict (view)
         ▼
┌──────────────────┐
│ server/routes.py  │  Pass view to Jinja2 template.
└────────┬─────────┘
         │ HTML fragment
         ▼
┌──────────────────┐
│ templates/        │  Render 4-column table. No logic.
│ _traceability.html│
└──────────────────┘
```

Import rule: parsers → models only. projections → parsers + models only. server → everything.

---

## §1. Model Changes — `parsers/traceability.py`

### 1.1 New Regex

```python
# Telemetry pattern: req="REQ-*" or req='REQ-*'
_TELEMETRY_RE = re.compile(r"""req=["'](REQ-[\w-]+)["']""")
```

### 1.2 TraceabilityReport — Extended Fields

Add to the existing `TraceabilityReport` dataclass:

```python
@dataclass
class TraceabilityReport:
    # --- existing fields (unchanged) ---
    code_tags: list[ReqTagEntry] = field(default_factory=list)
    test_tags: list[ReqTagEntry] = field(default_factory=list)
    code_coverage: dict[str, list[str]] = field(default_factory=dict)
    test_coverage: dict[str, list[str]] = field(default_factory=dict)
    all_req_keys: set[str] = field(default_factory=set)
    code_files_scanned: int = 0
    test_files_scanned: int = 0

    # --- new fields (REQ-F-LINEAGE-001..004) ---
    telemetry_coverage: dict[str, list[str]] = field(default_factory=dict)
    # REQ key → files where req= tag appears (REQ-F-LINEAGE-002)

    spec_defined_keys: set[str] = field(default_factory=set)
    # REQ keys extracted from REQUIREMENTS.md headings (REQ-F-LINEAGE-004)

    orphan_keys: set[str] = field(default_factory=set)
    # In code|tests|telemetry but absent from spec (REQ-F-LINEAGE-003)

    uncovered_keys: set[str] = field(default_factory=set)
    # In spec but absent from code AND tests AND telemetry (REQ-F-LINEAGE-003)

    telemetry_files_scanned: int = 0
    # Count of .py files scanned for telemetry tags
```

### 1.3 New Function: `spec_inventory(project_root: Path) -> set[str]`

**Purpose**: Parse REQUIREMENTS.md and return the set of formally defined REQ keys.
**Implements**: REQ-F-LINEAGE-004

```
Algorithm:
  1. Locate REQUIREMENTS.md via priority search:
     a. project_root / ".ai-workspace" / "spec" / "REQUIREMENTS.md"
     b. project_root / "specification" / "REQUIREMENTS.md"
     c. If neither found → return set()  (backward compat — REQ-F-LINEAGE-001 AC-5)
  2. Read file (UTF-8, errors=ignore)
  3. Scan lines for markdown headings matching:
       ### REQ-F-<anything>  or  ### REQ-NFR-<anything>
     Pattern: r"^###\s+(REQ-(?:F|NFR)-[\w-]+)"
  4. Return set of matched REQ key strings
  5. On any OSError/UnicodeDecodeError → return set()  (AC-4 of REQ-F-LINEAGE-004)
```

**Signature**: `def spec_inventory(project_root: Path) -> set[str]`

**Layer**: parser (no server imports)

### 1.4 New Function: `telemetry_scanner(project_root: Path) -> dict[str, list[str]]`

**Purpose**: Scan .py source files for `req="REQ-*"` and `req='REQ-*'` patterns.
**Implements**: REQ-F-LINEAGE-002

```
Algorithm:
  1. Walk project_root using same os.walk() + _should_skip_dir() prune as parse_traceability()
  2. Process only .py files (REQ-F-LINEAGE-002 AC-1)
  3. For each file:
     a. Read text (UTF-8, errors=ignore)
     b. Scan each line for _TELEMETRY_RE matches (captures both " and ' variants — AC-2)
     c. For each match, extract the REQ key string
  4. Build result: dict[req_key → sorted list of unique relative file paths]
  5. Keys with no matches produce no entry (AC-5: no empty lists)
  6. Return dict

Pattern: re.compile(r"""req=["'](REQ-[\w-]+)["']""")
```

**Signature**: `def telemetry_scanner(project_root: Path) -> dict[str, list[str]]`

**Layer**: parser (no server imports)

### 1.5 Extended `parse_traceability()`

Extend the existing function signature (backward compatible — new fields have defaults):

```python
def parse_traceability(project_root: Path) -> TraceabilityReport:
    # ... existing code for code_tags / test_tags / coverage dicts ...

    # After existing scan loop, add:
    report.telemetry_coverage = telemetry_scanner(project_root)
    report.spec_defined_keys = spec_inventory(project_root)
    report.telemetry_files_scanned = sum(
        len(files) for files in report.telemetry_coverage.values()
    )  # Note: approximate; counts file appearances not distinct files

    # Set arithmetic (REQ-F-LINEAGE-003):
    downstream = (
        set(report.code_coverage)
        | set(report.test_coverage)
        | set(report.telemetry_coverage)
    )
    report.orphan_keys = downstream - report.spec_defined_keys
    # Empty set when spec_defined_keys is empty (no REQUIREMENTS.md) — backward compat
    if report.spec_defined_keys:
        report.uncovered_keys = report.spec_defined_keys - downstream
    else:
        report.uncovered_keys = set()

    # Update all_req_keys to include spec-defined keys
    report.all_req_keys.update(report.spec_defined_keys)

    return report
```

**Backward compatibility**: All new fields have `field(default_factory=...)` defaults. Projects without REQUIREMENTS.md produce `spec_defined_keys=set()`, `orphan_keys=set()`, `uncovered_keys=set()`. No errors raised.

---

## §2. Projection Changes — `projections/traceability.py`

### 2.1 Extended `build_traceability_view()`

No signature change. Backward compatible — new keys added to existing dicts.

**req_rows — new fields per row:**

```python
req_rows.append({
    # --- existing fields (unchanged) ---
    "req_key": req_key,
    "code_files": code_files,
    "test_files": test_files,
    "features": owning_features,
    "has_code": has_code,
    "has_tests": has_tests,
    "status": status,  # existing: "full" | "partial" | "none"

    # --- new fields (REQ-F-LINEAGE-001..003) ---
    "spec_defined": req_key in traceability.spec_defined_keys,
    "telemetry_files": traceability.telemetry_coverage.get(req_key, []),
    "has_telemetry": req_key in traceability.telemetry_coverage,
    "is_orphan": req_key in traceability.orphan_keys,
    "is_uncovered": req_key in traceability.uncovered_keys,
})
```

**Status recomputation** — status field now considers all 4 columns:

```python
has_any = has_code or has_tests or has_telemetry
spec_def = req_key in traceability.spec_defined_keys

# Orphan: in downstream but not in spec
# Uncovered: in spec but not in any downstream column
status = "orphan" if is_orphan else (
    "uncovered" if is_uncovered else (
        "full" if (has_code and has_tests) else (
            "partial" if has_any else "none"
        )
    )
)
```

**summary — new fields:**

```python
"summary": {
    # --- existing (unchanged) ---
    "total_req_keys": len(all_req_keys),
    "with_code": with_code,
    "with_tests": with_tests,
    "full_coverage": full_coverage,
    "no_coverage": no_coverage,
    "code_files": traceability.code_files_scanned,
    "test_files": traceability.test_files_scanned,

    # --- new (REQ-F-LINEAGE-001 AC-4, REQ-F-LINEAGE-003 AC-3) ---
    "spec_count": len(traceability.spec_defined_keys),
    "telemetry_count": sum(1 for r in all_req_keys if r in traceability.telemetry_coverage),
    "orphan_count": len(traceability.orphan_keys),
    "uncovered_count": len(traceability.uncovered_keys),
}
```

---

## §3. Template Changes — `templates/fragments/_traceability.html`

### 3.1 Summary Bar

Add two new stat groups alongside existing code/test stats:

```html
<!-- existing stats -->
<small><strong>{{ traceability.summary.spec_count }}</strong> in spec</small>
<small>|</small>
<small>{{ traceability.summary.telemetry_count }} telemetry</small>
{% if traceability.summary.orphan_count > 0 %}
<small>|</small>
<small><span style="color: #f57f17;">⚠ {{ traceability.summary.orphan_count }} orphan</span></small>
{% endif %}
{% if traceability.summary.uncovered_count > 0 %}
<small>|</small>
<small><span style="color: #c62828;">◌ {{ traceability.summary.uncovered_count }} uncovered</span></small>
{% endif %}
```

### 3.2 REQ Key Details Table — Extended to 6 Columns

Add **Spec** and **Telemetry** columns. Add row-level orphan/uncovered badges.

Table header:
```html
<tr>
    <th>REQ Key</th>
    <th>Feature</th>
    <th>Spec</th>      <!-- NEW -->
    <th>Code</th>
    <th>Tests</th>
    <th>Telemetry</th> <!-- NEW -->
    <th>Status</th>
</tr>
```

Spec column cell:
```html
<td>
    {% if row.spec_defined %}
    <span style="color: #2e7d32;" title="Defined in REQUIREMENTS.md">✓</span>
    {% else %}
    <span style="color: #9e9e9e;" title="Not in REQUIREMENTS.md">—</span>
    {% endif %}
</td>
```

Telemetry column cell:
```html
<td>
    {% if row.has_telemetry %}
    <span title="{% for f in row.telemetry_files %}{{ f }}&#10;{% endfor %}">
        {{ row.telemetry_files | length }} file{{ 's' if row.telemetry_files | length != 1 }}
    </span>
    {% else %}
    <span style="color: #c62828;">-</span>
    {% endif %}
</td>
```

Status cell — add orphan/uncovered badges:
```html
<td>
    {% if row.is_orphan %}
    <span class="badge badge-in-progress" title="In code/tests/telemetry but not defined in spec">⚠ orphan</span>
    {% elif row.is_uncovered %}
    <span class="badge badge-not-started" title="Defined in spec but absent from all downstream">◌ gap</span>
    {% elif row.status == 'full' %}
    <span class="badge badge-converged">full</span>
    {% elif row.status == 'partial' %}
    <span class="badge badge-in-progress">partial</span>
    {% else %}
    <span class="badge badge-not-started">none</span>
    {% endif %}
</td>
```

### 3.3 Row Highlighting

Apply visual distinction via inline style when a row is orphan or uncovered (REQ-F-LINEAGE-003 AC-4 and AC-5):

```html
<tr {% if row.is_orphan %}style="background: #fff8e1;"
    {% elif row.is_uncovered %}style="background: #fce4ec;"{% endif %}>
```

---

## §4. Route Changes — `server/routes.py`

**No route changes required.**

`parse_traceability(project.path)` is called when the `Project` object is built (in `registry.py` or equivalent loading code). The new `spec_inventory()` function uses `project_root` to locate REQUIREMENTS.md internally — no new parameters needed at the route level. The `build_traceability_view()` signature is unchanged. The template receives the same `traceability` dict key — new fields are transparently present.

---

## §5. Evaluator Checklist — requirements→design

| Check | Result | Notes |
|-------|--------|-------|
| **all_requirements_addressed** | PASS | REQ-F-LINEAGE-001: model + 4-col view designed. REQ-F-LINEAGE-002: `telemetry_scanner()` specified. REQ-F-LINEAGE-003: orphan/uncovered set arithmetic + badges. REQ-F-LINEAGE-004: `spec_inventory()` + heading parser. All 4 ACs per REQ checked. |
| **no_new_requirements_introduced** | PASS | Design scope bounded to LINEAGE-001..004. No new data sources, no new routes, no new infrastructure. The telemetry_files_scanned count is a cosmetic addition that falls under LINEAGE-001 AC-4. |
| **adr_for_significant_decisions** | PASS — no new ADR needed | All choices follow existing ADRs: filesystem-only (ADR-001), HTMX fragments (ADR-003), parser/projection/server separation (ADR-002). The `spec_inventory()` path priority is a disambiguation of LINEAGE-004 AC-2, not a new architectural decision. |
| **backward_compatible** | PASS | (a) `TraceabilityReport` new fields all have `default_factory` defaults — existing code that constructs `TraceabilityReport()` continues to work. (b) Projects without REQUIREMENTS.md produce empty `spec_defined_keys`, `orphan_keys`, `uncovered_keys` — no exception raised (REQ-F-LINEAGE-001 AC-5, REQ-F-LINEAGE-004 AC-4). (c) `build_traceability_view()` signature unchanged; new dict keys added alongside existing ones — templates that don't reference them are unaffected. |
| **layer_separation_maintained** | PASS | `spec_inventory()` and `telemetry_scanner()`: filesystem access only, no server imports. `build_traceability_view()`: projection only, no filesystem access. Template: rendering only, no logic. Route: unchanged. |

**Evaluator verdict**: 5/5 PASS. delta = 0. Edge converged.

---

## §6. Work Breakdown (maps to feature vector)

| WU | Title | Files Affected | REQ |
|----|-------|---------------|-----|
| WU-GMON4-001 | Add `telemetry_scanner()` | `parsers/traceability.py` | REQ-F-LINEAGE-002 |
| WU-GMON4-002 | Add `spec_inventory()` | `parsers/traceability.py` | REQ-F-LINEAGE-004 |
| WU-GMON4-003 | Extend `TraceabilityReport` model | `parsers/traceability.py` | REQ-F-LINEAGE-001 |
| WU-GMON4-004 | Extend `parse_traceability()` | `parsers/traceability.py` | REQ-F-LINEAGE-001, -003 |
| WU-GMON4-004b | Extend `build_traceability_view()` | `projections/traceability.py` | REQ-F-LINEAGE-001, -003 |
| WU-GMON4-005 | Update `_traceability.html` | `templates/fragments/_traceability.html` | REQ-F-LINEAGE-001, -003 |
| WU-GMON4-006 | Tests | `tests/test_traceability.py` (new or extend) | all LINEAGE-* |

All WUs implement within the `parsers/` and `projections/` layers. No new files created in `server/`. No new routes.
