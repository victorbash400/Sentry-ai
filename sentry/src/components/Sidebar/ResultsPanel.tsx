'use client';

import { AlertTriangle, FileText, MapPinned, RefreshCw } from 'lucide-react';
import { Button } from '@/components/UI/Button';
import type { AnalysisResult, PriorityZone } from '@/lib/types';

interface ResultsPanelProps {
  result: AnalysisResult | null;
  selectedZoneId: string | null;
  onZoneClick: (zoneId: string) => void;
  onExportReport: () => void;
  onGenerateRoute: () => void;
  onScheduleFollowUp: () => void;
}

export function ResultsPanel({
  result,
  selectedZoneId,
  onZoneClick,
  onExportReport,
  onGenerateRoute,
  onScheduleFollowUp,
}: ResultsPanelProps) {
  if (!result || !result.summary) {
    return null;
  }

  const { summary, priorities } = result;
  const highRiskDetected = (summary?.highRiskCells ?? 0) > 0;

  return (
    <section className="space-y-4">
      <header className="space-y-1">
        <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/50">
          Intelligence
        </p>
        <h2 className="text-sm font-bold uppercase tracking-wider text-white">Risk Analysis</h2>
        <p className="text-xs text-white/60">
          High-risk zones requiring immediate mitigation.
        </p>
      </header>

      {highRiskDetected && (
        <div className="flex items-start gap-3 border-l-2 border-red-500 bg-red-900/20 px-4 py-3 text-sm text-red-200">
          <AlertTriangle className="mt-0.5 h-5 w-5 text-red-400" aria-hidden="true" />
          <div>
            <p className="font-mono font-bold uppercase tracking-wider text-red-400">CRITICAL RISK DETECTED</p>
            <p className="text-red-200/80 text-xs mt-1">
              {summary.highRiskCells} zones show extreme vulnerability. Review market data and soil moisture.
            </p>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {priorities.length === 0 && (
          <div className="border border-white/10 bg-white/5 px-4 py-3 text-xs text-white/50 font-mono">
            AWAITING ANALYSIS DATA...
          </div>
        )}

        {priorities.slice(0, 3).map((zone) => (
          <PriorityCard
            key={zone.id}
            zone={zone}
            isActive={zone.id === selectedZoneId}
            onClick={() => onZoneClick(zone.id)}
          />
        ))}
      </div>

      <footer className="space-y-2">
        <Button type="button" className="w-full" leftIcon={<MapPinned className="h-4 w-4" />} onClick={onGenerateRoute}>
          Generate patrol route
        </Button>
        <div className="grid grid-cols-2 gap-2">
          <Button
            type="button"
            variant="secondary"
            className="w-full"
            leftIcon={<FileText className="h-4 w-4" />}
            onClick={onExportReport}
          >
            Export report
          </Button>
          <Button
            type="button"
            variant="secondary"
            className="w-full"
            leftIcon={<RefreshCw className="h-4 w-4" />}
            onClick={onScheduleFollowUp}
          >
            Schedule follow-up
          </Button>
        </div>
      </footer>
    </section>
  );
}

interface PriorityCardProps {
  zone: PriorityZone;
  isActive: boolean;
  onClick: () => void;
}

function PriorityCard({ zone, isActive, onClick }: PriorityCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full border px-4 py-3 text-left transition focus-visible:outline focus-visible:outline-white ${isActive ? 'border-white bg-white/10' : 'border-white/10 bg-transparent hover:border-white/30 hover:bg-white/5'}`}
    >
      <div className="flex items-center justify-between font-mono">
        <p className="text-xs font-bold uppercase tracking-wider text-white">{zone.name}</p>
        <span className="text-xs font-medium text-white/80">{zone.riskScore}% RISK</span>
      </div>
      <div className="mt-2 space-y-1">
        {zone.factors.slice(0, 2).map((factor) => (
          <div key={factor.name} className="flex items-center gap-2 text-[10px] uppercase tracking-wide text-white/60 font-mono">
            <span className="inline-flex h-1 w-1 bg-white/60" aria-hidden="true" />
            {factor.name} ({factor.contribution}%)
          </div>
        ))}
      </div>
    </button>
  );
}
