"""Verify the configured OpenAI key + model actually work.

Makes one real Structured Outputs call through the app's own provider layer, so a pass
means the whole path works: key, model name, Responses API, and schema validation.

    python scripts/check_openai.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai import AIProviderError, get_ai_provider  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.prompts.extraction import JOB_SYSTEM, job_user_prompt  # noqa: E402
from app.schemas.extraction import JobProfile  # noqa: E402

SAMPLE_JD = """
Backend Engineer — Payments
We need 3+ years with Java and Spring Boot. You will own REST APIs, design PostgreSQL
schemas, and deploy with Docker on AWS. Kubernetes and Kafka are a plus.
Responsibilities: build payment services, own reliability and on-call, mentor juniors.
"""


async def main() -> int:
    provider = get_ai_provider()
    print(f"provider      : {provider.name}")
    print(f"model         : {settings.openai_model}")
    print(f"model (fast)  : {settings.openai_model_fast}")

    if provider.name != "openai":
        print("\nNot using OpenAI. Set OPENAI_API_KEY in backend/.env and AI_PROVIDER=auto.")
        return 1

    print("\nCalling the Responses API with a strict JSON schema…")
    try:
        profile = await provider.structured(
            system=JOB_SYSTEM,
            user=job_user_prompt(SAMPLE_JD),
            schema=JobProfile,
        )
    except AIProviderError as exc:
        print(f"\nFAILED: {exc}")
        return 1

    print("\nOK — the model returned a valid JobProfile:")
    print(f"  title      : {profile.title}")
    print(f"  seniority  : {profile.seniority}")
    print(f"  min years  : {profile.min_years_experience}")
    must = [s.name for s in profile.required_skills if s.importance == "must_have"]
    nice = [s.name for s in profile.required_skills if s.importance == "nice_to_have"]
    print(f"  must-have  : {', '.join(must) or '—'}")
    print(f"  nice-to-have: {', '.join(nice) or '—'}")
    print(f"  keywords   : {', '.join(profile.keywords[:8])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
