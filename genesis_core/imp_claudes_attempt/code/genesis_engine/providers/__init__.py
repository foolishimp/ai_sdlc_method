# Implements: GENESIS_ENGINE_SPEC §6.2 (F_P Binding Point)
"""Provider registry — maps provider names to F_P implementations."""

from .base import FPProvider
from .claude import ClaudeProvider
from .gemini import GeminiProvider

_REGISTRY: dict[str, type[FPProvider]] = {
    "claude": ClaudeProvider,
    "gemini": GeminiProvider,
}


def get_provider(name: str, **kwargs) -> FPProvider:
    """Look up a provider by name and instantiate it."""
    cls = _REGISTRY.get(name)
    if cls is None:
        available = ", ".join(sorted(_REGISTRY.keys()))
        raise ValueError(f"Unknown provider '{name}'. Available: {available}")
    return cls(**kwargs)


def register_provider(name: str, cls: type[FPProvider]) -> None:
    """Register a custom provider at runtime."""
    _REGISTRY[name] = cls


def list_providers() -> list[str]:
    """Return names of all registered providers."""
    return sorted(_REGISTRY.keys())
