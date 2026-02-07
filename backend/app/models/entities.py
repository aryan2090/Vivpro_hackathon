from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PhaseEnum(str, Enum):
    NA = "NA"
    PHASE1 = "PHASE1"
    PHASE1_PHASE2 = "PHASE1/PHASE2"
    PHASE2 = "PHASE2"
    PHASE2_PHASE3 = "PHASE2/PHASE3"
    PHASE3 = "PHASE3"
    PHASE4 = "PHASE4"
    PHASE_NA = "Phase NA"


class StatusEnum(str, Enum):
    ACTIVE_NOT_RECRUITING = "ACTIVE_NOT_RECRUITING"
    COMPLETED = "COMPLETED"
    NOT_YET_RECRUITING = "NOT_YET_RECRUITING"
    RECRUITING = "RECRUITING"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"
    UNKNOWN = "UNKNOWN"
    WITHDRAWN = "WITHDRAWN"


class AgeCategoryEnum(str, Enum):
    ADULT = "adult"
    OLDER_ADULTS = "older-adults"
    CHILD = "child"
    ADOLESCENT = "adolescent"
    INFANT = "infant"
    TODDLER = "toddler"


class LocationFilter(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None


class ExtractedEntities(BaseModel):
    phase: Optional[str] = Field(None, description="Clinical trial phase")
    condition: Optional[str] = Field(None, description="Medical condition or disease")
    status: Optional[str] = Field(None, description="Trial recruitment status")
    location: Optional[LocationFilter] = Field(None, description="Geographic location filter")
    sponsor: Optional[str] = Field(None, description="Sponsoring organization")
    keyword: Optional[str] = Field(None, description="Gene, drug, or specific term")
    age_group: Optional[str] = Field(None, description="Target age group")
    enrollment_min: Optional[int] = Field(None, description="Minimum enrollment", ge=0)
    enrollment_max: Optional[int] = Field(None, description="Maximum enrollment", ge=0)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    clarification: Optional[str] = Field(None, description="Follow-up question for ambiguous queries")
