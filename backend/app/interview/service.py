"""Interview creation: builds the context snapshot and picks focus skills."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.interview import Interview
from app.models.job import JobDescription
from app.models.resume import Resume
from app.models.user import User
from app.schemas.api import InterviewCreate

DEFAULT_FOCUS = ["Problem Solving", "System Design", "Communication"]
MAX_FOCUS_SKILLS = 8


def derive_focus_skills(
    resume: Resume | None, job: JobDescription | None
) -> list[str]:
    """Skills the interview should target.

    Priority: skills the candidate claims AND the job requires, then remaining job
    must-haves (the real gaps), then remaining resume skills.
    """
    resume_skills = [s.get("name", "") for s in (resume.parsed or {}).get("skills", [])] if resume and resume.parsed else []
    resume_skills = [s for s in resume_skills if s]

    job_required: list[str] = []
    job_nice: list[str] = []
    if job and job.parsed:
        for entry in job.parsed.get("required_skills", []):
            name = entry.get("name", "")
            if not name:
                continue
            (job_required if entry.get("importance") == "must_have" else job_nice).append(name)

    lowered_resume = {s.lower() for s in resume_skills}
    overlap = [s for s in job_required if s.lower() in lowered_resume]
    gaps = [s for s in job_required if s.lower() not in lowered_resume]
    remaining = [s for s in resume_skills if s.lower() not in {x.lower() for x in overlap}]

    ordered: list[str] = []
    for group in (overlap, gaps, remaining, job_nice):
        for skill in group:
            if skill.lower() not in {o.lower() for o in ordered}:
                ordered.append(skill)

    return (ordered or DEFAULT_FOCUS)[:MAX_FOCUS_SKILLS]


def build_context(resume: Resume | None, job: JobDescription | None) -> dict:
    """Frozen snapshot of the inputs, so re-running an interview is reproducible."""
    context: dict = {}
    if resume and resume.parsed:
        context["resume"] = resume.parsed
    if job and job.parsed:
        context["job"] = job.parsed
        context["job_raw_title"] = job.title
    return context


def create_interview(
    db: Session, *, user: User, payload: InterviewCreate
) -> Interview:
    resume = (
        db.query(Resume)
        .filter(Resume.id == payload.resume_id, Resume.user_id == user.id)
        .one_or_none()
        if payload.resume_id
        else None
    )
    job = (
        db.query(JobDescription)
        .filter(JobDescription.id == payload.job_id, JobDescription.user_id == user.id)
        .one_or_none()
        if payload.job_id
        else None
    )

    interview = Interview(
        user_id=user.id,
        resume_id=resume.id if resume else None,
        job_id=job.id if job else None,
        mode=payload.mode,
        role=payload.role,
        company=payload.company,
        difficulty=payload.difficulty,
        planned_questions=payload.planned_questions,
        focus_skills=derive_focus_skills(resume, job),
        context=build_context(resume, job),
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview
