import type { SearchResponse, SuggestionResponse, ExtractedEntities } from '../types';

const API_BASE = '/api';

export async function searchTrials(
  query: string,
  page: number = 1,
  pageSize: number = 10
): Promise<SearchResponse> {
  const response = await fetch(
    `${API_BASE}/search/${encodeURIComponent(query)}?page=${page}&page_size=${pageSize}`
  );
  if (!response.ok) {
    throw new Error(`Search failed: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchSummary(query: string): Promise<string | null> {
  try {
    const response = await fetch(
      `${API_BASE}/summary/${encodeURIComponent(query)}`
    );
    if (!response.ok) return null;
    const data = await response.json();
    return data.summary ?? null;
  } catch {
    return null;
  }
}

export async function searchWithFilters(
  filters: Partial<ExtractedEntities>,
  page: number = 1,
  pageSize: number = 10,
): Promise<SearchResponse> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });

  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === null || value === '') continue;
    if (typeof value === 'object') {
      params.set(key, JSON.stringify(value));
    } else {
      params.set(key, String(value));
    }
  }

  const response = await fetch(`${API_BASE}/filter?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Filter search failed: ${response.statusText}`);
  }
  return response.json();
}

export async function getSuggestions(prefix: string): Promise<string[]> {
  if (prefix.length < 2) return [];
  const response = await fetch(
    `${API_BASE}/suggest?q=${encodeURIComponent(prefix)}`
  );
  if (!response.ok) return [];
  const data: SuggestionResponse = await response.json();
  return data.suggestions;
}
