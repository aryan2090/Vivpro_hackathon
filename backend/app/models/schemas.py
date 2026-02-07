from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .entities import ExtractedEntities


class Sponsor(BaseModel):
    name: str
    agency_class: Optional[str] = None
    lead_or_collaborator: Optional[str] = None


class Facility(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    status: Optional[str] = None


class AgeCategory(BaseModel):
    age_category: str


class TrialResult(BaseModel):
    nct_id: str
    brief_title: str
    official_title: Optional[str] = None
    phase: Optional[str] = None
    overall_status: Optional[str] = None
    enrollment: Optional[int] = None
    sponsors: List[Sponsor] = Field(default_factory=list)
    facilities: List[Facility] = Field(default_factory=list)
    conditions: List[Dict[str, str]] = Field(default_factory=list)
    brief_summaries_description: Optional[str] = None
    start_date: Optional[str] = None
    completion_date: Optional[str] = None
    age: List[AgeCategory] = Field(default_factory=list)
    gender: Optional[str] = None
    study_type: Optional[str] = None
    source: Optional[str] = None


class SearchResponse(BaseModel):
    query_interpretation: ExtractedEntities
    results: List[TrialResult]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    clarification: Optional[str] = None
    summary: Optional[str] = None


class SummaryResponse(BaseModel):
    summary: Optional[str] = None


class SuggestionResponse(BaseModel):
    suggestions: List[str]


class ErrorResponse(BaseModel):
    error: str
    detail: str
