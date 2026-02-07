import { useCallback } from 'react';

interface AISummaryProps {
  summary: string;
  onCitationClick: (index: number) => void;
}

export default function AISummary({ summary, onCitationClick }: AISummaryProps) {
  const renderSummaryWithCitations = useCallback(() => {
    const parts = summary.split(/(\[\d+\])/g);

    return parts.map((part, i) => {
      const citationMatch = part.match(/^\[(\d+)\]$/);
      if (citationMatch) {
        const index = parseInt(citationMatch[1], 10);
        return (
          <button
            key={i}
            onClick={(e) => {
              e.stopPropagation();
              onCitationClick(index - 1);
            }}
            className="inline-flex items-center justify-center w-5 h-5 mx-0.5 text-xs font-semibold text-[var(--color-primary)] bg-[var(--color-primary)]/10 rounded hover:bg-[var(--color-primary)]/20 transition-colors cursor-pointer"
            aria-label={`Jump to result ${index}`}
          >
            {index}
          </button>
        );
      }
      return <span key={i}>{part}</span>;
    });
  }, [summary, onCitationClick]);

  return (
    <div className="w-full max-w-3xl mx-auto mt-6 mb-6 p-5 bg-gradient-to-r from-[var(--color-primary)]/5 to-[var(--color-accent)]/5 rounded-lg border border-[var(--color-primary)]/20 animate-slideDown">
      <div className="flex items-start gap-3">
        <div className="shrink-0 w-8 h-8 flex items-center justify-center bg-[var(--color-primary)]/10 rounded-full">
          <svg className="w-4 h-4 text-[var(--color-primary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-[var(--color-primary)] mb-2">AI Summary</h3>
          <p className="text-sm text-[var(--color-text)] leading-relaxed">
            {renderSummaryWithCitations()}
          </p>
        </div>
      </div>
    </div>
  );
}
