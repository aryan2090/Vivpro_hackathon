"""Auto-suggestion service using Elasticsearch search_as_you_type fields."""

import logging
from typing import List

from elasticsearch import Elasticsearch

from ..config import get_settings

logger = logging.getLogger(__name__)

MIN_PREFIX_LENGTH = 2
DEFAULT_LIMIT = 10

COMMON_CONDITIONS = [
    "Breast Cancer",
    "Lung Cancer",
    "Diabetes",
    "Asthma",
    "COVID-19",
    "Heart Disease",
    "Alzheimer's",
    "Melanoma",
    "Leukemia",
    "Rheumatoid Arthritis",
    "Multiple Sclerosis",
]


class SuggestionService:
    def __init__(self) -> None:
        settings = get_settings()
        self.es = Elasticsearch([settings.es_url])
        self.index = settings.es_index

    async def get_suggestions(
        self, prefix: str, limit: int = DEFAULT_LIMIT
    ) -> List[str]:
        if not prefix or len(prefix.strip()) < MIN_PREFIX_LENGTH:
            return []

        prefix = prefix.strip()

        response = self.es.search(
            index=self.index,
            body={
                "size": limit,
                "query": {
                    "multi_match": {
                        "query": prefix,
                        "type": "bool_prefix",
                        "fields": [
                            "brief_title.suggest",
                            "brief_title.suggest._2gram",
                            "brief_title.suggest._3gram",
                            "official_title.suggest",
                            "official_title.suggest._2gram",
                            "official_title.suggest._3gram",
                        ],
                    }
                },
                "_source": ["brief_title"],
            },
        )

        suggestions: List[str] = []
        seen: set = set()

        for hit in response["hits"]["hits"]:
            title = hit["_source"].get("brief_title", "")
            key = title.lower()
            if key and key not in seen:
                seen.add(key)
                suggestions.append(title)

        if not suggestions:
            fallback = self.es.search(
                index=self.index,
                body={
                    "size": limit,
                    "query": {
                        "multi_match": {
                            "query": prefix,
                            "type": "phrase_prefix",
                            "fields": ["brief_title", "official_title"],
                        }
                    },
                    "_source": ["brief_title"],
                },
            )

            for hit in fallback["hits"]["hits"]:
                title = hit["_source"].get("brief_title", "")
                key = title.lower()
                if key and key not in seen:
                    seen.add(key)
                    suggestions.append(title)

        return suggestions[:limit]

    async def get_condition_suggestions(self, prefix: str) -> List[str]:
        if not prefix or len(prefix.strip()) < MIN_PREFIX_LENGTH:
            return []

        prefix_lower = prefix.strip().lower()
        matching = [c for c in COMMON_CONDITIONS if c.lower().startswith(prefix_lower)]
        return matching[:5]


suggestion_service = SuggestionService()
