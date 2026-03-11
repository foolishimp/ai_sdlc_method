"""Deterministic evaluator execution for the Codex runtime."""

from __future__ import annotations

import json
from pathlib import Path
import re
import shlex
import subprocess
import yaml

from .paths import CONFIG_ROOT, RuntimePaths
from .projections import load_feature, load_graph, load_project_constraints, load_yaml
from .traceability import build_trace_report, collect_req_inventory, scan_req_tags


VARIABLE_RE = re.compile(r"\$([A-Za-z0-9_.]+)")
REQ_KEY_RE = re.compile(r"REQ-[A-Z]+-[A-Z0-9]+-\d+")
VALID_AGENT_RESULTS = {"pass", "fail", "skip", "pending"}


def _lookup(data: dict, dotted_path: str):
    value = data
    for part in dotted_path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def resolve_template(value, context: dict):
    """Resolve `$foo.bar` references against a nested context."""

    if not isinstance(value, str):
        return value

    full_match = VARIABLE_RE.fullmatch(value)
    if full_match:
        return _lookup(context, full_match.group(1))

    def replace(match: re.Match[str]) -> str:
        resolved = _lookup(context, match.group(1))
        return "" if resolved is None else str(resolved)

    return VARIABLE_RE.sub(replace, value)


def _edge_config_path(paths: RuntimePaths, edge: str):
    graph = load_graph(paths)
    for transition in graph.get("transitions", []):
        arrow = "↔" if transition.get("edge_type") == "co_evolution" else "→"
        transition_edge = f"{transition['source']}{arrow}{transition['target']}"
        if transition_edge == edge:
            config_name = transition.get("edge_config", "").split("/")[-1]
            if not config_name:
                return None
            workspace_path = paths.edges_dir / config_name
            if workspace_path.exists():
                return workspace_path
            return CONFIG_ROOT / "edge_params" / config_name
    return None


def load_edge_checklist(paths: RuntimePaths, edge: str) -> list[dict]:
    """Load the checklist entries for an edge."""

    config_path = _edge_config_path(paths, edge)
    if config_path is None or not config_path.exists():
        return []
    return load_yaml(config_path).get("checklist", [])


def load_edge_config(paths: RuntimePaths, edge: str) -> dict:
    """Load the full edge configuration document for an edge."""

    config_path = _edge_config_path(paths, edge)
    if config_path is None or not config_path.exists():
        return {}
    return load_yaml(config_path)


def _has_value(value) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, bool):
        return value
    if isinstance(value, list):
        return any(_has_value(item) for item in value)
    if isinstance(value, dict):
        return any(_has_value(item) for item in value.values())
    return value is not None


def _spec_text(paths: RuntimePaths) -> str:
    spec_root = paths.project_root / "specification"
    chunks = []
    if not spec_root.exists():
        return ""
    for path in sorted(spec_root.rglob("*")):
        if path.is_file():
            try:
                chunks.append(path.read_text())
            except UnicodeDecodeError:
                continue
    return "\n".join(chunks)


def _read_relative_files(paths: RuntimePaths, relative_paths: list[str]) -> str:
    chunks = []
    for relative_path in relative_paths:
        path = paths.project_root / relative_path
        if not path.exists():
            continue
        try:
            chunks.append(path.read_text())
        except UnicodeDecodeError:
            continue
    return "\n".join(chunks)


def _agent_invocation_config(paths: RuntimePaths) -> dict:
    config = dict(load_project_constraints(paths).get("agent_invocation", {}))
    config.setdefault("mode", "heuristic")
    config.setdefault("fallback", "heuristic")
    return config


def _resolve_invocation_file(project_root: Path, configured_path: str | None) -> Path | None:
    if not configured_path:
        return None
    path = Path(configured_path)
    if path.is_absolute():
        return path
    return (project_root / path).resolve()


def _load_agent_invocation_records(paths: RuntimePaths, config: dict) -> tuple[dict, str | None, str | None]:
    if config.get("mode") != "file":
        return {}, None, None

    invocation_path = _resolve_invocation_file(paths.project_root, config.get("file"))
    if invocation_path is None:
        return {}, "agent_invocation.mode=file requires agent_invocation.file", None
    display_path = str(invocation_path)
    if not invocation_path.exists():
        return {}, f"agent invocation file not found: {display_path}", display_path

    try:
        if invocation_path.suffix.lower() == ".json":
            parsed = json.loads(invocation_path.read_text())
        else:
            parsed = yaml.safe_load(invocation_path.read_text())
    except (OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
        return {}, f"invalid agent invocation file: {exc}", display_path

    if isinstance(parsed, dict):
        rows = parsed.get("evaluations", [])
    elif isinstance(parsed, list):
        rows = parsed
    else:
        return {}, "agent invocation file must be a list or contain an 'evaluations' list", display_path

    index = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = row.get("name")
        result = row.get("result")
        if not name or result not in VALID_AGENT_RESULTS:
            continue
        key = (row.get("feature"), row.get("edge"), name)
        index[key] = row
    return index, None, display_path


def _file_invocation_match(index: dict, *, feature: str | None, edge: str, check_name: str) -> dict | None:
    for key in (
        (feature, edge, check_name),
        (None, edge, check_name),
        (feature, None, check_name),
        (None, None, check_name),
    ):
        if key in index:
            return index[key]
    return None


def _evaluate_agent_check(
    paths: RuntimePaths,
    edge: str,
    check: dict,
    *,
    feature: str | None = None,
    invocation_config: dict | None = None,
    invocation_records: dict | None = None,
    invocation_error: str | None = None,
    invocation_source: str | None = None,
) -> dict:
    context = load_project_constraints(paths)
    required = bool(resolve_template(check.get("required", True), context))
    check_name = check.get("name", "")
    invocation_config = invocation_config or {"mode": "heuristic", "fallback": "heuristic"}
    req_key = feature if feature and REQ_KEY_RE.fullmatch(feature) else None
    trace = build_trace_report(paths, req_key, direction="both") if req_key else {
        "forward": {"design": [], "code": [], "tests": [], "telemetry": [], "features": []},
        "gaps": [],
    }
    tags = scan_req_tags(paths.project_root)
    inventory = collect_req_inventory(paths.project_root)
    spec_text = _spec_text(paths)
    design_text = _read_relative_files(paths, trace["forward"].get("design", []))
    code_text = _read_relative_files(paths, trace["forward"].get("code", []))
    test_text = _read_relative_files(paths, trace["forward"].get("tests", []))
    feature_doc = load_feature(paths, feature)[0] if feature else None
    ambiguous_words = re.compile(r"\b(should|might|could|appropriate|reasonable)\b", re.IGNORECASE)

    def outcome(result: str, message: str, *, provider: str) -> dict:
        return {
            "name": check_name,
            "type": "agent",
            "result": result,
            "required": required,
            "message": message,
            "provider": provider,
            "invocation_mode": invocation_config.get("mode", "heuristic"),
            "evidence_source": invocation_source,
        }

    if invocation_config.get("mode") == "file":
        matched = _file_invocation_match(invocation_records or {}, feature=feature, edge=edge, check_name=check_name)
        if matched is not None:
            return outcome(matched["result"], matched.get("message", "external agent evaluation loaded"), provider="file")
        if invocation_config.get("fallback") == "fail":
            result = "fail" if required else "skip"
            return outcome(result, invocation_error or f"no external agent evaluation for check '{check_name}'", provider="file_missing")

    if check_name in {"correct_key_format"}:
        return outcome("pass" if req_key else "fail", "feature key matches REQ format" if req_key else "missing REQ key", provider="heuristic")
    if check_name in {"traces_to_intent"}:
        ok = bool((feature_doc or {}).get("intent")) or "Traces To" in spec_text
        return outcome("pass" if ok else "fail", "intent linkage present" if ok else "missing intent linkage", provider="heuristic")
    if check_name in {"all_intent_aspects_covered", "requirements_are_testable", "acceptance_criteria_specific"}:
        ok = req_key is not None and req_key in spec_text and "Acceptance Criteria" in spec_text
        return outcome("pass" if ok else "skip", "requirements document references feature with acceptance criteria" if ok else "requirements artifact not available", provider="heuristic")
    if check_name == "no_ambiguous_language":
        if not spec_text:
            return outcome("skip", "requirements artifact not available", provider="heuristic")
        return outcome("pass" if not ambiguous_words.search(spec_text) else "fail", "requirements language checked for ambiguity", provider="heuristic")
    if check_name == "document_has_required_sections":
        required_sections = (
            "Overview",
            "Terminology",
            "Functional Requirements",
            "Non-Functional Requirements",
            "Data Requirements",
            "Business Rules",
            "Success Criteria",
            "Assumptions and Dependencies",
        )
        ok = spec_text and all(section in spec_text for section in required_sections)
        return outcome("pass" if ok else "skip", "requirements sections verified" if ok else "full requirements document not available", provider="heuristic")
    if check_name == "terminology_defines_domain_terms":
        return outcome("pass" if "Terminology" in spec_text else "skip", "terminology section present" if "Terminology" in spec_text else "terminology section not found", provider="heuristic")
    if check_name == "success_criteria_measurable":
        return outcome("pass" if "Success Criteria" in spec_text else "skip", "success criteria section present" if "Success Criteria" in spec_text else "success criteria section not found", provider="heuristic")
    if check_name == "acceptance_criteria_bound_to_feature":
        bound = bool((feature_doc or {}).get("constraints", {}).get("acceptance_criteria"))
        return outcome("pass" if bound else "skip", "feature acceptance criteria bound" if bound else "no bound acceptance criteria", provider="heuristic")
    if check_name in {"all_reqs_traced_to_components", "no_orphan_components"}:
        ok = bool(design_text) and "Implements" in design_text and (req_key is None or req_key in design_text)
        return outcome("pass" if ok else "fail", "design traceability verified" if ok else "design traceability missing", provider="heuristic")
    if check_name == "interfaces_consistent":
        ok = "Interfaces" in design_text
        return outcome("pass" if ok else "skip", "design interfaces present" if ok else "interfaces section not found", provider="heuristic")
    if check_name == "dependencies_sound":
        ok = "Dependencies" in design_text
        return outcome("pass" if ok else "skip", "design dependencies present" if ok else "dependencies section not found", provider="heuristic")
    if check_name == "data_models_present":
        if req_key and req_key.startswith("REQ-DATA-"):
            return outcome("pass" if "Data Model" in design_text else "fail", "data model present" if "Data Model" in design_text else "data model missing", provider="heuristic")
        return outcome("skip", "not a data requirement", provider="heuristic")
    if check_name.endswith("_resolved"):
        dimension_name = check_name.replace("_resolved", "")
        resolved = _has_value(context.get("constraint_dimensions", {}).get(dimension_name, {}))
        return outcome("pass" if resolved else "fail", f"{dimension_name} resolved" if resolved else f"{dimension_name} unresolved", provider="heuristic")
    if check_name == "advisory_dimensions_considered":
        return outcome("skip", "advisory dimensions not heuristically evaluated", provider="heuristic")
    if check_name in {"code_matches_design"}:
        ok = bool(design_text) and bool(code_text)
        return outcome("pass" if ok else "fail", "design and code artifacts present" if ok else "missing design or code artifact", provider="heuristic")
    if check_name in {"follows_coding_standards", "code_quality"}:
        ok = bool(trace["forward"].get("code")) and not tags["untagged_code"]
        return outcome("pass" if ok else "fail", "code present and tagged" if ok else "code missing or untagged", provider="heuristic")
    if check_name in {"test_quality"}:
        ok = bool(trace["forward"].get("tests")) and not tags["untagged_tests"]
        return outcome("pass" if ok else "fail", "tests present and tagged" if ok else "tests missing or untagged", provider="heuristic")
    if check_name == "req_tags_present":
        if edge == "code↔unit_tests":
            ok = bool(trace["forward"].get("code")) and bool(trace["forward"].get("tests"))
        else:
            ok = bool(trace["forward"].get("code")) or bool(trace["forward"].get("tests"))
        return outcome("pass" if ok else "fail", "REQ tags detected in generated artifacts" if ok else "REQ tags missing from generated artifacts", provider="heuristic")
    if check_name in {"all_req_keys_covered", "all_req_keys_have_tests"}:
        ok = bool(trace["forward"].get("tests"))
        return outcome("pass" if ok else "fail", "test coverage detected for feature" if ok else "no tests traced to feature", provider="heuristic")
    if check_name in {"valid_req_references", "req_keys_exist_in_spec"}:
        referenced = set(tags["code_tags"]) | set(tags["test_tags"])
        ok = referenced.issubset(inventory)
        return outcome("pass" if ok else "fail", "tagged REQ keys exist in spec" if ok else "orphan REQ references found", provider="heuristic")
    if check_name in {"code_files_tagged"}:
        return outcome("pass" if not tags["untagged_code"] else "fail", "all code files tagged" if not tags["untagged_code"] else "untagged code files detected", provider="heuristic")
    if check_name in {"test_files_tagged"}:
        return outcome("pass" if not tags["untagged_tests"] else "fail", "all test files tagged" if not tags["untagged_tests"] else "untagged test files detected", provider="heuristic")
    if check_name == "code_req_keys_have_telemetry":
        ok = bool(trace["forward"].get("telemetry"))
        return outcome("pass" if ok else "fail", "telemetry tags detected" if ok else "telemetry tags missing", provider="heuristic")
    return outcome("skip", "no heuristic implemented for this agent check", provider="heuristic")


def run_deterministic_checks(paths: RuntimePaths, edge: str) -> list[dict]:
    """Run deterministic checklist entries for an edge in the project root."""

    context = load_project_constraints(paths)
    timeout = int(context.get("thresholds", {}).get("test_execution_timeout_seconds", 30))
    results = []
    for check in load_edge_checklist(paths, edge):
        if check.get("type") != "deterministic":
            continue

        required = resolve_template(check.get("required", True), context)
        command = resolve_template(check.get("command"), context)
        if not command:
            results.append(
                {
                    "name": check.get("name"),
                    "type": "deterministic",
                    "result": "skip",
                    "required": bool(required),
                    "message": "command unresolved",
                }
            )
            continue

        completed = subprocess.run(
            shlex.split(str(command)),
            cwd=paths.project_root,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        outcome = "pass" if completed.returncode == 0 else "fail"
        results.append(
            {
                "name": check.get("name"),
                "type": "deterministic",
                "result": outcome,
                "required": bool(required),
                "message": (completed.stdout + completed.stderr).strip(),
            }
        )
    return results


def run_agent_checks(paths: RuntimePaths, edge: str, *, feature: str | None = None) -> list[dict]:
    """Run agent checklist entries for an edge using the configured invocation contract."""

    invocation_config = _agent_invocation_config(paths)
    invocation_records, invocation_error, invocation_source = _load_agent_invocation_records(paths, invocation_config)
    results = []
    for check in load_edge_checklist(paths, edge):
        if check.get("type") != "agent":
            continue
        results.append(
            _evaluate_agent_check(
                paths,
                edge,
                check,
                feature=feature,
                invocation_config=invocation_config,
                invocation_records=invocation_records,
                invocation_error=invocation_error,
                invocation_source=invocation_source,
            )
        )

    required_results = [result for result in results if result.get("required")]
    if required_results and all(result.get("result") == "skip" for result in required_results):
        results.append(
            {
                "name": "agent_review_available",
                "type": "agent",
                "result": "fail",
                "required": True,
                "message": "no heuristic coverage for required agent checks",
            }
        )
    return results


__all__ = [
    "load_edge_checklist",
    "load_edge_config",
    "resolve_template",
    "run_agent_checks",
    "run_deterministic_checks",
]
