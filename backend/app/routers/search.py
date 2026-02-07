"""Search-related API endpoints including auto-suggestions."""

from fastapi import APIRouter, Query

from ..models.schemas import SuggestionResponse
from ..services.suggestion import suggestion_service

router = APIRouter()


@router.get("/suggestions", response_model=SuggestionResponse)
async def get_suggestions(
    q: str = Query("", description="Search prefix for suggestions"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of suggestions"),
) -> SuggestionResponse:
    suggestions = await suggestion_service.get_suggestions(q, limit=limit)
    return SuggestionResponse(suggestions=suggestions)
