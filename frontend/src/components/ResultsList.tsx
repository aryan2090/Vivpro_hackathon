import { useRef, useState, useCallback, useImperativeHandle, forwardRef } from 'react';
import type { TrialResult } from '../types';
import ResultCard from './ResultCard';
import Pagination from './Pagination';

interface ResultsListProps {
  results: TrialResult[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

export interface ResultsListHandle {
  scrollToResult: (index: number) => void;
}

const ResultsList = forwardRef<ResultsListHandle, ResultsListProps>(
  ({ results, total, page, pageSize, onPageChange }, ref) => {
    const cardRefs = useRef<(HTMLDivElement | null)[]>([]);
    const [highlightedIndex, setHighlightedIndex] = useState<number | null>(null);
    const totalPages = Math.ceil(total / pageSize);

    const scrollToResult = useCallback((index: number) => {
      const card = cardRefs.current[index];
      if (card) {
        card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setHighlightedIndex(index);
        setTimeout(() => setHighlightedIndex(null), 2000);
      }
    }, []);

    useImperativeHandle(ref, () => ({ scrollToResult }), [scrollToResult]);

    return (
      <div className="w-full max-w-3xl mx-auto">
        <p className="text-sm text-[var(--color-text-muted)] mb-4">
          {total} result{total !== 1 ? 's' : ''} found
        </p>
        <div className="space-y-4">
          {results.map((trial, i) => (
            <ResultCard
              key={trial.nct_id}
              ref={(el) => { cardRefs.current[i] = el; }}
              trial={trial}
              index={i}
              isHighlighted={highlightedIndex === i}
            />
          ))}
        </div>
        <Pagination currentPage={page} totalPages={totalPages} onPageChange={onPageChange} />
      </div>
    );
  }
);

export default ResultsList;
