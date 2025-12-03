'use client';

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { Button } from '@/components/UI/Button';
import type { AdvancedOptions, LayerKey } from '@/lib/types';

interface LayerOption {
  key: LayerKey;
  label: string;
  disabled?: boolean;
}

interface AdvancedOptionsProps {
  value: AdvancedOptions;
  onChange: (options: AdvancedOptions) => void;
  layers: LayerOption[];
}

export function AdvancedOptions({ value, onChange, layers }: AdvancedOptionsProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const toggleLayer = (layer: LayerKey) => {
    const exists = value.enabledLayers.includes(layer);
    const enabledLayers = exists
      ? value.enabledLayers.filter((item) => item !== layer)
      : [...value.enabledLayers, layer];
    onChange({ ...value, enabledLayers });
  };

  return (
    <section className="space-y-3">
      <Button
        type="button"
        variant="secondary"
        className="flex w-full items-center justify-between"
        onClick={() => setIsExpanded((prev) => !prev)}
      >
        <span className="text-left">
          <span className="block text-xs font-bold uppercase tracking-wider text-white">Advanced Configuration</span>
          <span className="block text-[10px] text-white/50 tracking-wide">Fine-tune display parameters</span>
        </span>
        <ChevronDown
          className={`h-4 w-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
        />
      </Button>

      {isExpanded && (
        <div className="space-y-5 border-t border-white/10 pt-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-white font-mono">
              <span className="uppercase tracking-wider">Display Threshold</span>
              <span>{value.displayThreshold}%</span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              step={5}
              value={value.displayThreshold}
              onChange={(event) =>
                onChange({ ...value, displayThreshold: Number(event.target.value) })
              }
              className="w-full accent-white"
            />
            <p className="text-[10px] text-white/40">
              Filter grid cells below risk threshold.
            </p>
          </div>

          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-white/80">Grid Granularity</p>
            <div className="grid grid-cols-3 gap-2 text-xs text-white font-mono">
              {[1, 2, 5].map((size) => (
                <label key={size} className="flex items-center gap-2 border border-white/10 bg-white/5 px-3 py-2 cursor-pointer hover:bg-white/10 transition">
                  <input
                    type="radio"
                    name="grid-granularity"
                    value={size}
                    checked={value.gridGranularity === size}
                    onChange={() => onChange({ ...value, gridGranularity: size as 1 | 2 | 5 })}
                    className="accent-white bg-transparent border-white/40"
                  />
                  {size}KM
                </label>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-white/80">Layer Visibility</p>
            <div className="space-y-2">
              {layers.map((layer) => (
                <label
                  key={layer.key}
                  className="flex items-center justify-between border border-white/10 bg-white/5 px-3 py-2 text-xs text-white font-mono cursor-pointer hover:bg-white/10 transition"
                >
                  <span className="uppercase">{layer.label}</span>
                  <input
                    type="checkbox"
                    checked={value.enabledLayers.includes(layer.key)}
                    disabled={layer.disabled}
                    onChange={() => toggleLayer(layer.key)}
                    className="h-4 w-4 accent-white bg-transparent border-white/40"
                  />
                </label>
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
