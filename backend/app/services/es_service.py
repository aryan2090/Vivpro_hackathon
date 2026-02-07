"""Elasticsearch query builder and search service.

Converts ExtractedEntities into Elasticsearch Query DSL and executes
searches against the clinical_trials index.
"""

import logging
from typing import Any, Dict, List, Optional

from elasticsearch import Elasticsearch

from ..config import get_settings
from ..models.entities import ExtractedEntities
from ..models.schemas import AgeCategory, Facility, Sponsor, TrialResult

logger = logging.getLogger(__name__)

_SOURCE_FIELDS = [
    "nct_id",
    "brief_title",
    "official_title",
    "phase",
    "overall_status",
    "enrollment",
    "sponsors",
    "facilities",
    "conditions",
    "brief_summaries_description",
    "start_date",
    "completion_date",
    "age",
    "gender",
    "study_type",
    "source",
]


class ElasticsearchService:
    def __init__(self) -> None:
        settings = get_settings()
        self.es = Elasticsearch([settings.es_url])
        self.index = settings.es_index

    def build_query(self, entities: ExtractedEntities) -> Dict[str, Any]:
        """Build Elasticsearch query DSL from extracted entities."""
        must_clauses: List[Dict[str, Any]] = []
        filter_clauses: List[Dict[str, Any]] = []

        # Phase - exact match filter
        if entities.phase:
            filter_clauses.append({"term": {"phase": entities.phase}})

        # Status - exact match filter
        if entities.status:
            filter_clauses.append({"term": {"overall_status": entities.status}})

        # Condition - text match across title and description
        if entities.condition:
            must_clauses.append(
                {
                    "multi_match": {
                        "query": entities.condition,
                        "fields": [
                            "brief_title^3",
                            "official_title^2",
                            "brief_summaries_description",
                        ],
                        "type": "best_fields",
                        "fuzziness": "AUTO",
                    }
                }
            )

        # Keyword - multi-match with phrase_prefix
        if entities.keyword:
            must_clauses.append(
                {
                    "multi_match": {
                        "query": entities.keyword,
                        "fields": [
                            "brief_title^2",
                            "official_title^2",
                            "brief_summaries_description",
                            "detailed_description",
                        ],
                        "type": "phrase_prefix",
                    }
                }
            )

        # Location - nested query on facilities
        if entities.location:
            location_filters: List[Dict[str, Any]] = []
            if entities.location.country:
                location_filters.append(
                    {"term": {"facilities.country": entities.location.country}}
                )
            if entities.location.state:
                location_filters.append(
                    {"term": {"facilities.state": entities.location.state}}
                )
            if entities.location.city:
                location_filters.append(
                    {"term": {"facilities.city": entities.location.city}}
                )
            if location_filters:
                filter_clauses.append(
                    {
                        "nested": {
                            "path": "facilities",
                            "query": {"bool": {"must": location_filters}},
                        }
                    }
                )

        # Sponsor - nested query
        if entities.sponsor:
            filter_clauses.append(
                {
                    "nested": {
                        "path": "sponsors",
                        "query": {"match": {"sponsors.name": entities.sponsor}},
                    }
                }
            )

        # Age group - nested query
        if entities.age_group:
            filter_clauses.append(
                {
                    "nested": {
                        "path": "age",
                        "query": {"term": {"age.age_category": entities.age_group}},
                    }
                }
            )

        # Enrollment range
        if entities.enrollment_min is not None or entities.enrollment_max is not None:
            range_query: Dict[str, int] = {}
            if entities.enrollment_min is not None:
                range_query["gte"] = entities.enrollment_min
            if entities.enrollment_max is not None:
                range_query["lte"] = entities.enrollment_max
            filter_clauses.append({"range": {"enrollment": range_query}})

        # Build final query
        if not must_clauses and not filter_clauses:
            return {"match_all": {}}

        query: Dict[str, Any] = {"bool": {}}
        if must_clauses:
            query["bool"]["must"] = must_clauses
        if filter_clauses:
            query["bool"]["filter"] = filter_clauses
        return query

    async def search(
        self,
        entities: ExtractedEntities,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[List[TrialResult], int]:
        """Execute search and return results with total count."""
        query = self.build_query(entities)

        response = self.es.search(
            index=self.index,
            body={
                "query": query,
                "from": (page - 1) * page_size,
                "size": page_size,
                "sort": [{"_score": "desc"}, {"enrollment": "desc"}],
                "_source": _SOURCE_FIELDS,
            },
        )

        results: List[TrialResult] = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            results.append(
                TrialResult(
                    nct_id=source["nct_id"],
                    brief_title=source["brief_title"],
                    official_title=source.get("official_title"),
                    phase=source.get("phase"),
                    overall_status=source.get("overall_status"),
                    enrollment=source.get("enrollment"),
                    sponsors=[Sponsor(**s) for s in source.get("sponsors", [])],
                    facilities=[
                        Facility(**f) for f in source.get("facilities", [])[:3]
                    ],
                    conditions=source.get("conditions", []),
                    brief_summaries_description=source.get(
                        "brief_summaries_description"
                    ),
                    start_date=source.get("start_date"),
                    completion_date=source.get("completion_date"),
                    age=[AgeCategory(**a) for a in source.get("age", [])],
                    gender=source.get("gender"),
                    study_type=source.get("study_type"),
                    source=source.get("source"),
                )
            )

        total = response["hits"]["total"]["value"]
        return results, total


es_service = ElasticsearchService()
