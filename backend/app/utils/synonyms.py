"""Domain synonym mappings for clinical trials entity extraction.

These dictionaries are used to:
1. Generate the synonym section of the LLM system prompt
2. Validate/normalize LLM output server-side
"""

STATUS_SYNONYMS: dict[str, str] = {
    "open": "RECRUITING",
    "recruiting": "RECRUITING",
    "active": "RECRUITING",
    "enrolling": "RECRUITING",
    "closed": "COMPLETED",
    "finished": "COMPLETED",
    "completed": "COMPLETED",
    "done": "COMPLETED",
    "upcoming": "NOT_YET_RECRUITING",
    "not started": "NOT_YET_RECRUITING",
    "planned": "NOT_YET_RECRUITING",
    "running": "RECRUITING",
    "ongoing": "ACTIVE_NOT_RECRUITING",
    "paused": "SUSPENDED",
    "halted": "SUSPENDED",
    "stopped": "TERMINATED",
    "ended early": "TERMINATED",
}

PHASE_MAPPINGS: dict[str, str] = {
    "phase 1": "PHASE1",
    "phase i": "PHASE1",
    "p1": "PHASE1",
    "phase 1/2": "PHASE1/PHASE2",
    "phase i/ii": "PHASE1/PHASE2",
    "phase 2": "PHASE2",
    "phase ii": "PHASE2",
    "p2": "PHASE2",
    "phase 2/3": "PHASE2/PHASE3",
    "phase ii/iii": "PHASE2/PHASE3",
    "phase 3": "PHASE3",
    "phase iii": "PHASE3",
    "p3": "PHASE3",
    "phase 4": "PHASE4",
    "phase iv": "PHASE4",
    "p4": "PHASE4",
}

AGE_GROUP_SYNONYMS: dict[str, str] = {
    "pediatric": "child",
    "children": "child",
    "kids": "child",
    "elderly": "older-adults",
    "seniors": "older-adults",
    "geriatric": "older-adults",
    "teens": "adolescent",
    "teenagers": "adolescent",
    "babies": "infant",
    "neonatal": "infant",
    "newborn": "infant",
}

LOCATION_NORMALIZATIONS: dict[str, str] = {
    "usa": "United States",
    "us": "United States",
    "united states": "United States",
    "america": "United States",
    "uk": "United Kingdom",
    "britain": "United Kingdom",
    "england": "United Kingdom",
}

VALID_PHASES = frozenset([
    "NA", "PHASE1", "PHASE1/PHASE2", "PHASE2",
    "PHASE2/PHASE3", "PHASE3", "PHASE4", "Phase NA",
])

VALID_STATUSES = frozenset([
    "ACTIVE_NOT_RECRUITING", "COMPLETED", "NOT_YET_RECRUITING",
    "RECRUITING", "SUSPENDED", "TERMINATED", "UNKNOWN", "WITHDRAWN",
])

VALID_AGE_GROUPS = frozenset([
    "adult", "older-adults", "child", "adolescent", "infant", "toddler",
])
