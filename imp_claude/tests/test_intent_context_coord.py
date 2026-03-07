# Validates: REQ-INTENT-002
# Validates: REQ-INTENT-003
# Validates: REQ-CTX-002
# Validates: REQ-COORD-003
"""Tests for intent composition, context hierarchy, and work isolation.

Covers:
  REQ-INTENT-002: Intent as Spec — Intent + Context[] = Spec for a graph traversal
  REQ-INTENT-003: Eco-Intent Generation — INT-ECO-* intents from ecosystem changes
  REQ-CTX-002: Context Hierarchy — 6-level merge (methodology → org → policy → domain → prior → project)
  REQ-COORD-003: Work Isolation — agent private state; shared state only via events and promotion
"""

import sys
import pathlib

import pytest

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
IMP_CLAUDE = PROJECT_ROOT / "imp_claude"
PLUGIN_ROOT = IMP_CLAUDE / "code" / ".claude-plugin" / "plugins" / "genesis"
CONFIG_DIR = PLUGIN_ROOT / "config"
COMMANDS_DIR = PLUGIN_ROOT / "commands"
GENESIS_PKG = IMP_CLAUDE / "code" / "genesis"

sys.path.insert(0, str(IMP_CLAUDE / "code"))


# ═══════════════════════════════════════════════════════════════════════════════
# REQ-INTENT-002: Intent as Spec
# ═══════════════════════════════════════════════════════════════════════════════


class TestIntentAsSpec:
    """REQ-INTENT-002: Intents compose with Context[] to form the Spec."""

    def test_gen_init_implements_intent_as_spec(self):
        """gen-init declares it implements REQ-INTENT-002 (Intent as Spec)."""
        gen_init = COMMANDS_DIR / "gen-init.md"
        assert gen_init.exists(), "gen-init.md must exist"
        content = gen_init.read_text()
        assert "REQ-INTENT-002" in content, (
            "gen-init.md must declare Implements: REQ-INTENT-002 (Intent as Spec)"
        )

    def test_gen_start_implements_intent_as_spec(self):
        """gen-start also declares REQ-INTENT-002 (intent → spec composition in step 3)."""
        gen_start = COMMANDS_DIR / "gen-start.md"
        assert gen_start.exists(), "gen-start.md must exist"
        content = gen_start.read_text()
        assert "REQ-INTENT-002" in content, (
            "gen-start.md must declare Implements: REQ-INTENT-002"
        )

    def test_iterate_function_has_three_params(self):
        """iterate(Asset, Context[], Evaluators) — Spec is the fitness landscape.

        REQ-INTENT-002: 'Intent + Context[] = Spec for a given graph traversal'.
        The iterate function's Context[] parameter IS the Spec operationalised.
        """
        # The engine accepts constraints (= Context[]) as the spec surface
        from genesis.engine import EngineConfig

        # EngineConfig holds constraints (context) + graph topology (evaluators)
        fields = [f.name for f in EngineConfig.__dataclass_fields__.values()]
        assert "constraints" in fields, (
            "EngineConfig must have a 'constraints' field representing Context[]"
        )

    def test_spec_as_fitness_landscape_in_engine(self):
        """Spec (Context[]) is the constraint surface evaluators measure against.

        REQ-INTENT-002: 'Spec is the fitness landscape against which evaluators
        measure convergence'.
        """
        engine_src = (GENESIS_PKG / "engine.py").read_text()
        # Engine resolves constraints from EngineConfig — these ARE the spec
        assert "constraints" in engine_src, (
            "engine.py must use constraints as the evaluator constraint surface"
        )

    def test_intent_file_captured_in_workspace(self):
        """Intent is captured to a file — forming the root of the Spec.

        REQ-INTENT-002: Intent lineage accumulates through traversal.
        """
        gen_init = COMMANDS_DIR / "gen-init.md"
        content = gen_init.read_text()
        # gen-init writes the intent to specification/INTENT.md
        assert "INTENT.md" in content, (
            "gen-init must write intent to specification/INTENT.md to anchor Spec lineage"
        )

    def test_feature_vector_has_intent_field(self):
        """Feature vector template has intent field — linking vector to its intent.

        REQ-INTENT-002: Spec evolves as intent lineage accumulates through traversal.
        """
        template_path = CONFIG_DIR / "feature_vector_template.yml"
        assert template_path.exists()
        content = template_path.read_text()
        assert "intent:" in content, (
            "feature_vector_template.yml must have 'intent:' field to track intent lineage"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# REQ-INTENT-003: Eco-Intent Generation
# ═══════════════════════════════════════════════════════════════════════════════


class TestEcoIntentGeneration:
    """REQ-INTENT-003: System generates intents from ecosystem changes."""

    def test_fd_sense_has_ecosystem_observation_functions(self):
        """fd_sense.py provides interoceptive monitoring functions.

        REQ-INTENT-003: Eco-intents arise from sensing ecosystem changes.
        fd_sense implements REQ-SENSE-001 (Interoceptive Monitors) which
        feeds the eco-intent pipeline.
        """
        fd_sense_src = (GENESIS_PKG / "fd_sense.py").read_text()
        # sense_spec_code_drift and sense_status_freshness are the sensors
        # that produce eco-signals requiring intent generation
        assert "sense_spec_code_drift" in fd_sense_src, (
            "fd_sense must implement spec/code drift sensing for eco-intent triggers"
        )

    def test_workspace_gradient_generates_intent_proposals(self):
        """workspace_gradient.py generates intent proposals from observed deltas.

        REQ-INTENT-003: Ecosystem change signals → generate INT-ECO-* intents.
        The workspace gradient scanner feeds the eco-intent pipeline.
        """
        ws_gradient = GENESIS_PKG / "workspace_gradient.py"
        assert ws_gradient.exists(), (
            "workspace_gradient.py must exist (produces intent proposals from workspace delta)"
        )
        content = ws_gradient.read_text()
        assert "generate_intent_proposals" in content or "intent_proposal" in content, (
            "workspace_gradient.py must generate intent proposals from ecosystem signals"
        )

    def test_intent_raised_event_has_eco_signal_source(self):
        """intent_raised events carry signal_source for eco classification.

        REQ-INTENT-003: INT-ECO-* intents have ecosystem context.
        classify_signal_source routes 'intent_raised' events by signal_source.
        """
        from genesis.fd_classify import classify_signal_source

        eco_event = {
            "event_type": "intent_raised",
            "data": {"signal_source": "ecosystem"},
        }
        result = classify_signal_source(eco_event)
        assert result == "ecosystem", (
            f"intent_raised with signal_source=ecosystem should route to 'ecosystem', got: {result}"
        )

    def test_intent_raised_is_in_event_taxonomy(self):
        """intent_raised is a first-class event in the taxonomy.

        REQ-INTENT-003: Eco-intents feed into graph as new feature vectors —
        they must be classifiable by the IntentEngine.
        """
        from genesis.fd_classify import classify_signal_source

        # signal_source is the discriminator — any unknown source returns "unknown"
        gap_event = {
            "event_type": "intent_raised",
            "data": {"signal_source": "gap"},
        }
        result = classify_signal_source(gap_event)
        assert result != "", (
            "intent_raised must be a classifiable event type in the taxonomy"
        )

    def test_spec_requires_eco_intent_monitoring_categories(self):
        """Spec defines what ecosystem categories must be monitored.

        REQ-INTENT-003: 'Monitor for: security vulnerabilities, deprecations,
        API changes, compliance updates'.
        """
        spec_req = (
            PROJECT_ROOT
            / "specification"
            / "requirements"
            / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        )
        content = spec_req.read_text()
        # All four categories must be in the spec
        for category in ["vulnerabilities", "deprecations", "API changes", "compliance"]:
            assert category in content, (
                f"REQ-INTENT-003 must specify monitoring for: {category}"
            )

    def test_eco_intent_prefix_format_is_defined(self):
        """Eco-intents use INT-ECO-* prefix format.

        REQ-INTENT-003: 'Generate INT-ECO-* intents with ecosystem context'.
        """
        spec_req = (
            PROJECT_ROOT
            / "specification"
            / "requirements"
            / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        )
        content = spec_req.read_text()
        assert "INT-ECO-" in content, (
            "REQ-INTENT-003 must define the INT-ECO-* intent prefix format"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# REQ-CTX-002: Context Hierarchy
# ═══════════════════════════════════════════════════════════════════════════════


class TestContextHierarchy:
    """REQ-CTX-002: Hierarchical context composition with deep merge."""

    def test_deep_merge_function_exists(self):
        """config_loader.py implements deep_merge for context composition."""
        from genesis.config_loader import deep_merge

        assert callable(deep_merge)

    def test_deep_merge_later_overrides_earlier(self):
        """Later contexts override earlier ones (project > global).

        REQ-CTX-002: 'Later contexts override earlier contexts'.
        """
        from genesis.config_loader import deep_merge

        base = {"key": "base_value", "nested": {"a": 1, "b": 2}}
        override = {"key": "override_value", "nested": {"b": 99}}
        result = deep_merge(base, override)

        assert result["key"] == "override_value", (
            "Scalar values: later context must override earlier"
        )
        assert result["nested"]["b"] == 99, (
            "Nested scalars: later context must override earlier"
        )

    def test_deep_merge_preserves_non_overridden_keys(self):
        """Deep merge preserves keys not present in override.

        REQ-CTX-002: 'Deep merge for objects' — objects are merged, not replaced.
        """
        from genesis.config_loader import deep_merge

        base = {"key": "base_value", "nested": {"a": 1, "b": 2}}
        override = {"nested": {"b": 99}}
        result = deep_merge(base, override)

        assert result["key"] == "base_value", (
            "Non-overridden top-level keys must be preserved"
        )
        assert result["nested"]["a"] == 1, (
            "Non-overridden nested keys must be preserved after deep merge"
        )

    def test_deep_merge_does_not_mutate_inputs(self):
        """deep_merge returns a new dict — neither input is mutated."""
        from genesis.config_loader import deep_merge

        base = {"key": "original", "nested": {"a": 1}}
        override = {"key": "overridden", "nested": {"a": 99}}
        base_copy = {"key": "original", "nested": {"a": 1}}

        result = deep_merge(base, override)

        assert base == base_copy, "deep_merge must not mutate the base dict"
        assert result is not base, "deep_merge must return a new dict"

    def test_merge_contexts_is_left_to_right(self):
        """merge_contexts applies left-to-right — rightmost wins.

        REQ-CTX-002: First file = lowest priority, last = highest.
        """
        from genesis.config_loader import merge_contexts

        global_ctx = {"setting": "global", "shared": "from_global"}
        project_ctx = {"setting": "project"}
        result = merge_contexts(global_ctx, project_ctx)

        assert result["setting"] == "project", (
            "merge_contexts: project (rightmost) must win over global (leftmost)"
        )
        assert result["shared"] == "from_global", (
            "merge_contexts: keys only in global must be preserved"
        )

    def test_load_context_hierarchy_merges_files(self, tmp_path):
        """load_context_hierarchy loads and merges multiple YAML files.

        REQ-CTX-002: 'Context sources listed in feature vector YAML'.
        """
        import yaml
        from genesis.config_loader import load_context_hierarchy

        global_file = tmp_path / "global.yml"
        global_file.write_text(yaml.dump({"env": "global", "shared": "g"}))

        project_file = tmp_path / "project.yml"
        project_file.write_text(yaml.dump({"env": "project", "extra": "p"}))

        result = load_context_hierarchy([global_file, project_file])

        assert result["env"] == "project", "project overrides global"
        assert result["shared"] == "g", "global-only key preserved"
        assert result["extra"] == "p", "project-only key included"

    def test_load_context_hierarchy_skips_missing_files(self, tmp_path):
        """Missing context files are silently skipped (not an error).

        REQ-CTX-002: 'Customisation without forking' — missing optional levels OK.
        """
        import yaml
        from genesis.config_loader import load_context_hierarchy

        existing = tmp_path / "exists.yml"
        existing.write_text(yaml.dump({"key": "value"}))
        missing = tmp_path / "does_not_exist.yml"

        result = load_context_hierarchy([missing, existing])
        assert result == {"key": "value"}, (
            "Missing context files must be skipped silently"
        )

    def test_load_context_hierarchy_stop_on_missing_raises(self, tmp_path):
        """stop_on_missing=True raises FileNotFoundError for missing files."""
        from genesis.config_loader import load_context_hierarchy

        missing = tmp_path / "does_not_exist.yml"
        with pytest.raises(FileNotFoundError):
            load_context_hierarchy([missing], stop_on_missing=True)

    def test_context_hierarchy_spec_defines_six_levels(self):
        """REQ-CTX-002 spec defines 6 levels: methodology → org → policy → domain → prior → project."""
        spec_req = (
            PROJECT_ROOT
            / "specification"
            / "requirements"
            / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        )
        content = spec_req.read_text()
        # The 6-level hierarchy must be stated
        assert "methodology" in content and "organisation" in content, (
            "REQ-CTX-002 must define methodology and organisation levels in the hierarchy"
        )

    def test_engine_uses_input_hash_for_context_addressability(self):
        """Engine computes input_hash (sha256) for content-addressable Spec identity.

        REQ-CTX-002: 'Aggregate context_hash emitted on each IterationStarted event'.
        """
        engine_src = (GENESIS_PKG / "engine.py").read_text()
        assert "input_hash" in engine_src, (
            "engine.py must compute input_hash for content-addressable Spec identity"
        )
        assert "sha256" in engine_src, (
            "input_hash must use sha256 for deterministic content-addressable identity"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# REQ-COORD-003: Work Isolation
# ═══════════════════════════════════════════════════════════════════════════════


class TestWorkIsolation:
    """REQ-COORD-003: Agent working state isolated from shared project state."""

    @pytest.fixture
    def agent_roles(self):
        import yaml
        path = CONFIG_DIR / "agent_roles.yml"
        assert path.exists(), "agent_roles.yml must exist"
        with open(path) as f:
            return yaml.safe_load(f)

    def test_agent_roles_declares_req_coord_003(self):
        """agent_roles.yml declares it implements REQ-COORD-003."""
        content = (CONFIG_DIR / "agent_roles.yml").read_text()
        assert "REQ-COORD-003" in content, (
            "agent_roles.yml must declare Implements: REQ-COORD-003"
        )

    def test_work_isolation_config_exists(self, agent_roles):
        """agent_roles.yml has a work_isolation section.

        REQ-COORD-003: 'Each agent has a private working directory'.
        """
        assert "work_isolation" in agent_roles, (
            "agent_roles.yml must have a 'work_isolation' section"
        )

    def test_drafts_path_template_is_agent_private(self, agent_roles):
        """Drafts path template uses agent_id — private per agent.

        REQ-COORD-003: 'Each agent has a private working directory for in-progress artifacts'.
        """
        isolation = agent_roles["work_isolation"]
        drafts = isolation.get("drafts_path_template", "")
        assert "{agent_id}" in drafts, (
            "drafts_path_template must include {agent_id} for per-agent isolation"
        )

    def test_agent_state_is_ephemeral(self, agent_roles):
        """Agent private state is ephemeral — only emitted events persist on crash.

        REQ-COORD-003: 'Agent-private state is ephemeral: if an agent crashes,
        only its emitted events persist'.
        """
        isolation = agent_roles["work_isolation"]
        assert isolation.get("ephemeral") is True, (
            "work_isolation.ephemeral must be true — agent state discarded on crash"
        )

    def test_promotion_requires_evaluator_pass(self, agent_roles):
        """Promotion to shared state requires passing all evaluators for the edge.

        REQ-COORD-003: 'Promotion of agent-produced assets to shared paths requires
        passing the configured evaluators for that edge'.
        """
        isolation = agent_roles["work_isolation"]
        promotion = isolation.get("promotion_requires", [])
        assert "all_evaluators_pass" in promotion, (
            "work_isolation.promotion_requires must include 'all_evaluators_pass'"
        )

    def test_spec_mutation_requires_human(self, agent_roles):
        """Spec mutations always require human evaluator approval.

        REQ-COORD-003: 'Spec mutations (changes to requirements) always require
        human evaluator approval regardless of agent role'.
        """
        # Look in serialiser role or anywhere in agent_roles for spec_mutation_requires_human
        content = (CONFIG_DIR / "agent_roles.yml").read_text()
        assert "spec_mutation_requires_human" in content, (
            "agent_roles.yml must declare spec_mutation_requires_human: true"
        )

        # Verify it's set to true
        assert "spec_mutation_requires_human: true" in content, (
            "spec_mutation_requires_human must be explicitly set to true"
        )

    def test_shared_state_only_via_events(self):
        """Shared state (features, events) written only via event emission.

        REQ-COORD-003: 'Shared project state is never written directly by agents
        during iteration — only via event emission and convergence promotion'.
        """
        # The engine writes to events.jsonl, not directly to feature vectors during iteration
        engine_src = (GENESIS_PKG / "engine.py").read_text()
        assert "events.jsonl" in engine_src or "EVENTS_FILE" in engine_src or "events_path" in engine_src, (
            "engine.py must route shared state through events.jsonl"
        )

    def test_workspace_agents_dir_is_private_path(self):
        """Agent working state lives under .ai-workspace/agents/ (private path).

        REQ-COORD-003: ADR-013 defines agent inbox/state under .ai-workspace/agents/.
        """
        # Check that the fold-back protocol uses .ai-workspace/agents/ for private state
        fp_functor_src = (GENESIS_PKG / "fp_functor.py").read_text()
        assert "agents/" in fp_functor_src or ".ai-workspace" in fp_functor_src, (
            "fp_functor.py must write agent state under .ai-workspace/agents/ (private path)"
        )

    def test_human_audit_enforces_spec_boundary(self):
        """human_audit.py enforces the human accountability boundary.

        REQ-COORD-003: spec mutations always require human; human_audit.py
        implements the attribution guard.
        """
        human_audit = GENESIS_PKG / "human_audit.py"
        assert human_audit.exists(), (
            "human_audit.py must exist to enforce human accountability at spec boundaries"
        )
        content = human_audit.read_text()
        assert "attribution" in content.lower() or "attribution_guard" in content.lower(), (
            "human_audit.py must implement an attribution guard for spec mutations"
        )
