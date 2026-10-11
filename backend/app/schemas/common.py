"""Standard response envelope used by every endpoint.

Success: {"success": true,  "message": "...", "data": {...}}
Error:   {"success": false, "message": "..."}   (see core/exceptions.py)
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

# FastAPI `responses=` mapping (status code -> OpenAPI response).
ResponsesDict = dict[int | str, dict[str, Any]]


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: T | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str


def ok(message: str, data=None) -> dict:
    """Small helper so routes read nicely: `return ok("Login successful", data)`."""
    return {"success": True, "message": message, "data": data}


class Page(BaseModel, Generic[T]):
    """Standard paginated list: {"items", "page", "page_size", "total", "total_pages"}."""

    items: list[T]
    page: int
    page_size: int
    total: int
    total_pages: int


def total_pages(total: int, page_size: int) -> int:
    return -(-total // page_size) if page_size > 0 else 0
