'use client';

import { useMemo } from 'react';
import { MapPin, Shapes, Trash2 } from 'lucide-react';
import { Button } from '@/components/UI/Button';
import { Select } from '@/components/UI/Select';
import type { DrawingMode, PinTypeOption } from '@/lib/types';

interface DrawingToolsProps {
  mode: DrawingMode;
  pinTypeId: string;
  pinOptions: PinTypeOption[];
  pinsCount: number;
  onModeChange: (mode: DrawingMode) => void;
  onPinTypeChange: (typeId: string) => void;
  onClearShapes: () => void;
  onClearPins: () => void;
}

export function DrawingTools({
  mode,
  pinTypeId,
  pinOptions,
  pinsCount,
  onModeChange,
  onPinTypeChange,
  onClearShapes,
  onClearPins,
}: DrawingToolsProps) {
  const selectOptions = useMemo(
    () =>
      pinOptions.map((option) => ({
        value: option.id,
        label: option.label,
        description: option.description,
      })),
    [pinOptions]
  );

  const hasPinOptions = selectOptions.length > 0;
  const isPolygonActive = mode === 'polygon';
  const isPinActive = mode === 'pin';

  return (
    <div className="pointer-events-auto absolute right-4 top-1/2 z-[1200] flex w-64 -translate-y-1/2 flex-col gap-4 border border-white/20 bg-[#1a1a1a] p-4 shadow-lg backdrop-blur-md">
      <div className="space-y-2">
        <Button
          type="button"
          variant={isPolygonActive ? 'primary' : 'secondary'}
          size="sm"
          leftIcon={<Shapes className="h-4 w-4" />}
          onClick={() => onModeChange(isPolygonActive ? 'none' : 'polygon')}
        >
          {isPolygonActive ? 'Finish polygon' : 'Draw area'}
        </Button>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          leftIcon={<Trash2 className="h-4 w-4" />}
          onClick={() => {
            onClearShapes();
            onModeChange('none');
          }}
        >
          Clear area
        </Button>
      </div>

      <div className="space-y-3 border border-white/10 bg-white/5 p-3">
        <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-widest text-white/50 font-mono">
          <span>Pins</span>
          <span>{pinsCount} ACTIVE</span>
        </div>
        <Select
          id="draw-pin-type"
          options={selectOptions}
          value={pinTypeId}
          onChange={(value) => {
            if (typeof value === 'string') {
              onPinTypeChange(value);
            }
          }}
          placeholder={hasPinOptions ? 'Choose pin type' : 'No pin types'}
          disabled={!hasPinOptions}
        />
        <Button
          type="button"
          variant={isPinActive ? 'primary' : 'secondary'}
          size="sm"
          leftIcon={<MapPin className="h-4 w-4" />}
          onClick={() => onModeChange(isPinActive ? 'none' : 'pin')}
          disabled={!hasPinOptions}
        >
          {isPinActive ? 'Stop placing pins' : 'Place pin'}
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onClearPins}
          disabled={pinsCount === 0}
        >
          Clear pins
        </Button>
      </div>
    </div>
  );
}
