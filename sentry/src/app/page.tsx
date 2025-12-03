'use client';

import { useCallback, useState } from 'react';
import { flushSync } from 'react-dom';
import { Sidebar } from '@/components/Sidebar/Sidebar';
import { MapView } from '@/components/Map/MapView';
import LandingPage from '@/components/LandingPage';
import { AnalysisProgressOverlay, type AnalysisProgress, type ProgressStep, type StepStatus } from '@/components/UI/AnalysisProgressOverlay';
import { AnalysisResultsPanel } from '@/components/UI/AnalysisResultsPanel';
import { DATE_RANGE_LIMITS, DEFAULT_ADVANCED_OPTIONS, DEFAULT_ANALYSIS_PARAMETERS, PIN_TYPE_OPTIONS, SIDEBAR_WIDTH } from '@/lib/constants';
import { runAnalysis } from '@/lib/api';
import type {
  AdvancedOptions,
  AnalysisParameters,
  AnalysisRequest,
  AnalysisResult,
  DrawingMode,
  LayerKey,
  LatLng,
  LocationSelection,
  ParkOption,
  MapPin,
} from '@/lib/types';

export default function DashboardPage() {
  const [location, setLocation] = useState<LocationSelection | null>(null);
  const [parameters, setParameters] = useState<AnalysisParameters>(DEFAULT_ANALYSIS_PARAMETERS);
  const [advancedOptions, setAdvancedOptions] = useState<AdvancedOptions>(DEFAULT_ADVANCED_OPTIONS);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedZoneId, setSelectedZoneId] = useState<string | null>(null);
  const [drawingMode, setDrawingMode] = useState<DrawingMode>('none');
  const [selectedPinType, setSelectedPinType] = useState(
    PIN_TYPE_OPTIONS[0]?.id ?? 'priority-zone'
  );
  const [pins, setPins] = useState<MapPin[]>([]);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState<AnalysisProgress | null>(null);
  const [showResultsPanel, setShowResultsPanel] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);

  const collapsedSidebarWidth = 72;
  const sidebarWidth = isSidebarCollapsed ? collapsedSidebarWidth : SIDEBAR_WIDTH;

  const handleSelectPark = useCallback((park: ParkOption) => {
    setLocation({
      type: 'park',
      parkId: park.id,
      parkName: park.name,
      bounds: park.bounds,
    });
    setDrawingMode('none');
  }, []);

  const handleClearLocation = useCallback(() => {
    setLocation(null);
    setSelectedZoneId(null);
    setDrawingMode('none');
  }, []);

  const handleNewSession = useCallback(() => {
    setLocation(null);
    setSelectedZoneId(null);
    setDrawingMode('none');
    setAnalysisResult(null);
    setShowResultsPanel(false);
    setAnalysisProgress(null);
    setPins([]);
    setError(null);
    setParameters(DEFAULT_ANALYSIS_PARAMETERS);
    setAdvancedOptions(DEFAULT_ADVANCED_OPTIONS);
  }, []);

  const handleToggleLayer = useCallback(
    (layer: LayerKey) => {
      setAdvancedOptions((current) => {
        const exists = current.enabledLayers.includes(layer);
        const enabledLayers = exists
          ? current.enabledLayers.filter((item) => item !== layer)
          : [...current.enabledLayers, layer];
        return { ...current, enabledLayers };
      });
    },
    []
  );

  const handlePolygonComplete = useCallback((polygon: LatLng[]) => {
    console.log('🔷 handlePolygonComplete called with', polygon.length, 'points');

    if (!polygon.length) {
      console.warn('⚠️ Empty polygon, skipping');
      return;
    }

    const latitudes = polygon.map((point) => point.lat);
    const longitudes = polygon.map((point) => point.lng);
    const southWest = { lat: Math.min(...latitudes), lng: Math.min(...longitudes) };
    const northEast = { lat: Math.max(...latitudes), lng: Math.max(...longitudes) };

    const newLocation = {
      type: 'custom' as const,
      polygon,
      bounds: { southWest, northEast },
    };

    console.log('📍 Setting location:', newLocation);
    setLocation(newLocation);
    setSelectedZoneId(null);
  }, []);

  const handlePinPlaced = useCallback(
    ({ position, typeId }: { position: LatLng; typeId: string }) => {
      const pin: MapPin = {
        id: `pin-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        typeId,
        position,
        createdAt: Date.now(),
      };

      setPins((current) => [...current, pin]);
      setLocation((current) => {
        const buffer = 0.01;
        const pointBounds = {
          southWest: { lat: position.lat - buffer, lng: position.lng - buffer },
          northEast: { lat: position.lat + buffer, lng: position.lng + buffer },
        };

        if (current?.type === 'custom') {
          const mergedBounds = current.bounds
            ? {
              southWest: {
                lat: Math.min(current.bounds.southWest.lat, pointBounds.southWest.lat),
                lng: Math.min(current.bounds.southWest.lng, pointBounds.southWest.lng),
              },
              northEast: {
                lat: Math.max(current.bounds.northEast.lat, pointBounds.northEast.lat),
                lng: Math.max(current.bounds.northEast.lng, pointBounds.northEast.lng),
              },
            }
            : pointBounds;

          return {
            ...current,
            type: 'custom',
            point: position,
            bounds: mergedBounds,
          };
        }

        return {
          type: 'custom',
          point: position,
          bounds: pointBounds,
        };
      });
      setSelectedZoneId(null);
    },
    []
  );

  const handlePinRemove = useCallback((pinId: string) => {
    setPins((current) => current.filter((pin) => pin.id !== pinId));
  }, []);

  const handleClearPins = useCallback(() => {
    setPins([]);
  }, []);

  const handleDrawingModeChange = useCallback((mode: DrawingMode) => {
    setDrawingMode(mode);
  }, []);

  const handlePinTypeChange = useCallback((typeId: string) => {
    setSelectedPinType(typeId);
  }, []);

  const handleStartPolygon = useCallback(() => {
    setDrawingMode('polygon');
  }, []);

  const handleStartPinPlacement = useCallback(() => {
    setDrawingMode('pin');
  }, []);

  const handleStopDrawing = useCallback(() => {
    setDrawingMode('none');
  }, []);

  const handleToggleSidebar = useCallback(() => {
    setIsSidebarCollapsed((prev) => !prev);
  }, []);

  const handleRunAnalysis = useCallback(async () => {
    if (!location) {
      setError('Select a park or draw an area before running the analysis.');
      return;
    }

    const clampDateRange = () => {
      const min = DATE_RANGE_LIMITS.min;
      const max = DATE_RANGE_LIMITS.max;

      let start = parameters.dateRange.start || min;
      let end = parameters.dateRange.end || max;

      if (end > max) {
        end = max;
      }

      if (start < min) {
        start = min;
      }

      if (start > end) {
        start = end;
      }

      return { start, end };
    };

    const sanitizedDateRange = clampDateRange();

    if (
      sanitizedDateRange.start !== parameters.dateRange.start ||
      sanitizedDateRange.end !== parameters.dateRange.end
    ) {
      setParameters((current) => ({
        ...current,
        dateRange: sanitizedDateRange,
      }));
    }

    setIsLoading(true);
    setError(null);
    setShowResultsPanel(false);
    setAnalysisProgress(createInitialProgressState('Starting analysis', 'initializing'));

    const payload: AnalysisRequest = {
      location,
      parameters: {
        ...parameters,
        dateRange: sanitizedDateRange,
      },
      advanced: advancedOptions,
    };

    console.info('[analysis] Running with date range:', sanitizedDateRange.start, '→', sanitizedDateRange.end);
    console.debug('[analysis] Parameters snapshot:', payload.parameters);

    try {
      const result = await runAnalysis(payload, {
        onProgress: (progressEvent) => {
          console.info('[analysis] Progress event:', progressEvent);
          console.log('Frontend received progress:', progressEvent);

          const percent = extractProgressPercent(progressEvent);
          const message = typeof progressEvent.message === 'string' ? progressEvent.message : '';

          if (progressEvent.type === 'status' || progressEvent.type === 'progress') {
            flushSync(() => {
              setAnalysisProgress((current) => {
                const base = current ?? createInitialProgressState(message || 'Starting analysis', progressEvent.step);
                const stats = mergeStatsFromEvent(base, progressEvent);
                const stepKey = normalizeStepKey(progressEvent.step);

                return {
                  ...base,
                  ...stats,
                  status: 'running',
                  message: message || base.message,
                  currentStep: stepKey,
                  progressPercent: percent ?? base.progressPercent,
                  steps: pushOrUpdateStep(base.steps, {
                    key: stepKey,
                    message: message || base.message,
                    status: 'active',
                    progressPercent: percent,
                  }),
                };
              });
            });
          } else if (progressEvent.type === 'satellite_images') {
            // Handle real-time satellite image updates
            flushSync(() => {
              setAnalysisProgress((current) => {
                const base = current ?? createInitialProgressState(message || 'Extracting imagery...', progressEvent.step);
                const satelliteImages = (progressEvent.data as any)?.satelliteImages || [];
                return {
                  ...base,
                  satelliteImages,
                  progressPercent: percent ?? base.progressPercent,
                };
              });
            });
          } else if (progressEvent.type === 'search_results') {
            // Handle Perplexity search results
            flushSync(() => {
              setAnalysisProgress((current) => {
                const base = current ?? createInitialProgressState(message || 'Searching...', progressEvent.step);
                return {
                  ...base,
                  searchResults: progressEvent.data as any,
                  steps: pushOrUpdateStep(base.steps, {
                    key: normalizeStepKey(progressEvent.step ?? 'web_search'),
                    message: message || 'Intelligence search complete',
                    status: 'complete',
                    progressPercent: percent,
                  }),
                };
              });
            });
          } else if (progressEvent.type === 'complete') {
            flushSync(() => {
              setAnalysisProgress((current) => {
                const stepKey = normalizeStepKey(progressEvent.step ?? 'complete');
                const base = current ?? createInitialProgressState(message || 'Analysis complete', stepKey);
                const stats = mergeStatsFromEvent(base, progressEvent);

                // Extract satellite images from the complete data
                const satelliteImages = (progressEvent.data as any)?.satelliteImages || [];

                return {
                  ...base,
                  ...stats,
                  status: 'complete',
                  message: message || base.message || 'Analysis complete',
                  currentStep: stepKey,
                  progressPercent: 100,
                  satelliteImages,
                  steps: pushOrUpdateStep(base.steps, {
                    key: stepKey,
                    message: message || 'Analysis complete',
                    status: 'complete',
                    progressPercent: 100,
                  }),
                };
              });
            });
          } else if (progressEvent.type === 'error') {
            flushSync(() => {
              setAnalysisProgress((current) => {
                const stepKey = normalizeStepKey(progressEvent.step ?? 'error');
                const base = current ?? createInitialProgressState(message || 'Analysis failed', stepKey);
                const stats = mergeStatsFromEvent(base, progressEvent);

                return {
                  ...base,
                  ...stats,
                  status: 'error',
                  message: message || base.message || 'Analysis failed',
                  currentStep: stepKey,
                  steps: pushOrUpdateStep(base.steps, {
                    key: stepKey,
                    message: message || 'Analysis failed',
                    status: 'error',
                  }),
                };
              });
            });
          }
        },
      });

      setAnalysisResult(result);
      setSelectedZoneId(result.priorities[0]?.id ?? null);
      setShowResultsPanel(true);

      // Keep overlay open - user must close manually
    } catch (apiError) {
      setError(apiError instanceof Error ? apiError.message : 'Unable to complete analysis.');
      setAnalysisProgress(createTerminalProgressState('error', 'Analysis failed'));

      // Keep error overlay open - user must close manually
    } finally {
      setIsLoading(false);
    }
  }, [advancedOptions, location, parameters]);

  const handleZoneClick = useCallback((zoneId: string) => {
    setSelectedZoneId(zoneId);
  }, []);

  const handlePlaceholderAction = useCallback((message: string) => {
    setError(message);
    setTimeout(() => setError(null), 4000);
  }, []);

  if (!hasStarted) {
    return <LandingPage onStart={() => setHasStarted(true)} />;
  }

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#0f0f0f]">
      {/* Background Grid */}
      <div
        className="absolute inset-0 z-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(to right, #ffffff 1px, transparent 1px), linear-gradient(to bottom, #ffffff 1px, transparent 1px)`,
          backgroundSize: '40px 40px'
        }}
      />

      <div
        className="relative z-10 shrink-0 transition-[width] duration-300 ease-in-out"
        style={{ width: `${sidebarWidth}px` }}
      >
        <Sidebar
          location={location}
          parameters={parameters}
          advancedOptions={advancedOptions}
          result={analysisResult}
          isLoading={isLoading}
          drawingMode={drawingMode}
          pinsCount={pins.length}
          selectedZoneId={selectedZoneId}
          onSelectPark={handleSelectPark}
          onClearLocation={handleClearLocation}
          onStartPolygon={handleStartPolygon}
          onStartPinPlacement={handleStartPinPlacement}
          onStopDrawing={handleStopDrawing}
          onParametersChange={setParameters}
          onAdvancedOptionsChange={setAdvancedOptions}
          onRunAnalysis={handleRunAnalysis}
          onZoneClick={handleZoneClick}
          onExportReport={() => handlePlaceholderAction('Report export will be available soon.')}
          onGenerateRoute={() => handlePlaceholderAction('Route generation is coming soon.')}
          onScheduleFollowUp={() => handlePlaceholderAction('Follow-up scheduling is under development.')}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={handleToggleSidebar}
          onNewSession={handleNewSession}
        />
      </div>

      <div className="relative z-10 flex flex-1">
        {error && (
          <div className="absolute left-1/2 top-4 z-20 w-[380px] -translate-x-1/2 border border-red-400/50 bg-red-900/20 px-4 py-3 text-sm text-red-200 shadow-lg backdrop-blur-sm">
            {error}
          </div>
        )}
        <div className="relative z-10 flex-1">
          <MapView
            location={location}
            result={analysisResult}
            advancedOptions={advancedOptions}
            selectedZoneId={selectedZoneId}
            drawingMode={drawingMode}
            selectedPinType={selectedPinType}
            pins={pins}
            onToggleLayer={handleToggleLayer}
            onDrawingModeChange={handleDrawingModeChange}
            onPolygonComplete={handlePolygonComplete}
            onClearShapes={handleClearLocation}
            onPinTypeChange={handlePinTypeChange}
            onPinPlaced={handlePinPlaced}
            onPinRemove={handlePinRemove}
            onClearPins={handleClearPins}
            onZoneClick={handleZoneClick}
            onNewSession={handleNewSession}
          />
        </div>
        <AnalysisProgressOverlay
          isVisible={!!analysisProgress}
          progress={analysisProgress}
          onClose={() => setAnalysisProgress(null)}
        />
        <AnalysisResultsPanel
          result={analysisResult}
          isVisible={showResultsPanel && !!analysisResult}
          onClose={() => setShowResultsPanel(false)}
        />
      </div>
    </div>
  );
}

function createInitialProgressState(message: string, rawStep?: string | number): AnalysisProgress {
  const key = normalizeStepKey(rawStep ?? 'initializing');
  return {
    status: 'running',
    currentStep: key,
    message,
    steps: [
      {
        key,
        label: formatStepLabel(key),
        message,
        status: 'active',
        startedAt: Date.now(),
      },
    ],
    progressPercent: 0,
  };
}

function createTerminalProgressState(status: 'complete' | 'error', message: string, rawStep?: string | number): AnalysisProgress {
  const key = normalizeStepKey(rawStep ?? status);
  return {
    status,
    currentStep: key,
    message,
    steps: [
      {
        key,
        label: formatStepLabel(key),
        message,
        status: status === 'complete' ? 'complete' : 'error',
        startedAt: Date.now(),
        completedAt: Date.now(),
        progressPercent: status === 'complete' ? 100 : undefined,
      },
    ],
    progressPercent: status === 'complete' ? 100 : 0,
  };
}

function pushOrUpdateStep(
  steps: ProgressStep[],
  payload: { key: string; message?: string; status: StepStatus; progressPercent?: number }
): ProgressStep[] {
  const timestamp = Date.now();
  const label = formatStepLabel(payload.key);
  const existingIndex = steps.findIndex((step) => step.key === payload.key);

  if (existingIndex !== -1) {
    const updated = [...steps];
    updated[existingIndex] = {
      ...updated[existingIndex],
      label,
      message: payload.message ?? updated[existingIndex].message,
      status: payload.status,
      progressPercent: payload.progressPercent ?? updated[existingIndex].progressPercent,
      completedAt:
        payload.status === 'complete' || payload.status === 'error'
          ? timestamp
          : updated[existingIndex].completedAt,
    };
    return updated;
  }

  const normalizedSteps: ProgressStep[] = steps.map((step, index): ProgressStep => {
    if (index === steps.length - 1 && step.status === 'active') {
      return { ...step, status: 'complete', completedAt: timestamp };
    }
    return step;
  });

  return [
    ...normalizedSteps,
    {
      key: payload.key,
      label,
      message: payload.message,
      status: payload.status,
      startedAt: timestamp,
      completedAt: payload.status === 'complete' || payload.status === 'error' ? timestamp : undefined,
      progressPercent: payload.progressPercent,
    },
  ];
}

function mergeStatsFromEvent(current: AnalysisProgress | null, event: Record<string, unknown>): Partial<AnalysisProgress> {
  const getNumber = (value: unknown) => (typeof value === 'number' ? value : undefined);
  const getString = (value: unknown) => (typeof value === 'string' ? value : undefined);

  return {
    totalCells: getNumber((event as Record<string, unknown>).total_cells ?? (event as Record<string, unknown>).totalCells) ?? current?.totalCells,
    cellsProcessed: getNumber((event as Record<string, unknown>).cells_processed ?? (event as Record<string, unknown>).cellsProcessed) ?? current?.cellsProcessed,
    imageCount: getNumber((event as Record<string, unknown>).image_count ?? (event as Record<string, unknown>).imageCount) ?? current?.imageCount,
    modelVersion: getString((event as Record<string, unknown>).model_version ?? (event as Record<string, unknown>).modelVersion) ?? current?.modelVersion,
  };
}

function extractProgressPercent(event: Record<string, unknown>) {
  const candidate =
    (event as Record<string, unknown>).progressPercent ??
    (event as Record<string, unknown>).progress_percent ??
    (event as Record<string, unknown>).percent ??
    (event as Record<string, unknown>).progress;
  return typeof candidate === 'number' ? candidate : undefined;
}

function formatStepLabel(raw: string) {
  if (!raw) {
    return 'Step';
  }
  return raw
    .split(/[_:\-]+/)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ');
}

function normalizeStepKey(raw?: string | number) {
  if (raw === undefined || raw === null || raw === '') {
    return `step-${Date.now()}`;
  }
  return String(raw);
}
