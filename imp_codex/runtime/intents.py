"""Named composition registry and typed intent payload helpers."""

from __future__ import annotations

from pathlib import Path

from .paths import CONFIG_ROOT, RuntimePaths
from .projections import feature_lookup, load_yaml


class _SafeFormatDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _registry_path(paths: RuntimePaths) -> Path:
    if paths.named_compositions_path.exists():
        return paths.named_compositions_path
    return CONFIG_ROOT / "named_compositions.yml"


def load_named_compositions(paths: RuntimePaths) -> dict:
    """Load the named composition registry."""

    registry_path = _registry_path(paths)
    if not registry_path.exists():
        return {}
    return load_yaml(registry_path).get("compositions", {})


def _matches_trigger(rule: dict, *, signal_source: str, edge: str | None) -> bool:
    signal_sources = set(rule.get("signal_sources", []))
    if signal_sources and signal_source not in signal_sources:
        return False
    edges = set(rule.get("edges", []))
    if edges and edge not in edges:
        return False
    return True


def _render_expression(expression: str, context: dict) -> str:
    return expression.format_map(_SafeFormatDict(context))


def resolve_affected_features(
    paths: RuntimePaths,
    *,
    feature: str | None,
    affected_features: list[str] | None = None,
    affected_req_keys: list[str] | None = None,
) -> list[str]:
    """Resolve the feature-vector scope for one intent payload.

    The canonical dispatch unit is a feature vector. If the caller only knows
    REQ keys, collapse them to owning features where possible and widen to
    ``["all"]`` when no precise feature scope can be derived.
    """

    resolved: list[str] = [item.strip() for item in affected_features or [] if str(item).strip()]
    if feature and feature.startswith("REQ-F-"):
        resolved.append(feature)

    req_keys = [item.strip() for item in affected_req_keys or [] if str(item).strip()]
    for req_key in req_keys:
        if req_key.startswith("REQ-F-"):
            resolved.append(req_key)

    feature_docs = feature_lookup(paths)
    unresolved_reqs = {
        req_key for req_key in req_keys
        if req_key not in resolved
    }
    if unresolved_reqs:
        for feature_id, feature_doc in feature_docs.items():
            owned = set(feature_doc.get("requirements") or [])
            if unresolved_reqs & owned:
                resolved.append(feature_id)

    resolved = list(dict.fromkeys(item for item in resolved if item))
    return resolved or ["all"]


def resolve_named_intent_payload(
    paths: RuntimePaths,
    *,
    signal_source: str,
    feature: str | None,
    edge: str | None,
    affected_features: list[str] | None = None,
    affected_req_keys: list[str] | None = None,
) -> dict:
    """Resolve a named composition and typed intent vector for an intent event."""

    registry = load_named_compositions(paths)
    selected_name = None
    selected = None
    for name, candidate in registry.items():
        if _matches_trigger(candidate.get("triggers", {}), signal_source=signal_source, edge=edge):
            selected_name = name
            selected = candidate
            break

    req_keys = list(affected_req_keys or ([] if feature is None else [feature]))
    features = resolve_affected_features(
        paths,
        feature=feature,
        affected_features=affected_features,
        affected_req_keys=req_keys,
    )
    if selected is None:
        resolution_level = "feature_set" if len(req_keys) > 1 else "feature"
        expression = "PLAN({signal_source})"
        composition = {
            "macro": "PLAN",
            "version": "v1",
            "bindings": {
                "signal_source": signal_source,
            },
        }
        return {
            "composition_name": None,
            "composition_expression": _render_expression(
                expression,
                {
                    "signal_source": signal_source,
                },
            ),
            "composition": composition,
            "affected_features": features,
            "affected_req_keys": req_keys,
            "intent_vector": {
                "source": signal_source,
                "parent": {"feature": feature, "edge": edge},
                "resolution_level": resolution_level,
                "composition_expression": _render_expression(expression, {"signal_source": signal_source}),
                "profile": "standard",
                "status": "proposed",
            },
        }

    render_context = {
        "edge": edge or "unknown",
        "feature": feature or "unknown",
        "first_req_key": req_keys[0] if req_keys else "unknown",
        "req_count": len(req_keys),
        "signal_source": signal_source,
    }
    expression = _render_expression(str(selected.get("expression", selected_name)), render_context)
    composition = {
        "macro": selected_name,
        "version": selected.get("version", "v1"),
        "bindings": render_context,
    }
    return {
        "composition_name": selected_name,
        "composition_expression": expression,
        "composition": composition,
        "affected_features": features,
        "affected_req_keys": req_keys,
        "intent_vector": {
            "source": signal_source,
            "parent": {"feature": feature, "edge": edge},
            "resolution_level": selected.get("resolution_level", "feature"),
            "composition_expression": expression,
            "profile": selected.get("default_profile", "standard"),
            "status": "proposed",
        },
        "vector_type": selected.get("vector_type", "feature"),
    }


__all__ = [
    "load_named_compositions",
    "resolve_affected_features",
    "resolve_named_intent_payload",
]
