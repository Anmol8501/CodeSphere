"""Collects every route module under the /api prefix."""

from fastapi import APIRouter

from app.api.routes import (
    admin,
    admin_problems,
    analytics,
    auth,
    health,
    leaderboard,
    learning,
    problems,
    progress,
    staff,
    student,
    workspace,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(student.router)
api_router.include_router(staff.router)
api_router.include_router(problems.router)
api_router.include_router(workspace.drafts_router)
api_router.include_router(workspace.executions_router)
api_router.include_router(workspace.submissions_router)
api_router.include_router(learning.router)
api_router.include_router(progress.router)
api_router.include_router(leaderboard.router)
api_router.include_router(analytics.router)
api_router.include_router(admin.router)
api_router.include_router(admin_problems.router)
