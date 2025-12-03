'use client';

import * as React from 'react';

export interface DateRangeValue {
  start: string;
  end: string;
}

export interface DateRangePickerProps {
  value: DateRangeValue;
  onChange: (value: DateRangeValue) => void;
  min?: string;
  max?: string;
}

export function DateRangePicker({ value, onChange, min, max }: DateRangePickerProps) {
  const handleChange = (field: 'start' | 'end') =>
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const nextValue = { ...value, [field]: event.target.value };
      onChange(nextValue);
    };

  return (
    <div className="grid grid-cols-2 gap-3">
      <label className="flex flex-col text-sm text-white font-mono">
        <span className="mb-1 text-[10px] font-bold uppercase tracking-widest text-white/50">Start Date</span>
        <input
          type="date"
          value={value.start}
          onChange={handleChange('start')}
          min={min}
          max={value.end || max}
          className="border border-white/20 bg-black/20 px-3 py-2 text-xs text-white focus-visible:outline focus-visible:outline-white"
        />
      </label>
      <label className="flex flex-col text-sm text-white font-mono">
        <span className="mb-1 text-[10px] font-bold uppercase tracking-widest text-white/50">End Date</span>
        <input
          type="date"
          value={value.end}
          onChange={handleChange('end')}
          min={value.start || min}
          max={max}
          className="border border-white/20 bg-black/20 px-3 py-2 text-xs text-white focus-visible:outline focus-visible:outline-white"
        />
      </label>
    </div>
  );
}
