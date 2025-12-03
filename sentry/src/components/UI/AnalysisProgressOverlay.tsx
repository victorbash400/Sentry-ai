"use client";

import { useEffect, useRef } from 'react';
import { Check, Loader2, AlertTriangle } from 'lucide-react';

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
}

interface AnalysisProgressOverlayProps {
  isVisible?: boolean;
  progress: AnalysisProgress | null;
}

export function AnalysisProgressOverlay({ isVisible = true, progress }: AnalysisProgressOverlayProps) {
  const timelineRef = useRef<HTMLDivElement | null>(null);
  const currentStep = progress?.steps.at(-1);
  const shouldShow = isVisible && !!progress;

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
    ? 'Analysis complete'
    : progress.status === 'error'
      ? 'Analysis failed'
      : 'Running analysis';

  return (
    <div className="pointer-events-none fixed right-6 top-1/2 z-50 w-[320px] max-w-[92vw] -translate-y-1/2">
      <div className="pointer-events-auto flex h-[460px] flex-col overflow-hidden rounded-2xl border border-neutral-200 bg-white/95 p-5 shadow-xl">
        <div className="mb-4 flex items-start justify-between gap-4">
          <div className="space-y-1">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-neutral-500">
              Live Pipeline
            </p>
            <p className="text-sm font-semibold text-neutral-900">{headerStatus}</p>
            {currentStep && (
              <div className="space-y-0.5">
                <p className="text-xs font-medium text-neutral-700">{currentStep.label}</p>
                {currentStep.message && (
                  <p className="text-[11px] text-neutral-500">{currentStep.message}</p>
                )}
              </div>
            )}
          </div>
          {typeof progress.progressPercent === 'number' && progress.status === 'running' && (
            <span className="text-xs font-mono text-neutral-500">
              {Math.round(progress.progressPercent)}%
            </span>
          )}
        </div>
        <div
          ref={timelineRef}
          className="flex-1 space-y-2 overflow-y-auto pr-1"
        >
          {progress.steps.length === 0 ? (
            <p className="text-xs text-neutral-500">Waiting for backend updates…</p>
          ) : (
            progress.steps.map((step, index) => (
              <StepRow key={`${step.key}-${step.startedAt}`} step={step} isLast={index === progress.steps.length - 1} />
            ))
          )}
        </div>

        <div className="mt-4 grid grid-cols-2 gap-2 rounded-xl border border-neutral-200 bg-neutral-50/70 px-3 py-2 text-xs text-neutral-600">
          {progress.totalCells !== undefined && (
            <StatBlock label="Cells" value={progress.totalCells} />
          )}
          {progress.cellsProcessed !== undefined && (
            <StatBlock label="Processed" value={progress.cellsProcessed} />
          )}
          {progress.imageCount !== undefined && (
            <StatBlock label="Images" value={progress.imageCount} />
          )}
          {progress.modelVersion && (
            <StatBlock label="Model" value={progress.modelVersion} />
          )}
        </div>
      </div>
    </div>
  );
}

function StepRow({ step, isLast }: { step: ProgressStep; isLast: boolean }) {
  return (
    <div className="flex gap-3 pb-3">
      <div className="flex flex-col items-center">
        <StepIndicator status={step.status} />
        {!isLast && <div className="mt-1 w-px flex-1 bg-neutral-200" />}
      </div>
      <div className="flex-1 space-y-1 border-b border-neutral-100 pb-3">
        <div className="flex items-center justify-between text-[11px] uppercase tracking-wide text-neutral-500">
          <span>{step.label}</span>
          {typeof step.progressPercent === 'number' && (
            <span className="font-mono text-[10px] text-neutral-500">
              {Math.round(step.progressPercent)}%
            </span>
          )}
        </div>
        {step.message && <p className="text-sm text-neutral-900">{step.message}</p>}
      </div>
    </div>
  );
}

function StepIndicator({ status }: { status: StepStatus }) {
  if (status === 'complete') {
    return (
      <div className="flex h-5 w-5 items-center justify-center rounded-full bg-neutral-900 text-white">
        <Check className="h-3 w-3" />
      </div>
    );
  }

  if (status === 'active') {
    return <Loader2 className="h-4 w-4 animate-spin text-neutral-900" />;
  }

  if (status === 'error') {
    return (
      <div className="flex h-5 w-5 items-center justify-center rounded-full bg-red-600 text-white">
        <AlertTriangle className="h-3 w-3" />
      </div>
    );
  }

  return <div className="h-5 w-5 rounded-full border border-dashed border-neutral-300" />;
}

function StatBlock({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex flex-col text-neutral-700">
      <span className="text-[11px] uppercase tracking-wide text-neutral-400">{label}</span>
      <span className="font-mono text-sm text-neutral-900">{value}</span>
    </div>
  );
}
