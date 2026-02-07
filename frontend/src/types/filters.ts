import type { ExtractedEntities, LocationFilter, PhaseValue, StatusValue, AgeCategoryValue } from './index';

export interface FilterState {
  phase: PhaseValue | null;
  status: StatusValue | null;
  condition: string;
  location: LocationFilter;
  sponsor: string;
  keyword: string;
  ageGroups: AgeCategoryValue[];
  enrollmentMin: number | null;
  enrollmentMax: number | null;
}

export const INITIAL_FILTER_STATE: FilterState = {
  phase: null,
  status: null,
  condition: '',
  location: { city: '', state: '', country: '' },
  sponsor: '',
  keyword: '',
  ageGroups: [],
  enrollmentMin: null,
  enrollmentMax: null,
};

export function filtersToEntities(filters: FilterState): Partial<ExtractedEntities> {
  const entities: Partial<ExtractedEntities> = {};

  if (filters.phase) entities.phase = filters.phase;
  if (filters.status) entities.status = filters.status;
  if (filters.condition) entities.condition = filters.condition;
  if (filters.location.city || filters.location.state || filters.location.country) {
    entities.location = {
      ...(filters.location.city && { city: filters.location.city }),
      ...(filters.location.state && { state: filters.location.state }),
      ...(filters.location.country && { country: filters.location.country }),
    };
  }
  if (filters.sponsor) entities.sponsor = filters.sponsor;
  if (filters.keyword) entities.keyword = filters.keyword;
  if (filters.ageGroups.length > 0) entities.age_group = filters.ageGroups[0];
  if (filters.enrollmentMin !== null) entities.enrollment_min = filters.enrollmentMin;
  if (filters.enrollmentMax !== null) entities.enrollment_max = filters.enrollmentMax;

  return entities;
}

export function entitiesToFilters(entities: ExtractedEntities): FilterState {
  return {
    phase: (entities.phase as PhaseValue) || null,
    status: (entities.status as StatusValue) || null,
    condition: entities.condition || '',
    location: {
      city: entities.location?.city || '',
      state: entities.location?.state || '',
      country: entities.location?.country || '',
    },
    sponsor: entities.sponsor || '',
    keyword: entities.keyword || '',
    ageGroups: entities.age_group ? [entities.age_group as AgeCategoryValue] : [],
    enrollmentMin: entities.enrollment_min ?? null,
    enrollmentMax: entities.enrollment_max ?? null,
  };
}
