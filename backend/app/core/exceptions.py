"""Custom exception + global handlers that produce the standard error envelope:

    {"success": false, "message": "...", "error": {"code": "...", "message": "..."},
     "errors": [...optional field errors...]}

`message` is kept for existing clients; `error.code` is a stable machine code.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("codearena")


DEFAULT_ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


class AppError(Exception):
    """Raise this from services/routes for expected, user-facing errors."""

    def __init__(
        self,
        status_code: int,
        message: str,
        headers: dict[str, str] | None = None,
        code: str | None = None,
    ):
        self.status_code = status_code
        self.message = message
        self.headers = headers
        self.code = code
        super().__init__(message)


def _error(status_code: int, message: str, errors=None, headers=None, code: str | None = None) -> JSONResponse:
    code = code or DEFAULT_ERROR_CODES.get(status_code, "ERROR")
    body: dict = {"success": False, "message": message, "error": {"code": code, "message": message}}
    if errors:
        body["errors"] = errors
    return JSONResponse(status_code=status_code, content=body, headers=headers)


def _friendly_validation_message(err: dict) -> str:
    field = str(err["loc"][-1]) if err.get("loc") else ""
    if field == "email" and err.get("type") == "value_error":
        return "Please enter a valid email address."
    if err.get("type") == "missing":
        return f"{field.replace('_', ' ').capitalize()} is required."
    if err.get("type") == "extra_forbidden":
        if field == "role":
            return "Role cannot be chosen during registration."
        return f"Unexpected field: {field}."
    if err.get("type") in ("enum", "literal_error"):
        # e.g. "Invalid difficulty. Input should be 'EASY', 'MEDIUM' or 'HARD'."
        return f"Invalid {field.replace('_', ' ')}. {err.get('msg', '')}."
    return err.get("msg", "Invalid value").removeprefix("Value error, ")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return _error(exc.status_code, exc.message, headers=exc.headers, code=exc.code)

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(_: Request, exc: StarletteHTTPException):
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        if exc.status_code == status.HTTP_404_NOT_FOUND and message == "Not Found":
            message = "The requested resource was not found."
        return _error(exc.status_code, message, headers=getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError):
        errors = [
            {
                "field": ".".join(
                    str(part) for part in err["loc"] if part not in ("body", "query", "path")
                ),
                "message": _friendly_validation_message(err),
            }
            for err in exc.errors()
        ]
        first = errors[0]["message"] if errors else "Invalid request."
        return _error(status.HTTP_422_UNPROCESSABLE_CONTENT, first, errors=errors)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception):
        # Log full details server-side; never send them to the client.
        logger.exception("Unhandled server error", exc_info=exc)
        return _error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Something went wrong on our side. Please try again later.",
        )
