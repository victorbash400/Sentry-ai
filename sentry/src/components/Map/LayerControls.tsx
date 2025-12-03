'use client';

import type { LayerKey } from '@/lib/types';

interface LayerControlsProps {
  layers: Array<{ key: LayerKey; label: string }>;
  enabledLayers: LayerKey[];
  onToggle: (layer: LayerKey) => void;
}

export function LayerControls({ layers, enabledLayers, onToggle }: LayerControlsProps) {
  return (
    <div className="absolute right-4 top-4 z-[1200] w-56 space-y-2 border border-white/20 bg-[#1a1a1a] px-4 py-3 shadow-md backdrop-blur-md">
      <header className="text-xs font-bold uppercase tracking-wider text-white font-mono">Map Layers</header>
      <div className="space-y-2 text-xs text-white font-mono">
        {layers.map((layer) => (
          <label key={layer.key} className="flex items-center justify-between cursor-pointer hover:text-white/80 transition">
            <span className="uppercase">{layer.label}</span>
            <input
              type="checkbox"
              className="h-4 w-4 accent-white bg-transparent border-white/40"
              checked={enabledLayers.includes(layer.key)}
              onChange={() => onToggle(layer.key)}
            />
          </label>
        ))}
      </div>
    </div>
  );
}
