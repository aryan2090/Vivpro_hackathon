export interface LocationFilter {
  city?: string;
  state?: string;
  country?: string;
}

export interface ExtractedEntities {
  phase?: string;
  condition?: string;
  status?: string;
  location?: LocationFilter;
  sponsor?: string;
  keyword?: string;
  age_group?: string;
  enrollment_min?: number;
  enrollment_max?: number;
  confidence: number;
  clarification?: string;
}

export interface Sponsor {
  name: string;
  agency_class?: string;
  lead_or_collaborator?: string;
}

export interface Facility {
  name?: string;
  city?: string;
  state?: string;
  zip?: string;
  country?: string;
  status?: string;
}

export interface AgeCategory {
  age_category: string;
}

export interface TrialResult {
  nct_id: string;
  brief_title: string;
  official_title?: string;
  phase?: string;
  overall_status?: string;
  enrollment?: number;
  sponsors: Sponsor[];
  facilities: Facility[];
  conditions: Record<string, string>[];
  brief_summaries_description?: string;
  start_date?: string;
  completion_date?: string;
  age: AgeCategory[];
  gender?: string;
  study_type?: string;
  source?: string;
}

export interface SearchResponse {
  query_interpretation: ExtractedEntities;
  results: TrialResult[];
  total: number;
  page: number;
  page_size: number;
  clarification?: string;
}

export interface SuggestionResponse {
  suggestions: string[];
}

export interface ErrorResponse {
  error: string;
  detail: string;
}

export const PHASE_VALUES = [
  "NA",
  "PHASE1",
  "PHASE1/PHASE2",
  "PHASE2",
  "PHASE2/PHASE3",
  "PHASE3",
  "PHASE4",
  "Phase NA",
] as const;

export type PhaseValue = (typeof PHASE_VALUES)[number];

export const STATUS_VALUES = [
  "ACTIVE_NOT_RECRUITING",
  "COMPLETED",
  "NOT_YET_RECRUITING",
  "RECRUITING",
  "SUSPENDED",
  "TERMINATED",
  "UNKNOWN",
  "WITHDRAWN",
] as const;

export type StatusValue = (typeof STATUS_VALUES)[number];

export const AGE_CATEGORIES = [
  "adult",
  "older-adults",
  "child",
  "adolescent",
  "infant",
  "toddler",
] as const;

export type AgeCategoryValue = (typeof AGE_CATEGORIES)[number];

export const STATUS_COLORS: Record<StatusValue, string> = {
  RECRUITING: "emerald",
  NOT_YET_RECRUITING: "amber",
  ACTIVE_NOT_RECRUITING: "blue",
  COMPLETED: "gray",
  TERMINATED: "red",
  WITHDRAWN: "red",
  SUSPENDED: "orange",
  UNKNOWN: "slate",
};
