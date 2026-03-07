"""Traceability and release analysis helpers for the Codex runtime."""

from __future__ import annotations

from collections import defaultdict
import hashlib
from pathlib import Path
import re
import subprocess
import unicodedata

import yaml

from .events import utc_now
from .paths import RuntimePaths
from .projections import (
    compute_aggregated_view,
    compute_context_hash,
    determine_next_edge,
    feature_lookup,
    iter_features,
    load_project_constraints,
)


REQ_RE = re.compile(r"REQ-[A-Z]+-[A-Z0-9]+-\d+")
IMPLEMENTS_RE = re.compile(r"Implements:\s*(REQ-[A-Z]+-[A-Z0-9]+-\d+)")
VALIDATES_RE = re.compile(r"Validates:\s*(REQ-[A-Z]+-[A-Z0-9]+-\d+)")
TELEMETRY_RE = re.compile(r"req\s*=\s*[\"'](REQ-[A-Z]+-[A-Z0-9]+-\d+)[\"']")


def _iter_project_files(project_root: Path):
    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", ".ai-workspace", "__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        yield path


def _read_text(path: Path) -> str:
    try:
        return path.read_text()
    except UnicodeDecodeError:
        return ""


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalized_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw
    return unicodedata.normalize("NFC", text).encode("utf-8")


def collect_req_inventory(project_root: Path) -> set[str]:
    """Collect all REQ keys mentioned in the specification tree."""

    spec_root = project_root / "specification"
    inventory: set[str] = set()
    if not spec_root.exists():
        return inventory
    for path in spec_root.rglob("*"):
        if not path.is_file():
            continue
        inventory.update(REQ_RE.findall(_read_text(path)))
    return inventory


def scan_req_tags(project_root: Path) -> dict:
    """Scan project files for Implements/Validates/telemetry tags."""

    code_tags: dict[str, set[str]] = defaultdict(set)
    test_tags: dict[str, set[str]] = defaultdict(set)
    telemetry_tags: dict[str, set[str]] = defaultdict(set)
    untagged_code: list[str] = []
    untagged_tests: list[str] = []

    for path in _iter_project_files(project_root):
        text = _read_text(path)
        if not text:
            continue
        path_str = str(path.relative_to(project_root))
        implements = set(IMPLEMENTS_RE.findall(text))
        validates = set(VALIDATES_RE.findall(text))
        telemetry = set(TELEMETRY_RE.findall(text))

        is_test = any(part in {"tests", "test", "spec"} for part in path.parts) or path.name.startswith("test_")
        if is_test:
            if validates:
                for req in validates:
                    test_tags[req].add(path_str)
            elif path.suffix in {".py", ".ts", ".js", ".go", ".rs", ".java", ".scala"}:
                untagged_tests.append(path_str)
        else:
            if implements:
                for req in implements:
                    code_tags[req].add(path_str)
            elif path.suffix in {".py", ".ts", ".js", ".go", ".rs", ".java", ".scala"} and path.parts[0] not in {"docs"}:
                untagged_code.append(path_str)

        for req in telemetry:
            telemetry_tags[req].add(path_str)

    return {
        "code_tags": {req: sorted(paths) for req, paths in code_tags.items()},
        "test_tags": {req: sorted(paths) for req, paths in test_tags.items()},
        "telemetry_tags": {req: sorted(paths) for req, paths in telemetry_tags.items()},
        "untagged_code": sorted(untagged_code),
        "untagged_tests": sorted(untagged_tests),
    }


def resolve_context_dir(paths: RuntimePaths) -> Path:
    """Resolve the tenant context directory for manifest/checkpoint operations."""

    if paths.codex_context_dir.exists():
        return paths.codex_context_dir
    return paths.workspace_root / "context"


def build_context_manifest(paths: RuntimePaths) -> dict:
    """Build a deterministic context manifest from the tenant context directory."""

    context_dir = resolve_context_dir(paths)
    entries = []
    if context_dir.exists():
        for path in sorted(context_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.name == "context_manifest.yml":
                continue
            normalized = _normalized_bytes(path)
            entries.append(
                {
                    "path": str(path.relative_to(context_dir)),
                    "sha256": f"sha256:{_sha256_hex(normalized)}",
                    "bytes": len(normalized),
                }
            )

    aggregate_payload = yaml.safe_dump(entries, sort_keys=True).encode("utf-8")
    return {
        "version": "1.0.0",
        "generated_at": utc_now(),
        "algorithm": "sha256-canonical-v1",
        "aggregate_hash": f"sha256:{_sha256_hex(aggregate_payload)}",
        "entries": entries,
    }


def _scan_design_paths(project_root: Path, req_key: str) -> list[str]:
    matches: list[str] = []
    for path in _iter_project_files(project_root):
        if not any(part in {"design", "docs"} for part in path.parts):
            continue
        if req_key in _read_text(path):
            matches.append(str(path.relative_to(project_root)))
    return sorted(matches)


def _max_feature_iteration(feature_doc: dict) -> int | None:
    iterations = [
        int(data.get("iteration"))
        for data in feature_doc.get("trajectory", {}).values()
        if isinstance(data, dict) and data.get("iteration") is not None
    ]
    return max(iterations) if iterations else None


def build_trace_report(paths: RuntimePaths, req_key: str, *, direction: str = "both") -> dict:
    """Build a cross-artifact trajectory view for one REQ key."""

    tags = scan_req_tags(paths.project_root)
    feature_matches = []
    for feature_doc, feature_path in iter_features(paths):
        if feature_doc.get("feature") != req_key:
            continue
        feature_matches.append(
            {
                "feature": req_key,
                "title": feature_doc.get("title"),
                "status": feature_doc.get("status"),
                "profile": feature_doc.get("profile"),
                "path": str(feature_path.relative_to(paths.project_root)),
                "next_edge": determine_next_edge(paths, feature_doc),
                "iteration": _max_feature_iteration(feature_doc),
            }
        )

    code_paths = tags["code_tags"].get(req_key, [])
    test_paths = tags["test_tags"].get(req_key, [])
    telemetry_paths = tags["telemetry_tags"].get(req_key, [])
    design_paths = _scan_design_paths(paths.project_root, req_key)
    intent_path = str(paths.intent_path.relative_to(paths.project_root)) if paths.intent_path.exists() else None

    forward = {
        "intent": intent_path,
        "features": feature_matches,
        "design": design_paths,
        "code": code_paths,
        "tests": test_paths,
        "telemetry": telemetry_paths,
    }
    backward = {
        "telemetry": telemetry_paths,
        "tests": test_paths,
        "code": code_paths,
        "design": design_paths,
        "features": feature_matches,
        "intent": intent_path,
    }

    gaps = []
    if not feature_matches:
        gaps.append(f"No feature vector found for {req_key}")
    if not design_paths:
        gaps.append(f"No design artifact found for {req_key}")
    if not code_paths:
        gaps.append(f"No code artifact found for {req_key}")
    if not test_paths:
        gaps.append(f"No test artifact found for {req_key}")
    if not telemetry_paths:
        gaps.append(f"No telemetry tag found for {req_key}")

    report = {
        "req_key": req_key,
        "direction": direction,
        "forward": forward if direction in {"forward", "both"} else {},
        "backward": backward if direction in {"backward", "both"} else {},
        "gaps": gaps,
    }
    return report


def current_git_ref(project_root: Path) -> str:
    """Return the current git commit hash when available."""

    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def build_checkpoint_snapshot(paths: RuntimePaths, *, context_hash: str, message: str, git_ref: str) -> dict:
    """Build a snapshot document summarizing current workspace state."""

    feature_states = []
    for feature_doc, _ in iter_features(paths):
        feature_states.append(
            {
                "feature": feature_doc.get("feature"),
                "status": feature_doc.get("status"),
                "current_edge": determine_next_edge(paths, feature_doc),
                "iteration": _max_feature_iteration(feature_doc),
            }
        )

    rollup = compute_aggregated_view(paths)
    return {
        "timestamp": utc_now(),
        "message": message,
        "context_hash": context_hash,
        "feature_states": feature_states,
        "tasks": {
            "in_progress": rollup["in_progress"],
            "pending": max(rollup["total"] - rollup["converged"] - rollup["in_progress"] - rollup["blocked"], 0),
            "blocked": rollup["blocked"],
        },
        "git_ref": git_ref,
    }


def req_domain(req_key: str) -> str:
    """Extract the domain token from a REQ key."""

    parts = req_key.split("-")
    return parts[2] if len(parts) >= 4 else "MISC"


def build_gap_report(paths: RuntimePaths, *, feature: str | None = None) -> dict:
    """Build a three-layer gap report from spec and repo contents."""

    inventory = sorted(collect_req_inventory(paths.project_root))
    tags = scan_req_tags(paths.project_root)
    if feature:
        inventory = [req for req in inventory if req.startswith(feature.replace("REQ-F-", "REQ-")) or feature in req]

    code_keys = set(tags["code_tags"])
    test_keys = set(tags["test_tags"])
    telemetry_keys = set(tags["telemetry_tags"])

    full_coverage = []
    partial_coverage = []
    no_coverage = []
    test_gaps = []
    telemetry_gaps = []
    for req in inventory:
        in_code = req in code_keys
        in_tests = req in test_keys
        in_telemetry = req in telemetry_keys
        covered = sum((in_code, in_tests, in_telemetry))
        if covered == 3:
            full_coverage.append(req)
        elif covered == 0:
            no_coverage.append(req)
        else:
            partial_coverage.append(req)
        if not in_tests:
            test_gaps.append(req)
        if in_code and not in_telemetry:
            telemetry_gaps.append(req)

    gap_clusters: dict[tuple[str, str], list[str]] = defaultdict(list)
    for req in test_gaps:
        gap_clusters[("gap", req_domain(req))].append(req)
    for req in telemetry_gaps:
        gap_clusters[("telemetry", req_domain(req))].append(req)

    context_hash = compute_context_hash(
        paths,
        load_project_constraints(paths).get("project", {}).get("default_profile", "standard"),
    )
    return {
        "total_req_keys": len(inventory),
        "inventory": inventory,
        "full_coverage": sorted(full_coverage),
        "partial_coverage": sorted(partial_coverage),
        "no_coverage": sorted(no_coverage),
        "test_gaps": sorted(test_gaps),
        "telemetry_gaps": sorted(telemetry_gaps),
        "layer_results": {
            "layer_1": "fail" if tags["untagged_code"] or tags["untagged_tests"] else "pass",
            "layer_2": "fail" if test_gaps else "pass",
            "layer_3": "fail" if telemetry_gaps else "pass",
        },
        "tag_scan": tags,
        "gap_clusters": {
            f"{kind}:{domain}": sorted(reqs)
            for (kind, domain), reqs in sorted(gap_clusters.items())
        },
        "context_hash": context_hash,
        "feature_status": {
            feature_id: doc.get("status")
            for feature_id, doc in feature_lookup(paths).items()
        },
    }


def build_release_manifest(paths: RuntimePaths, version: str, gap_report: dict) -> dict:
    """Build a release manifest document."""

    features = feature_lookup(paths)
    converged_features = {
        feature_id: doc.get("status")
        for feature_id, doc in features.items()
        if doc.get("status") == "converged"
    }
    overall_pct = 0
    total = gap_report.get("total_req_keys", 0)
    if total:
        overall_pct = int((len(gap_report.get("full_coverage", [])) / total) * 100)
    return {
        "version": version,
        "date": utc_now(),
        "context_hash": gap_report["context_hash"],
        "features_included": converged_features,
        "coverage": {
            "requirements": f"{len(gap_report.get('full_coverage', []))}/{total} ({overall_pct}%)",
            "design": f"{len(features)}/{len(features)} (100%)" if features else "0/0 (0%)",
            "code": f"{len(gap_report['tag_scan']['code_tags'])}/{total} ({int((len(gap_report['tag_scan']['code_tags']) / total) * 100) if total else 0}%)",
            "tests": f"{len(gap_report['tag_scan']['test_tags'])}/{total} ({int((len(gap_report['tag_scan']['test_tags']) / total) * 100) if total else 0}%)",
            "uat": "0/0 (0%)",
        },
        "known_gaps": gap_report.get("no_coverage", []) + gap_report.get("telemetry_gaps", []),
    }


__all__ = [
    "build_checkpoint_snapshot",
    "build_context_manifest",
    "build_gap_report",
    "build_release_manifest",
    "build_trace_report",
    "collect_req_inventory",
    "current_git_ref",
    "req_domain",
    "resolve_context_dir",
    "scan_req_tags",
]
