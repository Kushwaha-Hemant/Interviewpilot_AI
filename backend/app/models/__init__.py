"""Import every model here so `Base.metadata` is complete for create_all / Alembic."""

from app.database.base import Base
from app.models.interview import Interview, InterviewTurn
from app.models.job import JobDescription
from app.models.recruiter import InterviewInvite
from app.models.report import InterviewReport
from app.models.resume import Resume
from app.models.user import User
from app.models.verification import EmailVerification

__all__ = [
    "Base",
    "EmailVerification",
    "Interview",
    "InterviewInvite",
    "InterviewReport",
    "InterviewTurn",
    "JobDescription",
    "Resume",
    "User",
]
