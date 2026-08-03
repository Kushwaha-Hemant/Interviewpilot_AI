"""Feature 8 — voice interview: speech-to-text in, text-to-speech out.

The browser records a clip, POSTs it to /voice/transcribe, sends the transcript through
the normal answer path, then plays /voice/speak for the interviewer's next line.
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, Field

from app.ai import AIProviderError, get_ai_provider
from app.auth.dependencies import CurrentUser
from app.core.config import settings

router = APIRouter(prefix="/voice", tags=["voice"])

ALLOWED_AUDIO = {
    "audio/webm", "audio/ogg", "audio/wav", "audio/x-wav",
    "audio/mpeg", "audio/mp4", "audio/m4a", "video/webm",
}


class TranscriptOut(BaseModel):
    text: str


class SpeakRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


@router.post("/transcribe", response_model=TranscriptOut)
async def transcribe(user: CurrentUser, file: UploadFile = File(...)) -> TranscriptOut:
    content_type = (file.content_type or "").split(";")[0]
    if content_type and content_type not in ALLOWED_AUDIO:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported audio type: {content_type}",
        )

    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Audio clip too large"
        )

    try:
        text = await get_ai_provider().transcribe(
            audio=data, filename=file.filename or "answer.webm"
        )
    except (AIProviderError, NotImplementedError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return TranscriptOut(text=text)


@router.post("/speak")
async def speak(payload: SpeakRequest, user: CurrentUser) -> Response:
    try:
        audio = await get_ai_provider().speak(text=payload.text)
    except (AIProviderError, NotImplementedError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return Response(content=audio, media_type="audio/mpeg")
