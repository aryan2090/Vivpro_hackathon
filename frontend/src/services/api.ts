import type { SearchResponse, SuggestionResponse } from '../types';

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

export async function getSuggestions(prefix: string): Promise<string[]> {
  if (prefix.length < 2) return [];
  const response = await fetch(
    `${API_BASE}/suggest?q=${encodeURIComponent(prefix)}`
  );
  if (!response.ok) return [];
  const data: SuggestionResponse = await response.json();
  return data.suggestions;
}
