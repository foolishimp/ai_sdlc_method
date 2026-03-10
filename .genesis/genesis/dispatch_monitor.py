# Implements: REQ-F-SENSE-001, REQ-F-DISPATCH-001
"""dispatch_monitor — event stream watcher that drives autonomous dispatch.

A lightweight monitor that watches events.jsonl for appends and calls
run_dispatch_loop() on each change. This is the "constant dispatch monitor
over events" that makes /gen-start --auto a living homeostatic loop.

Two modes:
1. Single-pass (default): called inline by gen-start --auto on each iteration
2. Daemon mode: run_monitor() watches the file continuously (future use)

Design:
- Checks mtime on events.jsonl — if changed since last check, calls dispatch loop
- Does not use watchdog or inotify — stdlib only (no new dependencies)
- Daemon mode: polls every poll_interval_s seconds (default 0.5s)
- Terminates on KeyboardInterrupt or when max_rounds reached
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from .dispatch_loop import run_dispatch_loop


# ── State ─────────────────────────────────────────────────────────────────────


@dataclass
class MonitorState:
    """Mutable state for the file watcher."""
    last_mtime: float = 0.0
    last_size: int = 0
    rounds_fired: int = 0
    total_dispatched: int = 0
    total_converged: int = 0
    fh_pending: int = 0


# ── F_H resolution detection ──────────────────────────────────────────────────

# Events that signal an F_H gate has been resolved — dispatch can continue
FH_RESOLUTION_EVENTS = {
    "consensus_reached",      # CONSENSUS quorum attained
    "vote_cast",              # Final vote that tips quorum
    "review_approved",        # Human approved via /gen-review
    "feature_proposal_approved",  # PROP approved via /gen-review-proposal
    "edge_converged",         # Any edge that unblocks a dependent
}


def _events_since(events_path: Path, offset: int) -> list[dict]:
    """Read new events appended after byte offset."""
    events = []
    try:
        with open(events_path, "r") as f:
            f.seek(offset)
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except (FileNotFoundError, OSError):
        pass
    return events


def has_fh_resolution(events_path: Path, since_offset: int) -> bool:
    """True if any new events include an F_H resolution signal."""
    new_events = _events_since(events_path, since_offset)
    return any(e.get("event_type") in FH_RESOLUTION_EVENTS for e in new_events)


# ── Single-pass (inline) ──────────────────────────────────────────────────────


def check_and_dispatch(
    workspace_root: Path,
    state: MonitorState,
    events_path: Path | None = None,
    project_name: str = "ai_sdlc_method",
    max_rounds: int = 5,
) -> dict:
    """Single-pass dispatch check — call this on each gen-start --auto iteration.

    Returns immediately if events.jsonl hasn't changed since last call.
    Runs dispatch loop if new events detected.

    Args:
        workspace_root: Path to .ai-workspace parent
        state: MonitorState (persists mtime/size across calls in the same session)
        events_path: path to events.jsonl (defaults to workspace_root/.ai-workspace/events/events.jsonl)
        project_name: for OL events
        max_rounds: passed to run_dispatch_loop

    Returns:
        {
          "fired": bool,          # whether dispatch ran
          "dispatched": int,
          "converged": int,
          "fh_required": int,
          "fp_dispatched": int,
          "quiescent": bool,
        }
    """
    if events_path is None:
        events_path = workspace_root / ".ai-workspace" / "events" / "events.jsonl"

    try:
        stat = events_path.stat()
        current_mtime = stat.st_mtime
        current_size = stat.st_size
    except FileNotFoundError:
        return {"fired": False, "dispatched": 0, "converged": 0,
                "fh_required": 0, "fp_dispatched": 0, "quiescent": True}

    # No change since last check
    if current_mtime == state.last_mtime and current_size == state.last_size:
        return {"fired": False, "dispatched": 0, "converged": 0,
                "fh_required": 0, "fp_dispatched": 0, "quiescent": True}

    # Change detected — update state and run dispatch loop
    state.last_mtime = current_mtime
    state.last_size = current_size
    state.rounds_fired += 1

    result = run_dispatch_loop(
        workspace_root=workspace_root,
        events_path=events_path,
        project_name=project_name,
        max_rounds=max_rounds,
    )

    state.total_dispatched += result.get("dispatched", 0)
    state.total_converged += result.get("converged", 0)
    if result.get("fh_required", 0):
        state.fh_pending = result["fh_required"]
    else:
        state.fh_pending = 0

    return {
        "fired": True,
        "dispatched": result.get("dispatched", 0),
        "converged": result.get("converged", 0),
        "fh_required": result.get("fh_required", 0),
        "fp_dispatched": result.get("fp_dispatched", 0),
        "quiescent": result.get("quiescent", False),
    }


# ── Daemon mode (future: persistent background watcher) ───────────────────────


def run_monitor(
    workspace_root: Path,
    events_path: Path | None = None,
    project_name: str = "ai_sdlc_method",
    poll_interval_s: float = 0.5,
    max_rounds_per_fire: int = 5,
    max_total_fires: int = 1000,
    on_fh_required: callable | None = None,
) -> None:
    """Daemon mode: watch events.jsonl and dispatch on every append.

    Runs until KeyboardInterrupt or max_total_fires reached.

    Args:
        workspace_root: Path to .ai-workspace parent
        events_path: path to events.jsonl
        project_name: for OL events
        poll_interval_s: how often to check for changes (seconds)
        max_rounds_per_fire: passed to run_dispatch_loop per fire
        max_total_fires: safety limit on total dispatch runs
        on_fh_required: optional callback(fh_count) when F_H gates pending
    """
    if events_path is None:
        events_path = workspace_root / ".ai-workspace" / "events" / "events.jsonl"

    state = MonitorState()
    print(f"dispatch_monitor: watching {events_path} (poll={poll_interval_s}s)")

    try:
        fires = 0
        while fires < max_total_fires:
            result = check_and_dispatch(
                workspace_root=workspace_root,
                state=state,
                events_path=events_path,
                project_name=project_name,
                max_rounds=max_rounds_per_fire,
            )
            if result["fired"]:
                fires += 1
                print(
                    f"dispatch_monitor: fired={fires} "
                    f"dispatched={result['dispatched']} "
                    f"converged={result['converged']} "
                    f"fh_required={result['fh_required']} "
                    f"fp_dispatched={result['fp_dispatched']}"
                )
                if result["fh_required"] and on_fh_required:
                    on_fh_required(result["fh_required"])

            time.sleep(poll_interval_s)

    except KeyboardInterrupt:
        print(f"\ndispatch_monitor: stopped. Fired {fires} times, "
              f"total dispatched={state.total_dispatched}, "
              f"total converged={state.total_converged}")
