from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import ApiResponse, ok
from app.schemas.workspace import ExecutionHealth
from app.services import execution_service

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=ApiResponse[dict], summary="Health check (and the app timezone for calendar days)")
def health():
    # The timezone lets clients group "today" / "yesterday" exactly as the
    # server counts streaks and the heatmap (never the browser's own zone).
    return ok("CodeArena API is running", {"status": "ok", "timezone": settings.APP_TIMEZONE})


@router.get(
    "/health/execution",
    response_model=ApiResponse[ExecutionHealth],
    summary="Whether the code execution service (Judge0) is reachable",
)
def execution_health():
    # Only a boolean: no URLs, versions or other infrastructure details.
    available = execution_service.check_available()
    return ok("Execution service available" if available else "Execution service unavailable", ExecutionHealth(available=available))
