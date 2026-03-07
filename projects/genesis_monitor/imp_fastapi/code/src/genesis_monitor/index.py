# Implements: REQ-F-ELIN-001, REQ-F-ELIN-002, REQ-F-ELIN-005, ADR-004
"""EventIndex — built once at project load, queried O(1) per request.

Inspired by Prometheus TSDB / Loki label index / Jaeger trace store:
  - One pass over events at startup to build secondary indices
  - All HTTP handlers query the index, never the raw event list
  - Incremental append on file change (no full rebuild)

The OL event stream is a distributed trace:
  run_id  ≡ trace ID
  EdgeRun ≡ trace (edge_started → iterations → edge_converged)
  Iteration ≡ span
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import datetime, date

from genesis_monitor.models.events import Event
from genesis_monitor.projections.edge_runs import EdgeRun, build_edge_runs


class EventIndex:
    """Secondary index over a project's event stream.

    Build once:  EventIndex.build(events)
    Query often: index.timeline(...), index.feature_runs(id), index.run_detail(run_id)
    """

    def __init__(self) -> None:
        # Ordered chronologically — for range queries (scrubber / replay)
        self._runs: list[EdgeRun] = []

        # Secondary indices — all O(1) lookup
        self._by_run_id: dict[str, EdgeRun] = {}
        self._by_feature: dict[str, list[EdgeRun]] = defaultdict(list)
        self._by_edge: dict[str, list[EdgeRun]] = defaultdict(list)
        self._by_day: dict[date, list[EdgeRun]] = defaultdict(list)
        self._by_status: dict[str, list[EdgeRun]] = defaultdict(list)

        # Metadata
        self.event_count: int = 0
        self.built_at: datetime = datetime.now()

    # ── Build ───────────────────────────────────────────────────────────────

    @classmethod
    def build(cls, events: list[Event]) -> "EventIndex":
        """Build the index from the full event list. O(n) one-time cost."""
        idx = cls()
        idx.event_count = len(events)
        runs = build_edge_runs(events)
        for run in runs:
            idx._index_run(run)
        idx.built_at = datetime.now()
        return idx

    def _index_run(self, run: EdgeRun) -> None:
        """Add one EdgeRun to all secondary indices."""
        self._runs.append(run)
        self._by_run_id[run.run_id] = run
        if run.feature:
            self._by_feature[run.feature].append(run)
        if run.edge:
            self._by_edge[run.edge].append(run)
        day = run.started_at.date()
        self._by_day[day].append(run)
        self._by_status[run.status].append(run)

    def append(self, new_events: list[Event]) -> None:
        """Incrementally update the index with newly appended events.

        Re-runs build_edge_runs over ALL events (including existing) so that
        open runs can be completed by the new events. Efficient enough at
        current dogfood scale; replace with partial-rebuild at >100k events.
        """
        # Clear and rebuild from scratch — Phase 2 will do true incremental
        all_events = []
        for run in self._runs:
            all_events.extend(run.raw_events)
        all_events.extend(new_events)
        rebuilt = EventIndex.build(all_events)
        self._runs = rebuilt._runs
        self._by_run_id = rebuilt._by_run_id
        self._by_feature = rebuilt._by_feature
        self._by_edge = rebuilt._by_edge
        self._by_day = rebuilt._by_day
        self._by_status = rebuilt._by_status
        self.event_count = rebuilt.event_count

    # ── Query API ───────────────────────────────────────────────────────────

    def timeline(
        self,
        *,
        feature: str | None = None,
        edge: str | None = None,
        status: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[EdgeRun]:
        """Return EdgeRuns matching all provided filters, chronological order."""
        # Start from the smallest candidate set
        if feature and edge:
            candidates = [r for r in self._by_feature.get(feature, []) if r.edge == edge]
        elif feature:
            candidates = list(self._by_feature.get(feature, []))
        elif edge:
            candidates = list(self._by_edge.get(edge, []))
        elif status:
            candidates = list(self._by_status.get(status, []))
        else:
            candidates = list(self._runs)

        # Apply remaining filters
        if status and not (feature and not edge):
            candidates = [r for r in candidates if r.status == status]
        if since:
            candidates = [r for r in candidates if r.started_at >= since]
        if until:
            candidates = [r for r in candidates if r.started_at <= until]

        return sorted(candidates, key=lambda r: r.started_at)

    def timeline_fuzzy(
        self,
        *,
        feature: str | None = None,
        edge: str | None = None,
        status: str | None = None,
    ) -> list[EdgeRun]:
        """Substring-match filter — for user-entered partial queries."""
        runs = list(self._runs)
        if feature:
            runs = [r for r in runs if feature.lower() in r.feature.lower()]
        if edge:
            runs = [r for r in runs if edge.lower() in r.edge.lower()]
        if status:
            runs = [r for r in runs if r.status == status]
        return runs

    def feature_runs(self, feature_id: str) -> list[EdgeRun]:
        """All EdgeRuns for a feature, ordered chronologically."""
        return sorted(self._by_feature.get(feature_id, []), key=lambda r: r.started_at)

    def run_detail(self, run_id: str) -> EdgeRun | None:
        """O(1) lookup of a single EdgeRun by run_id."""
        return self._by_run_id.get(run_id)

    def days(self, runs: list[EdgeRun] | None = None) -> list[tuple[str, list[EdgeRun]]]:
        """Group runs by calendar day. Returns [(date_str, [runs]), ...] sorted."""
        target = runs if runs is not None else self._runs
        grouped: dict[str, list[EdgeRun]] = defaultdict(list)
        for run in target:
            grouped[run.started_at.strftime("%Y-%m-%d")].append(run)
        return sorted(grouped.items())

    def state_at(self, until: datetime, events: list[Event]) -> "EventIndex":
        """Reconstruct index from only events up to `until`. Enables time-travel."""
        filtered = [e for e in events if e.timestamp <= until]
        return EventIndex.build(filtered)

    # ── Summary stats ───────────────────────────────────────────────────────

    @property
    def total_runs(self) -> int:
        return len(self._runs)

    @property
    def converged_count(self) -> int:
        return len(self._by_status.get("converged", []))

    @property
    def in_progress_count(self) -> int:
        return len(self._by_status.get("in_progress", []))

    @property
    def failed_count(self) -> int:
        return (
            len(self._by_status.get("failed", []))
            + len(self._by_status.get("aborted", []))
        )

    @property
    def features(self) -> list[str]:
        return sorted(self._by_feature.keys())

    @property
    def edges(self) -> list[str]:
        return sorted(self._by_edge.keys())
