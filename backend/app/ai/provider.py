"""Provider-agnostic AI interface.

Everything in the app talks to this, never to the OpenAI SDK directly. That keeps the
mock provider a first-class citizen (so the app runs with no API key) and makes swapping
or A/B-ing models a one-file change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import TypeVar

from pydantic import BaseModel

TModel = TypeVar("TModel", bound=BaseModel)


class AIProvider(ABC):
    """Contract every provider implements."""

    name: str = "base"

    @abstractmethod
    async def structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[TModel],
        fast: bool = False,
    ) -> TModel:
        """Return a validated instance of `schema` (OpenAI Structured Outputs)."""

    @abstractmethod
    async def stream_text(
        self,
        *,
        system: str,
        user: str,
        fast: bool = False,
    ) -> AsyncIterator[str]:
        """Yield text deltas as they are produced."""

    @abstractmethod
    async def text(self, *, system: str, user: str, fast: bool = False) -> str:
        """Return a complete, non-streamed text response."""

    async def transcribe(self, *, audio: bytes, filename: str) -> str:
        """Feature 8 — speech to text. Optional per provider."""
        raise NotImplementedError(f"{self.name} provider does not support transcription")

    async def speak(self, *, text: str) -> bytes:
        """Feature 8 — text to speech, returns audio bytes. Optional per provider."""
        raise NotImplementedError(f"{self.name} provider does not support speech synthesis")


class AIProviderError(RuntimeError):
    """Raised when the upstream model call fails after retries."""
