import { useState, useCallback, useRef } from 'react';
import SearchBar from './components/SearchBar';
import QueryInterpretation from './components/QueryInterpretation';
import FilterPanel from './components/FilterPanel';
import ResultsList from './components/ResultsList';
import type { ResultsListHandle } from './components/ResultsList';
import AISummary from './components/AISummary';
import ClarificationBanner from './components/ClarificationBanner';
import EmptyState from './components/EmptyState';
import { searchTrials, searchWithFilters, fetchSummary } from './services/api';
import type { SearchResponse } from './types';
import type { FilterState } from './types/filters';
import { INITIAL_FILTER_STATE, entitiesToFilters, filtersToEntities } from './types/filters';

type AppState = 'idle' | 'loading' | 'results' | 'no-results' | 'error';
type SearchMode = 'nl' | 'filter';

export default function App() {
  const [appState, setAppState] = useState<AppState>('idle');
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [currentQuery, setCurrentQuery] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterState>(INITIAL_FILTER_STATE);
  const [isFilterPanelCollapsed, setIsFilterPanelCollapsed] = useState(true);
  const [searchMode, setSearchMode] = useState<SearchMode>('nl');
  const resultsListRef = useRef<ResultsListHandle>(null);

  const handleCitationClick = useCallback((index: number) => {
    resultsListRef.current?.scrollToResult(index);
  }, []);

  const handleSearch = useCallback(async (query: string, page: number = 1) => {
    setCurrentQuery(query);
    setSearchMode('nl');
    setAppState('loading');
    setErrorMessage(null);
    setSummary(null);
    try {
      const data = await searchTrials(query, page);
      setResponse(data);
      setAppState(data.results.length > 0 ? 'results' : 'no-results');

      // Sync filters from NL search interpretation and expand panel
      if (data.query_interpretation) {
        setFilters(entitiesToFilters(data.query_interpretation));
      }
      if (data.results.length > 0) {
        setIsFilterPanelCollapsed(false);
      }

      if (page === 1 && data.results.length > 0) {
        fetchSummary(query).then((s) => {
          setSummary(s);
        });
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'An error occurred');
      setAppState('error');
    }
  }, []);

  const handleFilterSearch = useCallback(
    async (currentFilters: FilterState, page: number = 1) => {
      setSearchMode('filter');
      setAppState('loading');
      setErrorMessage(null);
      setSummary(null);
      try {
        const entities = filtersToEntities(currentFilters);
        const data = await searchWithFilters(entities, page);
        setResponse(data);
        setAppState(data.results.length > 0 ? 'results' : 'no-results');
      } catch (err) {
        setErrorMessage(err instanceof Error ? err.message : 'An error occurred');
        setAppState('error');
      }
    },
    [],
  );

  const handleApplyFilters = useCallback(() => {
    handleFilterSearch(filters);
  }, [filters, handleFilterSearch]);

  const handleClearFilters = useCallback(() => {
    setFilters(INITIAL_FILTER_STATE);
  }, []);

  const handleChipRemove = useCallback(
    (type: string) => {
      const updated = { ...filters };
      switch (type) {
        case 'phase':
          updated.phase = null;
          break;
        case 'status':
          updated.status = null;
          break;
        case 'condition':
          updated.condition = '';
          break;
        case 'location':
          updated.location = { city: '', state: '', country: '' };
          break;
        case 'sponsor':
          updated.sponsor = '';
          break;
        case 'keyword':
          updated.keyword = '';
          break;
        case 'age_group':
          updated.ageGroups = [];
          break;
      }
      setFilters(updated);
      handleFilterSearch(updated);
    },
    [filters, handleFilterSearch],
  );

  const handlePageChange = useCallback(
    (page: number) => {
      if (searchMode === 'filter') {
        handleFilterSearch(filters, page);
      } else {
        handleSearch(currentQuery, page);
      }
      window.scrollTo({ top: 0, behavior: 'smooth' });
    },
    [currentQuery, filters, searchMode, handleSearch, handleFilterSearch],
  );

  const handleClarification = useCallback(
    (choice: string) => {
      handleSearch(choice);
    },
    [handleSearch],
  );

  return (
    <div className="min-h-screen bg-[var(--color-bg)] flex">
      <FilterPanel
        filters={filters}
        onFiltersChange={setFilters}
        onApply={handleApplyFilters}
        onClear={handleClearFilters}
        isCollapsed={isFilterPanelCollapsed}
        onToggleCollapse={() => setIsFilterPanelCollapsed((c) => !c)}
      />

      <div className="flex-1 min-w-0">
        <header
          className={`text-center px-4 transition-all duration-500 ease-in-out ${
            appState === 'idle' ? 'pt-24 pb-8' : 'pt-6 pb-4'
          }`}
        >
          {appState === 'idle' && (
            <>
              <h1 className="font-display text-4xl font-bold text-[var(--color-primary)] mb-2">
                Clinical Trials Search
              </h1>
              <p className="text-[var(--color-text-muted)] mb-8">
                Search clinical trials using natural language
              </p>
            </>
          )}
          <SearchBar onSearch={handleSearch} isLoading={appState === 'loading'} externalQuery={currentQuery} />
        </header>

        {response?.query_interpretation && appState !== 'idle' && appState !== 'loading' && (
          <QueryInterpretation
            entities={response.query_interpretation}
            onChipRemove={handleChipRemove}
          />
        )}

        {response?.clarification && appState === 'results' && (
          <ClarificationBanner question={response.clarification} onSelection={handleClarification} />
        )}

        <main className="max-w-3xl mx-auto px-4 pb-12">
          {appState === 'loading' && (
            <div className="mt-6 space-y-4">
              {Array.from({ length: 3 }, (_, i) => (
                <div
                  key={i}
                  className="bg-[var(--color-bg-card)] rounded-lg border border-gray-200 p-5 animate-shimmer"
                  style={{ animationDelay: `${i * 200}ms` }}
                >
                  <div className="h-5 bg-gray-200 rounded w-3/4 mb-3" />
                  <div className="h-3 bg-gray-200 rounded w-1/3 mb-4" />
                  <div className="h-3 bg-gray-200 rounded w-full mb-2" />
                  <div className="h-3 bg-gray-200 rounded w-2/3" />
                </div>
              ))}
            </div>
          )}

          {appState === 'results' && response && (
            <>
              {summary && response.page === 1 && (
                <AISummary
                  summary={summary}
                  onCitationClick={handleCitationClick}
                />
              )}
              <ResultsList
                ref={resultsListRef}
                results={response.results}
                total={response.total}
                page={response.page}
                pageSize={response.page_size}
                onPageChange={handlePageChange}
              />
            </>
          )}

          {appState === 'no-results' && <EmptyState type="no-results" onSuggestionClick={handleSearch} />}

          {appState === 'error' && (
            <EmptyState
              type="error"
              message={errorMessage ?? undefined}
              onRetry={() => handleSearch(currentQuery)}
            />
          )}
        </main>
      </div>
    </div>
  );
}
