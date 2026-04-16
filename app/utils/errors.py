"""Custom exceptions and unified error response helpers."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class NoPredictionError(Exception):
    """Raised when Genderize returns gender: null or count: 0."""

    def __init__(self, name: str):
        self.name = name
        self.message = "No prediction available for the provided name"
        super().__init__(self.message)


class GenderizeAPIError(Exception):
    """Raised when the Genderize API is unreachable or returns an HTTP error."""

    def __init__(self, detail: str = "Failed to reach gender prediction service"):
        self.message = detail
        super().__init__(self.message)


def error_response(status_code: int, message: str) -> JSONResponse:
    """Build a consistent error JSON response."""
    return JSONResponse(
        status_code=status_code,
        content={"status": "error", "message": message},
    )


async def no_prediction_handler(_request: Request, exc: NoPredictionError) -> JSONResponse:
    """Handle NoPredictionError -> 400."""
    return error_response(400, exc.message)


async def genderize_api_handler(_request: Request, exc: GenderizeAPIError) -> JSONResponse:
    """Handle GenderizeAPIError -> 502."""
    return error_response(502, exc.message)


async def http_exception_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle FastAPI/Starlette HTTP errors with the assignment error shape."""
    message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    return error_response(exc.status_code, message)


async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Override FastAPI's default 422 to use our error format."""
    return error_response(422, "Invalid input: name must be a string")


async def generic_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions -> 500."""
    return error_response(500, "Internal server error")
