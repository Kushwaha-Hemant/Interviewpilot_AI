"""InterviewPilot AI — FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.websocket import interview_ws_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
# DEBUG applies to our code only — the OpenAI/httpx clients log entire request bodies at
# DEBUG, which buries everything else.
logging.getLogger("app").setLevel(logging.DEBUG if settings.debug else logging.INFO)
for noisy in ("openai", "httpx", "httpcore", "urllib3"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

logger = logging.getLogger("interviewpilot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.ai import get_ai_provider

    provider = get_ai_provider()
    logger.info(
        "%s starting | env=%s | ai=%s | auth=%s",
        settings.app_name,
        settings.environment,
        provider.name,
        settings.auth_provider,
    )
    if provider.name == "mock":
        logger.warning(
            "Running with the MOCK AI provider — responses are simulated. "
            "Set OPENAI_API_KEY in backend/.env for real GPT interviews."
        )
    yield
    logger.info("%s shutting down", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI-powered mock interview platform",
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)
app.include_router(interview_ws_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    from app.ai import get_ai_provider

    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "ai_provider": get_ai_provider().name,
        "auth_provider": settings.auth_provider,
    }
