"""Service for generating AI-powered summaries of clinical trial search results."""

import logging
from typing import List, Optional

import anthropic

from ..config import get_settings
from ..models.schemas import TrialResult

logger = logging.getLogger(__name__)

SUMMARY_SYSTEM_PROMPT = """You are a clinical trials research assistant. Synthesize the provided clinical trial results into a concise overview.

Rules:
1. Write 3-5 sentences summarizing the key findings across the trials
2. Include numbered citation markers [1], [2], etc. to reference specific trials
3. Citation numbers correspond to the trial's position in the results (1-indexed)
4. Focus on: trial phases, conditions being studied, recruiting status, sponsor patterns, and notable enrollment sizes
5. Be objective and informative - help users quickly understand what types of trials match their search
6. Only cite trials that you specifically mention details from
7. Output plain text only - no markdown formatting"""


async def generate_summary(
    results: List[TrialResult], query: str
) -> Optional[str]:
    """Generate an AI summary of search results with citations.

    Args:
        results: List of trial results to summarize (uses first 10).
        query: The original search query for context.

    Returns:
        Summary string with [n] citation markers, or None if generation fails.
    """
    if not results:
        return None

    settings = get_settings()
    if not settings.anthropic_api_key:
        logger.warning("No Anthropic API key configured, skipping summary generation")
        return None

    trials_context = []
    for i, trial in enumerate(results[:10], start=1):
        conditions = ", ".join(
            val for c in trial.conditions for val in c.values() if val
        )[:200]
        sponsor = trial.sponsors[0].name if trial.sponsors else "Unknown"
        trials_context.append(
            f"[{i}] {trial.brief_title}\n"
            f"    NCT ID: {trial.nct_id}\n"
            f"    Phase: {trial.phase or 'N/A'}\n"
            f"    Status: {trial.overall_status or 'N/A'}\n"
            f"    Conditions: {conditions or 'N/A'}\n"
            f"    Sponsor: {sponsor}\n"
            f"    Enrollment: {trial.enrollment or 'N/A'}"
        )

    context_text = "\n\n".join(trials_context)
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    try:
        message = await client.messages.create(
            model=settings.claude_model,
            max_tokens=500,
            system=SUMMARY_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f'Search query: "{query}"\n\n'
                        f"Clinical trials found:\n\n{context_text}\n\n"
                        "Provide a brief summary with citations."
                    ),
                }
            ],
        )
        return message.content[0].text.strip()
    except anthropic.APIError as exc:
        logger.error("Summary generation API error: %s", exc)
        return None
    except Exception as exc:
        logger.error("Unexpected error generating summary: %s", exc, exc_info=True)
        return None
