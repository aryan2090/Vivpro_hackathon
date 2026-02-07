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

export default function ResultsList({ results, total, page, pageSize, onPageChange }: ResultsListProps) {
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="w-full max-w-3xl mx-auto">
      <p className="text-sm text-[var(--color-text-muted)] mb-4">
        {total} result{total !== 1 ? 's' : ''} found
      </p>
      <div className="space-y-4">
        {results.map((trial, i) => (
          <ResultCard key={trial.nct_id} trial={trial} index={i} />
        ))}
      </div>
      <Pagination currentPage={page} totalPages={totalPages} onPageChange={onPageChange} />
    </div>
  );
}
