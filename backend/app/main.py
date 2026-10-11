"""CodeArena FastAPI application entry point.

Run with:  uvicorn app.main:app --reload
Docs at:   http://localhost:8000/docs
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.db.session import SessionLocal
from app.services import execution_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Submissions left PENDING/RUNNING by a restart must never stay that way.
    try:
        with SessionLocal() as db:
            execution_service.expire_stuck_submissions(db)
    except SQLAlchemyError as exc:  # database unreachable / not migrated yet: requests will report it
        logging.getLogger("codearena").warning("startup_cleanup_skipped reason=%s", type(exc).__name__)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        title=settings.APP_NAME,
        version="0.1.0",
        description="CodeArena: coding learning & assessment platform. Code runs only inside Judge0.",
    )

    origins = settings.cors_origins_list
    # A wildcard origin must never be combined with credentials.
    allow_credentials = "*" not in origins
    if not allow_credentials:
        logging.getLogger("codearena").warning(
            "CORS_ORIGINS contains '*': credentials are disabled. List explicit origins instead."
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    register_exception_handlers(app)
    app.include_router(api_router)

    @app.get("/", include_in_schema=False)
    def root():
        return {"success": True, "message": "CodeArena API. See /docs", "data": None}

    return app


app = create_app()
