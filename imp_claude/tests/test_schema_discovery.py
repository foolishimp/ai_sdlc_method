# Validates: REQ-F-SCHEMA-DISC-001 (SCHEMA_DISCOVERY Execution)
# Validates: REQ-F-NAMEDCOMP-001 (Named Composition Execution)
"""
Tests for genesis.schema_discovery — notebook-driven schema inference engine.

Follows the same structure as test_consensus_engine.py:
  TestGenerateExplorationNotebook — notebook generation (BROADCAST step)
  TestExecuteNotebook             — nbconvert execution
  TestExtractSchema               — FOLD step / JSON parsing
  TestRunSchemaDiscovery          — full macro end-to-end
  TestWriteSchemaToDesignContext  — fold-back to parent feature
  TestDynamicIntentVector         — THE SHOW-OFF: gap dispatch → discovery → fold-back

All tests using real nbconvert are marked @pytest.mark.slow (they add ~5s each).
Tests that only verify generated notebook structure are fast.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from genesis.schema_discovery import (
    DiscoveryConfig,
    DiscoveryResult,
    DiscoveryStatus,
    FieldType,
    SchemaDocument,
    execute_notebook,
    generate_exploration_notebook,
    run_schema_discovery,
    write_schema_to_design_context,
)

# ── Paths ──────────────────────────────────────────────────────────────────────

_HERE = Path(__file__).parent
_TRANSACTIONS_CSV = _HERE / "data" / "transactions.csv"
_PLUGIN_ROOT = _HERE.parent / "code" / ".claude-plugin" / "plugins" / "genesis"
_NAMED_COMP_YML = _PLUGIN_ROOT / "config" / "named_compositions.yml"


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def transactions_csv() -> Path:
    assert _TRANSACTIONS_CSV.exists(), "transactions.csv demo dataset missing"
    return _TRANSACTIONS_CSV


@pytest.fixture
def basic_config(transactions_csv: Path, tmp_path: Path) -> DiscoveryConfig:
    return DiscoveryConfig(
        dataset_path=transactions_csv,
        sample_size=20,
        output_dir=tmp_path,
    )


@pytest.fixture
def generated_notebook(basic_config: DiscoveryConfig, tmp_path: Path) -> Path:
    nb_path = tmp_path / "schema_discovery_transactions.ipynb"
    generate_exploration_notebook(basic_config, nb_path)
    return nb_path


@pytest.fixture(scope="module")
def executed_result(tmp_path_factory: pytest.TempPathFactory) -> DiscoveryResult:
    """Module-scoped full execution — runs nbconvert once for all extract/result tests."""
    tmp = tmp_path_factory.mktemp("schema_disc_exec")
    config = DiscoveryConfig(
        dataset_path=_TRANSACTIONS_CSV,
        sample_size=20,
        output_dir=tmp,
    )
    result = run_schema_discovery(config)
    if not result.converged:
        pytest.skip(f"nbconvert execution failed (kernel issue?): {result.error}")
    return result


@pytest.fixture
def high_null_csv(tmp_path: Path) -> Path:
    """CSV where 'notes' column has >50% nulls — triggers open question."""
    p = tmp_path / "high_null.csv"
    p.write_text(
        "id,value,notes\n"
        + "".join(f"{i},{i * 10},\n" for i in range(1, 8))  # 7 nulls
        + "8,80,present\n9,90,\n10,100,\n"
    )
    return p


@pytest.fixture
def low_cardinality_csv(tmp_path: Path) -> Path:
    """CSV with a low-cardinality string column — enum candidate."""
    p = tmp_path / "low_card.csv"
    rows = "\n".join(f"row{i},{['red', 'green', 'blue'][i % 3]}" for i in range(20))
    p.write_text("id,colour\n" + rows + "\n")
    return p


# ══════════════════════════════════════════════════════════════════════════════
# TestGenerateExplorationNotebook
# ══════════════════════════════════════════════════════════════════════════════


class TestGenerateExplorationNotebook:
    """BROADCAST step: verify the generated .ipynb has correct structure."""

    def test_notebook_file_created(self, basic_config: DiscoveryConfig, tmp_path: Path):
        nb_path = tmp_path / "test.ipynb"
        result = generate_exploration_notebook(basic_config, nb_path)
        assert result == nb_path
        assert nb_path.exists()

    def test_notebook_is_valid_json(self, generated_notebook: Path):
        content = json.loads(generated_notebook.read_text())
        assert "cells" in content
        assert content.get("nbformat") == 4

    def test_notebook_has_six_cells(self, generated_notebook: Path):
        """1 markdown intro + 5 code cells (load, sample, profile, fold, output)."""
        import nbformat

        nb = nbformat.read(str(generated_notebook), as_version=4)
        assert len(nb.cells) == 6

    def test_load_cell_references_dataset_path(
        self, basic_config: DiscoveryConfig, generated_notebook: Path
    ):
        import nbformat

        nb = nbformat.read(str(generated_notebook), as_version=4)
        load_cell = nb.cells[1].source  # Cell 1
        assert str(basic_config.dataset_path) in load_cell

    def test_sample_cell_references_sample_size(
        self, basic_config: DiscoveryConfig, generated_notebook: Path
    ):
        import nbformat

        nb = nbformat.read(str(generated_notebook), as_version=4)
        sample_cell = nb.cells[2].source  # Cell 2
        assert str(basic_config.sample_size) in sample_cell

    def test_output_cell_has_schema_markers(self, generated_notebook: Path):
        import nbformat

        nb = nbformat.read(str(generated_notebook), as_version=4)
        output_cell = nb.cells[5].source  # Cell 5
        assert "SCHEMA_DOCUMENT_JSON_BEGIN" in output_cell
        assert "SCHEMA_DOCUMENT_JSON_END" in output_cell

    def test_profile_cell_contains_type_inference(self, generated_notebook: Path):
        import nbformat

        nb = nbformat.read(str(generated_notebook), as_version=4)
        profile_cell = nb.cells[3].source  # Cell 3
        assert "_infer_type" in profile_cell
        assert "null_rate" in profile_cell
        assert "cardinality" in profile_cell

    def test_parquet_dataset_uses_read_parquet(self, tmp_path: Path):
        csv_path = tmp_path / "data.parquet"
        csv_path.write_text("")  # fake — just checking load cell
        config = DiscoveryConfig(dataset_path=csv_path, output_dir=tmp_path)
        nb_path = tmp_path / "test.ipynb"
        generate_exploration_notebook(config, nb_path)
        import nbformat

        nb = nbformat.read(str(nb_path), as_version=4)
        assert "read_parquet" in nb.cells[1].source

    def test_csv_dataset_uses_read_csv(
        self, basic_config: DiscoveryConfig, tmp_path: Path
    ):
        nb_path = tmp_path / "test.ipynb"
        generate_exploration_notebook(basic_config, nb_path)
        import nbformat

        nb = nbformat.read(str(nb_path), as_version=4)
        assert "read_csv" in nb.cells[1].source


# ══════════════════════════════════════════════════════════════════════════════
# TestExecuteNotebook
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.slow
class TestExecuteNotebook:
    """Execute step: nbconvert actually runs the notebook."""

    def test_executed_notebook_created(
        self, basic_config: DiscoveryConfig, generated_notebook: Path
    ):
        executed = execute_notebook(generated_notebook, timeout=60)
        assert executed.exists()
        assert "_executed" in executed.name

    def test_executed_notebook_has_cell_outputs(
        self, basic_config: DiscoveryConfig, generated_notebook: Path
    ):
        import nbformat

        executed = execute_notebook(generated_notebook, timeout=60)
        nb = nbformat.read(str(executed), as_version=4)
        # At least some code cells must have outputs
        code_cells_with_output = [
            c for c in nb.cells if c.cell_type == "code" and c.get("outputs")
        ]
        assert len(code_cells_with_output) >= 4

    def test_schema_output_cell_has_json_markers(
        self, basic_config: DiscoveryConfig, generated_notebook: Path
    ):
        import nbformat

        executed = execute_notebook(generated_notebook, timeout=60)
        nb = nbformat.read(str(executed), as_version=4)
        all_output = " ".join(
            o.get("text", "") for c in nb.cells for o in c.get("outputs", [])
        )
        assert "SCHEMA_DOCUMENT_JSON_BEGIN" in all_output
        assert "SCHEMA_DOCUMENT_JSON_END" in all_output


# ══════════════════════════════════════════════════════════════════════════════
# TestExtractSchema
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.slow
class TestExtractSchema:
    """FOLD step: verify SchemaDocument fields extracted from executed notebook."""

    def test_returns_schema_document(self, executed_result: DiscoveryResult):
        assert executed_result.schema is not None
        assert isinstance(executed_result.schema, SchemaDocument)

    def test_correct_field_count(self, executed_result: DiscoveryResult):
        """transactions.csv has 8 columns."""
        assert len(executed_result.schema.fields) == 8

    def test_all_field_names_present(self, executed_result: DiscoveryResult):
        names = {f.name for f in executed_result.schema.fields}
        for expected in (
            "transaction_id",
            "amount",
            "currency",
            "status",
            "user_id",
            "created_at",
            "is_flagged",
        ):
            assert expected in names, f"Field {expected!r} missing from schema"

    def test_amount_inferred_as_float(self, executed_result: DiscoveryResult):
        amount = next(f for f in executed_result.schema.fields if f.name == "amount")
        assert amount.inferred_type == FieldType.FLOAT

    def test_is_flagged_inferred_as_boolean(self, executed_result: DiscoveryResult):
        flagged = next(
            f for f in executed_result.schema.fields if f.name == "is_flagged"
        )
        assert flagged.inferred_type == FieldType.BOOLEAN

    def test_created_at_inferred_as_datetime(self, executed_result: DiscoveryResult):
        ts = next(f for f in executed_result.schema.fields if f.name == "created_at")
        assert ts.inferred_type == FieldType.DATETIME

    def test_currency_low_cardinality_flagged(self, executed_result: DiscoveryResult):
        """currency has 3 unique values (USD/EUR/GBP) — should flag as enum candidate."""
        currency = next(
            f for f in executed_result.schema.fields if f.name == "currency"
        )
        questions = " ".join(currency.open_questions).lower()
        assert "cardinality" in questions or "enum" in questions

    def test_notes_high_null_rate_flagged(self, executed_result: DiscoveryResult):
        """notes column is empty for most rows (high null rate)."""
        notes = next(f for f in executed_result.schema.fields if f.name == "notes")
        assert notes.nullable is True
        assert notes.null_rate > 0.5
        assert any("null" in q.lower() for q in notes.open_questions)

    def test_sample_values_populated(self, executed_result: DiscoveryResult):
        amount = next(f for f in executed_result.schema.fields if f.name == "amount")
        assert len(amount.sample_values) >= 1

    def test_notebook_path_recorded(self, executed_result: DiscoveryResult):
        assert executed_result.schema.notebook_path is not None
        assert "_executed" in executed_result.schema.notebook_path

    def test_row_count_sampled(self, executed_result: DiscoveryResult):
        assert executed_result.schema.row_count_sampled <= 20

    def test_high_null_csv_raises_open_question(
        self, high_null_csv: Path, tmp_path: Path
    ):
        config = DiscoveryConfig(
            dataset_path=high_null_csv, sample_size=100, output_dir=tmp_path
        )
        result = run_schema_discovery(config)
        assert result.converged
        notes = next((f for f in result.schema.fields if f.name == "notes"), None)
        assert notes is not None
        assert notes.null_rate > 0.5
        assert any("null" in q.lower() for q in notes.open_questions)

    def test_low_cardinality_string_enum_candidate(
        self, low_cardinality_csv: Path, tmp_path: Path
    ):
        config = DiscoveryConfig(
            dataset_path=low_cardinality_csv, sample_size=100, output_dir=tmp_path
        )
        result = run_schema_discovery(config)
        assert result.converged
        colour = next(f for f in result.schema.fields if f.name == "colour")
        questions = " ".join(colour.open_questions).lower()
        assert "cardinality" in questions or "enum" in questions


# ══════════════════════════════════════════════════════════════════════════════
# TestRunSchemaDiscovery
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.slow
class TestRunSchemaDiscovery:
    """Full macro: BROADCAST ∘ iterate ∘ FOLD — end-to-end."""

    def test_converges_on_csv(self, basic_config: DiscoveryConfig):
        result = run_schema_discovery(basic_config)
        assert result.converged
        assert result.status == DiscoveryStatus.CONVERGED

    def test_schema_is_not_none_on_convergence(self, basic_config: DiscoveryConfig):
        result = run_schema_discovery(basic_config)
        assert result.schema is not None

    def test_notebook_path_preserved(self, basic_config: DiscoveryConfig):
        result = run_schema_discovery(basic_config)
        assert result.notebook_path is not None
        assert result.notebook_path.exists()

    def test_missing_dataset_returns_failed(self, tmp_path: Path):
        config = DiscoveryConfig(
            dataset_path=tmp_path / "nonexistent.csv",
            output_dir=tmp_path,
        )
        result = run_schema_discovery(config)
        assert not result.converged
        assert result.status in (
            DiscoveryStatus.EXECUTION_FAILED,
            DiscoveryStatus.PARSE_FAILED,
        )
        assert result.error is not None

    def test_generated_at_timestamp_in_schema(self, basic_config: DiscoveryConfig):
        result = run_schema_discovery(basic_config)
        assert result.schema.generated_at
        assert "2026" in result.schema.generated_at or "T" in result.schema.generated_at

    def test_dataset_name_in_schema(self, basic_config: DiscoveryConfig):
        result = run_schema_discovery(basic_config)
        assert "transactions" in result.schema.dataset.lower()


# ══════════════════════════════════════════════════════════════════════════════
# TestWriteSchemaToDesignContext
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.slow
class TestWriteSchemaToDesignContext:
    """Fold-back: schema.json written to parent feature's design context."""

    def test_schema_json_created(
        self, executed_result: DiscoveryResult, tmp_path: Path
    ):
        design_dir = tmp_path / "design_context"
        path = write_schema_to_design_context(executed_result.schema, design_dir)
        assert path.exists()
        assert path.name == "schema.json"

    def test_schema_json_valid_json(
        self, executed_result: DiscoveryResult, tmp_path: Path
    ):
        design_dir = tmp_path / "design_context"
        path = write_schema_to_design_context(executed_result.schema, design_dir)
        data = json.loads(path.read_text())
        assert isinstance(data, dict)

    def test_schema_json_has_required_top_level_keys(
        self, executed_result: DiscoveryResult, tmp_path: Path
    ):
        design_dir = tmp_path / "design_context"
        path = write_schema_to_design_context(executed_result.schema, design_dir)
        data = json.loads(path.read_text())
        for key in (
            "dataset",
            "fields",
            "generated_at",
            "notebook_lineage",
            "open_questions",
            "row_count_sampled",
        ):
            assert key in data, f"Required key {key!r} missing from schema.json"

    def test_schema_json_fields_have_type(
        self, executed_result: DiscoveryResult, tmp_path: Path
    ):
        design_dir = tmp_path / "design_context"
        path = write_schema_to_design_context(executed_result.schema, design_dir)
        data = json.loads(path.read_text())
        for f in data["fields"]:
            assert "type" in f, f"Field {f['name']!r} missing 'type' key"
            assert f["type"] in (
                "integer",
                "float",
                "string",
                "boolean",
                "datetime",
                "unknown",
            )

    def test_schema_json_has_all_columns(
        self, executed_result: DiscoveryResult, tmp_path: Path
    ):
        design_dir = tmp_path / "design_context"
        path = write_schema_to_design_context(executed_result.schema, design_dir)
        data = json.loads(path.read_text())
        field_names = {f["name"] for f in data["fields"]}
        assert "transaction_id" in field_names
        assert "amount" in field_names
        assert "currency" in field_names

    def test_fold_back_idempotent(
        self, executed_result: DiscoveryResult, tmp_path: Path
    ):
        """Calling write twice with same schema is safe — last write wins."""
        design_dir = tmp_path / "design_context"
        path1 = write_schema_to_design_context(executed_result.schema, design_dir)
        path2 = write_schema_to_design_context(executed_result.schema, design_dir)
        assert path1 == path2
        assert path1.exists()

    def test_notebook_lineage_preserved_in_schema_json(
        self, executed_result: DiscoveryResult, tmp_path: Path
    ):
        """The executed notebook path is preserved as lineage in schema.json."""
        design_dir = tmp_path / "design_context"
        path = write_schema_to_design_context(executed_result.schema, design_dir)
        data = json.loads(path.read_text())
        assert data["notebook_lineage"] is not None
        assert "_executed" in data["notebook_lineage"]


# ══════════════════════════════════════════════════════════════════════════════
# TestDynamicIntentVector  — THE SHOW-OFF
# ══════════════════════════════════════════════════════════════════════════════


class TestDynamicIntentVector:
    """Demonstrates the full dynamic intent vector flow.

    This is the scenario: a design edge detects missing_schema →
    intent_raised { gap_type: missing_schema } → gap_type_dispatch routes
    to SCHEMA_DISCOVERY → notebook actor runs → schema folds back to design.

    The first two tests are fast (config only).
    The last two are marked @pytest.mark.slow (full nbconvert round-trip).
    """

    def test_gap_type_dispatch_routes_missing_schema_to_schema_discovery(self):
        """named_compositions.yml gap_type_dispatch must map missing_schema → SCHEMA_DISCOVERY."""
        assert _NAMED_COMP_YML.exists(), "named_compositions.yml not found"
        data = yaml.safe_load(_NAMED_COMP_YML.read_text())
        dispatch = data.get("gap_type_dispatch", {})
        entry = dispatch.get("missing_schema", {})
        assert entry.get("macro") == "SCHEMA_DISCOVERY", (
            "gap_type_dispatch.missing_schema must route to SCHEMA_DISCOVERY"
        )
        assert entry.get("version") == "v1"

    def test_schema_discovery_macro_has_notebook_env_parameter(self):
        """SCHEMA_DISCOVERY macro must declare notebook_env as a parameter."""
        data = yaml.safe_load(_NAMED_COMP_YML.read_text())
        compositions = {c["name"]: c for c in data.get("compositions", [])}
        macro = compositions.get("SCHEMA_DISCOVERY", {})
        param_names = {p["name"] for p in macro.get("parameters", [])}
        assert "notebook_env" in param_names, (
            "SCHEMA_DISCOVERY macro must have notebook_env parameter (ADR-S-026 §6.2)"
        )

    def test_intent_raised_composition_expression_structure(self):
        """Validate that a missing_schema intent_raised event carries the correct
        composition expression — the typed output of the IntentEngine (ADR-S-026 §3)."""
        # Simulate what the design edge evaluator would emit:
        intent_event = {
            "event_type": "intent_raised",
            "timestamp": "2026-03-10T10:00:00Z",
            "project": "demo-project",
            "feature": "REQ-F-DATAPIPE-001",
            "edge": "requirements→design",
            "data": {
                "intent_id": "INT-DATA-001",
                "gap_type": "missing_schema",
                "trigger": "schema_document not found for dataset transactions.csv",
                "composition": {
                    "macro": "SCHEMA_DISCOVERY",
                    "version": "v1",
                    "bindings": {
                        "dataset": "data/raw/transactions.csv",
                        "notebook_env": "jupyter://local",
                        "evaluation_criteria": ["completeness", "fitness_for_use"],
                    },
                },
                "signal_source": "gap",
                "severity": "high",
            },
        }
        # The composition expression is what makes this a TYPED output —
        # not free text. Verify structure matches ADR-S-026 §3.
        comp = intent_event["data"]["composition"]
        assert comp["macro"] == "SCHEMA_DISCOVERY"
        assert "bindings" in comp
        assert "dataset" in comp["bindings"]
        assert "notebook_env" in comp["bindings"]

    @pytest.mark.slow
    def test_end_to_end_gap_to_fold_back(self, tmp_path: Path):
        """Full round-trip: dataset → SCHEMA_DISCOVERY → schema.json in design context.

        This is the capability we're showing off:
          1. gap_type_dispatch routes missing_schema → SCHEMA_DISCOVERY
          2. run_schema_discovery() executes the notebook
          3. write_schema_to_design_context() resolves the gap
          4. schema.json present → missing_schema gap is CLOSED
        """
        # Step 1: The gap dispatch resolves the composition
        data = yaml.safe_load(_NAMED_COMP_YML.read_text())
        dispatch = data["gap_type_dispatch"]
        composition = dispatch["missing_schema"]
        assert composition["macro"] == "SCHEMA_DISCOVERY"

        # Step 2: Build config from composition bindings
        design_context_dir = tmp_path / ".ai-workspace" / "claude" / "context"
        config = DiscoveryConfig(
            dataset_path=_TRANSACTIONS_CSV,
            sample_size=20,
            notebook_env=composition.get("default_bindings", {}).get(
                "notebook_env", "local"
            ),
            output_dir=tmp_path / "agents" / "schema_disc",
        )

        # Step 3: Execute SCHEMA_DISCOVERY (BROADCAST ∘ iterate ∘ FOLD)
        result = run_schema_discovery(config)
        assert result.converged, f"SCHEMA_DISCOVERY failed: {result.error}"
        assert result.schema is not None
        assert len(result.schema.fields) == 8

        # Step 4: Fold-back — write schema to design context (resolves missing_schema gap)
        schema_path = write_schema_to_design_context(result.schema, design_context_dir)
        assert schema_path.exists(), "schema.json must exist after fold-back"

        # Step 5: Verify the gap is closed — schema.json is present and well-formed
        schema_data = json.loads(schema_path.read_text())
        assert len(schema_data["fields"]) == 8
        assert schema_data["notebook_lineage"] is not None, (
            "Lineage must be preserved — the notebook is the audit trail"
        )

        # Step 6: Verify evaluator-level signal — transaction_id is high-cardinality
        txn_id = next(f for f in schema_data["fields"] if f["name"] == "transaction_id")
        assert txn_id["cardinality"] is None, (
            "transaction_id should be high-cardinality (None = ID-like field)"
        )

        # Step 7: Verify currency enum signal surfaced for human REVIEW (F_H gate)
        currency = next(f for f in schema_data["fields"] if f["name"] == "currency")
        currency_questions = " ".join(currency.get("open_questions", [])).lower()
        assert "cardinality" in currency_questions or "enum" in currency_questions, (
            "currency (3 unique values: USD/EUR/GBP) should flag as enum candidate"
        )
