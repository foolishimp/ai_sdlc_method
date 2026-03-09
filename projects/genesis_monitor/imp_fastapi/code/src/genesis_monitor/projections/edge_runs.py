# Implements: REQ-F-ELIN-001, REQ-F-ELIN-002, REQ-F-ELIN-005, REQ-F-EXEC-001
"""Group event stream into EdgeRun objects — one per (feature, edge) traversal.

An EdgeRun is a bounded sequence of events sharing a common (feature, edge) traversal:
  edge_started → iteration_completed × N → edge_converged | command_error | transaction_aborted

OL runId is used as the primary grouping key when present. For flat events,
the key is synthesised from (feature, edge, edge_started timestamp).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from genesis_monitor.models.events import Event


@dataclass
class IterationSummary:
    """Summary of one iterate() cycle within an edge run."""
    iteration: int
    timestamp: datetime
    delta: int | None
    status: str  # iterating | converged | blocked | failed
    evaluators_passed: int
    evaluators_failed: int
    evaluators_skipped: int
    evaluators_total: int
    context_hash: str
    evaluator_details: list[dict] = field(default_factory=list)  # from evaluator_detail events


@dataclass
class EdgeRun:
    """A single traversal of one graph edge for one feature."""
    run_id: str                          # OL runId or synthesised key
    feature: str                         # REQ-F-* ID
    edge: str                            # e.g. "code↔unit_tests"
    project: str
    started_at: datetime
    ended_at: datetime | None            # None if still in_progress
    status: str                          # in_progress | converged | failed | aborted
    convergence_type: str                # standard | question_answered | time_box_expired | ""
    iterations: list[IterationSummary] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)  # output file paths from OL outputs[]
    evaluator_details: list[dict] = field(default_factory=list)  # raw evaluator_detail events
    raw_events: list[Event] = field(default_factory=list)
    # ADR-009: executor attribution for this run's convergence
    executor: str = ""   # "engine" | "claude" | "retroactive" | "unknown"
    emission: str = ""   # "live" | "retroactive"

    @property
    def duration_seconds(self) -> float | None:
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()

    @property
    def final_delta(self) -> int | None:
        if not self.iterations:
            return None
        for it in reversed(self.iterations):
            if it.delta is not None:
                return it.delta
        return None

    @property
    def iteration_count(self) -> int:
        return len(self.iterations)


def build_edge_runs(events: list[Event]) -> list[EdgeRun]:
    """Group events into EdgeRun objects, sorted by started_at ascending.

    Algorithm:
    1. First pass: collect edge_started events → open a run bucket per (feature, edge).
    2. Second pass: route iteration_completed / evaluator_detail / edge_converged /
       command_error / transaction_aborted events into open buckets.
    3. Close buckets on terminal events.
    4. Any leftover iteration events not preceded by edge_started get a synthesised run.
    """
    # Key: (feature, edge) → list of open EdgeRun (may have multiple sequential runs on same edge)
    open_runs: dict[tuple[str, str], list[EdgeRun]] = {}
    completed: list[EdgeRun] = []

    def _get_feature_edge(ev: Event) -> tuple[str, str]:
        d = ev.data
        feature = (
            ev.data.get("feature")
            or d.get("run", {}).get("facets", {}).get("sdlc:req_keys", {}).get("feature_id", "")
            or d.get("run", {}).get("facets", {}).get("sdlc_req_keys", {}).get("feature_id", "")
            or ""
        )
        edge = (
            ev.data.get("edge")
            or d.get("run", {}).get("facets", {}).get("sdlc:req_keys", {}).get("edge", "")
            or d.get("job", {}).get("name", "")
            or ""
        )
        # Fallback: nested data dict (flat format)
        if not feature:
            feature = d.get("data", {}).get("feature", "") if isinstance(d.get("data"), dict) else ""
        if not edge:
            edge = d.get("data", {}).get("edge", "") if isinstance(d.get("data"), dict) else ""
        return feature, edge

    def _get_run_id(ev: Event) -> str:
        return (
            ev.data.get("run", {}).get("runId", "")
            or ev.data.get("run_id", "")
            or ""
        )

    def _extract_artifacts(ev: Event) -> list[str]:
        """Pull file paths from OL outputs[] and _metadata.original_data.file_path."""
        paths: list[str] = []
        outputs = ev.data.get("outputs", [])
        for out in outputs:
            if isinstance(out, dict):
                name = out.get("name", "")
                if name.startswith("file://"):
                    paths.append(name[7:])  # strip file://
                elif name:
                    paths.append(name)
        fp = (
            ev.data.get("_metadata", {}).get("original_data", {}).get("file_path", "")
            or ev.data.get("asset", "")
        )
        if fp and fp not in paths:
            paths.append(fp)
        return paths

    def _active_run(key: tuple[str, str]) -> EdgeRun | None:
        """Return the most recently opened (still open) run for this (feature, edge) key."""
        runs = open_runs.get(key, [])
        return runs[-1] if runs else None

    def _open_run(key: tuple[str, str], ev: Event, run_id: str) -> EdgeRun:
        run = EdgeRun(
            run_id=run_id or f"{key[0]}:{key[1]}:{ev.timestamp.isoformat()}",
            feature=key[0],
            edge=key[1],
            project=ev.project,
            started_at=ev.timestamp,
            ended_at=None,
            status="in_progress",
            convergence_type="",
        )
        open_runs.setdefault(key, []).append(run)
        return run

    def _close_run(key: tuple[str, str], ev: Event, status: str, conv_type: str = "") -> None:
        run = _active_run(key)
        if run is None:
            return
        run.raw_events.append(ev)
        run.ended_at = ev.timestamp
        run.status = status
        run.convergence_type = conv_type
        run.artifacts.extend(_extract_artifacts(ev))
        # ADR-009: derive executor/emission from closing event, then fallback to raw_events
        if ev.executor:
            run.executor = ev.executor
            run.emission = ev.emission
        else:
            for past in reversed(run.raw_events):
                if past.executor:
                    run.executor = past.executor
                    run.emission = past.emission
                    break
        open_runs[key].pop()
        if not open_runs[key]:
            del open_runs[key]
        completed.append(run)

    # Sort events chronologically before processing
    sorted_events = sorted(events, key=lambda e: e.timestamp)

    for ev in sorted_events:
        et = ev.event_type
        feature, edge = _get_feature_edge(ev)
        key = (feature, edge)
        run_id = _get_run_id(ev)

        if et == "edge_started":
            if not feature and not edge:
                continue
            run = _open_run(key, ev, run_id)
            run.raw_events.append(ev)

        elif et in ("iteration_completed", "iteration_started", "iteration_failed"):
            run = _active_run(key)
            if run is None and (feature or edge):
                # iteration without edge_started — synthesise a run
                run = _open_run(key, ev, run_id)

            if run is not None:
                run.raw_events.append(ev)
                if et == "iteration_completed":
                    d = ev.data
                    evals = d.get("evaluators", {})
                    # Support both nested dict and flat fields
                    if isinstance(evals, dict):
                        passed = evals.get("passed", 0)
                        failed = evals.get("failed", 0)
                        skipped = evals.get("skipped", 0)
                        total = evals.get("total", passed + failed + skipped)
                    else:
                        passed = failed = skipped = total = 0

                    status_str = d.get("status", "iterating")
                    delta_val = d.get("delta")
                    if delta_val is None:
                        delta_val = d.get("data", {}).get("delta") if isinstance(d.get("data"), dict) else None

                    it = IterationSummary(
                        iteration=d.get("iteration", len(run.iterations) + 1),
                        timestamp=ev.timestamp,
                        delta=delta_val,
                        status=status_str,
                        evaluators_passed=passed,
                        evaluators_failed=failed,
                        evaluators_skipped=skipped,
                        evaluators_total=total,
                        context_hash=d.get("context_hash", ""),
                    )
                    run.iterations.append(it)
                    run.artifacts.extend(_extract_artifacts(ev))

                    # Auto-close converged runs (some flows emit converged status on iteration event)
                    if status_str == "converged":
                        conv_type = d.get("convergence_type", "standard")
                        _close_run(key, ev, "converged", conv_type)

        elif et == "evaluator_detail":
            run = _active_run(key)
            if run is not None:
                detail = {
                    "check_name": ev.data.get("data", {}).get("check_name", "") if isinstance(ev.data.get("data"), dict) else "",
                    "check_type": ev.data.get("data", {}).get("check_type", "") if isinstance(ev.data.get("data"), dict) else "",
                    "result": ev.data.get("data", {}).get("result", "") if isinstance(ev.data.get("data"), dict) else "",
                    "expected": ev.data.get("data", {}).get("expected", "") if isinstance(ev.data.get("data"), dict) else "",
                    "observed": ev.data.get("data", {}).get("observed", "") if isinstance(ev.data.get("data"), dict) else "",
                    "iteration": ev.data.get("data", {}).get("iteration", 0) if isinstance(ev.data.get("data"), dict) else 0,
                }
                run.evaluator_details.append(detail)
                # Also link to the latest iteration
                if run.iterations:
                    run.iterations[-1].evaluator_details.append(detail)

        elif et == "edge_converged":
            conv_type = ""
            d = ev.data
            if isinstance(d.get("data"), dict):
                conv_type = d["data"].get("convergence_type", "standard")
            elif "convergence_type" in d:
                conv_type = d.get("convergence_type", "standard")
            _close_run(key, ev, "converged", conv_type or "standard")

        elif et in ("command_error", "iteration_failed"):
            _close_run(key, ev, "failed")

        elif et == "transaction_aborted":
            _close_run(key, ev, "aborted")

    # Collect still-open runs as in_progress
    for runs in open_runs.values():
        completed.extend(runs)

    # Sort chronologically
    return sorted(completed, key=lambda r: r.started_at)


def group_runs_by_day(runs: list[EdgeRun]) -> list[tuple[str, list[EdgeRun]]]:
    """Return runs grouped by UTC date, as [(date_str, [EdgeRun, ...]), ...]."""
    from collections import defaultdict
    by_day: dict[str, list[EdgeRun]] = defaultdict(list)
    for run in runs:
        day = run.started_at.strftime("%Y-%m-%d")
        by_day[day].append(run)
    return sorted(by_day.items())
