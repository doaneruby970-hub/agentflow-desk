"""LLM provider abstraction layer."""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings


@dataclass
class LLMResponse:
    """Standardized LLM response."""

    content: str
    prompt_tokens: int
    completion_tokens: int
    model: str
    provider: str
    latency_ms: int


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> LLMResponse:
        """Generate chat completion."""

    @abstractmethod
    async def create_embedding(self, text: str, model: str) -> list[float]:
        """Generate text embedding."""

    @abstractmethod
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """Estimate cost in USD."""


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.provider_name = "openai"

        # Pricing per 1M tokens (as of 2026-07)
        self.pricing = {
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4o-2024-08-06": {"input": 2.50, "output": 10.00},
            "o1-preview": {"input": 15.00, "output": 60.00},
            "o1-mini": {"input": 3.00, "output": 12.00},
            "text-embedding-3-small": {"input": 0.02, "output": 0.0},
            "text-embedding-3-large": {"input": 0.13, "output": 0.0},
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> LLMResponse:
        """Generate chat completion with retry."""
        start_time = time.time()

        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        if response_format:
            kwargs["response_format"] = response_format

        response = await self.client.chat.completions.create(**kwargs)

        latency_ms = int((time.time() - start_time) * 1000)

        return LLMResponse(
            content=response.choices[0].message.content or "",
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            model=response.model,
            provider=self.provider_name,
            latency_ms=latency_ms,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def create_embedding(self, text: str, model: str) -> list[float]:
        """Generate text embedding with retry."""
        response = await self.client.embeddings.create(
            model=model,
            input=text,
        )
        return response.data[0].embedding

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """Estimate cost in USD."""
        if model not in self.pricing:
            return 0.0

        input_cost = (prompt_tokens / 1_000_000) * self.pricing[model]["input"]
        output_cost = (completion_tokens / 1_000_000) * self.pricing[model]["output"]
        return input_cost + output_cost


class ClaudeProvider(LLMProvider):
    """Anthropic Claude API provider."""

    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)
        self.provider_name = "anthropic"

        # Pricing per 1M tokens (as of 2026-07)
        self.pricing = {
            "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
            "claude-3-5-sonnet-20240620": {"input": 3.00, "output": 15.00},
            "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
            "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> LLMResponse:
        """Generate chat completion with retry."""
        start_time = time.time()

        # Extract system message if present
        system_message = None
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(msg)

        kwargs = {
            "model": model,
            "messages": user_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
        }
        if system_message:
            kwargs["system"] = system_message

        response = await self.client.messages.create(**kwargs)

        latency_ms = int((time.time() - start_time) * 1000)

        content = response.content[0].text if response.content else ""

        return LLMResponse(
            content=content,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            model=response.model,
            provider=self.provider_name,
            latency_ms=latency_ms,
        )

    async def create_embedding(self, text: str, model: str) -> list[float]:
        """Claude does not provide embedding API, fallback to OpenAI."""
        raise NotImplementedError("Claude provider does not support embeddings")

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """Estimate cost in USD."""
        if model not in self.pricing:
            return 0.0

        input_cost = (prompt_tokens / 1_000_000) * self.pricing[model]["input"]
        output_cost = (completion_tokens / 1_000_000) * self.pricing[model]["output"]
        return input_cost + output_cost


class LLMService:
    """High-level LLM service with provider management."""

    def __init__(self):
        self.provider = self._init_provider()

    def _init_provider(self) -> LLMProvider:
        """Initialize LLM provider based on configuration."""
        if settings.llm_provider == "openai":
            return OpenAIProvider(api_key=settings.openai_api_key)
        elif settings.llm_provider == "anthropic":
            return ClaudeProvider(api_key=settings.anthropic_api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> LLMResponse:
        """Generate chat completion using configured provider."""
        model = model or settings.llm_model
        return await self.provider.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )

    async def create_embedding(self, text: str, model: str | None = None) -> list[float]:
        """Generate embedding using configured provider."""
        model = model or settings.embedding_model
        return await self.provider.create_embedding(text=text, model=model)

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """Estimate cost for given token usage."""
        return self.provider.estimate_cost(prompt_tokens, completion_tokens, model)


# Global LLM service instance
llm_service = LLMService()
