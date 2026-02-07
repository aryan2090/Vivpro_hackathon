"""Search-related API endpoints including auto-suggestions."""

import logging

from fastapi import APIRouter, HTTPException, Query

from ..models.schemas import SearchResponse, SuggestionResponse, SummaryResponse
from ..services.es_service import es_service
from ..services.llm_service import extract_entities
from ..services.suggestion import suggestion_service
from ..services.summary_service import generate_summary

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search/{query}", response_model=SearchResponse)
async def search_trials(
    query: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
) -> SearchResponse:
    """Search clinical trials using a natural language query."""
    try:
        entities = await extract_entities(query)
        results, total = await es_service.search(entities, page, page_size)
        return SearchResponse(
            query_interpretation=entities,
            results=results,
            total=total,
            page=page,
            page_size=page_size,
            clarification=entities.clarification,
        )
    except Exception as exc:
        logger.error("Search failed for query '%s': %s", query, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/summary/{query}", response_model=SummaryResponse)
async def get_summary(query: str) -> SummaryResponse:
    """Generate an AI summary for a search query's results."""
    try:
        entities = await extract_entities(query)
        results, _ = await es_service.search(entities, page=1, page_size=10)
        summary = await generate_summary(results, query) if results else None
        return SummaryResponse(summary=summary)
    except Exception as exc:
        logger.error("Summary failed for query '%s': %s", query, exc, exc_info=True)
        return SummaryResponse(summary=None)


@router.get("/suggest", response_model=SuggestionResponse)
async def get_suggestions(
    q: str = Query(..., min_length=2, description="Partial query text"),
) -> SuggestionResponse:
    """Get type-ahead suggestions for partial query."""
    try:
        suggestions = await suggestion_service.get_suggestions(q)
        return SuggestionResponse(suggestions=suggestions)
    except Exception as exc:
        logger.error("Suggestions failed for q='%s': %s", q, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
