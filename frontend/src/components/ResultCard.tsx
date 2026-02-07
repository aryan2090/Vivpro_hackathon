import { useState } from 'react';
import type { TrialResult, StatusValue } from '../types';
import { STATUS_COLORS } from '../types';

const COLOR_MAP: Record<string, { bg: string; text: string; border: string }> = {
  emerald: { bg: '#d1fae5', text: '#065f46', border: '#6ee7b7' },
  amber: { bg: '#fef3c7', text: '#92400e', border: '#fcd34d' },
  blue: { bg: '#dbeafe', text: '#1e40af', border: '#93c5fd' },
  gray: { bg: '#f3f4f6', text: '#374151', border: '#d1d5db' },
  red: { bg: '#fee2e2', text: '#991b1b', border: '#fca5a5' },
  orange: { bg: '#ffedd5', text: '#9a3412', border: '#fdba74' },
  slate: { bg: '#f1f5f9', text: '#334155', border: '#cbd5e1' },
};

function getStatusColors(status?: string) {
  const colorName = STATUS_COLORS[status as StatusValue] || 'slate';
  return COLOR_MAP[colorName] || COLOR_MAP.slate;
}

function formatPhase(phase?: string) {
  if (!phase) return null;
  return phase.replace(/^PHASE/i, 'Phase ').replace(/\//g, '/Phase ');
}

export default function ResultCard({ trial, index }: { trial: TrialResult; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const colors = getStatusColors(trial.overall_status);
  const sponsor = trial.sponsors[0]?.name || 'Unknown';
  const conditions = trial.conditions
    .flatMap((c) => Object.values(c))
    .filter(Boolean);

  return (
    <div
      onClick={() => setExpanded(!expanded)}
      className="bg-[var(--color-bg-card)] rounded-lg shadow-sm border border-gray-200 border-l-4 p-5 hover:shadow-md transition-shadow cursor-pointer animate-fadeIn"
      style={{
        borderLeftColor: colors.border,
        animationDelay: `${index * 50}ms`,
      }}
    >
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2 sm:gap-4">
        <div className="flex-1 min-w-0">
          <h3 className="font-display text-lg font-semibold text-[var(--color-text)] leading-snug">
            {trial.brief_title}
          </h3>
          <span className="text-xs text-[var(--color-text-muted)] font-mono">{trial.nct_id}</span>
        </div>
        {trial.overall_status && (
          <span
            className="self-start shrink-0 px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap"
            style={{ backgroundColor: colors.bg, color: colors.text }}
          >
            {trial.overall_status.replace(/_/g, ' ')}
          </span>
        )}
      </div>

      <div className="flex flex-wrap gap-4 mt-3 text-sm text-[var(--color-text-muted)]">
        {trial.phase && <span>{formatPhase(trial.phase)}</span>}
        <span>Sponsor: {sponsor}</span>
        {trial.enrollment != null && (
          <span>Enrollment: {trial.enrollment.toLocaleString()}</span>
        )}
      </div>

      {conditions.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {conditions.map((c, i) => (
            <span key={i} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
              {c}
            </span>
          ))}
        </div>
      )}

      {expanded && (
        <div className="mt-4 pt-4 border-t border-gray-200 animate-fadeIn">
          {trial.brief_summaries_description && (
            <p className="text-sm text-[var(--color-text)] leading-relaxed mb-3">
              {trial.brief_summaries_description}
            </p>
          )}
          {trial.facilities.length > 0 && (
            <div className="text-sm text-[var(--color-text-muted)]">
              <span className="font-medium">Locations:</span>
              <ul className="mt-1 space-y-1">
                {trial.facilities.map((f, i) => (
                  <li key={i}>
                    {[f.name, f.city, f.state, f.country].filter(Boolean).join(' | ')}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
