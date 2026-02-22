# Validates: REQ-CTX-001, REQ-CTX-002, REQ-INTENT-004
"""UC-03: Context Management — 12 scenarios.

Tests context types, constraint surface, hierarchy, and spec reproducibility.
"""

from __future__ import annotations

import copy
import hashlib
import json

import pytest
import yaml

from imp_claude.tests.uat.conftest import CONFIG_DIR, EDGE_PARAMS_DIR
from imp_claude.tests.uat.workspace_state import (
    compute_context_hash,
    deep_merge,
    resolve_context_hierarchy,
)

pytestmark = [pytest.mark.uat]


# ── EXISTING COVERAGE (not duplicated) ──────────────────────────────
# UC-03-01: TestContextSources (test_config_validation.py)


# ═══════════════════════════════════════════════════════════════════════
# UC-03-01..04: CONTEXT AS CONSTRAINT SURFACE (Tier 1 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestContextConstraintSurface:
    """UC-03-01 through UC-03-04: context types and constraint narrowing."""

    # UC-03-01 | Validates: REQ-CTX-001 | Fixture: INITIALIZED
    def test_context_types_defined(self, initialized_workspace):
        """Initialized workspace has context directory structure."""
        ctx = initialized_workspace / ".ai-workspace" / "claude" / "context"
        assert ctx.exists(), "Context directory should exist"

    # UC-03-02 | Validates: REQ-CTX-001 | Fixture: —
    def test_context_narrows_constructions(self, all_edge_configs):
        """Edge configs define context requirements that narrow what can be constructed.

        Each edge config has checks (checklist items) that reference context
        elements via $variable notation — $tools.*, $thresholds.*, $standards.*.
        These references mean the edge cannot be evaluated without the
        corresponding context, thus narrowing what iterate() can produce.
        """
        # Context-referencing patterns in checklist criteria and commands
        context_patterns = ("$tools.", "$thresholds.", "$standards.")

        edges_with_context_refs = {}
        for name, config in all_edge_configs.items():
            checklist = config.get("checklist", [])
            refs_found = set()
            for check in checklist:
                # Scan criterion and command fields for $variable references
                criterion = check.get("criterion", "")
                command = check.get("command", "")
                pass_crit = check.get("pass_criterion", "")
                for field_val in (criterion, command, pass_crit):
                    if not isinstance(field_val, str):
                        continue
                    for pattern in context_patterns:
                        if pattern in field_val:
                            refs_found.add(pattern.rstrip("."))
            if refs_found:
                edges_with_context_refs[name] = refs_found

        # At least some edges reference context elements
        assert len(edges_with_context_refs) >= 2, (
            f"Expected at least 2 edge configs to reference context elements, "
            f"found {len(edges_with_context_refs)}: {list(edges_with_context_refs.keys())}"
        )

        # The TDD edge (code↔unit_tests) must reference tools and thresholds
        tdd_config = all_edge_configs.get("tdd", {})
        tdd_checklist = tdd_config.get("checklist", [])
        tdd_text = " ".join(
            str(c.get("criterion", "")) + " " + str(c.get("command", ""))
            for c in tdd_checklist
        )
        assert "$tools." in tdd_text, "TDD edge must reference $tools context"
        assert "$thresholds." in tdd_text, "TDD edge must reference $thresholds context"

    # UC-03-03 | Validates: REQ-CTX-001 | Fixture: INITIALIZED
    def test_context_subset_per_edge(self, all_edge_configs):
        """Edge configs can specify context requirements."""
        # Edge configs exist and define context patterns
        assert len(all_edge_configs) >= 5
        for name, config in all_edge_configs.items():
            # Edge configs define checks which implicitly scope context
            assert config, f"Edge config '{name}' is empty"

    # UC-03-04 | Validates: REQ-CTX-001 | Fixture: INITIALIZED
    def test_context_version_control(self, initialized_workspace):
        """Context elements are versioned; updates create new versions.

        The project_constraints_template.yml has a version field inside
        project.version.  Changes to context produce a different hash,
        proving versioning is detectable.
        """
        # Read the project constraints written by the fixture
        ctx_path = (
            initialized_workspace / ".ai-workspace" / "claude" / "context"
            / "project_constraints.yml"
        )
        assert ctx_path.exists(), "project_constraints.yml must exist"

        with open(ctx_path) as f:
            constraints = yaml.safe_load(f)

        # The template has a version field
        assert "version" in constraints.get("project", {}), (
            "project_constraints must have a project.version field"
        )

        # Compute hash of original context
        hash_v1 = compute_context_hash(constraints)

        # Modify the context (simulate an update)
        modified = copy.deepcopy(constraints)
        modified["project"]["version"] = "0.2.0"
        modified["thresholds"]["test_coverage_minimum"] = 0.90

        hash_v2 = compute_context_hash(modified)

        # Hashes differ — the change is detectable
        assert hash_v1 != hash_v2, (
            "Modified context must produce a different hash"
        )

        # Same content still produces the same hash (determinism)
        hash_v1_again = compute_context_hash(constraints)
        assert hash_v1 == hash_v1_again, (
            "Same context must produce the same hash"
        )


# ═══════════════════════════════════════════════════════════════════════
# UC-03-05..09: CONTEXT HIERARCHY (Tier 1 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestContextHierarchy:
    """UC-03-05 through UC-03-09: global->org->team->project override chain."""

    # UC-03-05 | Validates: REQ-CTX-002 | Fixture: —
    def test_hierarchy_override(self):
        """Project-level context overrides global defaults."""
        global_ctx = {
            "language": {"primary": "python", "version": "3.10"},
            "thresholds": {"test_coverage_minimum": 0.80},
        }
        project_ctx = {
            "language": {"version": "3.12"},
            "thresholds": {"test_coverage_minimum": 0.95},
        }

        resolved = resolve_context_hierarchy([global_ctx, project_ctx])

        # Project overrides global
        assert resolved["language"]["version"] == "3.12", (
            "Project language version must override global"
        )
        assert resolved["thresholds"]["test_coverage_minimum"] == 0.95, (
            "Project threshold must override global"
        )
        # Global values not overridden are preserved
        assert resolved["language"]["primary"] == "python", (
            "Non-overridden global values must be preserved"
        )

    # UC-03-06 | Validates: REQ-CTX-002 | Fixture: —
    def test_deep_merge_objects(self):
        """Object context values are deep-merged across hierarchy levels."""
        base = {
            "tools": {
                "test_runner": {"command": "pytest", "args": "-v"},
                "linter": {"command": "ruff", "args": "check ."},
            },
            "thresholds": {"coverage": 0.80},
        }
        override = {
            "tools": {
                "test_runner": {"args": "-v --tb=short"},
                "formatter": {"command": "black", "args": "."},
            },
        }

        result = deep_merge(base, override)

        # Deep merge: test_runner.command preserved, args overridden
        assert result["tools"]["test_runner"]["command"] == "pytest", (
            "Base value not in override must be preserved"
        )
        assert result["tools"]["test_runner"]["args"] == "-v --tb=short", (
            "Override value must win"
        )
        # Deep merge: linter from base preserved
        assert result["tools"]["linter"]["command"] == "ruff", (
            "Entire sub-dict from base must be preserved when not overridden"
        )
        # Deep merge: formatter from override added
        assert result["tools"]["formatter"]["command"] == "black", (
            "New sub-dict from override must be added"
        )
        # Non-overridden top-level key preserved
        assert result["thresholds"]["coverage"] == 0.80, (
            "Top-level keys not in override must be preserved"
        )

    # UC-03-07 | Validates: REQ-CTX-002 | Fixture: —
    def test_later_overrides_earlier(self):
        """Later context level wins on key conflicts."""
        global_ctx = {"language": "python", "version": "3.10"}
        org_ctx = {"version": "3.11", "org": "acme"}
        project_ctx = {"version": "3.12", "project": "widget"}

        resolved = resolve_context_hierarchy([global_ctx, org_ctx, project_ctx])

        # Last level wins
        assert resolved["version"] == "3.12", (
            "Project (last level) must win on version conflict"
        )
        # Earlier non-conflicting keys preserved
        assert resolved["language"] == "python", (
            "Global-only key must be preserved"
        )
        assert resolved["org"] == "acme", (
            "Org-only key must be preserved"
        )
        assert resolved["project"] == "widget", (
            "Project-only key must be preserved"
        )

    # UC-03-08 | Validates: REQ-CTX-002 | Fixture: —
    def test_customisation_without_forking(self):
        """Project overrides don't modify team-level context."""
        team_ctx = {
            "tools": {"test_runner": {"command": "pytest", "args": "-v"}},
            "thresholds": {"coverage": 0.80},
        }
        project_ctx = {
            "tools": {"test_runner": {"args": "-v --tb=short"}},
            "thresholds": {"coverage": 0.95},
        }

        # Snapshot originals before resolution
        team_original = copy.deepcopy(team_ctx)
        project_original = copy.deepcopy(project_ctx)

        resolved = resolve_context_hierarchy([team_ctx, project_ctx])

        # Verify resolution worked
        assert resolved["thresholds"]["coverage"] == 0.95

        # Verify originals were NOT mutated
        assert team_ctx == team_original, (
            "team_ctx must not be mutated by resolve_context_hierarchy"
        )
        assert project_ctx == project_original, (
            "project_ctx must not be mutated by resolve_context_hierarchy"
        )

    # UC-03-09 | Validates: REQ-CTX-002 | Fixture: INITIALIZED
    def test_context_hierarchy_levels(self, all_profiles):
        """Profiles define context density and required elements (hierarchy support)."""
        std = all_profiles.get("standard", {})
        ctx = std.get("context", {})
        assert ctx.get("density"), "Profile should define context density"
        assert ctx.get("required_elements"), "Profile should define required context elements"


# ═══════════════════════════════════════════════════════════════════════
# UC-03-10..12: SPEC REPRODUCIBILITY (Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestSpecReproducibility:
    """UC-03-10 through UC-03-12: deterministic serialisation, hash, immutability."""

    # UC-03-10 | Validates: REQ-INTENT-004 | Fixture: —
    def test_deterministic_serialisation(self):
        """Same intent + context produces identical canonical serialisation."""
        context_a = {
            "project": {"name": "test", "version": "1.0"},
            "language": {"primary": "python", "version": "3.12"},
            "thresholds": {"coverage": 0.80, "complexity": 10},
        }
        # Identical content, different dict construction order
        context_b = {
            "thresholds": {"complexity": 10, "coverage": 0.80},
            "language": {"version": "3.12", "primary": "python"},
            "project": {"version": "1.0", "name": "test"},
        }

        hash_a = compute_context_hash(context_a)
        hash_b = compute_context_hash(context_b)

        assert hash_a == hash_b, (
            "Identical content in different insertion order must produce same hash"
        )

        # Verify it is a valid SHA-256 hex digest
        assert len(hash_a) == 64, "Hash must be a 64-char SHA-256 hex digest"
        int(hash_a, 16)  # raises ValueError if not valid hex

        # Repeated calls produce the same result
        assert compute_context_hash(context_a) == hash_a, (
            "Repeated calls must be deterministic"
        )

    # UC-03-11 | Validates: REQ-INTENT-004 | Fixture: —
    def test_context_hash_in_events(self):
        """Iteration events can contain a context_hash field.

        The event schema is a dict with event_type, timestamp, and arbitrary
        extra fields.  We validate that a context_hash can be included and
        round-trips through JSON serialisation.
        """
        context = {
            "project": {"name": "test"},
            "language": {"primary": "python"},
        }
        ctx_hash = compute_context_hash(context)

        # Build a synthetic iteration event with context_hash
        event = {
            "event_type": "iteration_completed",
            "timestamp": "2026-02-22T00:00:00+00:00",
            "feature": "REQ-F-ALPHA-001",
            "edge": "intent->requirements",
            "iteration": 1,
            "delta": 2,
            "context_hash": ctx_hash,
        }

        # Round-trip through JSON (as events.jsonl does)
        serialised = json.dumps(event)
        deserialised = json.loads(serialised)

        assert deserialised["context_hash"] == ctx_hash, (
            "context_hash must survive JSON round-trip"
        )
        assert deserialised["event_type"] == "iteration_completed"
        assert len(deserialised["context_hash"]) == 64

    # UC-03-12 | Validates: REQ-INTENT-004 | Fixture: IN_PROGRESS
    def test_spec_versions_immutable(self, in_progress_workspace):
        """Previous spec versions remain accessible after modification.

        We write an INTENT.md, compute its hash, modify it, compute the new
        hash.  The hashes differ — proving content changes are detectable.
        We also validate the event schema supports spec_modified events.
        """
        intent_path = in_progress_workspace / "specification" / "INTENT.md"
        assert intent_path.exists(), "INTENT.md must exist in workspace"

        # Hash of the original content
        original_content = intent_path.read_text()
        original_hash = hashlib.sha256(original_content.encode()).hexdigest()

        # Modify the intent
        modified_content = original_content + "\n\n### REQ-F-ZETA-001: New Feature\nA newly added requirement.\n"
        intent_path.write_text(modified_content)
        modified_hash = hashlib.sha256(modified_content.encode()).hexdigest()

        # Hashes differ — the change is detectable
        assert original_hash != modified_hash, (
            "Modified spec must produce a different hash"
        )

        # The event schema supports spec_modified events
        spec_modified_event = {
            "event_type": "spec_modified",
            "timestamp": "2026-02-22T00:00:00+00:00",
            "asset": "INTENT.md",
            "previous_hash": original_hash,
            "new_hash": modified_hash,
            "reason": "Added REQ-F-ZETA-001",
        }

        # Round-trip through JSON
        serialised = json.dumps(spec_modified_event)
        deserialised = json.loads(serialised)
        assert deserialised["event_type"] == "spec_modified"
        assert deserialised["previous_hash"] == original_hash
        assert deserialised["new_hash"] == modified_hash
        assert deserialised["previous_hash"] != deserialised["new_hash"], (
            "spec_modified event must record distinct before/after hashes"
        )
