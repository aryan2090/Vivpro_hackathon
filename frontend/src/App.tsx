import { useState } from 'react';
import SearchBar from './components/SearchBar';
import QueryInterpretation from './components/QueryInterpretation';
import ResultCard from './components/ResultCard';
import { searchTrials } from './services/api';
import type { ExtractedEntities, TrialResult } from './types';

function App() {
  const [results, setResults] = useState<TrialResult[]>([]);
  const [queryInterpretation, setQueryInterpretation] = useState<ExtractedEntities | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [clarification, setClarification] = useState<string | null>(null);
  const [currentQuery, setCurrentQuery] = useState('');
  const [hasSearched, setHasSearched] = useState(false);

  async function handleSearch(query: string, searchPage: number = 1) {
    setIsLoading(true);
    setError(null);
    setCurrentQuery(query);
    try {
      const data = await searchTrials(query, searchPage, pageSize);
      setResults(data.results);
      setQueryInterpretation(data.query_interpretation);
      setTotal(data.total);
      setPage(data.page);
      setClarification(data.clarification || null);
      setHasSearched(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setResults([]);
      setQueryInterpretation(null);
    } finally {
      setIsLoading(false);
    }
  }

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      <header className="pt-12 pb-8 px-4 text-center">
        <h1 className="font-display text-4xl font-bold text-[var(--color-primary)] mb-2">
          Clinical Trials Search
        </h1>
        <p className="text-[var(--color-text-muted)] mb-8">
          Search clinical trials using natural language
        </p>
        <SearchBar onSearch={handleSearch} isLoading={isLoading} />
      </header>

      <main className="max-w-3xl mx-auto px-4 pb-12">
        {queryInterpretation && <QueryInterpretation entities={queryInterpretation} />}

        {clarification && (
          <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
            {clarification}
          </div>
        )}

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {error}
          </div>
        )}

        {hasSearched && !error && (
          <p className="mt-6 mb-4 text-sm text-[var(--color-text-muted)]">
            {total} result{total !== 1 ? 's' : ''} found
          </p>
        )}

        <div className="space-y-4">
          {results.map((trial, i) => (
            <ResultCard key={trial.nct_id} trial={trial} index={i} />
          ))}
        </div>

        {totalPages > 1 && (
          <div className="flex justify-center items-center gap-4 mt-8">
            <button
              onClick={() => handleSearch(currentQuery, page - 1)}
              disabled={page <= 1 || isLoading}
              className="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="text-sm text-[var(--color-text-muted)]">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => handleSearch(currentQuery, page + 1)}
              disabled={page >= totalPages || isLoading}
              className="px-4 py-2 rounded-lg border border-gray-300 text-sm hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
