"""GET /api/classify endpoint."""

from fastapi import APIRouter, Query

from app.schemas.responses import SuccessResponse
from app.services.genderize import classify_name
from app.utils.errors import error_response

router = APIRouter()


@router.get("/classify", response_model=SuccessResponse)
async def classify(name: str = Query(None)):
    """
    Classify a name by gender using the Genderize API.

    Query Parameters:
        name (str): The name to classify. Required.

    Returns:
        SuccessResponse with gender prediction data.
    """
    if name is None or name.strip() == "":
        return error_response(400, "Missing or empty 'name' query parameter")

    result = await classify_name(name)
    return {"status": "success", "data": result}
