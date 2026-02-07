interface EmptyStateProps {
  type: 'no-results' | 'error';
  message?: string;
  onRetry?: () => void;
  onSuggestionClick?: (query: string) => void;
}

const SUGGESTED_QUERIES = [
  'Phase 3 cancer trials',
  'Recruiting diabetes studies',
  'COVID-19 vaccine trials',
];

export default function EmptyState({ type, message, onRetry, onSuggestionClick }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 animate-fadeIn">
      <div className="w-24 h-24 mb-6 rounded-full bg-gray-100 flex items-center justify-center">
        {type === 'no-results' ? (
          <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        ) : (
          <svg className="w-12 h-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        )}
      </div>

      <h2 className="font-display text-2xl text-gray-700 mb-2">
        {type === 'no-results' ? 'No trials found' : 'Something went wrong'}
      </h2>
      <p className="text-[var(--color-text-muted)] text-center max-w-md mb-6">
        {message ||
          (type === 'no-results'
            ? "We couldn't find any clinical trials matching your search criteria."
            : 'There was an error processing your request. Please try again.')}
      </p>

      {type === 'error' && onRetry && (
        <button
          onClick={onRetry}
          className="px-6 py-2 bg-[var(--color-primary)] text-white rounded-lg hover:bg-[var(--color-primary-dark)] transition-colors cursor-pointer mb-6"
        >
          Try Again
        </button>
      )}

      {type === 'no-results' && onSuggestionClick && (
        <div className="text-center">
          <p className="text-sm text-[var(--color-text-muted)] mb-3">Try one of these searches:</p>
          <div className="flex flex-wrap justify-center gap-2">
            {SUGGESTED_QUERIES.map((q, i) => (
              <button
                key={i}
                onClick={() => onSuggestionClick(q)}
                className="px-4 py-2 rounded-full border border-[var(--color-primary-light)] text-[var(--color-primary)] hover:bg-[var(--color-primary)]/10 transition-colors cursor-pointer text-sm"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
