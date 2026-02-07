interface ClarificationBannerProps {
  question: string;
  onSelection: (choice: string) => void;
}

function extractOptions(question: string): string[] {
  const quoted = question.match(/['"]([^'"]+)['"]/g);
  if (quoted) {
    return quoted.map((m) => m.slice(1, -1));
  }
  const orMatch = question.match(/did you mean\s+(.+?)\s*\?/i);
  if (orMatch) {
    return orMatch[1]
      .split(/\s+or\s+/i)
      .map((s) => s.trim())
      .filter(Boolean);
  }
  return [];
}

export default function ClarificationBanner({ question, onSelection }: ClarificationBannerProps) {
  const options = extractOptions(question);

  return (
    <div className="w-full py-4 px-6 bg-amber-50 border-y border-amber-200 animate-slideDown">
      <p className="text-amber-800 font-medium mb-3">{question}</p>
      {options.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {options.map((opt, i) => (
            <button
              key={i}
              onClick={() => onSelection(opt)}
              className="px-4 py-2 rounded-full bg-white border border-amber-300 text-amber-800 hover:bg-amber-100 transition-colors text-sm"
            >
              {opt}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
