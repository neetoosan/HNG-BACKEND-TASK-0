"""Service layer for calling the Genderize API and processing results."""

from datetime import datetime, timezone
from os import getenv

import httpx

from app.utils.errors import GenderizeAPIError, NoPredictionError

# Module-level async client reuses TCP connections across requests.
_client: httpx.AsyncClient | None = None


async def get_client() -> httpx.AsyncClient:
    """Return a shared httpx.AsyncClient, creating it on first use."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=10.0)
    return _client


async def close_client() -> None:
    """Gracefully close the shared HTTP client."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        _client = None


async def classify_name(name: str) -> dict:
    """
    Call the Genderize API and process the response.

    Returns a dict matching the SuccessResponse.data structure.

    Raises:
        NoPredictionError: if gender is null or count is 0.
        GenderizeAPIError: if the external API is unreachable.
    """
    client = await get_client()
    params = {"name": name}
    api_key = getenv("your_api_key_here")
    if api_key:
        params["apikey"] = api_key

    try:
        response = await client.get(
            "https://api.genderize.io",
            params=params,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError:
        raise GenderizeAPIError("Failed to reach gender prediction service")
    except httpx.RequestError:
        raise GenderizeAPIError("Failed to reach gender prediction service")
    except ValueError:
        raise GenderizeAPIError("Invalid response from gender prediction service")

    if data.get("gender") is None or data.get("count", 0) == 0:
        raise NoPredictionError(name)

    probability = data["probability"]
    sample_size = data["count"]

    return {
        "name": name,
        "gender": data["gender"],
        "probability": probability,
        "sample_size": sample_size,
        "is_confident": probability >= 0.7 and sample_size >= 100,
        "processed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
