'use client';

import { useEffect, useRef, useState } from 'react';
import { Check, Loader2, AlertTriangle, ExternalLink, Satellite, Search } from 'lucide-react';

export type StepStatus = 'waiting' | 'active' | 'complete' | 'error';

export interface ProgressStep {
  key: string;
  label: string;
  message?: string;
  status: StepStatus;
  startedAt: number;
  completedAt?: number;
  progressPercent?: number;
}

export interface SearchResult {
  title: string;
  url: string;
  snippet: string;
  date?: string;
  last_updated?: string;
}

export interface SearchData {
  query: string;
  results: SearchResult[];
  id?: string;
}

export interface SatelliteImage {
  url: string;
  id: string;
  timestamp?: number;
}

export interface AnalysisProgress {
  status: 'idle' | 'running' | 'complete' | 'error';
  currentStep?: string;
  message?: string;
  steps: ProgressStep[];
  totalCells?: number;
  imageCount?: number;
  cellsProcessed?: number;
  modelVersion?: string;
  progressPercent?: number;
  searchResults?: SearchData;
  satelliteImages?: SatelliteImage[];
}

interface AnalysisProgressOverlayProps {
  isVisible?: boolean;
  progress: AnalysisProgress | null;
  onClose?: () => void;
}

export function AnalysisProgressOverlay({ isVisible = true, progress, onClose }: AnalysisProgressOverlayProps) {
  const timelineRef = useRef<HTMLDivElement | null>(null);
  const currentStep = progress?.steps.at(-1);
  const shouldShow = isVisible && !!progress;
  const [expandedCitation, setExpandedCitation] = useState<number | null>(null);

  useEffect(() => {
    if (!progress || !timelineRef.current) {
      return;
    }
    timelineRef.current.scrollTo({ top: timelineRef.current.scrollHeight, behavior: 'smooth' });
  }, [progress?.steps.length, progress]);

  if (!shouldShow || !progress) {
    return null;
  }

  const headerStatus = progress.status === 'complete'
    ? 'Analysis Complete'
    : progress.status === 'error'
      ? 'Analysis Failed'
      : 'Running Analysis';

  const searchResults = progress.searchResults?.results || [];
  const satelliteImages = progress.satelliteImages || [];

  return (
    <div className="pointer-events-none fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Main Overlay - Much Larger */}
      <div className="pointer-events-auto relative z-10 flex h-[85vh] w-full max-w-5xl overflow-hidden border border-white/10 bg-[#0a0a0a] shadow-2xl">
        {/* Header */}
        <div className="absolute left-0 right-0 top-0 z-20 border-b border-white/10 bg-[#0a0a0a]/95 px-8 py-6 backdrop-blur-sm">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.2em] text-white/40">
                SENTRY INTELLIGENCE PIPELINE
              </p>
              <h2 className="text-2xl font-bold uppercase tracking-wider text-white">
                {headerStatus}
              </h2>
              {currentStep && (
                <div className="space-y-1">
                  <p className="font-mono text-sm font-medium text-white/80">{currentStep.label}</p>
                  {currentStep.message && (
                    <p className="text-xs text-white/50">{currentStep.message}</p>
                  )}
                </div>
              )}
            </div>
            <div className="flex items-start space-x-4">
              {typeof progress.progressPercent === 'number' && progress.status === 'running' && (
                <div className="flex flex-col items-end space-y-1">
                  <span className="font-mono text-3xl font-bold text-white">
                    {Math.round(progress.progressPercent)}%
                  </span>
                  <div className="h-1 w-32 overflow-hidden bg-white/10">
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-500"
                      style={{ width: `${progress.progressPercent}%` }}
                    />
                  </div>
                </div>
              )}
              {onClose && (
                <button
                  onClick={onClose}
                  className="flex h-8 w-8 items-center justify-center rounded-full border border-white/20 text-white/60 transition-all hover:border-white/40 hover:bg-white/10 hover:text-white"
                  aria-label="Close"
                >
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M12 4L4 12M4 4l8 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Content Grid */}
        <div className="mt-32 grid h-full w-full grid-cols-2 gap-6 overflow-hidden p-8">
          {/* Left Column - Timeline */}
          <div className="flex flex-col space-y-4">
            <h3 className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-white/50">
              Pipeline Stages
            </h3>
            <div
              ref={timelineRef}
              className="flex-1 space-y-3 overflow-y-auto pr-2 scrollbar-thin scrollbar-track-white/5 scrollbar-thumb-white/20"
            >
              {progress.steps.length === 0 ? (
                <p className="font-mono text-xs text-white/40">Initializing...</p>
              ) : (
                progress.steps.map((step, index) => (
                  <StepRow
                    key={`${step.key}-${step.startedAt}`}
                    step={step}
                    isLast={index === progress.steps.length - 1}
                  />
                ))
              )}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-3 border-t border-white/10 pt-4">
              {progress.totalCells !== undefined && (
                <StatBlock label="Grid Cells" value={progress.totalCells} />
              )}
              {progress.imageCount !== undefined && (
                <StatBlock label="Sat Images" value={progress.imageCount} />
              )}
            </div>
          </div>

          {/* Right Column - Search Results & Satellite Images */}
          <div className="flex flex-col space-y-4 overflow-hidden">
            {/* Search Results with Citations */}
            {searchResults.length > 0 && (
              <div className="flex flex-col space-y-3">
                <div className="flex items-center space-x-2">
                  <Search className="h-4 w-4 text-cyan-400" />
                  <h3 className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-white/50">
                    Intelligence Sources ({searchResults.length})
                  </h3>
                </div>
                <div className="max-h-[35vh] space-y-2 overflow-y-auto pr-2 scrollbar-thin scrollbar-track-white/5 scrollbar-thumb-white/20">
                  {searchResults.map((result, idx) => (
                    <CitationCard
                      key={idx}
                      result={result}
                      index={idx}
                      isExpanded={expandedCitation === idx}
                      onToggle={() => setExpandedCitation(expandedCitation === idx ? null : idx)}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Satellite Thumbnails */}
            {satelliteImages.length > 0 && (
              <div className="flex flex-col space-y-3">
                <div className="flex items-center space-x-2">
                  <Satellite className="h-4 w-4 text-blue-400" />
                  <h3 className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-white/50">
                    Satellite Imagery ({satelliteImages.length})
                  </h3>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {satelliteImages.slice(0, 4).map((img, idx) => (
                    <div key={idx} className="group relative aspect-video overflow-hidden border border-white/10 bg-black/40">
                      <img
                        src={img.url}
                        alt={`Satellite ${idx + 1}`}
                        className="h-full w-full object-cover opacity-80 transition-opacity group-hover:opacity-100"
                      />
                      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-2">
                        <p className="font-mono text-[9px] text-white/60">
                          {img.timestamp ? new Date(img.timestamp).toLocaleDateString() : 'Sentinel-2'}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StepRow({ step, isLast }: { step: ProgressStep; isLast: boolean }) {
  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center">
        <StepIndicator status={step.status} />
        {!isLast && <div className="mt-1 w-px flex-1 bg-white/10" />}
      </div>
      <div className="flex-1 space-y-1 pb-3">
        <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-wide text-white/50">
          <span>{step.label}</span>
          {typeof step.progressPercent === 'number' && (
            <span className="text-cyan-400">
              {Math.round(step.progressPercent)}%
            </span>
          )}
        </div>
        {step.message && <p className="text-sm text-white/70">{step.message}</p>}
      </div>
    </div>
  );
}

function StepIndicator({ status }: { status: StepStatus }) {
  if (status === 'complete') {
    return (
      <div className="flex h-5 w-5 items-center justify-center rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/50">
        <Check className="h-3 w-3" />
      </div>
    );
  }

  if (status === 'active') {
    return (
      <div className="relative flex h-5 w-5 items-center justify-center">
        <div className="absolute h-5 w-5 animate-ping rounded-full bg-cyan-400/30" />
        <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="flex h-5 w-5 items-center justify-center rounded-full bg-red-600 text-white shadow-lg shadow-red-500/50">
        <AlertTriangle className="h-3 w-3" />
      </div>
    );
  }

  return <div className="h-5 w-5 rounded-full border border-dashed border-white/20" />;
}

function CitationCard({
  result,
  index,
  isExpanded,
  onToggle
}: {
  result: SearchResult;
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="group border border-white/10 bg-white/5 p-3 transition-all hover:border-cyan-500/30 hover:bg-white/10">
      <div className="flex items-start justify-between space-x-2">
        <div className="flex-1 space-y-1">
          <div className="flex items-start space-x-2">
            <span className="font-mono text-[10px] font-bold text-cyan-400">
              [{index + 1}]
            </span>
            <h4 className="flex-1 text-xs font-semibold leading-tight text-white/90">
              {result.title}
            </h4>
          </div>
          <p className={`text-[11px] leading-relaxed text-white/60 ${isExpanded ? '' : 'line-clamp-2'}`}>
            {result.snippet}
          </p>
          {isExpanded && result.date && (
            <p className="font-mono text-[9px] text-white/40">
              Published: {result.date}
            </p>
          )}
        </div>
        <a
          href={result.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-shrink-0 text-cyan-400 opacity-0 transition-opacity group-hover:opacity-100"
        >
          <ExternalLink className="h-3 w-3" />
        </a>
      </div>
      <button
        onClick={onToggle}
        className="mt-2 font-mono text-[9px] uppercase tracking-wider text-white/40 hover:text-cyan-400"
      >
        {isExpanded ? 'Show Less' : 'Read More'}
      </button>
    </div>
  );
}

function StatBlock({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex flex-col space-y-1 border border-white/10 bg-white/5 p-3">
      <span className="font-mono text-[9px] uppercase tracking-wide text-white/40">{label}</span>
      <span className="font-mono text-lg font-bold text-white">{value}</span>
    </div>
  );
}
