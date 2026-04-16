"""Tests for the HNG Stage 0 classify endpoint."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client


@pytest.mark.anyio
async def test_success_response_shape(client):
    prediction = {"gender": "male", "probability": 0.99, "count": 1234}

    with patch("app.main.get_genderize_prediction", AsyncMock(return_value=prediction)):
        response = await client.get("/api/classify?name=john")

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"

    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["name"] == "john"
    assert body["data"]["gender"] == "male"
    assert body["data"]["probability"] == 0.99
    assert body["data"]["sample_size"] == 1234
    assert body["data"]["is_confident"] is True
    datetime.strptime(body["data"]["processed_at"], "%Y-%m-%dT%H:%M:%SZ")


@pytest.mark.anyio
async def test_missing_name_returns_400(client):
    response = await client.get("/api/classify")

    assert response.status_code == 400
    assert response.headers["access-control-allow-origin"] == "*"
    assert response.json()["status"] == "error"


@pytest.mark.anyio
async def test_empty_name_returns_400(client):
    response = await client.get("/api/classify?name=")

    assert response.status_code == 400
    assert response.json()["status"] == "error"


@pytest.mark.anyio
async def test_multiple_name_values_returns_422(client):
    response = await client.get("/api/classify?name=john&name=jane")

    assert response.status_code == 422
    assert response.json()["status"] == "error"


@pytest.mark.anyio
async def test_null_gender_returns_no_prediction_error(client):
    prediction = {"gender": None, "probability": 0.0, "count": 0}

    with patch("app.main.get_genderize_prediction", AsyncMock(return_value=prediction)):
        response = await client.get("/api/classify?name=unknown")

    assert response.status_code == 400
    assert response.json() == {
        "status": "error",
        "message": "No prediction available for the provided name",
    }


@pytest.mark.anyio
async def test_zero_count_returns_no_prediction_error(client):
    prediction = {"gender": "male", "probability": 0.0, "count": 0}

    with patch("app.main.get_genderize_prediction", AsyncMock(return_value=prediction)):
        response = await client.get("/api/classify?name=unknown")

    assert response.status_code == 400
    assert response.json()["message"] == "No prediction available for the provided name"


@pytest.mark.anyio
async def test_confidence_false_when_probability_low(client):
    prediction = {"gender": "male", "probability": 0.69, "count": 500}

    with patch("app.main.get_genderize_prediction", AsyncMock(return_value=prediction)):
        response = await client.get("/api/classify?name=alex")

    assert response.status_code == 200
    assert response.json()["data"]["is_confident"] is False


@pytest.mark.anyio
async def test_confidence_false_when_sample_size_low(client):
    prediction = {"gender": "female", "probability": 0.99, "count": 99}

    with patch("app.main.get_genderize_prediction", AsyncMock(return_value=prediction)):
        response = await client.get("/api/classify?name=sarah")

    assert response.status_code == 200
    assert response.json()["data"]["is_confident"] is False


@pytest.mark.anyio
async def test_fallback_keeps_common_names_available(client):
    with patch(
        "app.main.get_genderize_prediction",
        AsyncMock(side_effect=httpx.ConnectError("network down")),
    ):
        response = await client.get("/api/classify?name=john")

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["data"]["name"] == "john"


@pytest.mark.anyio
async def test_external_failure_for_unknown_name_returns_502(client):
    with patch(
        "app.main.get_genderize_prediction",
        AsyncMock(side_effect=httpx.ConnectError("network down")),
    ):
        response = await client.get("/api/classify?name=notafallbackname")

    assert response.status_code == 502
    assert response.json() == {
        "status": "error",
        "message": "Failed to reach gender prediction service",
    }
