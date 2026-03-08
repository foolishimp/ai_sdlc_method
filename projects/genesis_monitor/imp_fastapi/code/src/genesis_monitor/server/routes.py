# Implements: REQ-F-DASH-001, REQ-F-DASH-002, REQ-F-DASH-003, REQ-F-DASH-004, REQ-F-DASH-005, REQ-F-DASH-006, REQ-F-STREAM-002
# Implements: REQ-F-VREL-003, REQ-F-CDIM-002, REQ-F-REGIME-002, REQ-F-CONSC-003, REQ-F-PROTO-001
# Implements: REQ-F-MTEN-001, REQ-F-MTEN-002, REQ-F-MTEN-003
# Implements: REQ-F-ELIN-001, REQ-F-ELIN-002, REQ-F-ELIN-003, REQ-F-FLIN-001, REQ-F-FLIN-002
# Implements: REQ-F-GVIZ-001, REQ-F-GVIZ-002, REQ-F-GVIZ-003, REQ-F-GVIZ-004, REQ-F-GVIZ-005
# Implements: REQ-F-TSER-001, REQ-F-TSER-002, REQ-F-TSER-003, REQ-F-TSER-004
"""FastAPI route definitions — page routes, fragment routes, SSE endpoint."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import math

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse

from genesis_monitor.projections import (
    build_compliance_report,
    build_consciousness_timeline,
    build_convergence_table,
    build_dimension_coverage,
    build_feature_matrix,
    build_graph_mermaid,
    build_project_tree,
    build_regime_summary,
    build_spawn_tree,
)
from genesis_monitor.projections.feature_module_map import build_feature_module_map
from genesis_monitor.projections.temporal import (
    get_event_density,
    reconstruct_features,
    reconstruct_status,
)
from genesis_monitor.projections.traceability import build_traceability_view
from genesis_monitor.index import EventIndex

if TYPE_CHECKING:
    from genesis_monitor.registry import ProjectRegistry
    from genesis_monitor.server.broadcaster import SSEBroadcaster


def create_router(registry: ProjectRegistry, broadcaster: SSEBroadcaster) -> APIRouter:
    """Create the FastAPI router with all routes."""
    router = APIRouter()
    _start_time = time.time()

    def _get_historical_state(project, t: str | None, design: str | None = None):
        events = project.events
        if design:
            events = [e for e in events if e.project == design]
        if t:
            try:
                limit = datetime.fromisoformat(t.replace('Z', '+00:00'))
                events = [e for e in events if e.timestamp <= limit]
                features = reconstruct_features(events, limit)
                status = reconstruct_status(events, limit)
                return events, features, status
            except Exception:
                pass
        if design:
            limit = datetime.now(tz=UTC)
            features = reconstruct_features(events, limit)
            status = reconstruct_status(events, limit)
            return events, features, status
        return events, project.features, project.status

    @router.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        projects = registry.list_projects()
        tree = build_project_tree(projects)
        return request.app.state.templates.TemplateResponse(
            request,
            "index.html",
            {"projects": projects, "tree": tree},
        )

    @router.get("/project/{project_id}", response_class=HTMLResponse)
    async def project_detail(request: Request, project_id: str, t: str = None, design: str = None):
        project = registry.get_project(project_id)
        if not project:
            return HTMLResponse("<h1>Project not found</h1>", status_code=404)
        events, features, status = _get_historical_state(project, t, design)
        available_designs = sorted(list(set(e.project for e in project.events if e.project)))
        design_counts = {d: sum(1 for e in project.events if e.project == d)
                         for d in available_designs}
        graph_mermaid = build_graph_mermaid(project.topology, status)
        convergence = build_convergence_table(status, events)
        matrix = build_feature_matrix(features)
        feature_module_map = build_feature_module_map(features, project.traceability)
        signals = status.telem_signals if status else []
        spawn_tree = build_spawn_tree(features)
        dimensions = build_dimension_coverage(project.topology, features, project.constraints)
        regimes = build_regime_summary(events)
        consciousness = build_consciousness_timeline(events)
        compliance = build_compliance_report(project)
        traceability = build_traceability_view(features, project.traceability)
        return request.app.state.templates.TemplateResponse(
            request,
            "project.html",
            {
                "project": project,
                "design": design,
                "t": t,
                "available_designs": available_designs,
                "design_counts": design_counts,
                "graph_mermaid": graph_mermaid,
                "convergence": convergence,
                "matrix": matrix,
                "feature_module_map": feature_module_map,
                "features": features,
                "signals": signals,
                "events": events,
                "all_events": events,
                "recent_events": events[-50:],
                "density": get_event_density(events),
                "spawn_tree": spawn_tree,
                "dimensions": dimensions,
                "regimes": regimes,
                "consciousness": consciousness,
                "compliance": compliance,
                "traceability": traceability,
                "current_time": datetime.now().strftime("%H:%M:%S"),
            },
        )

    @router.get("/fragments/project/{project_id}/graph", response_class=HTMLResponse)
    async def fragment_graph(request: Request, project_id: str, t: str = None, design: str = None):
        project = registry.get_project(project_id)
        if not project: return HTMLResponse("")
        _, _, status = _get_historical_state(project, t, design)
        mermaid = build_graph_mermaid(project.topology, status)
        return request.app.state.templates.TemplateResponse(
            request,
            "fragments/_graph.html",
            {"mermaid_code": mermaid, "current_time": datetime.now().strftime("%H:%M:%S")},
        )

    @router.get("/fragments/project/{project_id}/convergence", response_class=HTMLResponse)
    async def fragment_convergence(request: Request, project_id: str, t: str = None, design: str = None):
        project = registry.get_project(project_id)
        if not project: return HTMLResponse("")
        events, _, status = _get_historical_state(project, t, design)
        convergence = build_convergence_table(status, events)
        return request.app.state.templates.TemplateResponse(
            request,
            "fragments/_convergence.html",
            {"convergence": convergence, "current_time": datetime.now().strftime("%H:%M:%S")},
        )

    @router.get("/fragments/project/{project_id}/features", response_class=HTMLResponse)
    async def fragment_features(request: Request, project_id: str, t: str = None, design: str = None):
        project = registry.get_project(project_id)
        if not project: return HTMLResponse("")
        _, features, _ = _get_historical_state(project, t, design)
        return request.app.state.templates.TemplateResponse(
            request,
            "fragments/_features.html",
            {"features": features, "current_time": datetime.now().strftime("%H:%M:%S")},
        )

    @router.get("/fragments/project/{project_id}/gantt", response_class=HTMLResponse)
    async def fragment_gantt(request: Request, project_id: str, t: str = None, design: str = None):
        project = registry.get_project(project_id)
        if not project: return HTMLResponse("")
        _, features, _ = _get_historical_state(project, t, design)
        matrix = build_feature_matrix(features)
        return request.app.state.templates.TemplateResponse(
            request,
            "fragments/_gantt.html",
            {"matrix": matrix, "current_time": datetime.now().strftime("%H:%M:%S")},
        )

    @router.get("/fragments/project/{project_id}/events", response_class=HTMLResponse)
    async def fragment_events(request: Request, project_id: str, t: str = None, design: str = None):
        project = registry.get_project(project_id)
        if not project: return HTMLResponse("")
        events, _, _ = _get_historical_state(project, t, design)
        return request.app.state.templates.TemplateResponse(
            request,
            "fragments/_events.html",
            {"events": events[-50:], "current_time": datetime.now().strftime("%H:%M:%S")},
        )

    @router.get("/fragments/project/{project_id}/telem", response_class=HTMLResponse)
    async def fragment_telem(request: Request, project_id: str, t: str = None, design: str = None):
        project = registry.get_project(project_id)
        if not project: return HTMLResponse("")
        _, _, status = _get_historical_state(project, t, design)
        signals = status.telem_signals if status else []
        return request.app.state.templates.TemplateResponse(
            request,
            "fragments/_telem.html",
            {"signals": signals, "current_time": datetime.now().strftime("%H:%M:%S")},
        )

    @router.get("/fragments/tree", response_class=HTMLResponse)
    async def fragment_tree(request: Request):
        projects = registry.list_projects()
        tree = build_project_tree(projects)
        return request.app.state.templates.TemplateResponse(
            request,
            "fragments/_tree.html",
            {"projects": projects, "tree": tree},
        )

    @router.get("/fragments/project-list", response_class=HTMLResponse)
    async def fragment_project_list(request: Request):
        projects = registry.list_projects()
        return request.app.state.templates.TemplateResponse(
            request,
            "fragments/_project_list.html",
            {"projects": projects},
        )

    @router.get("/fragments/project/{project_id}/edges", response_class=HTMLResponse)
    async def fragment_edges(request: Request, project_id: str, t: str = None, design: str = None):
        project = registry.get_project(project_id)
        if not project: return HTMLResponse("")
        events, _, status = _get_historical_state(project, t, design)
        convergence = build_convergence_table(status, events)
        return request.app.state.templates.TemplateResponse(
            request,
            "fragments/_edges.html",
            {"convergence": convergence, "current_time": datetime.now().strftime("%H:%M:%S")},
        )

    @router.get("/fragments/project/{project_id}/spawn-tree", response_class=HTMLResponse)
    async def fragment_spawn_tree(request: Request, project_id: str, t: str = None, design: str = None):
        project = registry.get_project(project_id)
        if not project: return HTMLResponse("")
        _, features, _ = _get_historical_state(project, t, design)
        spawn_tree = build_spawn_tree(features)
        return request.app.state.templates.TemplateResponse(
            request,
            "fragments/_spawn_tree.html",
            {"spawn_tree": spawn_tree, "current_time": datetime.now().strftime("%H:%M:%S")},
        )

    @router.get("/fragments/project/{project_id}/dimensions", response_class=HTMLResponse)
    async def fragment_dimensions(request: Request, project_id: str, t: str = None, design: str = None):
        project = registry.get_project(project_id)
        if not project: return HTMLResponse("")
        _, features, _ = _get_historical_state(project, t, design)
        dimensions = build_dimension_coverage(project.topology, features, project.constraints)
        return request.app.state.templates.TemplateResponse(
            request,
            "fragments/_dimensions.html",
            {"dimensions": dimensions, "current_time": datetime.now().strftime("%H:%M:%S")},
        )

    @router.get("/fragments/project/{project_id}/regimes", response_class=HTMLResponse)
    async def fragment_regimes(request: Request, project_id: str, t: str = None, design: str = None):
        project = registry.get_project(project_id)
        if not project: return HTMLResponse("")
        events, _, _ = _get_historical_state(project, t, design)
        regimes = build_regime_summary(events)
        return request.app.state.templates.TemplateResponse(
            request,
            "fragments/_regimes.html",
            {"regimes": regimes, "current_time": datetime.now().strftime("%H:%M:%S")},
        )

    @router.get("/fragments/project/{project_id}/consciousness", response_class=HTMLResponse)
    async def fragment_consciousness(request: Request, project_id: str, t: str = None, design: str = None):
        project = registry.get_project(project_id)
        if not project: return HTMLResponse("")
        events, _, _ = _get_historical_state(project, t, design)
        consciousness = build_consciousness_timeline(events)
        return request.app.state.templates.TemplateResponse(
            request,
            "fragments/_consciousness.html",
            {"consciousness": consciousness, "current_time": datetime.now().strftime("%H:%M:%S")},
        )

    @router.get("/fragments/project/{project_id}/compliance", response_class=HTMLResponse)
    async def fragment_compliance(request: Request, project_id: str, t: str = None, design: str = None):
        project = registry.get_project(project_id)
        if not project: return HTMLResponse("")
        compliance = build_compliance_report(project)
        return request.app.state.templates.TemplateResponse(
            request,
            "fragments/_compliance.html",
            {"compliance": compliance, "current_time": datetime.now().strftime("%H:%M:%S")},
        )

    @router.get("/fragments/project/{project_id}/traceability", response_class=HTMLResponse)
    async def fragment_traceability(request: Request, project_id: str, t: str = None, design: str = None):
        project = registry.get_project(project_id)
        if not project: return HTMLResponse("")
        _, features, _ = _get_historical_state(project, t, design)
        traceability = build_traceability_view(features, project.traceability)
        return request.app.state.templates.TemplateResponse(
            request,
            "fragments/_traceability.html",
            {"traceability": traceability, "current_time": datetime.now().strftime("%H:%M:%S")},
        )

    @router.get("/fragments/project/{project_id}/feature-module-map", response_class=HTMLResponse)
    async def fragment_feature_module_map(request: Request, project_id: str, t: str = None, design: str = None):
        project = registry.get_project(project_id)
        if not project: return HTMLResponse("")
        _, features, _ = _get_historical_state(project, t, design)
        feature_module_map = build_feature_module_map(features, project.traceability)
        return request.app.state.templates.TemplateResponse(
            request,
            "fragments/_feature_module_map.html",
            {"feature_module_map": feature_module_map, "current_time": datetime.now().strftime("%H:%M:%S")},
        )

    @router.get("/lineage/source/feature/{feature_id}", response_class=HTMLResponse)
    async def get_feature_source(request: Request, feature_id: str):
        projects = registry.list_projects()
        target_proj = None
        for p in projects:
            for f in p.features:
                if f.feature_id == feature_id:
                    target_proj = p
                    break
            if target_proj: break
        if not target_proj: return HTMLResponse("Feature not found.", status_code=404)
        feat_path = target_proj.path / "features" / "active" / f"{feature_id}.yml"
        if not feat_path.exists():
            feat_path = target_proj.path / "features" / "completed" / f"{feature_id}.yml"
        if not feat_path.exists(): return HTMLResponse("Source not found.", status_code=404)
        return HTMLResponse(f"<div class='raw-data-block'><pre><code>{feat_path.read_text()}</code></pre></div>")

    def _get_index(project, t: str | None, design: str | None) -> EventIndex:
        """Return the pre-built index, or a time-scoped reconstruction for scrubber use."""
        if t or design:
            events, _, _ = _get_historical_state(project, t, design)
            return EventIndex.build(events)
        return project.index or EventIndex.build(project.events)

    @router.get("/project/{project_id}/timeline", response_class=HTMLResponse)
    async def project_timeline(request: Request, project_id: str, t: str = None, design: str = None,
                               feature: str = None, edge: str = None, status: str = None):
        project = registry.get_project(project_id)
        if not project:
            return HTMLResponse("<h1>Project not found</h1>", status_code=404)
        idx = _get_index(project, t, design)
        runs = idx.timeline_fuzzy(feature=feature or None, edge=edge or None, status=status or None)
        days = idx.days(runs)
        available_designs = sorted(list(set(e.project for e in project.events if e.project)))
        return request.app.state.templates.TemplateResponse(
            request,
            "timeline.html",
            {
                "project": project,
                "runs": runs,
                "days": days,
                "design": design,
                "t": t,
                "filter_feature": feature or "",
                "filter_edge": edge or "",
                "filter_status": status or "",
                "available_designs": available_designs,
                "total_runs": idx.total_runs,
                "converged_count": idx.converged_count,
                "failed_count": idx.failed_count,
                "in_progress_count": idx.in_progress_count,
            },
        )

    @router.get("/fragments/project/{project_id}/timeline-runs", response_class=HTMLResponse)
    async def fragment_timeline_runs(request: Request, project_id: str, t: str = None, design: str = None,
                                     feature: str = None, edge: str = None, status: str = None):
        project = registry.get_project(project_id)
        if not project: return HTMLResponse("")
        idx = _get_index(project, t, design)
        runs = idx.timeline_fuzzy(feature=feature or None, edge=edge or None, status=status or None)
        days = idx.days(runs)
        return request.app.state.templates.TemplateResponse(
            request,
            "fragments/_timeline_runs.html",
            {"project": project, "days": days, "runs": runs},
        )

    @router.get("/fragments/project/{project_id}/run-detail/{run_id}", response_class=HTMLResponse)
    async def fragment_run_detail(request: Request, project_id: str, run_id: str):
        project = registry.get_project(project_id)
        if not project: return HTMLResponse("")
        # O(1) index lookup
        idx = project.index or EventIndex.build(project.events)
        run = idx.run_detail(run_id)
        if not run: return HTMLResponse("<p>Run not found.</p>")
        return request.app.state.templates.TemplateResponse(
            request,
            "fragments/_run_detail.html",
            {"project": project, "run": run},
        )

    @router.get("/project/{project_id}/feature/{feature_id}", response_class=HTMLResponse)
    async def feature_lineage(request: Request, project_id: str, feature_id: str,
                               t: str = None, design: str = None):
        project = registry.get_project(project_id)
        if not project:
            return HTMLResponse("<h1>Project not found</h1>", status_code=404)
        _, features, _ = _get_historical_state(project, t, design)
        idx = _get_index(project, t, design)
        feature_runs = idx.feature_runs(feature_id)
        fv = next((f for f in features if f.feature_id == feature_id), None)
        return request.app.state.templates.TemplateResponse(
            request,
            "feature_lineage.html",
            {
                "project": project,
                "feature_id": feature_id,
                "fv": fv,
                "feature_runs": feature_runs,
                "design": design,
                "t": t,
            },
        )

    @router.get("/project/{project_id}/artifact", response_class=HTMLResponse)
    async def artifact_view(request: Request, project_id: str, path: str = ""):
        """Render a project artifact (document, code, test file) by relative path."""
        project = registry.get_project(project_id)
        if not project:
            return HTMLResponse("<h1>Project not found</h1>", status_code=404)
        if not path:
            return HTMLResponse("<p>No path specified.</p>", status_code=400)
        import html as _html
        from pathlib import Path as _Path
        artifact_path = _Path(path) if _Path(path).is_absolute() else project.path / path
        if not artifact_path.exists():
            return request.app.state.templates.TemplateResponse(
                request,
                "artifact.html",
                {"project": project, "path": path, "content": None, "error": "File not found"},
            )
        try:
            raw = artifact_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            return request.app.state.templates.TemplateResponse(
                request,
                "artifact.html",
                {"project": project, "path": path, "content": None, "error": str(e)},
            )
        suffix = artifact_path.suffix.lower()
        if suffix == ".md":
            # Simple markdown → HTML (headings, code blocks, paragraphs)
            content_type = "markdown"
        elif suffix in (".py", ".ts", ".js", ".yml", ".yaml", ".json", ".sh", ".toml"):
            content_type = "code"
        else:
            content_type = "text"
        return request.app.state.templates.TemplateResponse(
            request,
            "artifact.html",
            {
                "project": project,
                "path": path,
                "content": raw,
                "content_type": content_type,
                "suffix": suffix,
                "error": None,
            },
        )

    # ── Graph visualization helpers (REQ-F-GVIZ-001..005, ADR-007) ───────────────

    _CANONICAL_NODE_ORDER = [
        "intent", "requirements", "feature_decomposition", "design",
        "module_decomposition", "basis_projections", "code", "unit_tests",
        "uat_tests", "cicd", "telemetry",
    ]

    def _parse_edge_nodes(edge: str) -> tuple[str, str]:
        """Split 'intent→requirements' or 'code↔unit_tests' into (source, target)."""
        for sep in ("→", "↔", "->"):
            if sep in edge:
                parts = edge.split(sep, 1)
                return parts[0].strip(), parts[1].strip()
        clean = edge.strip()
        return clean, clean  # self-loop fallback

    def _build_graph_data(project_id: str, runs: list) -> dict:
        """Aggregate EdgeRun list into graph-data JSON for D3.js rendering.

        Returns: {project_id, nodes, runs, features}
        """
        # Collect unique nodes and their stats
        node_stats: dict[str, dict] = {}
        for run in runs:
            src, tgt = _parse_edge_nodes(run.edge or "")
            for nid in [n for n in [src, tgt] if n]:
                if nid not in node_stats:
                    node_stats[nid] = {
                        "id": nid,
                        "label": nid.replace("_", " ").title(),
                        "total_runs": 0,
                        "converged_count": 0,
                        "in_progress_count": 0,
                        "failed_count": 0,
                    }
                node_stats[nid]["total_runs"] += 1
                if run.status == "converged":
                    node_stats[nid]["converged_count"] += 1
                elif run.status == "in_progress":
                    node_stats[nid]["in_progress_count"] += 1
                else:
                    node_stats[nid]["failed_count"] += 1

        # Sort nodes by canonical SDLC order, unknown types appended at right
        def _node_order(nid: str) -> int:
            try:
                return _CANONICAL_NODE_ORDER.index(nid)
            except ValueError:
                return len(_CANONICAL_NODE_ORDER)

        nodes = sorted(node_stats.values(), key=lambda n: _node_order(n["id"]))
        for i, n in enumerate(nodes):
            n["x_order"] = i

        # Feature colour assignment: stable, sorted feature list
        feature_ids = sorted({r.feature for r in runs if r.feature})
        colour_idx = {fid: i for i, fid in enumerate(feature_ids)}

        # Feature status: most severe wins (in_progress > failed > converged)
        _severity = {"in_progress": 2, "failed": 1, "aborted": 1, "converged": 0, "": 0}
        feature_status: dict[str, str] = {}
        feature_run_count: dict[str, int] = {}
        for run in runs:
            if not run.feature:
                continue
            feature_run_count[run.feature] = feature_run_count.get(run.feature, 0) + 1
            cur_sev = _severity.get(feature_status.get(run.feature, ""), 0)
            new_sev = _severity.get(run.status, 0)
            if new_sev > cur_sev:
                feature_status[run.feature] = run.status if run.status != "aborted" else "failed"

        # Build run objects for D3
        run_dicts = []
        for run in runs:
            src, tgt = _parse_edge_nodes(run.edge or "")
            run_dicts.append({
                "run_id": run.run_id,
                "feature": run.feature or "",
                "edge": run.edge or "",
                "source": src,
                "target": tgt,
                "status": run.status,
                "iteration_count": run.iteration_count,
                "final_delta": run.final_delta,
                "started_at": run.started_at.isoformat(),
                "ended_at": run.ended_at.isoformat() if run.ended_at else None,
                "duration_seconds": run.duration_seconds,
                "colour_index": colour_idx.get(run.feature or "", 0),
            })

        # Feature summary sorted: in_progress first, failed, converged, then by ID
        _status_sort = {"in_progress": 0, "failed": 1, "converged": 2}
        feature_list = [
            {
                "id": fid,
                "colour_index": colour_idx[fid],
                "run_count": feature_run_count.get(fid, 0),
                "status": feature_status.get(fid, "converged"),
            }
            for fid in feature_ids
        ]
        feature_list.sort(key=lambda f: (_status_sort.get(f["status"], 3), f["id"]))

        return {
            "project_id": project_id,
            "nodes": nodes,
            "runs": run_dicts,
            "features": feature_list,
        }

    @router.get("/project/{project_id}/timeline/graph-data")
    async def timeline_graph_data(
        request: Request,
        project_id: str,
        t: str = None,
        design: str = None,
        feature: str = None,
        edge: str = None,
        status: str = None,
    ):
        """JSON graph data for D3.js Event Trail visualization. REQ-F-GVIZ-001."""
        project = registry.get_project(project_id)
        if not project:
            return JSONResponse({"error": "not found"}, status_code=404)
        idx = _get_index(project, t, design)
        runs = idx.timeline_fuzzy(feature=feature or None, edge=edge or None, status=status or None)
        return JSONResponse(_build_graph_data(project_id, runs))

    # ── SSE / health ──────────────────────────────────────────────────────────

    @router.get("/events/stream")
    async def sse_stream(request: Request):
        return EventSourceResponse(broadcaster.subscribe(), ping=5)

    @router.get("/api/health")
    async def health():
        uptime = int(time.time() - _start_time)
        return {"status": "ok", "projects": len(registry.list_projects()), "uptime_seconds": uptime}

    return router
