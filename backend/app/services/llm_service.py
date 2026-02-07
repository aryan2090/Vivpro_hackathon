"""LLM service for extracting structured entities from natural language queries.

Uses the Anthropic Claude API to parse clinical trial search queries into
structured filters matching the ExtractedEntities model.
"""

import json
import logging
import re

import anthropic

from ..config import get_settings
from ..models.entities import ExtractedEntities, LocationFilter
from ..utils.synonyms import (
    AGE_GROUP_SYNONYMS,
    LOCATION_NORMALIZATIONS,
    PHASE_MAPPINGS,
    STATUS_SYNONYMS,
    VALID_AGE_GROUPS,
    VALID_PHASES,
    VALID_STATUSES,
)

logger = logging.getLogger(__name__)


def _build_system_prompt() -> str:
    """Build the system prompt with dynamic synonym sections."""
    status_lines = "\n".join(
        f'   - "{k}" -> {v}' for k, v in STATUS_SYNONYMS.items()
    )
    phase_lines = "\n".join(
        f'   - "{k}" -> {v}' for k, v in PHASE_MAPPINGS.items()
    )
    age_lines = "\n".join(
        f'   - "{k}" -> {v}' for k, v in AGE_GROUP_SYNONYMS.items()
    )
    location_lines = "\n".join(
        f'   - "{k}" -> {v}' for k, v in LOCATION_NORMALIZATIONS.items()
    )

    return f"""You are a clinical trials search assistant. Extract structured filters from natural language queries about clinical trials.

Available fields to extract:
- phase: One of: NA, PHASE1, PHASE1/PHASE2, PHASE2, PHASE2/PHASE3, PHASE3, PHASE4, Phase NA
- condition: The medical condition or disease (e.g., "Breast Cancer", "Diabetes", "Asthma")
- status: One of: ACTIVE_NOT_RECRUITING, COMPLETED, NOT_YET_RECRUITING, RECRUITING, SUSPENDED, TERMINATED, UNKNOWN, WITHDRAWN
- location: Object with optional city, state, and/or country fields
- sponsor: Organization name (e.g., "AstraZeneca", "Pfizer", "National Cancer Institute (NCI)")
- keyword: Specific terms like gene names (BRCA1, EGFR), drug names, or technical terms not captured by other fields
- age_group: One of: "adult", "older-adults", "child", "adolescent", "infant", "toddler"
- enrollment_min: Minimum number of participants (integer)
- enrollment_max: Maximum number of participants (integer)

Domain synonym mappings (translate user terms to correct enum values):

Status synonyms:
{status_lines}

Phase synonyms:
{phase_lines}

Age group synonyms:
{age_lines}

Location normalizations:
{location_lines}

Additional enrollment interpretations:
   - "large trials", "big studies" -> enrollment_min: 500
   - "small trials", "small studies" -> enrollment_max: 100

Output ONLY a valid JSON object with this exact schema:
{{
  "phase": "PHASE2" or null,
  "condition": "disease name" or null,
  "status": "RECRUITING" or null,
  "location": {{"city": "...", "state": "...", "country": "..."}} or null,
  "sponsor": "company name" or null,
  "keyword": "gene/drug name" or null,
  "age_group": "adult" or null,
  "enrollment_min": 500 or null,
  "enrollment_max": null,
  "confidence": 0.0 to 1.0,
  "clarification": "question to ask user" or null
}}

Rules:
1. Only extract entities that are clearly stated or strongly implied in the query.
2. Set confidence based on query clarity:
   - 0.9-1.0: All terms are clear and unambiguous
   - 0.7-0.9: Mostly clear with minor uncertainty
   - 0.5-0.7: Some ambiguity present
   - 0.3-0.5: Significant ambiguity or possible misspellings
   - Below 0.3: Gibberish, unrelated, or empty query
3. Set clarification to a helpful question when:
   - The query is ambiguous and could match multiple interpretations
   - Medical terms appear misspelled and you cannot confidently auto-correct
   - The query is too broad (no specific condition, phase, or status)
   - The query contains conflicting filters
   - The query is gibberish or unrelated to clinical trials
4. Set clarification to null when the query is clear enough (confidence >= 0.7).
5. Return null for fields not mentioned or implied in the query.
6. For the location field, only include sub-fields (city, state, country) that are specified. Omit sub-fields that are null.
7. Always respond with valid JSON only. No markdown, no code fences, no explanations."""


SYSTEM_PROMPT = _build_system_prompt()


def _parse_json_response(text: str) -> dict:
    """Parse JSON from LLM response, handling markdown code fences."""
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code fences
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))

    # Try finding the first { ... } block (supports one level of nesting)
    match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))

    raise json.JSONDecodeError("No JSON object found in response", text, 0)


def _validate_and_normalize(data: dict) -> dict:
    """Validate and normalize LLM output against known enum values."""
    if data.get("phase") and data["phase"] not in VALID_PHASES:
        logger.warning("LLM returned invalid phase: %s", data["phase"])
        data["phase"] = None

    if data.get("status") and data["status"] not in VALID_STATUSES:
        logger.warning("LLM returned invalid status: %s", data["status"])
        data["status"] = None

    if data.get("age_group") and data["age_group"] not in VALID_AGE_GROUPS:
        logger.warning("LLM returned invalid age_group: %s", data["age_group"])
        data["age_group"] = None

    if "confidence" in data:
        data["confidence"] = max(0.0, min(1.0, float(data["confidence"])))

    loc = data.get("location")
    if isinstance(loc, dict):
        loc = {k: v for k, v in loc.items() if v is not None}
        if loc:
            data["location"] = LocationFilter(**loc)
        else:
            data["location"] = None

    for field in ("enrollment_min", "enrollment_max"):
        val = data.get(field)
        if val is not None:
            try:
                data[field] = int(val)
            except (TypeError, ValueError):
                data[field] = None

    return data


async def extract_entities(query: str) -> ExtractedEntities:
    """Extract structured entities from a natural language clinical trials query.

    Args:
        query: The user's natural language search query.

    Returns:
        ExtractedEntities with extracted filters, confidence score,
        and optional clarification question.
    """
    if not query or not query.strip():
        return ExtractedEntities(
            confidence=0.1,
            clarification="Please enter a search query about clinical trials.",
        )

    settings = get_settings()
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    try:
        message = await client.messages.create(
            model=settings.claude_model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Extract entities from this clinical trials "
                        f'search query: "{query.strip()}"'
                    ),
                }
            ],
        )

        response_text = message.content[0].text
        logger.debug("LLM response: %s", response_text)

        data = _parse_json_response(response_text)
        data = _validate_and_normalize(data)

        return ExtractedEntities(**data)

    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse LLM JSON response: %s", exc)
        return ExtractedEntities(
            confidence=0.3,
            clarification="I had trouble understanding your query. Could you rephrase it?",
        )
    except anthropic.APIError as exc:
        logger.error("Anthropic API error: %s", exc)
        return ExtractedEntities(
            confidence=0.0,
            clarification="The search service is temporarily unavailable. Please try again.",
        )
    except Exception as exc:
        logger.error("Unexpected error in entity extraction: %s", exc, exc_info=True)
        return ExtractedEntities(
            confidence=0.0,
            clarification="An unexpected error occurred. Please try again.",
        )
