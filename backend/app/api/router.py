from fastapi import APIRouter

from app.api.routes import auth, dashboard, interviews, jobs, recruiter, reports, resumes, voice

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(resumes.router)
api_router.include_router(jobs.router)
api_router.include_router(interviews.router)
api_router.include_router(reports.router)
api_router.include_router(dashboard.router)
api_router.include_router(voice.router)
api_router.include_router(recruiter.router)
