import pytest
from pydantic import ValidationError

from app.models.entities import (
    AgeCategoryEnum,
    ExtractedEntities,
    LocationFilter,
    PhaseEnum,
    StatusEnum,
)
from app.models.schemas import (
    AgeCategory,
    ErrorResponse,
    Facility,
    SearchResponse,
    Sponsor,
    SuggestionResponse,
    TrialResult,
)


class TestPhaseEnum:
    def test_all_data_values_present(self, clinical_trials_data):
        data_phases = {r["phase"] for r in clinical_trials_data if r.get("phase")}
        enum_values = {e.value for e in PhaseEnum}
        missing = data_phases - enum_values
        assert not missing, f"PhaseEnum missing: {missing}"

    def test_string_serialization(self):
        assert PhaseEnum.PHASE2.value == "PHASE2"
        assert PhaseEnum.PHASE1_PHASE2.value == "PHASE1/PHASE2"
        assert PhaseEnum.PHASE_NA.value == "Phase NA"

    def test_from_value(self):
        assert PhaseEnum("PHASE3") == PhaseEnum.PHASE3
        assert PhaseEnum("PHASE2/PHASE3") == PhaseEnum.PHASE2_PHASE3


class TestStatusEnum:
    def test_all_data_values_present(self, clinical_trials_data):
        data_statuses = {r["overall_status"] for r in clinical_trials_data if r.get("overall_status")}
        enum_values = {e.value for e in StatusEnum}
        missing = data_statuses - enum_values
        assert not missing, f"StatusEnum missing: {missing}"

    def test_unknown_exists(self):
        assert StatusEnum.UNKNOWN.value == "UNKNOWN"


class TestAgeCategoryEnum:
    def test_all_data_values_present(self, clinical_trials_data):
        data_ages = set()
        for r in clinical_trials_data:
            for a in r.get("age", []):
                if a.get("age_category"):
                    data_ages.add(a["age_category"])
        enum_values = {e.value for e in AgeCategoryEnum}
        missing = data_ages - enum_values
        assert not missing, f"AgeCategoryEnum missing: {missing}"


class TestLocationFilter:
    def test_empty(self):
        loc = LocationFilter()
        assert loc.city is None
        assert loc.state is None
        assert loc.country is None

    def test_partial(self):
        loc = LocationFilter(country="United States")
        assert loc.country == "United States"
        assert loc.city is None

    def test_full(self):
        loc = LocationFilter(city="Boston", state="Massachusetts", country="United States")
        assert loc.city == "Boston"


class TestExtractedEntities:
    def test_defaults(self):
        e = ExtractedEntities()
        assert e.confidence == 0.8
        assert e.phase is None
        assert e.condition is None

    def test_confidence_valid_range(self):
        assert ExtractedEntities(confidence=0.0).confidence == 0.0
        assert ExtractedEntities(confidence=1.0).confidence == 1.0

    def test_confidence_too_low(self):
        with pytest.raises(ValidationError):
            ExtractedEntities(confidence=-0.1)

    def test_confidence_too_high(self):
        with pytest.raises(ValidationError):
            ExtractedEntities(confidence=1.5)

    def test_enrollment_min_negative(self):
        with pytest.raises(ValidationError):
            ExtractedEntities(enrollment_min=-1)

    def test_full_extraction(self):
        e = ExtractedEntities(
            phase="PHASE3",
            condition="Lung Cancer",
            status="RECRUITING",
            location=LocationFilter(country="United States"),
            sponsor="AstraZeneca",
            keyword="EGFR",
            age_group="adult",
            enrollment_min=100,
            enrollment_max=500,
            confidence=0.95,
        )
        assert e.phase == "PHASE3"
        assert e.location.country == "United States"

    def test_round_trip(self):
        e = ExtractedEntities(condition="Asthma", confidence=0.9)
        restored = ExtractedEntities(**e.model_dump())
        assert restored == e


class TestSponsor:
    def test_from_real_data(self, sample_trial):
        for s_data in sample_trial["sponsors"]:
            sponsor = Sponsor(**s_data)
            assert sponsor.name

    def test_minimal(self):
        s = Sponsor(name="Test Org")
        assert s.agency_class is None

    def test_name_required(self):
        with pytest.raises(ValidationError):
            Sponsor()


class TestFacility:
    def test_from_real_data(self, sample_trial):
        for f_data in sample_trial["facilities"]:
            facility = Facility(**f_data)
            assert facility.country is not None

    def test_includes_zip_and_status(self):
        f = Facility(name="Site", zip="02115", status="RECRUITING")
        assert f.zip == "02115"
        assert f.status == "RECRUITING"

    def test_all_optional(self):
        f = Facility()
        assert f.name is None


class TestTrialResult:
    def test_minimal(self, sample_trial_minimal):
        trial = TrialResult(**sample_trial_minimal)
        assert trial.nct_id == "NCT00000001"
        assert trial.sponsors == []
        assert trial.age == []

    def test_nct_id_required(self):
        with pytest.raises(ValidationError):
            TrialResult(brief_title="Missing NCT ID")

    def test_brief_title_required(self):
        with pytest.raises(ValidationError):
            TrialResult(nct_id="NCT00000001")

    def test_from_real_data(self, sample_trial):
        trial = TrialResult(
            nct_id=sample_trial["nct_id"],
            brief_title=sample_trial["brief_title"],
            official_title=sample_trial.get("official_title"),
            phase=sample_trial.get("phase"),
            overall_status=sample_trial.get("overall_status"),
            enrollment=sample_trial.get("enrollment_numeric"),
            sponsors=[Sponsor(**s) for s in sample_trial.get("sponsors", [])],
            facilities=[Facility(**f) for f in sample_trial.get("facilities", [])],
            conditions=sample_trial.get("conditions", []),
            brief_summaries_description=sample_trial.get("brief_summaries_description"),
            start_date=sample_trial.get("start_date"),
            completion_date=sample_trial.get("completion_date"),
            age=[AgeCategory(**a) for a in sample_trial.get("age", [])],
            gender=sample_trial.get("gender"),
            study_type=sample_trial.get("study_type"),
            source=sample_trial.get("source"),
        )
        assert trial.nct_id == sample_trial["nct_id"]
        assert len(trial.sponsors) == len(sample_trial["sponsors"])

    def test_round_trip(self):
        trial = TrialResult(
            nct_id="NCT12345678",
            brief_title="Test",
            sponsors=[Sponsor(name="Org")],
            age=[AgeCategory(age_category="adult")],
        )
        restored = TrialResult(**trial.model_dump())
        assert restored == trial


class TestSearchResponse:
    def test_full_response(self):
        resp = SearchResponse(
            query_interpretation=ExtractedEntities(condition="Asthma", confidence=0.95),
            results=[TrialResult(nct_id="NCT00000001", brief_title="Trial 1")],
            total=42,
            page=1,
            page_size=10,
        )
        assert resp.total == 42
        assert len(resp.results) == 1

    def test_with_clarification(self):
        resp = SearchResponse(
            query_interpretation=ExtractedEntities(confidence=0.4),
            results=[],
            total=0,
            page=1,
            page_size=10,
            clarification="Did you mean Lung Cancer or Lung Disease?",
        )
        assert resp.clarification is not None

    def test_page_must_be_positive(self):
        with pytest.raises(ValidationError):
            SearchResponse(
                query_interpretation=ExtractedEntities(),
                results=[],
                total=0,
                page=0,
                page_size=10,
            )


class TestSuggestionResponse:
    def test_basic(self):
        resp = SuggestionResponse(suggestions=["Asthma", "Asthma, Exercise-Induced"])
        assert len(resp.suggestions) == 2

    def test_empty(self):
        resp = SuggestionResponse(suggestions=[])
        assert resp.suggestions == []


class TestErrorResponse:
    def test_basic(self):
        err = ErrorResponse(error="NotFound", detail="No trials match")
        assert err.error == "NotFound"

    def test_both_required(self):
        with pytest.raises(ValidationError):
            ErrorResponse(error="Oops")
