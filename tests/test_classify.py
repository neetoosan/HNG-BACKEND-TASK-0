"""Tests for the GET /api/classify endpoint."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _mock_genderize_response(gender="male", probability=0.99, count=1234):
    """Helper to build a mock Genderize API response."""
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "count": count,
        "name": "test",
        "gender": gender,
        "probability": probability,
    }
    mock_resp.raise_for_status = lambda: None
    return mock_resp


@pytest.mark.anyio
async def test_successful_classification(client):
    """Test a normal successful request."""
    with patch("app.services.genderize.get_client") as mock_get:
        mock_client = AsyncMock()
        mock_client.get.return_value = _mock_genderize_response()
        mock_get.return_value = mock_client

        resp = await client.get("/api/classify", params={"name": "james"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"]["name"] == "james"
    assert body["data"]["gender"] == "male"
    assert body["data"]["probability"] == 0.99
    assert body["data"]["sample_size"] == 1234
    assert body["data"]["is_confident"] is True
    assert "processed_at" in body["data"]
    assert body["data"]["processed_at"].endswith("Z")
    datetime.strptime(body["data"]["processed_at"], "%Y-%m-%dT%H:%M:%SZ")


@pytest.mark.anyio
async def test_missing_name(client):
    """Test request with no name query param -> 400."""
    resp = await client.get("/api/classify")
    assert resp.status_code == 400
    body = resp.json()
    assert body["status"] == "error"
    assert "name" in body["message"].lower() or "missing" in body["message"].lower()


@pytest.mark.anyio
async def test_empty_name(client):
    """Test request with empty name -> 400."""
    resp = await client.get("/api/classify", params={"name": ""})
    assert resp.status_code == 400
    body = resp.json()
    assert body["status"] == "error"


@pytest.mark.anyio
async def test_no_prediction_null_gender(client):
    """Test Genderize returning gender: null -> error response."""
    with patch("app.services.genderize.get_client") as mock_get:
        mock_client = AsyncMock()
        mock_client.get.return_value = _mock_genderize_response(
            gender=None, probability=0.0, count=0
        )
        mock_get.return_value = mock_client

        resp = await client.get("/api/classify", params={"name": "xyzabc123"})

    assert resp.status_code == 400
    body = resp.json()
    assert body["status"] == "error"
    assert "no prediction" in body["message"].lower()


@pytest.mark.anyio
async def test_no_prediction_zero_count(client):
    """Test Genderize returning count: 0 -> error response."""
    with patch("app.services.genderize.get_client") as mock_get:
        mock_client = AsyncMock()
        mock_client.get.return_value = _mock_genderize_response(
            gender="male", probability=0.0, count=0
        )
        mock_get.return_value = mock_client

        resp = await client.get("/api/classify", params={"name": "unknown"})

    assert resp.status_code == 400
    assert resp.json() == {
        "status": "error",
        "message": "No prediction available for the provided name",
    }


@pytest.mark.anyio
async def test_confidence_false_low_probability(client):
    """Test is_confident is false when probability < 0.7."""
    with patch("app.services.genderize.get_client") as mock_get:
        mock_client = AsyncMock()
        mock_client.get.return_value = _mock_genderize_response(
            probability=0.5, count=200
        )
        mock_get.return_value = mock_client

        resp = await client.get("/api/classify", params={"name": "alex"})

    assert resp.status_code == 200
    assert resp.json()["data"]["is_confident"] is False


@pytest.mark.anyio
async def test_confidence_false_low_sample(client):
    """Test is_confident is false when sample_size < 100."""
    with patch("app.services.genderize.get_client") as mock_get:
        mock_client = AsyncMock()
        mock_client.get.return_value = _mock_genderize_response(
            probability=0.95, count=50
        )
        mock_get.return_value = mock_client

        resp = await client.get("/api/classify", params={"name": "alex"})

    assert resp.status_code == 200
    assert resp.json()["data"]["is_confident"] is False


@pytest.mark.anyio
async def test_confidence_true(client):
    """Test is_confident is true when probability >= 0.7 AND sample_size >= 100."""
    with patch("app.services.genderize.get_client") as mock_get:
        mock_client = AsyncMock()
        mock_client.get.return_value = _mock_genderize_response(
            probability=0.85, count=500
        )
        mock_get.return_value = mock_client

        resp = await client.get("/api/classify", params={"name": "sarah"})

    assert resp.status_code == 200
    assert resp.json()["data"]["is_confident"] is True


@pytest.mark.anyio
async def test_cors_header(client):
    """Verify CORS header is present."""
    with patch("app.services.genderize.get_client") as mock_get:
        mock_client = AsyncMock()
        mock_client.get.return_value = _mock_genderize_response()
        mock_get.return_value = mock_client

        resp = await client.get(
            "/api/classify",
            params={"name": "test"},
            headers={"origin": "http://example.com"},
        )

    assert resp.headers.get("access-control-allow-origin") == "*"


@pytest.mark.anyio
async def test_genderize_timeout_returns_502(client):
    """Test external API request failures map to the required 502 shape."""
    with patch("app.services.genderize.get_client") as mock_get:
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("timeout")
        mock_get.return_value = mock_client

        resp = await client.get("/api/classify", params={"name": "james"})

    assert resp.status_code == 502
    assert resp.json() == {
        "status": "error",
        "message": "Failed to reach gender prediction service",
    }


@pytest.mark.anyio
async def test_unknown_route_uses_error_shape(client):
    """Test framework HTTP errors keep the required error response shape."""
    resp = await client.get("/not-found")

    assert resp.status_code == 404
    assert resp.json()["status"] == "error"
    assert "message" in resp.json()
