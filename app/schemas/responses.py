"""Pydantic response models for the classify endpoint."""

from pydantic import BaseModel


class ClassifyData(BaseModel):
    """Successful classification result data."""

    name: str
    gender: str
    probability: float
    sample_size: int
    is_confident: bool
    processed_at: str  # ISO 8601 UTC


class SuccessResponse(BaseModel):
    """Wrapper for successful responses."""

    status: str = "success"
    data: ClassifyData


class ErrorResponse(BaseModel):
    """Wrapper for error responses."""

    status: str = "error"
    message: str
