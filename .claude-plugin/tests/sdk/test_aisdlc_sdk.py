#!/usr/bin/env python3
"""
Claude Agent SDK tests for AISDLC plugin.

# Implements: REQ-NFR-TEST-001 (Automated Testing)
# Validates: TCS-SDK-001 through TCS-SDK-010

Uses the official claude-agent-sdk to test plugin behavior.
Install: pip install claude-agent-sdk pytest pytest-asyncio
"""

import pytest
import re
from typing import List

# Skip all tests if SDK not installed
pytest.importorskip("claude_agent_sdk")

from claude_agent_sdk import query, ClaudeSDKClient, ClaudeAgentOptions


# =============================================================================
# Helper Functions
# =============================================================================

def extract_req_keys(text: str) -> List[str]:
    """Extract REQ-* keys from text."""
    pattern = r'REQ-[A-Z]+-[A-Z]*-?\d{3}'
    return re.findall(pattern, text)


async def collect_response(prompt: str, options: ClaudeAgentOptions) -> str:
    """Run query and collect full response text."""
    collected = []
    async for message in query(prompt=prompt, options=options):
        # Handle different message types
        if hasattr(message, 'content'):
            for block in message.content:
                if hasattr(block, 'text'):
                    collected.append(block.text)
        elif hasattr(message, 'result'):
            collected.append(message.result)
        elif isinstance(message, str):
            collected.append(message)
    return "\n".join(collected)


# =============================================================================
# Requirements Stage Tests
# =============================================================================

class TestRequirementsStage:
    """Test the Requirements Agent behavior."""

    @pytest.mark.asyncio
    async def test_generates_req_keys(self, aisdlc_options):
        """Requirements stage should generate REQ-* keys."""
        prompt = """
        Using the AI SDLC methodology, extract requirements from this intent:
        'Build a user authentication system with email/password login'

        Generate formal requirements with REQ-F-* and REQ-NFR-* keys.
        """

        output = await collect_response(prompt, aisdlc_options)
        req_keys = extract_req_keys(output)

        assert len(req_keys) >= 2, f"Expected 2+ REQ keys, got {len(req_keys)}: {output[:500]}"
        assert any('REQ-F-' in k for k in req_keys), "Missing functional requirements"

    @pytest.mark.asyncio
    async def test_nfr_categorization(self, aisdlc_options):
        """Performance requirements should be categorized as NFR."""
        prompt = """
        Extract requirements for: 'API must respond in under 200ms with 99.9% uptime'
        Use REQ-NFR-* for non-functional requirements.
        """

        output = await collect_response(prompt, aisdlc_options)

        assert 'REQ-NFR-' in output, "Performance should be non-functional requirement"


# =============================================================================
# TDD Workflow Tests
# =============================================================================

class TestTDDWorkflow:
    """Test the Code Agent TDD behavior."""

    @pytest.mark.asyncio
    async def test_tdd_phases_mentioned(self, aisdlc_options):
        """Code stage should reference TDD phases."""
        prompt = """
        Implement REQ-F-AUTH-001: User login endpoint.
        Follow the TDD workflow: RED (write failing test), GREEN (implement), REFACTOR.
        Describe each phase.
        """

        output = await collect_response(prompt, aisdlc_options)
        output_upper = output.upper()

        # Check for TDD phase mentions
        has_red = 'RED' in output_upper or 'FAILING TEST' in output_upper
        has_green = 'GREEN' in output_upper or 'PASS' in output_upper
        has_refactor = 'REFACTOR' in output_upper

        assert has_red, "Should mention RED phase"
        assert has_green, "Should mention GREEN phase"
        assert has_refactor, "Should mention REFACTOR phase"


# =============================================================================
# Traceability Tests
# =============================================================================

class TestTraceability:
    """Test requirement traceability through pipeline."""

    @pytest.mark.asyncio
    async def test_keys_in_design(self, aisdlc_options):
        """Design should reference requirement keys."""
        prompt = """
        Create a design document for these requirements:
        - REQ-F-PAY-001: Process credit card payments
        - REQ-NFR-PERF-001: Payment processing < 2 seconds

        The design MUST reference these REQ-* keys.
        """

        output = await collect_response(prompt, aisdlc_options)

        assert 'REQ-F-PAY-001' in output, "Design should reference REQ-F-PAY-001"
        assert 'REQ-NFR-PERF-001' in output, "Design should reference REQ-NFR-PERF-001"


# =============================================================================
# Multi-Turn Conversation Tests
# =============================================================================

class TestMultiTurn:
    """Test multi-turn conversations using ClaudeSDKClient."""

    @pytest.mark.asyncio
    async def test_context_preserved(self, aisdlc_options):
        """Context should be preserved across turns."""
        async with ClaudeSDKClient(options=aisdlc_options) as client:
            # Turn 1: Generate requirements
            await client.query("Generate a requirement REQ-F-TEST-001 for user login")
            response1 = []
            async for msg in client.receive_response():
                if hasattr(msg, 'content'):
                    for block in msg.content:
                        if hasattr(block, 'text'):
                            response1.append(block.text)

            # Turn 2: Reference the requirement
            await client.query("Now describe REQ-F-TEST-001 in more detail")
            response2 = []
            async for msg in client.receive_response():
                if hasattr(msg, 'content'):
                    for block in msg.content:
                        if hasattr(block, 'text'):
                            response2.append(block.text)

            full_response = "\n".join(response2)
            assert 'REQ-F-TEST-001' in full_response, "Should remember requirement from previous turn"
