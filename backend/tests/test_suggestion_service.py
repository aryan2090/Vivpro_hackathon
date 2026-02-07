"""Tests for the auto-suggestion service."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.suggestion import SuggestionService


@pytest.fixture
def service():
    with patch("app.services.suggestion.Elasticsearch"):
        with patch("app.services.suggestion.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                es_url="http://localhost:9200",
                es_index="clinical_trials",
            )
            svc = SuggestionService()
    return svc


def _mock_es_response(titles):
    return {
        "hits": {
            "total": {"value": len(titles)},
            "hits": [{"_source": {"brief_title": t}} for t in titles],
        }
    }


class TestGetSuggestionsValidation:
    @pytest.mark.asyncio
    async def test_empty_prefix_returns_empty(self, service):
        assert await service.get_suggestions("") == []

    @pytest.mark.asyncio
    async def test_single_char_returns_empty(self, service):
        assert await service.get_suggestions("a") == []

    @pytest.mark.asyncio
    async def test_whitespace_only_returns_empty(self, service):
        assert await service.get_suggestions("   ") == []

    @pytest.mark.asyncio
    async def test_none_prefix_returns_empty(self, service):
        assert await service.get_suggestions(None) == []


class TestGetSuggestionsPrimary:
    @pytest.mark.asyncio
    async def test_returns_titles_from_hits(self, service):
        service.es.search = MagicMock(
            return_value=_mock_es_response(
                ["Dose Escalation Study", "Dose Finding Trial"]
            )
        )
        result = await service.get_suggestions("Dose")
        assert result == ["Dose Escalation Study", "Dose Finding Trial"]

    @pytest.mark.asyncio
    async def test_deduplicates_case_insensitive(self, service):
        service.es.search = MagicMock(
            return_value=_mock_es_response(["Test Trial", "test trial", "TEST TRIAL"])
        )
        result = await service.get_suggestions("Test")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_respects_limit(self, service):
        titles = [f"Trial {i}" for i in range(20)]
        service.es.search = MagicMock(return_value=_mock_es_response(titles))
        result = await service.get_suggestions("Trial", limit=5)
        assert len(result) <= 5

    @pytest.mark.asyncio
    async def test_query_uses_bool_prefix(self, service):
        service.es.search = MagicMock(
            return_value=_mock_es_response(["Cancer Study"])
        )
        await service.get_suggestions("can")
        call_body = service.es.search.call_args[1]["body"]
        assert call_body["query"]["multi_match"]["type"] == "bool_prefix"


class TestGetSuggestionsFallback:
    @pytest.mark.asyncio
    async def test_fallback_when_primary_empty(self, service):
        empty = _mock_es_response([])
        fallback = _mock_es_response(["Cancer Treatment Study"])
        service.es.search = MagicMock(side_effect=[empty, fallback])
        result = await service.get_suggestions("Can")
        assert result == ["Cancer Treatment Study"]
        assert service.es.search.call_count == 2

    @pytest.mark.asyncio
    async def test_no_fallback_when_primary_has_results(self, service):
        primary = _mock_es_response(["Cancer Study"])
        service.es.search = MagicMock(return_value=primary)
        result = await service.get_suggestions("Can")
        assert service.es.search.call_count == 1


class TestGetConditionSuggestions:
    @pytest.mark.asyncio
    async def test_matching_prefix(self, service):
        result = await service.get_condition_suggestions("Brea")
        assert "Breast Cancer" in result

    @pytest.mark.asyncio
    async def test_case_insensitive(self, service):
        result = await service.get_condition_suggestions("dia")
        assert "Diabetes" in result

    @pytest.mark.asyncio
    async def test_no_match(self, service):
        result = await service.get_condition_suggestions("xyz")
        assert result == []

    @pytest.mark.asyncio
    async def test_short_prefix_returns_empty(self, service):
        result = await service.get_condition_suggestions("a")
        assert result == []
