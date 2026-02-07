import { useState, useRef, useEffect } from 'react';
import { getSuggestions } from '../services/api';

const EXAMPLE_QUERIES = [
  'Phase 3 lung cancer trials',
  'Recruiting diabetes studies in California',
  'BRCA1 breast cancer research',
  'Open melanoma immunotherapy trials',
];

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
  externalQuery?: string;
}

export default function SearchBar({ onSearch, isLoading, externalQuery }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const submittedRef = useRef(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      setPlaceholderIndex((i) => (i + 1) % EXAMPLE_QUERIES.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (externalQuery !== undefined && externalQuery !== query) {
      setQuery(externalQuery);
    }
  }, [externalQuery]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  function handleInputChange(value: string) {
    setQuery(value);
    setSelectedIndex(-1);
    submittedRef.current = false;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      const results = await getSuggestions(value.trim());
      if (submittedRef.current) return;
      setSuggestions(results);
      setShowSuggestions(results.length > 0);
    }, 300);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    submittedRef.current = true;
    setSuggestions([]);
    setShowSuggestions(false);
    onSearch(trimmed);
  }

  function selectSuggestion(suggestion: string) {
    setQuery(suggestion);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    submittedRef.current = true;
    setSuggestions([]);
    setShowSuggestions(false);
    onSearch(suggestion);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!showSuggestions || suggestions.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((i) => (i < suggestions.length - 1 ? i + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((i) => (i > 0 ? i - 1 : suggestions.length - 1));
    } else if (e.key === 'Enter' && selectedIndex >= 0) {
      e.preventDefault();
      selectSuggestion(suggestions[selectedIndex]);
    }
  }

  return (
    <div ref={containerRef} className="relative w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
          placeholder={EXAMPLE_QUERIES[placeholderIndex]}
          className="font-display italic flex-1 px-4 py-3 rounded-lg border border-gray-300 bg-[var(--color-bg-card)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]/50 focus:outline-none focus:border-[var(--color-accent)] focus:ring-2 focus:ring-[var(--color-accent)]/30 transition-colors"
        />
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="px-4 sm:px-6 py-3 rounded-lg bg-[var(--color-accent)] text-white font-medium hover:bg-[var(--color-accent-dark)] transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
        >
          {isLoading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {showSuggestions && suggestions.length > 0 && (
        <ul className="absolute z-10 w-full mt-2 bg-[var(--color-bg-card)] rounded-lg shadow-lg border border-gray-200 animate-slideDown">
          {suggestions.map((suggestion, i) => (
            <li
              key={i}
              onClick={() => selectSuggestion(suggestion)}
              className={`px-4 py-3 cursor-pointer transition-colors ${
                i < suggestions.length - 1 ? 'border-b border-gray-100' : ''
              } ${
                i === selectedIndex
                  ? 'bg-[var(--color-primary)]/10'
                  : 'hover:bg-[var(--color-primary)]/10'
              }`}
            >
              {suggestion}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
