# Implements: REQ-F-CONSENSUS-001, REQ-F-CDX-006
"""Replay-driven CONSENSUS observer artifacts and closeout triggers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .commands import gen_consensus_close
from .consensus import current_cycle, format_timestamp, gating_comments, quorum_state, review_id_for
from .events import load_events
from .paths import RuntimePaths, bootstrap_workspace
from .projections import dump_yaml, load_yaml


@dataclass(frozen=True)
class ConsensusObserverResult:
    """Summary of one consensus observer reconciliation pass."""

    processed_reviews: int
    actions_written: int
    closeouts_emitted: int
    reviews: list[dict[str, Any]]


def _observer_dir(paths: RuntimePaths, review_id: str, cycle_id: str) -> Path:
    path = paths.consensus_reviews_dir / review_id / cycle_id / "observer"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _observer_state_path(paths: RuntimePaths, review_id: str, cycle_id: str) -> Path:
    return _observer_dir(paths, review_id, cycle_id) / "state.yml"


def _observer_actions_dir(paths: RuntimePaths, review_id: str, cycle_id: str) -> Path:
    path = _observer_dir(paths, review_id, cycle_id) / "actions"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sync_yaml(path: Path, payload: dict[str, Any]) -> bool:
    """Write one YAML document if it differs from the current content."""

    if path.exists():
        try:
            current = load_yaml(path)
        except Exception:
            current = None
        if current == payload:
            return False
    dump_yaml(path, payload)
    return True


def _sync_pending_disposition_actions(
    paths: RuntimePaths,
    state: dict[str, Any],
    *,
    actor: str,
    now_value: str,
    comments: list[dict[str, Any]],
) -> tuple[int, list[dict[str, Any]]]:
    """Write or clear advisory action files for outstanding gating comments."""

    actions_dir = _observer_actions_dir(paths, state["review_id"], state["cycle_id"])
    desired_paths: set[Path] = set()
    actions: list[dict[str, Any]] = []
    writes = 0

    for comment in comments:
        if comment.get("disposition"):
            continue
        payload = {
            "observer_id": actor,
            "trigger_reason": "pending_disposition",
            "review_id": state["review_id"],
            "cycle_id": state["cycle_id"],
            "artifact": state["artifact"],
            "source_run_id": comment.get("run_id"),
            "comment_id": comment["comment_id"],
            "participant": comment["participant"],
            "timestamp": comment["timestamp"],
            "content_ref": comment.get("content_ref", ""),
            "recorded_at": now_value,
        }
        path = actions_dir / f"dispose-{comment['comment_id']}.yml"
        desired_paths.add(path)
        if _sync_yaml(path, payload):
            writes += 1
        actions.append({"kind": "pending_disposition", "path": str(path), "comment_id": comment["comment_id"]})

    for existing in actions_dir.glob("*.yml"):
        if existing in desired_paths:
            continue
        existing.unlink()

    return writes, actions


def _observer_state_payload(
    state: dict[str, Any],
    *,
    actor: str,
    now_value: str,
    actions: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "observer_id": actor,
        "recorded_at": now_value,
        "review_id": state["review_id"],
        "cycle_id": state["cycle_id"],
        "artifact": state["artifact"],
        "source_run_id": state["terminal_run_id"],
        "current_cycle_open": state["current_cycle_open"],
        "outcome": state["outcome"],
        "terminal_run_id": state["terminal_run_id"],
        "gating_comments_remaining": list(state["gating_comments_remaining"]),
        "approve_votes": state["approve_votes"],
        "reject_votes": state["reject_votes"],
        "abstain_votes": state["abstain_votes"],
        "eligible_votes": state["eligible_votes"],
        "actions": actions,
    }


def _now_string(now: str | datetime | None) -> str:
    if isinstance(now, str):
        return now
    if isinstance(now, datetime):
        return format_timestamp(now)
    return format_timestamp(datetime.now(timezone.utc))


def run_consensus_observer(
    project_root: Path,
    *,
    review_id: str | None = None,
    actor: str = "consensus-observer",
    now: str | datetime | None = None,
) -> ConsensusObserverResult:
    """Reconcile open consensus reviews into derived observer artifacts."""

    paths = bootstrap_workspace(project_root)
    events = load_events(paths.events_file)
    review_ids = sorted(
        {
            candidate
            for event in events
            for candidate in [review_id_for(event)]
            if candidate
        }
    )
    if review_id is not None:
        review_ids = [candidate for candidate in review_ids if candidate == review_id]

    processed: list[dict[str, Any]] = []
    actions_written = 0
    closeouts_emitted = 0
    now_value = _now_string(now)

    for current_review_id in review_ids:
        cycle = current_cycle(events, current_review_id)
        if cycle is None:
            continue
        state = quorum_state(events, current_review_id, cycle["cycle_id"], now=now_value)
        comments = gating_comments(events, current_review_id, cycle["cycle_id"])
        writes, actions = _sync_pending_disposition_actions(
            paths,
            state,
            actor=actor,
            now_value=now_value,
            comments=comments,
        )
        actions_written += writes

        closeout_result = None
        if state["outcome"] in {"passed", "failed"} and state["terminal_run_id"] is None:
            closeout_result = gen_consensus_close(
                paths.project_root,
                review_id=current_review_id,
                cycle_id=cycle["cycle_id"],
                actor=actor,
                event_time=now_value,
            )
            if closeout_result["emitted"]:
                closeouts_emitted += 1
                events = load_events(paths.events_file)
                state = quorum_state(events, current_review_id, cycle["cycle_id"], now=now_value)

        state_path = _observer_state_path(paths, state["review_id"], state["cycle_id"])
        state_payload = _observer_state_payload(state, actor=actor, now_value=now_value, actions=actions)
        if _sync_yaml(state_path, state_payload):
            actions_written += 1

        processed.append(
            {
                "review_id": state["review_id"],
                "cycle_id": state["cycle_id"],
                "state_path": str(state_path),
                "outcome": state["outcome"],
                "terminal_run_id": state["terminal_run_id"],
                "pending_actions": actions,
                "closeout": closeout_result,
            }
        )

    return ConsensusObserverResult(
        processed_reviews=len(processed),
        actions_written=actions_written,
        closeouts_emitted=closeouts_emitted,
        reviews=processed,
    )


__all__ = ["ConsensusObserverResult", "run_consensus_observer"]
