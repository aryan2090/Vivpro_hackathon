"""Tests for FastAPI search and suggestion endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.entities import ExtractedEntities
from app.models.schemas import TrialResult


@pytest.fixture
def client():
    return TestClient(app)


SAMPLE_RESULT = TrialResult(
    nct_id="NCT00000001",
    brief_title="Test Trial for Lung Cancer",
    phase="PHASE3",
    overall_status="RECRUITING",
    enrollment=200,
)


# ---------- Health endpoint ----------


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_contains_es_url(self, client):
        response = client.get("/health")
        data = response.json()
        assert "es_url" in data


# ---------- CORS ----------


class TestCORS:
    def test_cors_headers_for_allowed_origin(self, client):
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_cors_blocked_for_disallowed_origin(self, client):
        response = client.options(
            "/health",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") != "http://evil.com"


# ---------- Search endpoint ----------


class TestSearchEndpoint:
    @patch("app.routers.search.es_service")
    @patch("app.routers.search.extract_entities", new_callable=AsyncMock)
    def test_search_returns_results(self, mock_extract, mock_es, client):
        entities = ExtractedEntities(condition="lung cancer", confidence=0.9)
        mock_extract.return_value = entities
        mock_es.search = AsyncMock(return_value=([SAMPLE_RESULT], 1))

        response = client.get("/api/search/lung cancer")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert len(data["results"]) == 1
        assert data["results"][0]["nct_id"] == "NCT00000001"
        assert data["query_interpretation"]["condition"] == "lung cancer"

    @patch("app.routers.search.es_service")
    @patch("app.routers.search.extract_entities", new_callable=AsyncMock)
    def test_search_pagination_params(self, mock_extract, mock_es, client):
        entities = ExtractedEntities()
        mock_extract.return_value = entities
        mock_es.search = AsyncMock(return_value=([], 0))

        response = client.get("/api/search/test?page=2&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 5
        mock_es.search.assert_called_once_with(entities, 2, 5)

    def test_search_invalid_page_returns_422(self, client):
        response = client.get("/api/search/test?page=0")
        assert response.status_code == 422

    def test_search_invalid_page_size_returns_422(self, client):
        response = client.get("/api/search/test?page_size=101")
        assert response.status_code == 422

    @patch("app.routers.search.es_service")
    @patch("app.routers.search.extract_entities", new_callable=AsyncMock)
    def test_search_includes_clarification(self, mock_extract, mock_es, client):
        entities = ExtractedEntities(
            confidence=0.5,
            clarification="Did you mean breast cancer or lung cancer?",
        )
        mock_extract.return_value = entities
        mock_es.search = AsyncMock(return_value=([], 0))

        response = client.get("/api/search/cancer")
        assert response.status_code == 200
        data = response.json()
        assert data["clarification"] == "Did you mean breast cancer or lung cancer?"

    @patch("app.routers.search.extract_entities", new_callable=AsyncMock)
    def test_search_service_error_returns_500(self, mock_extract, client):
        mock_extract.side_effect = RuntimeError("LLM unavailable")

        response = client.get("/api/search/test")
        assert response.status_code == 500


# ---------- Suggest endpoint ----------


class TestSuggestEndpoint:
    @patch("app.routers.search.suggestion_service")
    def test_suggest_returns_suggestions(self, mock_svc, client):
        mock_svc.get_suggestions = AsyncMock(
            return_value=["Cancer Treatment A", "Cancer Study B"]
        )

        response = client.get("/api/suggest?q=can")
        assert response.status_code == 200
        data = response.json()
        assert len(data["suggestions"]) == 2
        assert "Cancer Treatment A" in data["suggestions"]

    def test_suggest_requires_min_length_2(self, client):
        response = client.get("/api/suggest?q=a")
        assert response.status_code == 422

    def test_suggest_missing_q_returns_422(self, client):
        response = client.get("/api/suggest")
        assert response.status_code == 422

    @patch("app.routers.search.suggestion_service")
    def test_suggest_service_error_returns_500(self, mock_svc, client):
        mock_svc.get_suggestions = AsyncMock(side_effect=RuntimeError("ES down"))

        response = client.get("/api/suggest?q=test")
        assert response.status_code == 500


# ---------- OpenAPI docs ----------


class TestOpenAPIDocs:
    def test_docs_accessible(self, client):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_accessible(self, client):
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema_has_metadata(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "Clinical Trials Search API"
        assert schema["info"]["version"] == "1.0.0"
        assert schema["info"]["description"] == "Natural language search for clinical trials"

    def test_openapi_schema_has_search_tag(self, client):
        response = client.get("/openapi.json")
        schema = response.json()
        tag_names = [t["name"] for t in schema.get("tags", [])]
        assert "search" in tag_names
