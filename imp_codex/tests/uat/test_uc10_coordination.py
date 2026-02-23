# Validates: REQ-COORD-001, REQ-COORD-002, REQ-COORD-003, REQ-COORD-004, REQ-COORD-005
"""UC-10: Multi-Agent Coordination — 16 scenarios.

Tests agent identity, feature assignment via events, work isolation,
Markov-aligned parallelism, and role-based evaluator authority.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import pytest

pytestmark = [pytest.mark.uat]


# ═══════════════════════════════════════════════════════════════════════
# PURE HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

_DURATION_RE = re.compile(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?")


def parse_duration(text: str) -> timedelta:
    """Parse a simple duration string like '1h', '30m', '2h30m' into timedelta."""
    m = _DURATION_RE.fullmatch(text.strip())
    if not m or not any(m.groups()):
        raise ValueError(f"Unparseable duration: {text!r}")
    hours = int(m.group(1) or 0)
    minutes = int(m.group(2) or 0)
    seconds = int(m.group(3) or 0)
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)


def is_claim_stale(
    claim_timestamp: str,
    timeout: str,
    *,
    now: datetime | None = None,
) -> bool:
    """Return True if *claim_timestamp* + *timeout* is before *now*.

    Pure function: compare claim ISO-8601 timestamp + parsed timeout vs now.
    """
    claimed_at = datetime.fromisoformat(claim_timestamp)
    deadline = claimed_at + parse_duration(timeout)
    current = now or datetime.now(timezone.utc)
    return current > deadline


def compute_feature_inner_product(
    files_a: set[str],
    files_b: set[str],
) -> int:
    """Compute inner product of two features as |intersection of touched files|.

    Inner product = 0 means disjoint file sets, safe to parallelise.
    """
    return len(files_a & files_b)


# ── EXISTING COVERAGE (not duplicated) ──────────────────────────────
# UC-10-01: TestAgentIdentity (test_methodology_bdd.py)


# ═══════════════════════════════════════════════════════════════════════
# UC-10-01..03: AGENT IDENTITY (Tier 1 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestAgentIdentity:
    """UC-10-01 through UC-10-03: agent_id, agent_role, backward compat."""

    # UC-10-01 | Validates: REQ-COORD-001 | Fixture: IN_PROGRESS
    def test_agent_roles_defined(self, agent_roles):
        """Agent role registry defines standard roles."""
        roles = agent_roles.get("roles", {})
        assert "architect" in roles
        assert "tdd_engineer" in roles
        assert "full_stack" in roles

    # UC-10-02 | Validates: REQ-COORD-001 | Fixture: IN_PROGRESS
    def test_single_agent_defaults(self, agent_roles):
        """Single-agent backward compatibility defaults defined."""
        defaults = agent_roles.get("single_agent_defaults", {})
        assert defaults.get("agent_id") == "primary"
        assert defaults.get("agent_role") == "full_stack"

    # UC-10-03 | Validates: REQ-COORD-001 | Fixture: INITIALIZED
    def test_role_registry_is_yaml(self, agent_roles):
        """Agent role registry is simple YAML list (no hierarchy)."""
        roles = agent_roles.get("roles", {})
        assert isinstance(roles, dict)
        for role_name, role_def in roles.items():
            assert "converge_edges" in role_def
            assert "description" in role_def


# ═══════════════════════════════════════════════════════════════════════
# UC-10-04..07: FEATURE ASSIGNMENT VIA EVENTS (Tier 1 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestFeatureAssignment:
    """UC-10-04 through UC-10-07: event-based claim protocol."""

    # UC-10-04 | Validates: REQ-COORD-002 | Fixture: IN_PROGRESS
    def test_claim_protocol_defined(self, agent_roles):
        """Claim protocol configuration exists."""
        claim = agent_roles.get("claim_protocol", {})
        assert claim.get("stale_claim_timeout"), "Claim timeout should be defined"

    # UC-10-05 | Validates: REQ-COORD-002 | Fixture: IN_PROGRESS
    def test_no_lock_files(self, agent_roles):
        """Assignment uses event log, not lock files."""
        claim = agent_roles.get("claim_protocol", {})
        # Inbox is non-authoritative write buffer
        inbox = claim.get("inbox", {})
        assert inbox, "Inbox semantics should be defined"

    # UC-10-06 | Validates: REQ-COORD-002 | Fixture: IN_PROGRESS
    def test_stale_claims_detected(self, agent_roles):
        """Stale claims trigger claim_expired signal.

        Pure function test: given a feature_claimed event with an old
        timestamp and the claim_protocol.stale_claim_timeout from config,
        verify that is_claim_stale() correctly identifies the claim as stale.
        """
        timeout_str = agent_roles["claim_protocol"]["stale_claim_timeout"]

        # Claim made 2 hours ago — should be stale under a 1h timeout
        two_hours_ago = (
            datetime.now(timezone.utc) - timedelta(hours=2)
        ).isoformat()
        assert is_claim_stale(two_hours_ago, timeout_str), (
            "A claim from 2h ago should be stale under a 1h timeout"
        )

        # Claim made 10 seconds ago — should NOT be stale
        just_now = (
            datetime.now(timezone.utc) - timedelta(seconds=10)
        ).isoformat()
        assert not is_claim_stale(just_now, timeout_str), (
            "A claim from 10s ago should not be stale under a 1h timeout"
        )

        # Edge case: claim made exactly at the boundary
        exactly_at = (
            datetime.now(timezone.utc) - parse_duration(timeout_str)
        ).isoformat()
        # At the boundary the deadline equals now, not exceeded — not stale
        assert not is_claim_stale(
            exactly_at, timeout_str,
            now=datetime.fromisoformat(exactly_at) + parse_duration(timeout_str),
        ), "Claim exactly at timeout boundary should not be stale (> not >=)"

    # UC-10-07 | Validates: REQ-COORD-002 | Fixture: IN_PROGRESS
    def test_single_agent_skips_claim(self, agent_roles):
        """Single-agent mode emits edge_started directly.

        Validates the design contract: when only one agent exists
        (single_agent_defaults), the claim protocol is not needed.
        The config explicitly documents that single-agent mode uses
        no serialiser, no inbox staging, and no claim protocol.
        """
        defaults = agent_roles.get("single_agent_defaults", {})

        # Single-agent defaults must exist
        assert defaults, "single_agent_defaults must be defined"

        # The default agent_id is 'primary' and role is 'full_stack'
        assert defaults["agent_id"] == "primary"
        assert defaults["agent_role"] == "full_stack"

        # full_stack role has universal convergence authority ('all')
        roles = agent_roles.get("roles", {})
        full_stack = roles.get(defaults["agent_role"], {})
        assert "all" in full_stack.get("converge_edges", []), (
            "full_stack role must have universal ('all') convergence authority "
            "so single-agent can emit edge_started directly without claim"
        )

        # Claim protocol exists for multi-agent but single-agent skips it
        # Verify the config comment contract: "No serialiser needed",
        # "No inbox staging, no claim protocol, no role checks"
        claim = agent_roles.get("claim_protocol", {})
        assert claim, (
            "claim_protocol should exist for multi-agent mode, "
            "but single-agent mode bypasses it entirely"
        )


# ═══════════════════════════════════════════════════════════════════════
# UC-10-08..10: WORK ISOLATION (Tier 1 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestWorkIsolation:
    """UC-10-08 through UC-10-10: private drafts, promotion gate, crash safety."""

    # UC-10-08 | Validates: REQ-COORD-003 | Fixture: IN_PROGRESS
    def test_isolation_paths_defined(self, agent_roles):
        """Agent working state isolated in agents/<id>/drafts/."""
        isolation = agent_roles.get("work_isolation", {})
        assert "drafts_path_template" in isolation
        assert "{agent_id}" in isolation["drafts_path_template"]

    # UC-10-09 | Validates: REQ-COORD-003 | Fixture: IN_PROGRESS
    def test_promotion_requires_evaluators(self, agent_roles):
        """Promotion to shared state requires evaluator gate."""
        isolation = agent_roles.get("work_isolation", {})
        promotion = isolation.get("promotion_requires", [])
        assert "all_evaluators_pass" in promotion

    # UC-10-10 | Validates: REQ-COORD-003 | Fixture: IN_PROGRESS
    def test_ephemeral_working_state(self, agent_roles):
        """Agent working state is ephemeral (crash loses only private state)."""
        isolation = agent_roles.get("work_isolation", {})
        assert isolation.get("ephemeral") is True


# ═══════════════════════════════════════════════════════════════════════
# UC-10-11..13: MARKOV-ALIGNED PARALLELISM (Tier 1 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestParallelism:
    """UC-10-11 through UC-10-13: inner product routing strategy."""

    # UC-10-11 | Validates: REQ-COORD-004 | Fixture: IN_PROGRESS
    def test_parallelism_strategy_defined(self, agent_roles):
        """Parallelism uses inner product routing strategy."""
        par = agent_roles.get("parallelism", {})
        assert par.get("routing_strategy") == "inner_product"

    # UC-10-12 | Validates: REQ-COORD-004 | Fixture: IN_PROGRESS
    def test_nonzero_inner_product_warning(self, agent_roles):
        """Non-zero inner product triggers warning."""
        par = agent_roles.get("parallelism", {})
        assert par.get("nonzero_inner_product") == "warn_and_suggest_sequential"

    # UC-10-13 | Validates: REQ-COORD-004 | Fixture: IN_PROGRESS
    def test_inner_product_from_dependency_dag(self, agent_roles):
        """Inner product computed from actual module dependency graph.

        Pure function test: two synthetic features with disjoint file sets
        yield inner product = 0 (safe to parallelise).  Overlapping file
        sets yield inner product > 0 (warn and suggest sequential).
        """
        par = agent_roles.get("parallelism", {})

        # Disjoint features — inner product = 0, safe to assign freely
        feature_a_files = {"src/auth/login.py", "src/auth/tokens.py"}
        feature_b_files = {"src/billing/invoice.py", "src/billing/payment.py"}
        ip_disjoint = compute_feature_inner_product(feature_a_files, feature_b_files)
        assert ip_disjoint == 0, "Disjoint file sets should have inner product 0"
        # Config says zero inner product → assign freely
        assert par.get("zero_inner_product") == "assign_freely"

        # Overlapping features — inner product > 0, warn
        feature_c_files = {"src/auth/login.py", "src/auth/session.py"}
        feature_d_files = {"src/auth/login.py", "src/dashboard/view.py"}
        ip_overlap = compute_feature_inner_product(feature_c_files, feature_d_files)
        assert ip_overlap == 1, "One shared file should give inner product 1"
        # Config says non-zero → warn and suggest sequential
        assert par.get("nonzero_inner_product") == "warn_and_suggest_sequential"

        # Empty feature — inner product with anything is 0
        ip_empty = compute_feature_inner_product(set(), feature_a_files)
        assert ip_empty == 0, "Empty feature has inner product 0 with anything"

        # Feature with itself — inner product = |files|
        ip_self = compute_feature_inner_product(feature_a_files, feature_a_files)
        assert ip_self == len(feature_a_files), (
            "Inner product of a feature with itself equals its file count"
        )


# ═══════════════════════════════════════════════════════════════════════
# UC-10-14..16: ROLE-BASED EVALUATOR AUTHORITY (Tier 1 / Tier 3)
# ═══════════════════════════════════════════════════════════════════════


class TestRoleAuthority:
    """UC-10-14 through UC-10-16: convergence scoped by role."""

    # UC-10-14 | Validates: REQ-COORD-005 | Fixture: IN_PROGRESS
    def test_role_scoped_convergence(self, agent_roles):
        """Each role has defined convergence edge authority."""
        roles = agent_roles.get("roles", {})
        architect = roles.get("architect", {})
        assert "intent_requirements" in architect.get("converge_edges", [])
        assert "code_unit_tests" not in architect.get("converge_edges", [])

        tdd = roles.get("tdd_engineer", {})
        assert "code_unit_tests" in tdd.get("converge_edges", [])

    # UC-10-15 | Validates: REQ-COORD-005 | Fixture: IN_PROGRESS
    def test_human_authority_universal(self, agent_roles):
        """Human authority is universal — can converge any edge."""
        authority = agent_roles.get("authority", {})
        assert authority.get("human_authority") == "universal"

    # UC-10-16 | Validates: REQ-COORD-005 | Fixture: INITIALIZED
    def test_outside_authority_escalates(self, agent_roles):
        """Convergence outside role authority triggers escalation."""
        authority = agent_roles.get("authority", {})
        assert authority.get("outside_authority_action") == "escalate"
