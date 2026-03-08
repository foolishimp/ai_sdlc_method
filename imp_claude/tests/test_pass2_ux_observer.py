# Validates: REQ-LIFE-010, REQ-LIFE-011, REQ-LIFE-012, REQ-UX-002, REQ-UX-004, REQ-UX-007
"""
Pass 2 traceability gap closure — UX and Observer dispatch wiring.

Tests that the implementations added by Pass 2 are present and correct:
  - Gap 1: on-observer-check.sh hook (REQ-LIFE-010, REQ-LIFE-011, REQ-LIFE-012)
  - Gap 2: Progressive Disclosure in gen-start.md (REQ-UX-002)
  - Gap 3: Auto-selection from context in gen-iterate.md (REQ-UX-004)
  - Gap 4: Zoom State Management in gen-zoom.md (REQ-UX-007)
"""

import pathlib
import re
import stat

import pytest

# ---------------------------------------------------------------------------
# Paths (mirrors conftest.py constants)
# ---------------------------------------------------------------------------
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
IMP_CLAUDE = PROJECT_ROOT / "imp_claude"
PLUGIN_ROOT = IMP_CLAUDE / "code/.claude-plugin/plugins/genesis"
HOOKS_DIR = PLUGIN_ROOT / "hooks"
COMMANDS_DIR = PLUGIN_ROOT / "commands"
AGENTS_DIR = PLUGIN_ROOT / "agents"

OBSERVER_HOOK = HOOKS_DIR / "on-observer-check.sh"
GEN_START = COMMANDS_DIR / "gen-start.md"
GEN_ITERATE = COMMANDS_DIR / "gen-iterate.md"
GEN_ZOOM = COMMANDS_DIR / "gen-zoom.md"

DEV_OBSERVER = AGENTS_DIR / "gen-dev-observer.md"
CICD_OBSERVER = AGENTS_DIR / "gen-cicd-observer.md"
OPS_OBSERVER = AGENTS_DIR / "gen-ops-observer.md"


# ===========================================================================
# Gap 1 — Observer Agent Dispatch Wiring (REQ-LIFE-010, 011, 012)
# ===========================================================================

class TestObserverDispatchHook:
    """REQ-LIFE-010, REQ-LIFE-011, REQ-LIFE-012 — the hook that wires the
    three observer agents to actual runtime triggers must exist and reference
    all three agents."""

    # Validates: REQ-LIFE-010, REQ-LIFE-011, REQ-LIFE-012
    def test_hook_file_exists(self):
        """on-observer-check.sh must exist in the hooks directory."""
        assert OBSERVER_HOOK.exists(), (
            f"Missing observer dispatch hook: {OBSERVER_HOOK}\n"
            "Create imp_claude/code/.claude-plugin/plugins/genesis/hooks/on-observer-check.sh"
        )

    # Validates: REQ-LIFE-010, REQ-LIFE-011, REQ-LIFE-012
    def test_hook_is_executable(self):
        """Hook script must be executable."""
        assert OBSERVER_HOOK.exists(), "Hook file missing — see test_hook_file_exists"
        mode = OBSERVER_HOOK.stat().st_mode
        assert mode & stat.S_IXUSR, (
            f"Hook is not executable (mode={oct(mode)}). "
            "Run: chmod +x imp_claude/code/.claude-plugin/plugins/genesis/hooks/on-observer-check.sh"
        )

    # Validates: REQ-LIFE-010
    def test_hook_references_dev_observer(self):
        """Hook must reference gen-dev-observer (REQ-LIFE-010)."""
        content = OBSERVER_HOOK.read_text()
        assert "gen-dev-observer" in content, (
            "on-observer-check.sh must reference 'gen-dev-observer' agent"
        )

    # Validates: REQ-LIFE-011
    def test_hook_references_cicd_observer(self):
        """Hook must reference gen-cicd-observer (REQ-LIFE-011)."""
        content = OBSERVER_HOOK.read_text()
        assert "gen-cicd-observer" in content, (
            "on-observer-check.sh must reference 'gen-cicd-observer' agent"
        )

    # Validates: REQ-LIFE-012
    def test_hook_references_ops_observer(self):
        """Hook must reference gen-ops-observer (REQ-LIFE-012)."""
        content = OBSERVER_HOOK.read_text()
        assert "gen-ops-observer" in content, (
            "on-observer-check.sh must reference 'gen-ops-observer' agent"
        )

    # Validates: REQ-LIFE-010, REQ-LIFE-011, REQ-LIFE-012
    def test_hook_emits_observer_dispatched_event(self):
        """Hook must emit an observer_dispatched event (or similar) to events.jsonl."""
        content = OBSERVER_HOOK.read_text()
        # Hook should write an event — look for event emission to events.jsonl
        assert "observer_dispatched" in content or "observer_signal" in content, (
            "on-observer-check.sh must emit an event (observer_dispatched or observer_signal) "
            "to events.jsonl when an observer is dispatched"
        )
        # Should reference events.jsonl or EVENTS_FILE
        assert "events.jsonl" in content or "EVENTS_FILE" in content, (
            "on-observer-check.sh must write events to events.jsonl"
        )

    # Validates: REQ-LIFE-010, REQ-LIFE-011, REQ-LIFE-012
    def test_hook_has_implements_tags(self):
        """Hook must carry Implements tags for all three REQ keys."""
        content = OBSERVER_HOOK.read_text()
        assert "REQ-LIFE-010" in content, "Hook missing 'Implements: REQ-LIFE-010' tag"
        assert "REQ-LIFE-011" in content, "Hook missing 'Implements: REQ-LIFE-011' tag"
        assert "REQ-LIFE-012" in content, "Hook missing 'Implements: REQ-LIFE-012' tag"

    # Validates: REQ-LIFE-010
    def test_dev_observer_agent_exists(self):
        """gen-dev-observer.md must exist (the agent being dispatched)."""
        assert DEV_OBSERVER.exists(), f"Missing dev observer agent: {DEV_OBSERVER}"

    # Validates: REQ-LIFE-011
    def test_cicd_observer_agent_exists(self):
        """gen-cicd-observer.md must exist (the agent being dispatched)."""
        assert CICD_OBSERVER.exists(), f"Missing CI/CD observer agent: {CICD_OBSERVER}"

    # Validates: REQ-LIFE-012
    def test_ops_observer_agent_exists(self):
        """gen-ops-observer.md must exist (the agent being dispatched)."""
        assert OPS_OBSERVER.exists(), f"Missing ops observer agent: {OPS_OBSERVER}"

    # Validates: REQ-LIFE-010, REQ-LIFE-011, REQ-LIFE-012
    def test_hook_dispatch_is_context_based(self):
        """Hook must dispatch different observers based on detected context,
        not unconditionally. Look for conditional logic (if/case)."""
        content = OBSERVER_HOOK.read_text()
        # Bash conditionals
        has_conditionals = "if " in content or "case " in content
        assert has_conditionals, (
            "on-observer-check.sh must use conditional dispatch — different observers "
            "for different workspace contexts (dev iteration vs CI/CD vs ops telemetry)"
        )


# ===========================================================================
# Gap 2 — Progressive Disclosure (REQ-UX-002)
# ===========================================================================

class TestProgressiveDisclosure:
    """REQ-UX-002 — gen-start.md must implement a first-run path that shows
    minimal options (3 or fewer) and defers advanced config."""

    # Validates: REQ-UX-002
    def test_gen_start_has_progressive_disclosure_section(self):
        """gen-start.md must contain a 'Progressive Disclosure' section."""
        content = GEN_START.read_text()
        assert "Progressive Disclosure" in content or "progressive" in content.lower(), (
            "gen-start.md must contain a 'Progressive Disclosure' or 'progressive' section "
            "describing the first-run simplified path (REQ-UX-002)"
        )

    # Validates: REQ-UX-002
    def test_gen_start_has_first_run_detection(self):
        """gen-start.md must describe how first-run is detected."""
        content = GEN_START.read_text()
        # First-run detection: empty/missing events.jsonl or no workspace
        has_firstrun = (
            "first-run" in content.lower()
            or "first run" in content.lower()
            or "no workspace" in content.lower()
            or "events.jsonl" in content
        )
        assert has_firstrun, (
            "gen-start.md must describe first-run detection "
            "(e.g., empty events.jsonl or missing .ai-workspace)"
        )

    # Validates: REQ-UX-002
    def test_gen_start_first_run_shows_limited_options(self):
        """gen-start.md first-run path must offer 3 or fewer choices."""
        content = GEN_START.read_text()
        # Look for numbered choices "1. ...\n  2. ...\n  3. ..."
        # within the progressive disclosure section
        section_match = re.search(
            r"Progressive Disclosure.*?(?=\n## |\Z)",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        assert section_match, "Progressive Disclosure section not found"
        section = section_match.group(0)

        # Count top-level numbered options
        options = re.findall(r"^\s{0,4}[1-9]\.", section, re.MULTILINE)
        assert len(options) <= 5, (
            f"First-run path shows {len(options)} top-level choices — "
            "should show 3 or fewer to implement progressive disclosure"
        )
        # Must have at least 1 option
        assert len(options) >= 1, "Progressive Disclosure section must define at least 1 option"

    # Validates: REQ-UX-002
    def test_gen_start_defers_advanced_config(self):
        """gen-start.md must explicitly defer advanced config on first-run."""
        content = GEN_START.read_text()
        # Should mention deferring advanced options
        has_deferral = (
            "deferred" in content.lower()
            or "defer" in content.lower()
            or "not shown" in content.lower()
            or "reveal" in content.lower()
        )
        assert has_deferral, (
            "gen-start.md must state which advanced options are deferred on first-run "
            "(graph topology, profiles, context hierarchy, etc.)"
        )

    # Validates: REQ-UX-002
    def test_gen_start_has_ux002_implements_tag(self):
        """gen-start.md must carry an Implements: REQ-UX-002 tag."""
        content = GEN_START.read_text()
        assert "REQ-UX-002" in content, (
            "gen-start.md must reference REQ-UX-002 in an Implements comment"
        )


# ===========================================================================
# Gap 3 — Auto-selection from Context (REQ-UX-004)
# ===========================================================================

class TestAutoSelectionFromContext:
    """REQ-UX-004 — gen-iterate.md must describe how feature and edge are
    auto-selected from workspace state when no --feature/--edge is provided."""

    # Validates: REQ-UX-004
    def test_gen_iterate_has_auto_selection_section(self):
        """gen-iterate.md must contain an 'Auto-selection' section."""
        content = GEN_ITERATE.read_text()
        assert (
            "Auto-selection" in content
            or "auto-select" in content.lower()
            or "auto selection" in content.lower()
        ), (
            "gen-iterate.md must contain an 'Auto-selection from Context' section "
            "describing automatic feature/edge detection (REQ-UX-004)"
        )

    # Validates: REQ-UX-004
    def test_gen_iterate_reads_features_active_dir(self):
        """Auto-selection must read from .ai-workspace/features/active/."""
        content = GEN_ITERATE.read_text()
        assert "features/active" in content, (
            "gen-iterate.md auto-selection must read from '.ai-workspace/features/active/' "
            "to discover active feature vectors"
        )

    # Validates: REQ-UX-004
    def test_gen_iterate_ranks_by_recency(self):
        """Auto-selection must rank features by recency (most recently modified/touched)."""
        content = GEN_ITERATE.read_text()
        has_recency = (
            "recency" in content.lower()
            or "recently" in content.lower()
            or "most recent" in content.lower()
            or "last event" in content.lower()
        )
        assert has_recency, (
            "gen-iterate.md must describe ranking by recency "
            "(most recently touched feature selected when multiple active)"
        )

    # Validates: REQ-UX-004
    def test_gen_iterate_describes_edge_determination(self):
        """Auto-selection must determine the next edge automatically."""
        content = GEN_ITERATE.read_text()
        # Look for edge determination logic near the auto-selection section
        section_match = re.search(
            r"Auto.selection.*?(?=\n## |\Z)",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        assert section_match, "Auto-selection section not found"
        section = section_match.group(0)

        has_edge_logic = (
            "edge" in section.lower()
            and (
                "next" in section.lower()
                or "first" in section.lower()
                or "pending" in section.lower()
                or "converged" in section.lower()
            )
        )
        assert has_edge_logic, (
            "Auto-selection section must describe how the next edge is determined "
            "(e.g., first non-converged edge in topology order)"
        )

    # Validates: REQ-UX-004
    def test_gen_iterate_has_ux004_implements_tag(self):
        """gen-iterate.md must carry a REQ-UX-004 Implements tag."""
        content = GEN_ITERATE.read_text()
        assert "REQ-UX-004" in content, (
            "gen-iterate.md must reference REQ-UX-004 in an Implements comment"
        )

    # Validates: REQ-UX-004
    def test_gen_iterate_has_fallback_prompting(self):
        """Auto-selection must fall back to prompting when context is ambiguous."""
        content = GEN_ITERATE.read_text()
        section_match = re.search(
            r"Auto.selection.*?(?=\n## |\Z)",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        assert section_match, "Auto-selection section not found"
        section = section_match.group(0)

        has_fallback = (
            "fallback" in section.lower()
            or "fall back" in section.lower()
            or "ambiguous" in section.lower()
            or "prompt" in section.lower()
        )
        assert has_fallback, (
            "Auto-selection must describe fallback to prompting when context is ambiguous "
            "(no active features, tied recency, malformed trajectory, etc.)"
        )


# ===========================================================================
# Gap 4 — Edge Zoom Management (REQ-UX-007)
# ===========================================================================

class TestEdgeZoomManagement:
    """REQ-UX-007 — gen-zoom.md must explicitly manage zoom state, preventing
    double-iteration and enabling clean fold-back."""

    # Validates: REQ-UX-007
    def test_gen_zoom_has_zoom_state_management_section(self):
        """gen-zoom.md must contain a 'Zoom State Management' section."""
        content = GEN_ZOOM.read_text()
        assert "Zoom State Management" in content, (
            "gen-zoom.md must contain a 'Zoom State Management' section (REQ-UX-007)"
        )

    # Validates: REQ-UX-007
    def test_gen_zoom_references_zoom_state_yml(self):
        """Zoom state management must reference zoom_state.yml."""
        content = GEN_ZOOM.read_text()
        assert "zoom_state.yml" in content, (
            "gen-zoom.md must reference '.ai-workspace/spec/zoom_state.yml' "
            "as the zoom state tracking file"
        )

    # Validates: REQ-UX-007
    def test_gen_zoom_emits_edge_zoomed_event(self):
        """Zoom-in operation must emit an edge_zoomed event."""
        content = GEN_ZOOM.read_text()
        assert "edge_zoomed" in content, (
            "gen-zoom.md must describe emission of 'edge_zoomed' event on zoom-in"
        )

    # Validates: REQ-UX-007
    def test_gen_zoom_emits_edge_folded_back_event(self):
        """Fold-back operation must emit an edge_folded_back event."""
        content = GEN_ZOOM.read_text()
        assert "edge_folded_back" in content, (
            "gen-zoom.md must describe emission of 'edge_folded_back' event on fold-back"
        )

    # Validates: REQ-UX-007
    def test_gen_zoom_prevents_double_zoom(self):
        """Zoom management must prevent re-zooming an already-zoomed edge."""
        content = GEN_ZOOM.read_text()
        has_guard = (
            "already zoomed" in content.lower()
            or "double-zoom" in content.lower()
            or "double zoom" in content.lower()
            or "already in `zoomed_edges`" in content.lower()
            or ("fold-back" in content.lower() and "before" in content.lower())
        )
        assert has_guard, (
            "gen-zoom.md must describe prevention of re-zooming an already-zoomed edge "
            "(requires fold-back first)"
        )

    # Validates: REQ-UX-007
    def test_gen_zoom_describes_fold_back_protocol(self):
        """Fold-back must collapse sub-graph results back to parent edge."""
        content = GEN_ZOOM.read_text()
        section_match = re.search(
            r"Fold.Back.*?Protocol.*?(?=\n### |\n## |\Z)",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        # Either a dedicated fold-back section, or fold-back described within zoom management
        has_foldback = (
            section_match is not None
            or "fold-back" in content.lower()
            and "parent edge" in content.lower()
        )
        assert has_foldback, (
            "gen-zoom.md must describe the fold-back protocol — collapsing sub-graph "
            "results back to the parent edge status"
        )

    # Validates: REQ-UX-007
    def test_gen_zoom_has_ux007_implements_tag(self):
        """gen-zoom.md must carry a REQ-UX-007 Implements tag."""
        content = GEN_ZOOM.read_text()
        assert "REQ-UX-007" in content, (
            "gen-zoom.md must reference REQ-UX-007 in an Implements comment"
        )
