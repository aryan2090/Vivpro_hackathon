import type { ExtractedEntities } from '../types';

const ENTITY_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  phase: { bg: 'bg-indigo-100', text: 'text-indigo-800', border: 'border-indigo-200' },
  condition: { bg: 'bg-teal-100', text: 'text-teal-800', border: 'border-teal-200' },
  status: { bg: 'bg-emerald-100', text: 'text-emerald-800', border: 'border-emerald-200' },
  location: { bg: 'bg-slate-100', text: 'text-slate-800', border: 'border-slate-200' },
  keyword: { bg: 'bg-amber-100', text: 'text-amber-800', border: 'border-amber-200' },
  sponsor: { bg: 'bg-purple-100', text: 'text-purple-800', border: 'border-purple-200' },
  age_group: { bg: 'bg-rose-100', text: 'text-rose-800', border: 'border-rose-200' },
};

interface Chip {
  label: string;
  value: string;
  type: string;
}

interface QueryInterpretationProps {
  entities: ExtractedEntities;
  onChipRemove?: (type: string) => void;
}

export default function QueryInterpretation({ entities, onChipRemove }: QueryInterpretationProps) {
  const chips: Chip[] = [];

  if (entities.phase) chips.push({ label: 'Phase', value: entities.phase, type: 'phase' });
  if (entities.condition) chips.push({ label: 'Condition', value: entities.condition, type: 'condition' });
  if (entities.status) {
    chips.push({ label: 'Status', value: entities.status.replace(/_/g, ' '), type: 'status' });
  }
  if (entities.location) {
    const parts = [entities.location.city, entities.location.state, entities.location.country].filter(Boolean);
    if (parts.length > 0) {
      chips.push({ label: 'Location', value: parts.join(', '), type: 'location' });
    }
  }
  if (entities.keyword) chips.push({ label: 'Keyword', value: entities.keyword, type: 'keyword' });
  if (entities.sponsor) chips.push({ label: 'Sponsor', value: entities.sponsor, type: 'sponsor' });
  if (entities.age_group) chips.push({ label: 'Age Group', value: entities.age_group, type: 'age_group' });

  if (chips.length === 0) return null;

  return (
    <div className="py-4 px-6 bg-[var(--color-bg)] border-y border-gray-200">
      <span className="text-sm text-[var(--color-text-muted)] mr-3">We understood:</span>
      <span className="inline-flex flex-wrap gap-2">
        {chips.map((chip, i) => {
          const colors = ENTITY_COLORS[chip.type];
          return (
            <span
              key={chip.type}
              className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium border animate-fadeIn ${colors.bg} ${colors.text} ${colors.border}`}
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <span className="font-semibold">{chip.label}:</span> {chip.value}
              {onChipRemove && (
                <button
                  onClick={() => onChipRemove(chip.type)}
                  className={`ml-1 w-4 h-4 inline-flex items-center justify-center rounded-full hover:bg-black/10 transition-colors cursor-pointer ${colors.text}`}
                  aria-label={`Remove ${chip.label} filter`}
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </span>
          );
        })}
      </span>
    </div>
  );
}
