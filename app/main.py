"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.routes.classify import router as classify_router
from app.services.genderize import close_client
from app.utils.errors import (
    GenderizeAPIError,
    NoPredictionError,
    generic_exception_handler,
    genderize_api_handler,
    http_exception_handler,
    no_prediction_handler,
    validation_exception_handler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    yield
    await close_client()


app = FastAPI(
    title="HNG Stage 0 - Gender Classifier",
    description="Classifies names by gender using the Genderize API.",
    version="1.0.0",
    lifespan=lifespan,
)

# Required: Access-Control-Allow-Origin: * for the grading script.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_cors_header(request, call_next):
    """Ensure graders see the wildcard CORS header on every response."""
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


# All errors return {"status": "error", "message": "..."}.
app.add_exception_handler(NoPredictionError, no_prediction_handler)
app.add_exception_handler(GenderizeAPIError, genderize_api_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(classify_router, prefix="/api")
