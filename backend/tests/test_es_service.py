"""Tests for the Elasticsearch query builder and search service."""

from unittest.mock import MagicMock, patch

import pytest

from app.models.entities import ExtractedEntities, LocationFilter
from app.models.schemas import AgeCategory, Facility, Sponsor, TrialResult
from app.services.es_service import ElasticsearchService


@pytest.fixture
def service():
    with patch("app.services.es_service.Elasticsearch"):
        with patch("app.services.es_service.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                es_url="http://localhost:9200",
                es_index="clinical_trials",
            )
            svc = ElasticsearchService()
    return svc


# ---------- build_query tests ----------


class TestBuildQueryEmpty:
    def test_empty_entities_returns_match_all(self, service):
        entities = ExtractedEntities()
        query = service.build_query(entities)
        assert query == {"match_all": {}}

    def test_all_none_returns_match_all(self, service):
        entities = ExtractedEntities(
            phase=None, condition=None, status=None, location=None,
            sponsor=None, keyword=None, age_group=None,
            enrollment_min=None, enrollment_max=None,
        )
        query = service.build_query(entities)
        assert query == {"match_all": {}}


class TestBuildQueryPhase:
    def test_phase_only(self, service):
        entities = ExtractedEntities(phase="PHASE2")
        query = service.build_query(entities)
        assert query == {
            "bool": {
                "filter": [{"term": {"phase": "PHASE2"}}],
            }
        }


class TestBuildQueryStatus:
    def test_status_only(self, service):
        entities = ExtractedEntities(status="RECRUITING")
        query = service.build_query(entities)
        assert query == {
            "bool": {
                "filter": [{"term": {"overall_status": "RECRUITING"}}],
            }
        }


class TestBuildQueryCondition:
    def test_condition_produces_multi_match(self, service):
        entities = ExtractedEntities(condition="Asthma")
        query = service.build_query(entities)
        assert "bool" in query
        must = query["bool"]["must"]
        assert len(must) == 1
        mm = must[0]["multi_match"]
        assert mm["query"] == "Asthma"
        assert mm["type"] == "best_fields"
        assert mm["fuzziness"] == "AUTO"
        assert "brief_title^3" in mm["fields"]
        assert "official_title^2" in mm["fields"]
        assert "brief_summaries_description" in mm["fields"]


class TestBuildQueryKeyword:
    def test_keyword_produces_phrase_prefix(self, service):
        entities = ExtractedEntities(keyword="BRCA1")
        query = service.build_query(entities)
        must = query["bool"]["must"]
        assert len(must) == 1
        mm = must[0]["multi_match"]
        assert mm["query"] == "BRCA1"
        assert mm["type"] == "phrase_prefix"
        assert "detailed_description" in mm["fields"]


class TestBuildQueryLocation:
    def test_location_country_only(self, service):
        entities = ExtractedEntities(
            location=LocationFilter(country="United States")
        )
        query = service.build_query(entities)
        nested = query["bool"]["filter"][0]["nested"]
        assert nested["path"] == "facilities"
        must = nested["query"]["bool"]["must"]
        assert len(must) == 1
        assert must[0] == {"term": {"facilities.country": "United States"}}

    def test_location_full(self, service):
        entities = ExtractedEntities(
            location=LocationFilter(
                city="Boston", state="Massachusetts", country="United States"
            )
        )
        query = service.build_query(entities)
        nested = query["bool"]["filter"][0]["nested"]
        must = nested["query"]["bool"]["must"]
        assert len(must) == 3

    def test_location_empty_produces_match_all(self, service):
        entities = ExtractedEntities(
            location=LocationFilter()
        )
        query = service.build_query(entities)
        assert query == {"match_all": {}}


class TestBuildQuerySponsor:
    def test_sponsor_nested(self, service):
        entities = ExtractedEntities(sponsor="Pfizer")
        query = service.build_query(entities)
        nested = query["bool"]["filter"][0]["nested"]
        assert nested["path"] == "sponsors"
        assert nested["query"] == {"match": {"sponsors.name": "Pfizer"}}


class TestBuildQueryAgeGroup:
    def test_age_group_nested(self, service):
        entities = ExtractedEntities(age_group="adult")
        query = service.build_query(entities)
        nested = query["bool"]["filter"][0]["nested"]
        assert nested["path"] == "age"
        assert nested["query"] == {"term": {"age.age_category": "adult"}}


class TestBuildQueryEnrollment:
    def test_enrollment_min_only(self, service):
        entities = ExtractedEntities(enrollment_min=100)
        query = service.build_query(entities)
        range_q = query["bool"]["filter"][0]["range"]["enrollment"]
        assert range_q == {"gte": 100}

    def test_enrollment_max_only(self, service):
        entities = ExtractedEntities(enrollment_max=500)
        query = service.build_query(entities)
        range_q = query["bool"]["filter"][0]["range"]["enrollment"]
        assert range_q == {"lte": 500}

    def test_enrollment_both(self, service):
        entities = ExtractedEntities(enrollment_min=50, enrollment_max=200)
        query = service.build_query(entities)
        range_q = query["bool"]["filter"][0]["range"]["enrollment"]
        assert range_q == {"gte": 50, "lte": 200}


class TestBuildQueryCombined:
    def test_phase_and_condition(self, service):
        entities = ExtractedEntities(phase="PHASE3", condition="Diabetes")
        query = service.build_query(entities)
        assert "must" in query["bool"]
        assert "filter" in query["bool"]
        assert len(query["bool"]["must"]) == 1
        assert len(query["bool"]["filter"]) == 1

    def test_multiple_filters(self, service):
        entities = ExtractedEntities(
            phase="PHASE2",
            status="RECRUITING",
            sponsor="Pfizer",
            age_group="adult",
        )
        query = service.build_query(entities)
        assert len(query["bool"]["filter"]) == 4


# ---------- search tests ----------


def _mock_es_response(hits, total=None):
    if total is None:
        total = len(hits)
    return {
        "hits": {
            "total": {"value": total},
            "hits": [{"_source": h} for h in hits],
        }
    }


SAMPLE_HIT = {
    "nct_id": "NCT00000001",
    "brief_title": "Test Trial",
    "official_title": "Official Test Trial",
    "phase": "PHASE2",
    "overall_status": "RECRUITING",
    "enrollment": 150,
    "sponsors": [{"name": "Pfizer", "agency_class": "INDUSTRY", "lead_or_collaborator": "LEAD"}],
    "facilities": [
        {"name": "Hospital A", "city": "Boston", "state": "MA", "zip": "02115", "country": "United States", "status": "RECRUITING"},
        {"name": "Hospital B", "city": "NYC", "state": "NY", "zip": "10001", "country": "United States", "status": "RECRUITING"},
        {"name": "Hospital C", "city": "LA", "state": "CA", "zip": "90001", "country": "United States", "status": "RECRUITING"},
        {"name": "Hospital D", "city": "Chicago", "state": "IL", "zip": "60601", "country": "United States", "status": "RECRUITING"},
    ],
    "conditions": [{"name": "Asthma"}],
    "brief_summaries_description": "A test trial description.",
    "start_date": "2024-01-01",
    "completion_date": "2025-12-31",
    "age": [{"age_category": "adult"}, {"age_category": "older-adults"}],
    "gender": "All",
    "study_type": "Interventional",
    "source": "ClinicalTrials.gov",
}


class TestSearch:
    @pytest.mark.asyncio
    async def test_search_maps_results(self, service):
        service.es.search = MagicMock(return_value=_mock_es_response([SAMPLE_HIT]))
        entities = ExtractedEntities(condition="Asthma")

        results, total = await service.search(entities)

        assert total == 1
        assert len(results) == 1
        r = results[0]
        assert isinstance(r, TrialResult)
        assert r.nct_id == "NCT00000001"
        assert r.phase == "PHASE2"
        assert r.enrollment == 150

    @pytest.mark.asyncio
    async def test_search_sponsors_mapped(self, service):
        service.es.search = MagicMock(return_value=_mock_es_response([SAMPLE_HIT]))
        results, _ = await service.search(ExtractedEntities())

        r = results[0]
        assert len(r.sponsors) == 1
        assert isinstance(r.sponsors[0], Sponsor)
        assert r.sponsors[0].name == "Pfizer"
        assert r.sponsors[0].agency_class == "INDUSTRY"

    @pytest.mark.asyncio
    async def test_search_facilities_limited_to_3(self, service):
        service.es.search = MagicMock(return_value=_mock_es_response([SAMPLE_HIT]))
        results, _ = await service.search(ExtractedEntities())

        r = results[0]
        assert len(r.facilities) == 3
        assert isinstance(r.facilities[0], Facility)
        assert r.facilities[0].zip == "02115"
        assert r.facilities[0].status == "RECRUITING"

    @pytest.mark.asyncio
    async def test_search_age_mapped_to_age_category(self, service):
        service.es.search = MagicMock(return_value=_mock_es_response([SAMPLE_HIT]))
        results, _ = await service.search(ExtractedEntities())

        r = results[0]
        assert len(r.age) == 2
        assert isinstance(r.age[0], AgeCategory)
        assert r.age[0].age_category == "adult"
        assert r.age[1].age_category == "older-adults"

    @pytest.mark.asyncio
    async def test_search_conditions_as_dicts(self, service):
        service.es.search = MagicMock(return_value=_mock_es_response([SAMPLE_HIT]))
        results, _ = await service.search(ExtractedEntities())

        r = results[0]
        assert r.conditions == [{"name": "Asthma"}]

    @pytest.mark.asyncio
    async def test_search_extra_fields(self, service):
        service.es.search = MagicMock(return_value=_mock_es_response([SAMPLE_HIT]))
        results, _ = await service.search(ExtractedEntities())

        r = results[0]
        assert r.gender == "All"
        assert r.study_type == "Interventional"
        assert r.source == "ClinicalTrials.gov"
        assert r.completion_date == "2025-12-31"

    @pytest.mark.asyncio
    async def test_search_empty_response(self, service):
        service.es.search = MagicMock(return_value=_mock_es_response([]))
        results, total = await service.search(ExtractedEntities())

        assert results == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_search_pagination(self, service):
        service.es.search = MagicMock(return_value=_mock_es_response([], total=100))
        await service.search(ExtractedEntities(), page=3, page_size=20)

        call_body = service.es.search.call_args[1]["body"]
        assert call_body["from"] == 40
        assert call_body["size"] == 20

    @pytest.mark.asyncio
    async def test_search_partial_data(self, service):
        minimal_hit = {
            "nct_id": "NCT00000002",
            "brief_title": "Minimal Trial",
        }
        service.es.search = MagicMock(return_value=_mock_es_response([minimal_hit]))
        results, total = await service.search(ExtractedEntities())

        assert total == 1
        r = results[0]
        assert r.nct_id == "NCT00000002"
        assert r.sponsors == []
        assert r.facilities == []
        assert r.conditions == []
        assert r.age == []
        assert r.gender is None
        assert r.study_type is None
