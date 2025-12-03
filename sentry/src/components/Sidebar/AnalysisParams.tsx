'use client';

import { useMemo } from 'react';
import { Sunrise, Sun, Sunset, Moon } from 'lucide-react';
import { Button } from '@/components/UI/Button';
import { DateRangePicker } from '@/components/UI/DateRangePicker';
import { Select } from '@/components/UI/Select';
import {
  DATE_RANGE_PRESETS,
  DATE_RANGE_LIMITS,
  resolveDateRangePreset,
} from '@/lib/constants';
import type {
  AnalysisParameters,
  TimeOfDay,
} from '@/lib/types';

const TIME_OF_DAY_CONFIG: Array<{
  key: TimeOfDay;
  label: string;
  icon: typeof Sunrise;
}> = [
    { key: 'dawn', label: 'Dawn', icon: Sunrise },
    { key: 'day', label: 'Day', icon: Sun },
    { key: 'dusk', label: 'Dusk', icon: Sunset },
    { key: 'night', label: 'Night', icon: Moon },
  ];

interface AnalysisParamsProps {
  parameters: AnalysisParameters;
  onChange: (params: AnalysisParameters) => void;
  cropOptions: string[];
  riskFactorOptions: string[];
}

export function AnalysisParams({
  parameters,
  onChange,
  cropOptions,
  riskFactorOptions,
}: AnalysisParamsProps) {
  const cropSelectOptions = useMemo(
    () => cropOptions.map((item) => ({ value: item, label: item })),
    [cropOptions]
  );

  const presetOptions = useMemo(
    () =>
      DATE_RANGE_PRESETS.map((preset) => {
        const range = resolveDateRangePreset(preset);
        const isActive =
          parameters.dateRange.start === range.start &&
          parameters.dateRange.end === range.end;
        return { ...preset, range, isActive };
      }),
    [parameters.dateRange]
  );

  const handlePresetSelect = (range: { start: string; end: string }) => {
    onChange({ ...parameters, dateRange: range });
  };

  const handleDateChange = (next: { start: string; end: string }) => {
    onChange({ ...parameters, dateRange: next });
  };

  const toggleTimeOfDay = (time: TimeOfDay) => {
    const exists = parameters.timeOfDay.includes(time);
    const timeOfDay = exists
      ? parameters.timeOfDay.filter((value) => value !== time)
      : [...parameters.timeOfDay, time];
    onChange({ ...parameters, timeOfDay });
  };

  const toggleThreat = (threat: string) => {
    const exists = parameters.riskFactors.includes(threat);
    const nextThreats = exists
      ? parameters.riskFactors.filter((value) => value !== threat)
      : [...parameters.riskFactors, threat];
    onChange({ ...parameters, riskFactors: nextThreats });
  };

  return (
    <section aria-labelledby="analysis-params-heading" className="space-y-4">
      <div className="space-y-1">
        <p
          id="analysis-params-heading"
          className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/50"
        >
          Parameters
        </p>
        <h2 className="text-sm font-bold uppercase tracking-wider text-white">Analysis Configuration</h2>
      </div>

      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wider text-white/80">Timeframe Presets</p>
        <div className="flex flex-wrap gap-2">
          {presetOptions.map((preset) => (
            <Button
              key={preset.id}
              type="button"
              size="sm"
              variant={preset.isActive ? 'primary' : 'secondary'}
              aria-pressed={preset.isActive}
              title={preset.description}
              onClick={() => handlePresetSelect(preset.range)}
            >
              {preset.label}
            </Button>
          ))}
        </div>
        <p className="text-[10px] text-white/40 font-mono">
          {presetOptions.find((preset) => preset.isActive)?.description ??
            'SELECT PRESET OR CUSTOM RANGE'}
        </p>
      </div>

      <DateRangePicker
        value={parameters.dateRange}
        onChange={handleDateChange}
        min={DATE_RANGE_LIMITS.min}
        max={DATE_RANGE_LIMITS.max}
      />

      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wider text-white/80">Temporal Focus</p>
        <div className="grid grid-cols-2 gap-2">
          {TIME_OF_DAY_CONFIG.map(({ key, label, icon: Icon }) => {
            const isActive = parameters.timeOfDay.includes(key);
            return (
              <Button
                key={key}
                type="button"
                variant={isActive ? 'primary' : 'secondary'}
                size="sm"
                className="justify-start"
                aria-pressed={isActive}
                onClick={() => toggleTimeOfDay(key)}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Button>
            );
          })}
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-xs font-semibold uppercase tracking-wider text-white/80" htmlFor="species-select">
          Target Crop
        </label>
        <Select
          id="species-select"
          options={cropSelectOptions}
          value={parameters.cropType}
          onChange={(value) =>
            onChange({ ...parameters, cropType: (value as string | undefined) ?? 'Maize' })
          }
          placeholder="Select Crop (e.g. Maize)"
          isSearchable={false}
        />
      </div>

      <fieldset className="space-y-3">
        <legend className="text-xs font-semibold uppercase tracking-wider text-white/80">Risk Factors</legend>
        <div className="grid grid-cols-1 gap-2">
          {riskFactorOptions.map((threat) => {
            const isChecked = parameters.riskFactors.includes(threat);
            return (
              <label
                key={threat}
                className="flex items-center justify-between border border-white/10 bg-white/5 px-3 py-2 text-sm text-white shadow-sm transition hover:border-white/30 hover:bg-white/10 cursor-pointer font-mono"
              >
                <span className="capitalize">{threat}</span>
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => toggleThreat(threat)}
                  className="h-4 w-4 accent-white bg-transparent border-white/40"
                />
              </label>
            );
          })}
        </div>
      </fieldset>
    </section>
  );
}
