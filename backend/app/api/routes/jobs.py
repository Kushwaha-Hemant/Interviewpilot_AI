"""Feature 4 — job description ingestion and structured extraction."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.ai.ingestion import parse_job
from app.auth.dependencies import CurrentUser, DbSession
from app.models.job import JobDescription
from app.schemas.api import JobCreate, JobOut

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def create_job(payload: JobCreate, user: CurrentUser, db: DbSession) -> JobDescription:
    job = JobDescription(
        user_id=user.id,
        raw_text=payload.raw_text,
        title=payload.title,
        company=payload.company,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return await parse_job(db, job)


@router.get("", response_model=list[JobOut])
def list_jobs(user: CurrentUser, db: DbSession) -> list[JobDescription]:
    return list(
        db.scalars(
            select(JobDescription)
            .where(JobDescription.user_id == user.id)
            .order_by(JobDescription.created_at.desc())
        )
    )


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, user: CurrentUser, db: DbSession) -> JobDescription:
    job = db.get(JobDescription, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_job(job_id: str, user: CurrentUser, db: DbSession) -> None:
    job = db.get(JobDescription, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    db.delete(job)
    db.commit()
