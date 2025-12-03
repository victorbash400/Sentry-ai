'use client';

import { useMemo, type ReactNode } from 'react';
import { PanelLeft, PanelRight } from 'lucide-react';
import { Button } from '@/components/UI/Button';
import { LoadingSpinner } from '@/components/UI/LoadingSpinner';
import { COLOR_PALETTE, KENYAN_PARKS, LAYER_LABELS, CROP_OPTIONS, RISK_FACTOR_OPTIONS } from '@/lib/constants';
import type {
  AdvancedOptions,
  AnalysisParameters,
  AnalysisResult,
  DrawingMode,
  LocationSelection,
  ParkOption,
} from '@/lib/types';
import { AnalysisParams } from './AnalysisParams';
import { AdvancedOptions as AdvancedOptionsSection } from './AdvancedOptions';
import { LocationInput } from './LocationInput';
import { ResultsPanel } from './ResultsPanel';

interface SidebarProps {
  location: LocationSelection | null;
  parameters: AnalysisParameters;
  advancedOptions: AdvancedOptions;
  result: AnalysisResult | null;
  isLoading: boolean;
  drawingMode: DrawingMode;
  pinsCount: number;
  selectedZoneId: string | null;
  onSelectPark: (park: ParkOption) => void;
  onClearLocation: () => void;
  onStartPolygon: () => void;
  onStartPinPlacement: () => void;
  onStopDrawing: () => void;
  onParametersChange: (params: AnalysisParameters) => void;
  onAdvancedOptionsChange: (options: AdvancedOptions) => void;
  onRunAnalysis: () => void;
  onZoneClick: (zoneId: string) => void;
  onExportReport: () => void;
  onGenerateRoute: () => void;
  onScheduleFollowUp: () => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  onNewSession?: () => void;
}

export function Sidebar(props: SidebarProps) {
  const {
    location,
    parameters,
    advancedOptions,
    result,
    isLoading,
    drawingMode,
    pinsCount,
    selectedZoneId,
    onSelectPark,
    onClearLocation,
    onStartPolygon,
    onStartPinPlacement,
    onStopDrawing,
    onParametersChange,
    onAdvancedOptionsChange,
    onRunAnalysis,
    onZoneClick,
    onExportReport,
    onGenerateRoute,
    onScheduleFollowUp,
    isCollapsed,
    onToggleCollapse,
    onNewSession,
  } = props;

  const isRunDisabled = !location || isLoading;

  const layerOptions = useMemo(
    () =>
      (Object.entries(LAYER_LABELS) as Array<[keyof typeof LAYER_LABELS, string]>).map(
        ([key, label]) => ({ key, label })
      ),
    []
  );

  if (isCollapsed) {
    return (
      <aside
        className="flex h-full w-full flex-col items-center border-r border-white/10 bg-[#1a1a1a] px-3 py-6"
        aria-label="Collapsed navigation"
      >
        <button
          type="button"
          onClick={onToggleCollapse}
          className="flex h-10 w-10 items-center justify-center border border-white/30 bg-transparent text-white transition hover:border-white hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-white"
          aria-label="Expand sidebar"
        >
          <PanelRight className="h-5 w-5" aria-hidden="true" />
        </button>
      </aside>
    );
  }

  return (
    <aside
      className="flex h-full w-full flex-col border-r border-white/10 bg-[#1a1a1a] font-mono text-white"
    >
      <div className="flex items-start justify-between gap-4 border-b border-white/10 px-6 pb-4 pt-6">
        <div className="space-y-1">
          <div className="flex items-center gap-3 mb-1">
            <img src="/sentry_logo.svg" alt="Sentry" className="h-6 w-6" />
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/50">
              SENTRY // INTELLIGENCE
            </p>
          </div>
          <h1 className="text-lg font-bold tracking-tight text-white">
            CLIMATE RISK ANALYSIS
          </h1>
          <p className="text-xs text-white/70">
            Multi-modal agricultural data platform
          </p>
        </div>
        <div className="flex shrink-0 gap-2">
          {onNewSession && (result || location) && (
            <button
              type="button"
              onClick={onNewSession}
              className="flex h-10 items-center gap-2 border border-white/30 bg-transparent px-3 text-white transition hover:border-white hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-white"
              aria-label="New session"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M2 8h12M8 2v12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
              <span className="text-xs font-medium tracking-wider">NEW</span>
            </button>
          )}
          <button
            type="button"
            onClick={onToggleCollapse}
            className="flex h-10 w-10 shrink-0 items-center justify-center border border-white/30 bg-transparent text-white transition hover:border-white hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-white"
            aria-label="Collapse sidebar"
          >
            <PanelLeft className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
      </div>

      <div className="flex flex-1 flex-col overflow-y-auto px-6 pb-6 pt-5">
        <div className="flex flex-1 flex-col gap-5 pr-1">
          <SidebarCard>
            <LocationInput
              value={location}
              parks={KENYAN_PARKS}
              drawingMode={drawingMode}
              onParkSelect={onSelectPark}
              onStartPolygon={onStartPolygon}
              onStartPinPlacement={onStartPinPlacement}
              onStopDrawing={onStopDrawing}
              onClear={onClearLocation}
              pinsCount={pinsCount}
            />
          </SidebarCard>

          <SidebarCard>
            <AnalysisParams
              parameters={parameters}
              onChange={onParametersChange}
              cropOptions={CROP_OPTIONS}
              riskFactorOptions={RISK_FACTOR_OPTIONS}
            />
          </SidebarCard>

          <SidebarCard>
            <AdvancedOptionsSection
              value={advancedOptions}
              onChange={onAdvancedOptionsChange}
              layers={layerOptions}
            />
          </SidebarCard>

          <SidebarCard>
            <Button
              type="button"
              className="w-full"
              onClick={onRunAnalysis}
              isLoading={isLoading}
              disabled={isRunDisabled}
            >
              Run analysis
            </Button>
          </SidebarCard>
        </div>
      </div>
    </aside>
  );
}

function SidebarCard({ children }: { children: ReactNode }) {
  return (
    <div className="border border-white/10 bg-[#252525] p-4">
      {children}
    </div>
  );
}
