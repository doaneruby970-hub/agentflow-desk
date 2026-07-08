"""Tests for LLM service."""

import pytest

from app.services.llm import LLMService, OpenAIProvider


@pytest.mark.asyncio
async def test_llm_service_initialization():
    """Test LLM service can be initialized."""
    service = LLMService()
    assert service.provider is not None


def test_openai_cost_estimation():
    """Test OpenAI cost estimation."""
    provider = OpenAIProvider(api_key="test-key")
    cost = provider.estimate_cost(
        prompt_tokens=1000,
        completion_tokens=500,
        model="gpt-4o-mini",
    )
    # gpt-4o-mini: $0.15/1M input, $0.60/1M output
    expected = (1000 / 1_000_000 * 0.15) + (500 / 1_000_000 * 0.60)
    assert abs(cost - expected) < 0.0001
