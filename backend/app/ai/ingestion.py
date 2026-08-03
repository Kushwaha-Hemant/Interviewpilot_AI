"""Features 3 + 4 — turn raw resume/JD text into structured profiles."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.ai import AIProviderError, get_ai_provider
from app.models.enums import ParseStatus
from app.models.job import JobDescription
from app.models.resume import Resume
from app.prompts.extraction import (
    JOB_SYSTEM,
    RESUME_SYSTEM,
    job_user_prompt,
    resume_user_prompt,
)
from app.schemas.extraction import JobProfile, ResumeProfile

logger = logging.getLogger(__name__)


async def parse_resume(db: Session, resume: Resume) -> Resume:
    provider = get_ai_provider()
    try:
        profile = await provider.structured(
            system=RESUME_SYSTEM,
            user=resume_user_prompt(resume.raw_text),
            schema=ResumeProfile,
        )
        resume.parsed = profile.model_dump()
        resume.parse_status = ParseStatus.READY
        resume.parse_error = None
    except AIProviderError as exc:
        logger.exception("Resume parsing failed for %s", resume.id)
        resume.parse_status = ParseStatus.FAILED
        resume.parse_error = str(exc)
    db.commit()
    db.refresh(resume)
    return resume


async def parse_job(db: Session, job: JobDescription) -> JobDescription:
    provider = get_ai_provider()
    try:
        profile = await provider.structured(
            system=JOB_SYSTEM,
            user=job_user_prompt(job.raw_text),
            schema=JobProfile,
        )
        job.parsed = profile.model_dump()
        job.parse_status = ParseStatus.READY
        job.parse_error = None
        # Let the extraction fill in metadata the user didn't type.
        job.title = job.title or profile.title or None
        job.company = job.company or profile.company or None
    except AIProviderError as exc:
        logger.exception("Job parsing failed for %s", job.id)
        job.parse_status = ParseStatus.FAILED
        job.parse_error = str(exc)
    db.commit()
    db.refresh(job)
    return job
