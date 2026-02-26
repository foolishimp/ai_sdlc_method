"""Tests for genesis_engine.providers — pluggable F_P interface."""

import pytest

from genesis_engine.models import CheckOutcome, ResolvedCheck
from genesis_engine.providers import get_provider, list_providers, register_provider
from genesis_engine.providers.base import FPProvider
from genesis_engine.providers.claude import ClaudeProvider
from genesis_engine.providers.gemini import GeminiProvider


def test_list_providers():
    providers = list_providers()
    assert "claude" in providers
    assert "gemini" in providers


def test_get_claude_provider():
    p = get_provider("claude", model="sonnet")
    assert isinstance(p, ClaudeProvider)
    assert p.name == "claude"


def test_get_gemini_provider():
    p = get_provider("gemini")
    assert isinstance(p, GeminiProvider)
    assert p.name == "gemini"


def test_get_unknown_provider():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("nonexistent")


def test_register_custom_provider():
    class MockProvider(FPProvider):
        @property
        def name(self):
            return "mock"

        def run_check(self, check, asset_content, context="", timeout=120):
            from genesis_engine.models import CheckResult
            return CheckResult(
                name=check.name, outcome=CheckOutcome.PASS,
                required=check.required, check_type=check.check_type,
                functional_unit=check.functional_unit, message="mock pass",
            )

    register_provider("mock", MockProvider)
    p = get_provider("mock")
    assert p.name == "mock"

    check = ResolvedCheck(
        name="test_check", check_type="agent", functional_unit="evaluate",
        criterion="always pass", source="test", required=True,
    )
    result = p.run_check(check, asset_content="test")
    assert result.outcome == CheckOutcome.PASS


def test_gemini_provider_stubs_to_skip():
    p = GeminiProvider()
    check = ResolvedCheck(
        name="test_check", check_type="agent", functional_unit="evaluate",
        criterion="test", source="test", required=True,
    )
    result = p.run_check(check, asset_content="test")
    assert result.outcome == CheckOutcome.SKIP
    assert "not yet implemented" in result.message


def test_claude_provider_skips_non_agent():
    p = ClaudeProvider()
    check = ResolvedCheck(
        name="det_check", check_type="deterministic", functional_unit="evaluate",
        criterion="test", source="test", required=True,
    )
    result = p.run_check(check, asset_content="test")
    assert result.outcome == CheckOutcome.SKIP
    assert "not F_P" in result.message
