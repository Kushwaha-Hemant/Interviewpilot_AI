"""OpenAI implementation built on the Responses API.

Uses:
  * `responses.parse`  -> Structured Outputs (strict JSON Schema, validated into Pydantic)
  * `responses.stream` -> token streaming for the interview room
  * `audio.transcriptions` / `audio.speech` -> voice mode (feature 8)
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from io import BytesIO

from openai import APIConnectionError, APIStatusError, AsyncOpenAI, RateLimitError

from app.ai.provider import AIProvider, AIProviderError, TModel
from app.core.config import settings

logger = logging.getLogger(__name__)

RETRYABLE = (RateLimitError, APIConnectionError)
MAX_ATTEMPTS = 3


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or settings.openai_api_key
        if not key:
            raise AIProviderError("OPENAI_API_KEY is not set")
        self._client = AsyncOpenAI(api_key=key)

    def _model(self, fast: bool) -> str:
        return settings.openai_model_fast if fast else settings.openai_model

    async def _with_retries(self, coro_factory):
        delay = 1.0
        last: Exception | None = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                return await coro_factory()
            except RETRYABLE as exc:
                last = exc
                logger.warning("OpenAI call failed (attempt %s/%s): %s", attempt, MAX_ATTEMPTS, exc)
                if attempt < MAX_ATTEMPTS:
                    await asyncio.sleep(delay)
                    delay *= 2
            except APIStatusError as exc:
                raise AIProviderError(f"OpenAI returned {exc.status_code}: {exc.message}") from exc
        raise AIProviderError(f"OpenAI call failed after {MAX_ATTEMPTS} attempts: {last}")

    # ------------------------------------------------------------------ structured

    async def structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[TModel],
        fast: bool = False,
    ) -> TModel:
        async def call():
            return await self._client.responses.parse(
                model=self._model(fast),
                input=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                text_format=schema,
            )

        response = await self._with_retries(call)
        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            raise AIProviderError(
                f"Model returned no parseable {schema.__name__} "
                f"(status={getattr(response, 'status', 'unknown')})"
            )
        return parsed

    # --------------------------------------------------------------------- text

    async def text(self, *, system: str, user: str, fast: bool = False) -> str:
        async def call():
            return await self._client.responses.create(
                model=self._model(fast),
                input=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )

        response = await self._with_retries(call)
        return (response.output_text or "").strip()

    # ------------------------------------------------------------------ streaming

    async def stream_text(
        self,
        *,
        system: str,
        user: str,
        fast: bool = False,
    ) -> AsyncIterator[str]:
        try:
            async with self._client.responses.stream(
                model=self._model(fast),
                input=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            ) as stream:
                async for event in stream:
                    if event.type == "response.output_text.delta":
                        yield event.delta
                    elif event.type == "response.error":
                        raise AIProviderError(str(event.error))
        except RETRYABLE as exc:
            # Streaming is user-facing; surface rather than silently retrying mid-sentence.
            raise AIProviderError(f"Streaming failed: {exc}") from exc

    # ---------------------------------------------------------------------- voice

    async def transcribe(self, *, audio: bytes, filename: str) -> str:
        buffer = BytesIO(audio)
        buffer.name = filename

        async def call():
            return await self._client.audio.transcriptions.create(
                model=settings.openai_stt_model,
                file=buffer,
            )

        result = await self._with_retries(call)
        return (result.text or "").strip()

    async def speak(self, *, text: str) -> bytes:
        async def call():
            return await self._client.audio.speech.create(
                model=settings.openai_tts_model,
                voice=settings.openai_tts_voice,
                input=text,
                response_format="mp3",
            )

        result = await self._with_retries(call)
        return result.read()
