import { useState, useRef, useEffect } from 'react';
import type { FilterState } from '../types/filters';
import { PHASE_VALUES, STATUS_VALUES, AGE_CATEGORIES } from '../types';
import type { PhaseValue, StatusValue, AgeCategoryValue } from '../types';

interface FilterPanelProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  onApply: () => void;
  onClear: () => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

function countActiveFilters(filters: FilterState): number {
  let count = 0;
  if (filters.phase) count++;
  if (filters.status) count++;
  if (filters.condition) count++;
  if (filters.location.city || filters.location.state || filters.location.country) count++;
  if (filters.sponsor) count++;
  if (filters.keyword) count++;
  if (filters.ageGroups.length > 0) count++;
  if (filters.enrollmentMin !== null) count++;
  if (filters.enrollmentMax !== null) count++;
  return count;
}

interface CustomSelectProps {
  value: string;
  placeholder: string;
  options: readonly string[];
  formatLabel: (value: string) => string;
  onChange: (value: string) => void;
}

function CustomSelect({ value, placeholder, options, formatLabel, onChange }: CustomSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3 py-2 text-sm text-left border border-gray-300 rounded-lg bg-[var(--color-bg-card)] text-[var(--color-text)] focus:outline-none focus:border-[var(--color-accent)] focus:ring-2 focus:ring-[var(--color-accent)]/30 transition-colors cursor-pointer flex items-center justify-between"
      >
        <span className={value ? '' : 'text-[var(--color-text-muted)]/60'}>
          {value ? formatLabel(value) : placeholder}
        </span>
        <svg
          className={`w-4 h-4 text-[var(--color-text-muted)] transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <ul className="absolute z-20 w-full mt-1 bg-[var(--color-bg-card)] rounded-lg shadow-lg border border-gray-200 animate-slideDown max-h-52 overflow-y-auto">
          <li
            onClick={() => { onChange(''); setIsOpen(false); }}
            className={`px-3 py-2 text-sm cursor-pointer transition-colors border-b border-gray-100 ${
              !value ? 'bg-[var(--color-primary)]/10 font-medium' : 'hover:bg-[var(--color-primary)]/10'
            }`}
          >
            {placeholder}
          </li>
          {options.map((option, i) => (
            <li
              key={option}
              onClick={() => { onChange(option); setIsOpen(false); }}
              className={`px-3 py-2 text-sm cursor-pointer transition-colors ${
                i < options.length - 1 ? 'border-b border-gray-100' : ''
              } ${
                value === option
                  ? 'bg-[var(--color-primary)]/10 font-medium'
                  : 'hover:bg-[var(--color-primary)]/10'
              }`}
            >
              {formatLabel(option)}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function FilterPanel({
  filters,
  onFiltersChange,
  onApply,
  onClear,
  isCollapsed,
  onToggleCollapse,
}: FilterPanelProps) {
  const updateFilter = <K extends keyof FilterState>(key: K, value: FilterState[K]) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const updateLocation = (field: 'city' | 'state' | 'country', value: string) => {
    onFiltersChange({
      ...filters,
      location: { ...filters.location, [field]: value },
    });
  };

  const toggleAgeGroup = (age: AgeCategoryValue) => {
    const newAgeGroups = filters.ageGroups.includes(age)
      ? filters.ageGroups.filter((a) => a !== age)
      : [...filters.ageGroups, age];
    updateFilter('ageGroups', newAgeGroups);
  };

  const activeCount = countActiveFilters(filters);
  const hasActiveFilters = activeCount > 0;

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      onApply();
    }
  };

  return (
    <aside
      className={`bg-[var(--color-bg)] border-r border-gray-200 transition-all duration-300 flex-shrink-0 ${
        isCollapsed ? 'w-12' : 'w-80'
      }`}
    >
      <button
        onClick={onToggleCollapse}
        className="p-3 w-full flex items-center justify-between hover:bg-black/5 transition-colors cursor-pointer"
      >
        {!isCollapsed && (
          <span className="font-display text-base font-semibold text-[var(--color-primary)]">Filters</span>
        )}
        {isCollapsed && hasActiveFilters && (
          <span className="w-5 h-5 rounded-full bg-[var(--color-accent)] text-white text-xs flex items-center justify-center font-medium">
            {activeCount}
          </span>
        )}
        <svg
          className={`w-4 h-4 text-[var(--color-text-muted)] transition-transform ${isCollapsed ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      {!isCollapsed && (
        <div className="px-4 pb-4 space-y-5 overflow-y-auto max-h-[calc(100vh-160px)] animate-fadeIn" onKeyDown={handleKeyDown}>
          {/* Phase */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text)] mb-1.5">
              Phase
            </label>
            <CustomSelect
              value={filters.phase || ''}
              placeholder="Any Phase"
              options={PHASE_VALUES}
              formatLabel={(v) => v.replace('PHASE', 'Phase ').replace('/', ' / Phase ')}
              onChange={(v) => updateFilter('phase', (v as PhaseValue) || null)}
            />
          </div>

          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text)] mb-1.5">
              Status
            </label>
            <CustomSelect
              value={filters.status || ''}
              placeholder="Any Status"
              options={STATUS_VALUES}
              formatLabel={(v) => v.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
              onChange={(v) => updateFilter('status', (v as StatusValue) || null)}
            />
          </div>

          {/* Condition */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text)] mb-1.5">
              Condition
            </label>
            <input
              type="text"
              value={filters.condition}
              onChange={(e) => updateFilter('condition', e.target.value)}
              placeholder="e.g., Lung Cancer"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-[var(--color-bg-card)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]/50 focus:outline-none focus:border-[var(--color-accent)] focus:ring-2 focus:ring-[var(--color-accent)]/30"
            />
          </div>

          {/* Location */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text)] mb-1.5">
              Location
            </label>
            <div className="space-y-2">
              <input
                type="text"
                placeholder="City"
                value={filters.location.city || ''}
                onChange={(e) => updateLocation('city', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-[var(--color-bg-card)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]/50 focus:outline-none focus:border-[var(--color-accent)] focus:ring-2 focus:ring-[var(--color-accent)]/30"
              />
              <input
                type="text"
                placeholder="State"
                value={filters.location.state || ''}
                onChange={(e) => updateLocation('state', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-[var(--color-bg-card)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]/50 focus:outline-none focus:border-[var(--color-accent)] focus:ring-2 focus:ring-[var(--color-accent)]/30"
              />
              <input
                type="text"
                placeholder="Country"
                value={filters.location.country || ''}
                onChange={(e) => updateLocation('country', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-[var(--color-bg-card)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]/50 focus:outline-none focus:border-[var(--color-accent)] focus:ring-2 focus:ring-[var(--color-accent)]/30"
              />
            </div>
          </div>

          {/* Sponsor */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text)] mb-1.5">
              Sponsor
            </label>
            <input
              type="text"
              value={filters.sponsor}
              onChange={(e) => updateFilter('sponsor', e.target.value)}
              placeholder="e.g., Pfizer"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-[var(--color-bg-card)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]/50 focus:outline-none focus:border-[var(--color-accent)] focus:ring-2 focus:ring-[var(--color-accent)]/30"
            />
          </div>

          {/* Keyword */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text)] mb-1.5">
              Keyword
            </label>
            <input
              type="text"
              value={filters.keyword}
              onChange={(e) => updateFilter('keyword', e.target.value)}
              placeholder="Gene, drug, or term"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-[var(--color-bg-card)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]/50 focus:outline-none focus:border-[var(--color-accent)] focus:ring-2 focus:ring-[var(--color-accent)]/30"
            />
          </div>

          {/* Age Groups */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text)] mb-1.5">
              Age Group
            </label>
            <div className="grid grid-cols-2 gap-1.5">
              {AGE_CATEGORIES.map((age) => (
                <label
                  key={age}
                  className={`flex items-center gap-2 text-sm cursor-pointer py-1.5 px-2 rounded-md transition-colors ${
                    filters.ageGroups.includes(age)
                      ? 'bg-[var(--color-primary)]/10 text-[var(--color-primary)]'
                      : 'text-[var(--color-text)] hover:bg-black/5'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={filters.ageGroups.includes(age)}
                    onChange={() => toggleAgeGroup(age)}
                    className="rounded border-gray-300 text-[var(--color-primary)] focus:ring-[var(--color-primary)]/30"
                  />
                  {age
                    .split('-')
                    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                    .join(' ')}
                </label>
              ))}
            </div>
          </div>

          {/* Enrollment Range */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text)] mb-1.5">
              Enrollment Range
            </label>
            <div className="flex gap-2">
              <input
                type="number"
                placeholder="Min"
                value={filters.enrollmentMin ?? ''}
                onChange={(e) =>
                  updateFilter('enrollmentMin', e.target.value ? parseInt(e.target.value, 10) : null)
                }
                min="0"
                className="w-1/2 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-[var(--color-bg-card)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]/50 focus:outline-none focus:border-[var(--color-accent)] focus:ring-2 focus:ring-[var(--color-accent)]/30"
              />
              <input
                type="number"
                placeholder="Max"
                value={filters.enrollmentMax ?? ''}
                onChange={(e) =>
                  updateFilter('enrollmentMax', e.target.value ? parseInt(e.target.value, 10) : null)
                }
                min="0"
                className="w-1/2 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-[var(--color-bg-card)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]/50 focus:outline-none focus:border-[var(--color-accent)] focus:ring-2 focus:ring-[var(--color-accent)]/30"
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2 pt-3 border-t border-gray-200">
            <button
              onClick={onApply}
              className="flex-1 py-2 text-sm font-medium bg-[var(--color-accent)] text-white rounded-lg hover:bg-[var(--color-accent-dark)] transition-colors cursor-pointer"
            >
              Apply Filters
            </button>
            <button
              onClick={onClear}
              disabled={!hasActiveFilters}
              className="px-4 py-2 text-sm font-medium border border-gray-300 rounded-lg text-[var(--color-text-muted)] hover:bg-black/5 transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Clear
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}
