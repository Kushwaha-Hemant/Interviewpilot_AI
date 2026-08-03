"""Feature 3 — resume upload, text extraction, structured parsing."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from sqlalchemy import select

from app.ai.ingestion import parse_resume
from app.auth.dependencies import CurrentUser, DbSession
from app.core.config import settings
from app.models.resume import Resume
from app.schemas.api import ResumeOut
from app.utils.pdf_text import PdfExtractionError, extract_text

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("", response_model=ResumeOut, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
) -> Resume:
    if (file.content_type or "") not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF resumes are supported",
        )

    data = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.max_upload_mb} MB limit",
        )

    try:
        raw_text = extract_text(data)
    except PdfExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    resume = Resume(
        user_id=user.id,
        filename=file.filename or "resume.pdf",
        raw_text=raw_text,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    # Persist the original alongside the extraction so reports can link back to it.
    target = settings.storage_path / "resumes" / f"{resume.id}.pdf"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    resume.storage_path = str(target)
    db.commit()

    return await parse_resume(db, resume)


@router.get("", response_model=list[ResumeOut])
def list_resumes(user: CurrentUser, db: DbSession) -> list[Resume]:
    return list(
        db.scalars(
            select(Resume).where(Resume.user_id == user.id).order_by(Resume.created_at.desc())
        )
    )


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(resume_id: str, user: CurrentUser, db: DbSession) -> Resume:
    resume = db.get(Resume, resume_id)
    if resume is None or resume.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume


@router.post("/{resume_id}/reparse", response_model=ResumeOut)
async def reparse_resume(resume_id: str, user: CurrentUser, db: DbSession) -> Resume:
    resume = db.get(Resume, resume_id)
    if resume is None or resume.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return await parse_resume(db, resume)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_resume(resume_id: str, user: CurrentUser, db: DbSession) -> None:
    resume = db.get(Resume, resume_id)
    if resume is None or resume.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    db.delete(resume)
    db.commit()
