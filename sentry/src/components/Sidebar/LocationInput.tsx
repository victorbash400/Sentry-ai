'use client';

import { useMemo } from 'react';
import { Button } from '@/components/UI/Button';
import { Select } from '@/components/UI/Select';
import { COLOR_PALETTE } from '@/lib/constants';
import { calculatePolygonMetrics } from '@/lib/mapUtils';
import type { DrawingMode, LocationSelection, ParkOption } from '@/lib/types';

interface LocationInputProps {
  value: LocationSelection | null;
  parks: ParkOption[];
  drawingMode: DrawingMode;
  onParkSelect: (park: ParkOption) => void;
  onStartPolygon: () => void;
  onStartPinPlacement: () => void;
  onStopDrawing: () => void;
  onClear: () => void;
  pinsCount: number;
}

export function LocationInput({
  value,
  parks,
  drawingMode,
  onParkSelect,
  onStartPolygon,
  onStartPinPlacement,
  onStopDrawing,
  onClear,
  pinsCount,
}: LocationInputProps) {
  const selectedParkId = value?.type === 'park' ? value.parkId : undefined;

  const selectOptions = useMemo(
    () =>
      parks.map((park) => ({
        value: park.id,
        label: park.name,
        description: park.description,
      })),
    [parks]
  );

  const handleSelect = (parkId?: string) => {
    if (!parkId) return;
    const park = parks.find((item) => item.id === parkId);
    if (park) {
      onParkSelect(park);
    }
  };

  const isPolygonActive = drawingMode === 'polygon';
  const isPinActive = drawingMode === 'pin';
  const polygonSummary = useMemo(() => calculatePolygonMetrics(value?.polygon), [value?.polygon]);
  const numberFormatter = useMemo(
    () => new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }),
    []
  );

  const locationSummary = (() => {
    if (!value) {
      return 'No area selected';
    }
    if (value.type === 'park') {
      return value.parkName ?? 'Park selected';
    }
    if (value.polygon?.length) {
      return `Custom area with ${value.polygon.length} points`;
    }
    return 'Custom area selected';
  })();

  return (
    <section aria-labelledby="location-heading" className="space-y-4">
      <div className="space-y-1">
        <p id="location-heading" className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/50">
          Targeting
        </p>
        <h2 className="text-sm font-bold uppercase tracking-wider text-white">Area Selection</h2>
        <p className="text-xs text-white/60">
          Define operational boundaries or select region.
        </p>
      </div>

      <div className="space-y-2">
        <Select
          id="park-select"
          options={selectOptions}
          placeholder="Select Region (e.g. Rift Valley)"
          value={selectedParkId}
          onChange={(parkId) => handleSelect(parkId as string | undefined)}
        />
        <Button
          type="button"
          variant="secondary"
          className="w-full"
          onClick={isPolygonActive ? onStopDrawing : onStartPolygon}
        >
          {isPolygonActive ? 'Cancel drawing' : 'Draw Farm Boundaries'}
        </Button>
        {isPolygonActive && (
          <div className="border border-blue-500/30 bg-blue-900/20 px-3 py-2 text-xs text-blue-200">
            <p className="font-mono font-bold uppercase tracking-wider text-blue-400">Drawing Mode Active</p>
            <p className="mt-1 opacity-80">Click points on map. Double-click to complete.</p>
          </div>
        )}
        <Button
          type="button"
          variant={isPinActive ? 'primary' : 'secondary'}
          className="w-full"
          onClick={isPinActive ? onStopDrawing : onStartPinPlacement}
        >
          {isPinActive ? 'Stop placing pins' : 'Place patrol pin on map'}
        </Button>

        <div className="border border-white/10 bg-white/5 px-3 py-2 text-xs text-white/80 font-mono">
          <span className="uppercase tracking-wider text-white/50">
            Current Selection:
          </span>{' '}
          <span className="text-white">{locationSummary}</span>
          <span className="ml-2 text-white/40">[{pinsCount} PINS]</span>
        </div>

        {polygonSummary && (
          <div className="border border-white/10 bg-white/5 px-3 py-2 text-xs text-white/70 font-mono">
            <p className="mb-2 text-[10px] uppercase tracking-[0.2em] text-white/40">
              Polygon Metrics
            </p>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1">
              <span>PTS: {polygonSummary.points}</span>
              <span>AREA: {numberFormatter.format(polygonSummary.areaSqKm)} km²</span>
              <span>PERIM: {numberFormatter.format(polygonSummary.perimeterKm)} km</span>
              <span className="text-green-400">STATUS: READY</span>
            </div>
          </div>
        )}
      </div>

      <Button type="button" variant="ghost" className="w-full text-xs uppercase tracking-widest opacity-60 hover:opacity-100" onClick={onClear}>
        Clear Selection
      </Button>
    </section>
  );
}
