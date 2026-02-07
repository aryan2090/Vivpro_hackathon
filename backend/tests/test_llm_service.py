"""Tests for the LLM entity extraction service."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.entities import ExtractedEntities, LocationFilter
from app.services.llm_service import (
    SYSTEM_PROMPT,
    _parse_json_response,
    _validate_and_normalize,
    extract_entities,
)
from app.utils.synonyms import (
    VALID_AGE_GROUPS,
    VALID_PHASES,
    VALID_STATUSES,
)


# ─── Helpers ───


def _mock_response(json_data: dict) -> MagicMock:
    """Create a mock Anthropic Message with JSON content."""
    content_block = MagicMock()
    content_block.text = json.dumps(json_data)
    message = MagicMock()
    message.content = [content_block]
    return message


def _mock_response_raw(text: str) -> MagicMock:
    """Create a mock Anthropic Message with raw text content."""
    content_block = MagicMock()
    content_block.text = text
    message = MagicMock()
    message.content = [content_block]
    return message


# ─── Tests for _parse_json_response ───


class TestParseJsonResponse:
    def test_pure_json(self):
        data = _parse_json_response('{"phase": "PHASE3", "confidence": 0.9}')
        assert data["phase"] == "PHASE3"
        assert data["confidence"] == 0.9

    def test_json_in_code_fence(self):
        text = '```json\n{"phase": "PHASE2", "confidence": 0.8}\n```'
        data = _parse_json_response(text)
        assert data["phase"] == "PHASE2"

    def test_json_in_plain_code_fence(self):
        text = '```\n{"condition": "Asthma", "confidence": 0.85}\n```'
        data = _parse_json_response(text)
        assert data["condition"] == "Asthma"

    def test_json_with_surrounding_text(self):
        text = 'Here is the result:\n{"condition": "Diabetes", "confidence": 0.9}\nDone.'
        data = _parse_json_response(text)
        assert data["condition"] == "Diabetes"

    def test_nested_location_object(self):
        text = json.dumps({
            "condition": "Cancer",
            "location": {"country": "United States"},
            "confidence": 0.9,
        })
        data = _parse_json_response(text)
        assert data["location"]["country"] == "United States"

    def test_no_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            _parse_json_response("no json here at all")


# ─── Tests for _validate_and_normalize ───


class TestValidateAndNormalize:
    def test_valid_data_passes_through(self):
        data = {"phase": "PHASE3", "status": "RECRUITING", "confidence": 0.9}
        result = _validate_and_normalize(data)
        assert result["phase"] == "PHASE3"
        assert result["status"] == "RECRUITING"

    def test_invalid_phase_set_to_none(self):
        data = {"phase": "EARLY_PHASE1", "confidence": 0.9}
        result = _validate_and_normalize(data)
        assert result["phase"] is None

    def test_invalid_status_set_to_none(self):
        data = {"status": "OPEN", "confidence": 0.9}
        result = _validate_and_normalize(data)
        assert result["status"] is None

    def test_invalid_age_group_set_to_none(self):
        data = {"age_group": "senior", "confidence": 0.9}
        result = _validate_and_normalize(data)
        assert result["age_group"] is None

    def test_valid_combined_phase(self):
        data = {"phase": "PHASE1/PHASE2", "confidence": 0.9}
        result = _validate_and_normalize(data)
        assert result["phase"] == "PHASE1/PHASE2"

    def test_confidence_clamped_high(self):
        data = {"confidence": 1.5}
        result = _validate_and_normalize(data)
        assert result["confidence"] == 1.0

    def test_confidence_clamped_low(self):
        data = {"confidence": -0.5}
        result = _validate_and_normalize(data)
        assert result["confidence"] == 0.0

    def test_location_dict_converted(self):
        data = {
            "location": {"country": "United States", "state": None},
            "confidence": 0.9,
        }
        result = _validate_and_normalize(data)
        assert isinstance(result["location"], LocationFilter)
        assert result["location"].country == "United States"

    def test_empty_location_set_to_none(self):
        data = {
            "location": {"city": None, "state": None, "country": None},
            "confidence": 0.9,
        }
        result = _validate_and_normalize(data)
        assert result["location"] is None

    def test_enrollment_coerced_to_int(self):
        data = {"enrollment_min": "500", "confidence": 0.9}
        result = _validate_and_normalize(data)
        assert result["enrollment_min"] == 500
        assert isinstance(result["enrollment_min"], int)

    def test_enrollment_invalid_set_to_none(self):
        data = {"enrollment_min": "not_a_number", "confidence": 0.9}
        result = _validate_and_normalize(data)
        assert result["enrollment_min"] is None

    def test_all_valid_phases_accepted(self):
        for phase in VALID_PHASES:
            data = {"phase": phase, "confidence": 0.9}
            result = _validate_and_normalize(data)
            assert result["phase"] == phase

    def test_all_valid_statuses_accepted(self):
        for status in VALID_STATUSES:
            data = {"status": status, "confidence": 0.9}
            result = _validate_and_normalize(data)
            assert result["status"] == status

    def test_all_valid_age_groups_accepted(self):
        for age in VALID_AGE_GROUPS:
            data = {"age_group": age, "confidence": 0.9}
            result = _validate_and_normalize(data)
            assert result["age_group"] == age


# ─── Tests for extract_entities ───


class TestExtractEntities:
    @pytest.mark.asyncio
    async def test_empty_query(self):
        result = await extract_entities("")
        assert isinstance(result, ExtractedEntities)
        assert result.confidence < 0.5
        assert result.clarification is not None

    @pytest.mark.asyncio
    async def test_whitespace_query(self):
        result = await extract_entities("   ")
        assert result.confidence < 0.5
        assert result.clarification is not None

    @pytest.mark.asyncio
    @patch("app.services.llm_service.anthropic.AsyncAnthropic")
    async def test_simple_condition_extraction(self, mock_client_cls):
        mock_instance = AsyncMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.messages.create.return_value = _mock_response({
            "phase": None,
            "condition": "Lung Cancer",
            "status": "RECRUITING",
            "location": None,
            "sponsor": None,
            "keyword": None,
            "age_group": None,
            "enrollment_min": None,
            "enrollment_max": None,
            "confidence": 0.95,
            "clarification": None,
        })

        result = await extract_entities("recruiting lung cancer trials")
        assert result.condition == "Lung Cancer"
        assert result.status == "RECRUITING"
        assert result.confidence == 0.95
        assert result.clarification is None

    @pytest.mark.asyncio
    @patch("app.services.llm_service.anthropic.AsyncAnthropic")
    async def test_complex_multi_field(self, mock_client_cls):
        mock_instance = AsyncMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.messages.create.return_value = _mock_response({
            "phase": "PHASE3",
            "condition": "Lung Cancer",
            "status": None,
            "location": {"country": "United States"},
            "sponsor": None,
            "keyword": None,
            "age_group": "adult",
            "enrollment_min": None,
            "enrollment_max": None,
            "confidence": 0.95,
            "clarification": None,
        })

        result = await extract_entities("Phase 3 lung cancer trials in the USA for adults")
        assert result.phase == "PHASE3"
        assert result.condition == "Lung Cancer"
        assert result.location is not None
        assert result.location.country == "United States"
        assert result.age_group == "adult"

    @pytest.mark.asyncio
    @patch("app.services.llm_service.anthropic.AsyncAnthropic")
    async def test_combined_phase(self, mock_client_cls):
        mock_instance = AsyncMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.messages.create.return_value = _mock_response({
            "phase": "PHASE1/PHASE2",
            "condition": None,
            "status": None,
            "location": None,
            "sponsor": None,
            "keyword": None,
            "age_group": None,
            "enrollment_min": None,
            "enrollment_max": None,
            "confidence": 0.9,
            "clarification": None,
        })

        result = await extract_entities("phase 1/2 studies")
        assert result.phase == "PHASE1/PHASE2"

    @pytest.mark.asyncio
    @patch("app.services.llm_service.anthropic.AsyncAnthropic")
    async def test_keyword_extraction(self, mock_client_cls):
        mock_instance = AsyncMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.messages.create.return_value = _mock_response({
            "phase": "PHASE2",
            "condition": "Breast Cancer",
            "status": None,
            "location": None,
            "sponsor": None,
            "keyword": "BRCA1",
            "age_group": None,
            "enrollment_min": None,
            "enrollment_max": None,
            "confidence": 0.95,
            "clarification": None,
        })

        result = await extract_entities(
            "Phase 2 trials for Breast Cancer associated with BRCA1"
        )
        assert result.phase == "PHASE2"
        assert result.condition == "Breast Cancer"
        assert result.keyword == "BRCA1"

    @pytest.mark.asyncio
    @patch("app.services.llm_service.anthropic.AsyncAnthropic")
    async def test_pediatric_synonym(self, mock_client_cls):
        mock_instance = AsyncMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.messages.create.return_value = _mock_response({
            "phase": None,
            "condition": "Asthma",
            "status": None,
            "location": None,
            "sponsor": None,
            "keyword": None,
            "age_group": "child",
            "enrollment_min": None,
            "enrollment_max": None,
            "confidence": 0.9,
            "clarification": None,
        })

        result = await extract_entities("pediatric asthma trials")
        assert result.age_group == "child"
        assert result.condition == "Asthma"

    @pytest.mark.asyncio
    @patch("app.services.llm_service.anthropic.AsyncAnthropic")
    async def test_sponsor_extraction(self, mock_client_cls):
        mock_instance = AsyncMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.messages.create.return_value = _mock_response({
            "phase": None,
            "condition": None,
            "status": None,
            "location": None,
            "sponsor": "Pfizer",
            "keyword": None,
            "age_group": None,
            "enrollment_min": None,
            "enrollment_max": None,
            "confidence": 0.85,
            "clarification": None,
        })

        result = await extract_entities("Pfizer sponsored trials")
        assert result.sponsor == "Pfizer"

    @pytest.mark.asyncio
    @patch("app.services.llm_service.anthropic.AsyncAnthropic")
    async def test_json_decode_error_fallback(self, mock_client_cls):
        mock_instance = AsyncMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.messages.create.return_value = _mock_response_raw(
            "I cannot understand this query"
        )

        result = await extract_entities("some query")
        assert result.confidence == 0.3
        assert result.clarification is not None

    @pytest.mark.asyncio
    @patch("app.services.llm_service.anthropic.AsyncAnthropic")
    async def test_api_error_fallback(self, mock_client_cls):
        import anthropic as anthropic_mod

        mock_instance = AsyncMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.messages.create.side_effect = anthropic_mod.APIError(
            message="rate limited",
            request=MagicMock(),
            body=None,
        )

        result = await extract_entities("diabetes trials")
        assert result.confidence == 0.0
        assert "unavailable" in result.clarification.lower()

    @pytest.mark.asyncio
    @patch("app.services.llm_service.anthropic.AsyncAnthropic")
    async def test_unexpected_error_fallback(self, mock_client_cls):
        mock_instance = AsyncMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.messages.create.side_effect = RuntimeError("unexpected")

        result = await extract_entities("diabetes trials")
        assert result.confidence == 0.0
        assert result.clarification is not None

    @pytest.mark.asyncio
    @patch("app.services.llm_service.anthropic.AsyncAnthropic")
    async def test_markdown_wrapped_json(self, mock_client_cls):
        mock_instance = AsyncMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.messages.create.return_value = _mock_response_raw(
            '```json\n{"condition": "Asthma", "confidence": 0.85}\n```'
        )

        result = await extract_entities("asthma studies")
        assert result.condition == "Asthma"
        assert result.confidence == 0.85

    @pytest.mark.asyncio
    @patch("app.services.llm_service.anthropic.AsyncAnthropic")
    async def test_invalid_phase_in_response_normalized(self, mock_client_cls):
        mock_instance = AsyncMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.messages.create.return_value = _mock_response({
            "phase": "EARLY_PHASE1",
            "condition": "Cancer",
            "confidence": 0.9,
        })

        result = await extract_entities("early phase cancer trials")
        assert result.phase is None
        assert result.condition == "Cancer"

    @pytest.mark.asyncio
    @patch("app.services.llm_service.anthropic.AsyncAnthropic")
    async def test_enrollment_extraction(self, mock_client_cls):
        mock_instance = AsyncMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.messages.create.return_value = _mock_response({
            "phase": None,
            "condition": None,
            "status": None,
            "location": None,
            "sponsor": None,
            "keyword": None,
            "age_group": None,
            "enrollment_min": 500,
            "enrollment_max": None,
            "confidence": 0.8,
            "clarification": None,
        })

        result = await extract_entities("large clinical trials")
        assert result.enrollment_min == 500


# ─── Tests for system prompt correctness ───


class TestSystemPrompt:
    def test_contains_all_valid_phases(self):
        for phase in VALID_PHASES:
            assert phase in SYSTEM_PROMPT, f"Phase {phase} missing from prompt"

    def test_contains_all_valid_statuses(self):
        for status in VALID_STATUSES:
            assert status in SYSTEM_PROMPT, f"Status {status} missing from prompt"

    def test_contains_all_valid_age_groups(self):
        for age in VALID_AGE_GROUPS:
            assert age in SYSTEM_PROMPT, f"Age group {age} missing from prompt"

    def test_contains_json_schema_fields(self):
        for field in [
            '"phase"', '"condition"', '"status"', '"location"',
            '"sponsor"', '"keyword"', '"age_group"',
            '"enrollment_min"', '"enrollment_max"',
            '"confidence"', '"clarification"',
        ]:
            assert field in SYSTEM_PROMPT, f"Field {field} missing from prompt"

    def test_contains_synonym_examples(self):
        assert '"open"' in SYSTEM_PROMPT
        assert '"pediatric"' in SYSTEM_PROMPT
        assert '"phase i"' in SYSTEM_PROMPT
        assert '"paused"' in SYSTEM_PROMPT
        assert '"usa"' in SYSTEM_PROMPT
