# Implements: REQ-F-SCHEMA-DISC-001 (SCHEMA_DISCOVERY Execution — Notebook-Driven)
# Implements: REQ-F-NAMEDCOMP-001 (Named Composition Execution)
"""
SCHEMA_DISCOVERY engine — notebook-driven schema inference from raw datasets.

Implements the SCHEMA_DISCOVERY named composition (ADR-S-026 / named_compositions.yml §6.2):

    BROADCAST(dataset, sample_fn: stratified_sample)
    ∘ iterate(each_sample, evaluators: [structure_detect, type_infer, null_rate, cardinality])
    ∘ FOLD(sample_schemas, merge_fn: schema_unifier)
    ∘ REVIEW(unified_schema, evaluator: F_H)   ← caller's responsibility
    → schema_document {fields, types, nullability, cardinality, examples, open_questions}

The REVIEW step (F_H) is NOT performed here — callers receive a SchemaDocument
and present it to the human evaluator.  This module is purely F_D: deterministic
schema inference executed via a Jupyter notebook that the caller can inspect,
annotate, and preserve as a lineage artifact.

Dynamic intent vector flow (the show-off):
    design edge detects missing_schema
    → intent_raised { gap_type: "missing_schema", composition: SCHEMA_DISCOVERY }
    → gap_type_dispatch: SCHEMA_DISCOVERY { dataset: …, notebook_env: … }
    → run_schema_discovery(config)          ← THIS MODULE
    → SchemaDocument produced
    → write_schema_to_design_context()      ← fold-back to parent feature
    → design edge resumes with schema defined

Lineage: every discovered schema carries notebook_path — the executed .ipynb
that is the full audit trail of how each field was classified.

Wire count (ADR-S-026 §6.2): SCHEMA_DISCOVERY : 1 → 1 (dataset → schema_document)
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


# ── Types ─────────────────────────────────────────────────────────────────────

class FieldType(str, Enum):
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    UNKNOWN = "unknown"


class DiscoveryStatus(str, Enum):
    CONVERGED = "converged"
    EXECUTION_FAILED = "execution_failed"
    PARSE_FAILED = "parse_failed"
    TIMEOUT = "timeout"


# ── Data Classes ───────────────────────────────────────────────────────────────

@dataclass
class FieldSchema:
    """Single column's inferred schema — output of the iterate step per field."""
    name: str
    inferred_type: FieldType
    nullable: bool               # True if any nulls observed in sample
    null_rate: float             # 0.0–1.0 fraction of nulls in sample
    cardinality: Optional[int]   # None = high-cardinality (> HIGH_CARDINALITY_THRESHOLD)
    sample_values: list[str]     # up to 3 representative non-null values as strings
    open_questions: list[str]    # field-level flags for the F_H reviewer


@dataclass
class SchemaDocument:
    """Output of SCHEMA_DISCOVERY — the fold-back payload for parent feature design."""
    dataset: str                 # original dataset filename
    row_count_sampled: int
    row_count_total: Optional[int]
    fields: list[FieldSchema]
    open_questions: list[str]    # dataset-level flags
    notebook_path: Optional[str] # lineage artifact — path to executed .ipynb
    generated_at: str            # ISO timestamp


@dataclass
class DiscoveryConfig:
    """Input configuration for SCHEMA_DISCOVERY — the bindings from the composition."""
    dataset_path: Path
    sample_size: int = 1000
    stratify_by: Optional[str] = None   # column name for stratified sampling; None = random
    notebook_env: str = "local"          # "local" or a URI (future: remote kernels)
    output_dir: Optional[Path] = None   # where to write notebook; None = tempdir
    timeout_seconds: int = 120


@dataclass
class DiscoveryResult:
    """Full output of run_schema_discovery() — ready for F_H REVIEW."""
    config: DiscoveryConfig
    status: DiscoveryStatus
    schema: Optional[SchemaDocument]
    notebook_path: Optional[Path]   # None only if generation itself failed
    error: Optional[str] = None

    @property
    def converged(self) -> bool:
        return self.status == DiscoveryStatus.CONVERGED


# ── Constants ──────────────────────────────────────────────────────────────────

HIGH_CARDINALITY_THRESHOLD = 50  # unique values above this → cardinality=None (ID-like)
NULL_RATE_WARNING_THRESHOLD = 0.5
LOW_CARDINALITY_ENUM_THRESHOLD = 10  # string with ≤ this many unique values → enum candidate
_SCHEMA_BEGIN = "SCHEMA_DOCUMENT_JSON_BEGIN"
_SCHEMA_END = "SCHEMA_DOCUMENT_JSON_END"


# ── Step 1: BROADCAST — generate exploration notebook ─────────────────────────

def generate_exploration_notebook(config: DiscoveryConfig, output_path: Path) -> Path:
    """Generate a Jupyter notebook that profiles config.dataset_path.

    The notebook embeds the dataset path and sample_size as literals so it is
    fully self-contained and re-runnable.  Cell 5 prints SCHEMA_DOCUMENT_JSON_BEGIN …
    SCHEMA_DOCUMENT_JSON_END so extract_schema_from_notebook() can parse the output
    without fragile heuristics.
    """
    try:
        import nbformat
        from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook
    except ImportError as exc:
        raise RuntimeError(
            "nbformat is required for notebook generation: pip install nbformat nbconvert"
        ) from exc

    suffix = config.dataset_path.suffix.lower()
    if suffix == ".parquet":
        load_stmt = f"df = pd.read_parquet(r'{config.dataset_path}')"
    elif suffix == ".json":
        load_stmt = f"df = pd.read_json(r'{config.dataset_path}')"
    else:  # .csv and everything else
        load_stmt = f"df = pd.read_csv(r'{config.dataset_path}')"

    nb = new_notebook()
    nb.cells = [
        # ── Intro ──────────────────────────────────────────────────────────────
        new_markdown_cell(
            "# SCHEMA_DISCOVERY — Exploration Notebook\n\n"
            "Generated by `genesis schema_discovery` engine.  "
            "Implements ADR-S-026 §6.2 `SCHEMA_DISCOVERY` named composition.\n\n"
            "**Do not edit cells 1–5 manually** — they are the machine-readable contract "
            "between this notebook and the schema_discovery engine."
        ),

        # ── Cell 1: Load ───────────────────────────────────────────────────────
        new_code_cell(f"""\
# Cell 1: Load dataset  (BROADCAST source)
import json
import warnings
import pandas as pd
warnings.filterwarnings('ignore')

{load_stmt}
row_count_total = len(df)
print(f"Loaded {{row_count_total}} rows × {{len(df.columns)}} columns")
print(f"Columns: {{list(df.columns)}}")
"""),

        # ── Cell 2: Sample ─────────────────────────────────────────────────────
        new_code_cell(f"""\
# Cell 2: Stratified sample  (BROADCAST — stratified_sample)
_sample_size = min({config.sample_size}, len(df))
{"_strat_col = " + repr(config.stratify_by) if config.stratify_by else "_strat_col = None"}

if _strat_col and _strat_col in df.columns:
    # Stratified: proportional sample per stratum
    sample = (
        df.groupby(_strat_col, group_keys=False)
          .apply(lambda g: g.sample(n=max(1, int(len(g) / len(df) * _sample_size)),
                                    random_state=42))
          .head(_sample_size)
    )
else:
    sample = df.sample(n=_sample_size, random_state=42)

print(f"Sample: {{len(sample)}} rows (stratify_by={{_strat_col!r}})")
"""),

        # ── Cell 3: Profile columns ────────────────────────────────────────────
        new_code_cell(f"""\
# Cell 3: Per-column profiling  (iterate — structure_detect, type_infer, null_rate, cardinality)
_HIGH_CARD = {HIGH_CARDINALITY_THRESHOLD}
_NULL_WARN  = {NULL_RATE_WARNING_THRESHOLD}
_ENUM_MAX   = {LOW_CARDINALITY_ENUM_THRESHOLD}

def _infer_type(series):
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    if pd.api.types.is_float_dtype(series):
        return "float"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    non_null = series.dropna().head(10)
    if len(non_null) > 0:
        try:
            pd.to_datetime(non_null, infer_datetime_format=True)
            return "datetime"
        except (ValueError, TypeError):
            pass
    return "string"

field_schemas = []
for _col in sample.columns:
    _s         = sample[_col]
    _null_rate = float(_s.isna().mean())
    _itype     = _infer_type(_s)
    _card      = int(_s.nunique())
    # High-cardinality: exceeds absolute threshold OR ALL values are unique (ID pattern)
    _card_val  = None if (_card > _HIGH_CARD or _card == len(sample)) else _card
    _samples   = [str(v) for v in _s.dropna().head(3).tolist()]

    _questions = []
    if _null_rate > _NULL_WARN:
        _questions.append(
            f"high null rate ({{_null_rate:.0%}}) — is this expected?")
    if _itype == "string" and _card <= _ENUM_MAX and len(_s.dropna()) > 0:
        _vals = sorted(_s.dropna().unique().tolist())
        _questions.append(
            f"low-cardinality string ({{_card}} values: {{_vals}}) — consider enum type")
    if _itype == "float" and _null_rate == 0.0:
        _head = _s.dropna().head(20)
        if all(float(v) == int(float(v)) for v in _head if pd.notna(v)):
            _questions.append(
                "float column contains only whole numbers — consider integer type")

    field_schemas.append({{
        "name":          _col,
        "inferred_type": _itype,
        "nullable":      _null_rate > 0.0,
        "null_rate":     round(_null_rate, 3),
        "cardinality":   _card_val,
        "sample_values": _samples,
        "open_questions": _questions,
    }})

print(f"Profiled {{len(field_schemas)}} columns")
"""),

        # ── Cell 4: FOLD ───────────────────────────────────────────────────────
        new_code_cell("""\
# Cell 4: FOLD — merge sample schemas into unified schema_document
from datetime import datetime, timezone as _tz

_dataset_qs = []
_high_null = [f["name"] for f in field_schemas if f["null_rate"] > 0.5]
if _high_null:
    _dataset_qs.append(
        f"{len(_high_null)} column(s) have >50% null rate: {', '.join(_high_null)}")

_schema_doc = {
    "row_count_sampled": len(sample),
    "row_count_total":   row_count_total,
    "fields":            field_schemas,
    "open_questions":    _dataset_qs,
    "generated_at":      datetime.now(_tz.utc).isoformat(),
}
print(f"Unified: {len(field_schemas)} fields, {len(_dataset_qs)} dataset-level questions")
"""),

        # ── Cell 5: Output schema (machine-readable marker) ────────────────────
        new_code_cell(f"""\
# Cell 5: Output schema as JSON  (DO NOT MODIFY — parsed by schema_discovery engine)
print("{_SCHEMA_BEGIN}")
print(json.dumps(_schema_doc, indent=2, default=str))
print("{_SCHEMA_END}")
"""),
    ]

    with open(output_path, "w") as fh:
        nbformat.write(nb, fh)
    return output_path


# ── Step 2: Execute notebook ───────────────────────────────────────────────────

def execute_notebook(notebook_path: Path, timeout: int = 120) -> Path:
    """Execute the exploration notebook in-place via jupyter nbconvert.

    Returns the path of the executed notebook (input path with '_executed' suffix).
    Raises RuntimeError if nbconvert returns non-zero exit code.
    Raises subprocess.TimeoutExpired if execution exceeds timeout + 30s grace.
    """
    executed_path = notebook_path.with_stem(notebook_path.stem + "_executed")
    result = subprocess.run(
        [
            "jupyter", "nbconvert",
            "--to", "notebook",
            "--execute",
            f"--ExecutePreprocessor.timeout={timeout}",
            "--output", str(executed_path),
            str(notebook_path),
        ],
        capture_output=True,
        text=True,
        timeout=timeout + 30,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"nbconvert execution failed (exit {result.returncode}):\n{result.stderr[-1000:]}"
        )
    return executed_path


# ── Step 3: FOLD — extract SchemaDocument from executed notebook ───────────────

def extract_schema_from_notebook(executed_path: Path, dataset_name: str) -> SchemaDocument:
    """Parse the executed notebook's cell outputs to produce a SchemaDocument.

    Locates the SCHEMA_DOCUMENT_JSON_BEGIN … SCHEMA_DOCUMENT_JSON_END block
    in Cell 5's stdout and deserialises it.  Raises ValueError if the markers
    are not found (notebook execution did not reach Cell 5).
    """
    try:
        import nbformat
    except ImportError as exc:
        raise RuntimeError("nbformat required: pip install nbformat") from exc

    nb = nbformat.read(str(executed_path), as_version=4)

    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        for output in cell.get("outputs", []):
            text = output.get("text", "") or ""
            if _SCHEMA_BEGIN not in text:
                continue
            start = text.find(_SCHEMA_BEGIN) + len(_SCHEMA_BEGIN) + 1
            end = text.find(_SCHEMA_END)
            if end <= start:
                continue
            data = json.loads(text[start:end])
            fields = [
                FieldSchema(
                    name=f["name"],
                    inferred_type=FieldType(f["inferred_type"]),
                    nullable=f["nullable"],
                    null_rate=f["null_rate"],
                    cardinality=f["cardinality"],
                    sample_values=f["sample_values"],
                    open_questions=f["open_questions"],
                )
                for f in data["fields"]
            ]
            return SchemaDocument(
                dataset=dataset_name,
                row_count_sampled=data["row_count_sampled"],
                row_count_total=data.get("row_count_total"),
                fields=fields,
                open_questions=data.get("open_questions", []),
                notebook_path=str(executed_path),
                generated_at=data.get("generated_at", ""),
            )

    raise ValueError(
        f"Schema markers ({_SCHEMA_BEGIN} / {_SCHEMA_END}) not found in "
        f"{executed_path}.  Notebook may not have completed Cell 5."
    )


# ── Fold-back ─────────────────────────────────────────────────────────────────

def write_schema_to_design_context(schema: SchemaDocument, design_context_dir: Path) -> Path:
    """Fold-back: write the approved SchemaDocument to the parent feature's design context.

    Creates (or overwrites) schema.json in design_context_dir.  The parent
    feature's requirements→design edge evaluator checks for this file to resolve
    the missing_schema gap (gap_type_dispatch.missing_schema → SCHEMA_DISCOVERY).

    Idempotent: overwriting with an updated schema is safe and intentional.
    """
    design_context_dir.mkdir(parents=True, exist_ok=True)
    schema_path = design_context_dir / "schema.json"

    out: dict = {
        "dataset": schema.dataset,
        "row_count_sampled": schema.row_count_sampled,
        "row_count_total": schema.row_count_total,
        "generated_at": schema.generated_at,
        "notebook_lineage": schema.notebook_path,
        "fields": [
            {
                "name": f.name,
                "type": f.inferred_type.value,
                "nullable": f.nullable,
                "null_rate": f.null_rate,
                "cardinality": f.cardinality,
                "sample_values": f.sample_values,
                "open_questions": f.open_questions,
            }
            for f in schema.fields
        ],
        "open_questions": schema.open_questions,
    }
    schema_path.write_text(json.dumps(out, indent=2))
    return schema_path


# ── Main entry point ──────────────────────────────────────────────────────────

def run_schema_discovery(config: DiscoveryConfig) -> DiscoveryResult:
    """Execute the full SCHEMA_DISCOVERY macro for a dataset.

    Implements:  BROADCAST ∘ iterate ∘ FOLD  (the F_D steps).
    The caller is responsible for the REVIEW step (F_H gate) — present
    schema.fields and schema.open_questions to the human evaluator, then
    call write_schema_to_design_context() to complete the fold-back.

    Returns DiscoveryResult.converged == True when a valid SchemaDocument
    was produced.  On failure the result carries the error and partial
    notebook_path for debugging.
    """
    output_dir = config.output_dir or Path(tempfile.mkdtemp(prefix="schema_disc_"))
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = config.dataset_path.stem
    notebook_path = output_dir / f"schema_discovery_{stem}.ipynb"

    try:
        generate_exploration_notebook(config, notebook_path)
        executed_path = execute_notebook(notebook_path, timeout=config.timeout_seconds)
        schema = extract_schema_from_notebook(executed_path, config.dataset_path.name)
        return DiscoveryResult(
            config=config,
            status=DiscoveryStatus.CONVERGED,
            schema=schema,
            notebook_path=executed_path,
        )

    except subprocess.TimeoutExpired:
        return DiscoveryResult(
            config=config,
            status=DiscoveryStatus.TIMEOUT,
            schema=None,
            notebook_path=notebook_path if notebook_path.exists() else None,
            error=f"Notebook execution timed out after {config.timeout_seconds}s",
        )
    except ValueError as exc:
        return DiscoveryResult(
            config=config,
            status=DiscoveryStatus.PARSE_FAILED,
            schema=None,
            notebook_path=notebook_path if notebook_path.exists() else None,
            error=str(exc),
        )
    except Exception as exc:
        return DiscoveryResult(
            config=config,
            status=DiscoveryStatus.EXECUTION_FAILED,
            schema=None,
            notebook_path=notebook_path if notebook_path.exists() else None,
            error=str(exc),
        )
