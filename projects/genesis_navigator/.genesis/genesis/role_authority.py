# Implements: REQ-COORD-005 (Role-Based Evaluator Authority)
"""Role authority — determines whether an agent role may converge an edge.

Loads agent_roles.yml from the plugin config directory or a workspace
override. Provides:

    check_role_authority(role, edge, roles_config) → bool
    convergence_action(role, edge, roles_config) → str
    normalise_edge(edge) → str

Edge names from the event log use Unicode arrows ("design→code",
"code↔unit_tests").  The role registry uses snake_case ("design_code",
"code_unit_tests").  normalise_edge() bridges the two representations.

Convergence actions (configured per workspace in agent_roles.yml):
    escalate  — emit convergence_escalated, hold for human approval
    reject    — emit convergence_escalated, deny convergence
    warn      — emit convergence_escalated, allow convergence

Human evaluators always have universal authority regardless of role.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml


# ═══════════════════════════════════════════════════════════════════════
# EDGE NORMALISATION
# ═══════════════════════════════════════════════════════════════════════

# Arrow characters used in event log edge names
_ARROW_RE = re.compile(r"[→↔]")


def normalise_edge(edge: str) -> str:
    """Normalise an event-log edge name to the config registry key.

    Examples:
        "design→code"        → "design_code"
        "code↔unit_tests"    → "code_unit_tests"
        "intent→requirements" → "intent_requirements"
        "code_unit_tests"    → "code_unit_tests"  (already normalised)
    """
    return _ARROW_RE.sub("_", edge).strip().lower()


# ═══════════════════════════════════════════════════════════════════════
# CONFIG LOADING
# ═══════════════════════════════════════════════════════════════════════

_DEFAULT_CONFIG_PATH = (
    Path(__file__).parent.parent
    / ".claude-plugin"
    / "plugins"
    / "genesis"
    / "config"
    / "agent_roles.yml"
)


def load_role_config(config_path: Optional[Path] = None) -> dict[str, Any]:
    """Load agent_roles.yml.  Falls back to the bundled default config."""
    path = config_path or _DEFAULT_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"Role config not found: {path}")
    with open(path) as f:
        return yaml.safe_load(f) or {}


# ═══════════════════════════════════════════════════════════════════════
# AUTHORITY CHECKS
# ═══════════════════════════════════════════════════════════════════════


def check_role_authority(
    role: str,
    edge: str,
    roles_config: dict[str, Any],
) -> bool:
    """Return True if *role* may converge *edge*.

    Rules:
    1. If roles_config is empty or roles section is missing → allow (fail-open).
    2. If role is not in the registry → deny (unknown role has no authority).
    3. If role's converge_edges is ["all"] → allow universally.
    4. Otherwise check if normalise_edge(edge) is in the role's converge_edges list.
    """
    roles = roles_config.get("roles", {})
    if not roles:
        return True  # no config → fail-open

    role_def = roles.get(role)
    if role_def is None:
        return False  # unknown role → no authority

    converge_edges = role_def.get("converge_edges", [])
    if "all" in converge_edges:
        return True

    norm = normalise_edge(edge)
    return norm in [normalise_edge(e) for e in converge_edges]


def convergence_action(
    role: str,
    edge: str,
    roles_config: dict[str, Any],
) -> str:
    """Return the configured action for out-of-authority convergence.

    Returns one of: "escalate", "reject", "warn".
    Defaults to "escalate" if not configured.
    """
    authority = roles_config.get("authority", {})
    return authority.get("outside_authority_action", "escalate")


def get_outside_authority_action(
    role: str,
    edge: str,
    roles_config: dict[str, Any],
) -> str:
    """Return the action to take when *role* tries to converge *edge* without authority.

    Returns "granted" if the role has authority (no action needed), otherwise
    returns the configured action: "escalate", "reject", or "warn".
    """
    if check_role_authority(role, edge, roles_config):
        return "granted"
    return convergence_action(role, edge, roles_config)


# ═══════════════════════════════════════════════════════════════════════
# EVENT EMISSION
# ═══════════════════════════════════════════════════════════════════════


def emit_convergence_escalated(
    events_path: Path,
    project: str,
    agent_id: str,
    agent_role: str,
    feature: str,
    edge: str,
    reason: str,
    action: str = "escalate",
) -> None:
    """Append a convergence_escalated event to events.jsonl (REQ-COORD-005)."""
    event = {
        "event_type": "convergence_escalated",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": project,
        "feature": feature,
        "edge": edge,
        "agent_id": agent_id,
        "data": {
            "agent_role": agent_role,
            "reason": reason,
            "action": action,
            "norm_edge": normalise_edge(edge),
        },
    }
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with open(events_path, "a") as f:
        f.write(json.dumps(event, separators=(",", ":")) + "\n")


# ═══════════════════════════════════════════════════════════════════════
# HIGH-LEVEL CONVERGENCE GATE
# ═══════════════════════════════════════════════════════════════════════


def check_convergence_gate(
    workspace: Path,
    project: str,
    agent_id: str,
    agent_role: str,
    feature: str,
    edge: str,
    roles_config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Check whether agent_role may converge edge, and emit events if not.

    Returns a result dict:
        {
            "allowed": bool,
            "action": str,       # "granted", "escalate", "reject", "warn"
            "reason": str,
        }

    Side effects:
        - If not allowed: emits convergence_escalated to workspace events.jsonl
    """
    if roles_config is None:
        try:
            roles_config = load_role_config()
        except FileNotFoundError:
            roles_config = {}

    action = get_outside_authority_action(agent_role, edge, roles_config)

    if action == "granted":
        return {"allowed": True, "action": "granted", "reason": "role has authority"}

    reason = f"role '{agent_role}' is not authorised to converge edge '{edge}'"
    allowed = action == "warn"  # warn allows convergence, escalate/reject block it

    # Emit convergence_escalated event
    ws_dir = (
        workspace / ".ai-workspace"
        if (workspace / ".ai-workspace").exists()
        else workspace
    )
    events_path = ws_dir / "events" / "events.jsonl"
    emit_convergence_escalated(
        events_path=events_path,
        project=project,
        agent_id=agent_id,
        agent_role=agent_role,
        feature=feature,
        edge=edge,
        reason=reason,
        action=action,
    )

    return {"allowed": allowed, "action": action, "reason": reason}
