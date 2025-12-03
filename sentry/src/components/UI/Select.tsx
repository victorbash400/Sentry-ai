'use client';

import * as React from 'react';

export interface SelectOption<TValue = string> {
  value: TValue;
  label: string;
  description?: string;
}

export interface SelectProps<TValue = string> {
  id?: string;
  options: SelectOption<TValue>[];
  placeholder?: string;
  value?: TValue;
  onChange: (value: TValue | undefined) => void;
  isSearchable?: boolean;
  disabled?: boolean;
  emptyLabel?: string;
}

export function Select<TValue = string>({
  id,
  options,
  placeholder = 'Select option',
  value,
  onChange,
  isSearchable = true,
  disabled = false,
  emptyLabel = 'No matches found',
}: SelectProps<TValue>) {
  const [isOpen, setIsOpen] = React.useState(false);
  const [query, setQuery] = React.useState('');
  const containerRef = React.useRef<HTMLDivElement | null>(null);

  const filteredOptions = React.useMemo(() => {
    if (!isSearchable || query.trim().length === 0) {
      return options;
    }
    const lowered = query.toLowerCase();
    return options.filter((option) =>
      [option.label, option.description]
        .filter(Boolean)
        .some((field) => field?.toLowerCase().includes(lowered))
    );
  }, [isSearchable, options, query]);

  const selectedOption = options.find((option) => option.value === value);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        event.target instanceof Node &&
        !containerRef.current.contains(event.target)
      ) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={containerRef}>
      <button
        id={id}
        type="button"
        disabled={disabled}
        className="flex w-full items-center justify-between border border-white/20 bg-transparent px-3 py-2 text-left text-sm text-white shadow-sm transition hover:border-white/40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white disabled:cursor-not-allowed disabled:opacity-60 font-mono"
        onClick={() => setIsOpen((prev) => !prev)}
      >
        <span className={selectedOption ? '' : 'text-white/40'}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <svg
          className="h-4 w-4 text-white/60"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="m6 9 6 6 6-6" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute z-20 mt-2 w-full border border-white/20 bg-[#1a1a1a] shadow-lg backdrop-blur-md">
          {isSearchable && (
            <div className="border-b border-white/10 p-2">
              <input
                autoFocus
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="SEARCH..."
                className="w-full border border-white/10 bg-black/20 px-2 py-1 text-sm text-white placeholder-white/30 focus-visible:outline focus-visible:outline-white font-mono"
              />
            </div>
          )}

          <ul className="max-h-48 overflow-y-auto py-1">
            {filteredOptions.length === 0 && (
              <li className="px-3 py-2 text-sm text-white/40 font-mono">{emptyLabel}</li>
            )}
            {filteredOptions.map((option) => (
              <li key={`${option.value}`}
                className="cursor-pointer px-3 py-2 text-sm text-white hover:bg-white/10 font-mono"
                onClick={() => {
                  onChange(option.value);
                  setIsOpen(false);
                  setQuery('');
                }}
              >
                <p className="font-medium">{option.label}</p>
                {option.description && (
                  <p className="text-xs text-white/50">{option.description}</p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
