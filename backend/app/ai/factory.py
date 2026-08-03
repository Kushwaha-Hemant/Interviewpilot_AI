"""Chooses the AI provider once per process."""

from __future__ import annotations

import logging
from functools import lru_cache

from app.ai.mock_provider import MockProvider
from app.ai.provider import AIProvider, AIProviderError
from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache
def get_ai_provider() -> AIProvider:
    choice = settings.resolved_ai_provider
    if choice == "openai":
        from app.ai.openai_provider import OpenAIProvider

        try:
            provider = OpenAIProvider()
            logger.info("AI provider: openai (model=%s)", settings.openai_model)
            return provider
        except AIProviderError as exc:
            if settings.ai_provider == "openai":
                raise
            logger.warning("Falling back to mock provider: %s", exc)

    logger.info("AI provider: mock (no OPENAI_API_KEY — responses are simulated)")
    return MockProvider()
