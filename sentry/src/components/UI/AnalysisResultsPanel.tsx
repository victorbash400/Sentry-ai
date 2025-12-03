'use client';

import { useState } from 'react';
import { AnalysisResult } from '@/lib/types';
import { ImageCarousel } from './ImageCarousel';
import { ImageViewerModal } from './ImageViewerModal';

interface AnalysisResultsPanelProps {
  result: AnalysisResult | null;
  isVisible?: boolean;
  onClose?: () => void;
}

export function AnalysisResultsPanel({ result, isVisible = true, onClose }: AnalysisResultsPanelProps) {
  const [isSourcesExpanded, setIsSourcesExpanded] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalImageIndex, setModalImageIndex] = useState(0);

  if (!isVisible || !result) {
    return null;
  }

  const summary = result.summary;
  const priorities = result.priorities || [];
  const satelliteImages = result.satelliteImages || [];

  // Debug logging
  console.log('📊 AnalysisResultsPanel - satelliteImages:', satelliteImages);
  console.log('📊 Full result object:', result);

  const handleViewLarge = (index: number) => {
    setModalImageIndex(index);
    setIsModalOpen(true);
  };

  return (
    <>
      <div className="pointer-events-none fixed right-6 top-1/2 z-40 w-[320px] max-w-[92vw] -translate-y-1/2">
        <div className="pointer-events-auto flex h-[460px] min-h-[460px] flex-col overflow-hidden border border-white/20 bg-[#1a1a1a] p-5 shadow-xl backdrop-blur-md">
          <div className="mb-4 flex items-start justify-between">
            <div className="space-y-1">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/50">
                Analysis Results
              </p>
              <h3 className="text-sm font-bold uppercase tracking-wider text-white">Risk Assessment</h3>
            </div>
            {onClose && (
              <button
                onClick={onClose}
                className="text-white/40 hover:text-white text-xs uppercase tracking-wider font-mono"
              >
                Close
              </button>
            )}
          </div>

          <div className="flex-1 space-y-4 overflow-y-auto pr-1">
            {result.marketData && (
              <div className="border border-white/10 bg-white/5 p-3">
                <h4 className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/60">Market Intelligence</h4>
                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div>
                    <span className="text-white/50">Current Price</span>
                    <p className="font-bold text-white">{result.marketData.currentPrice} {result.marketData.currency}</p>
                  </div>
                  <div>
                    <span className="text-white/50">Volatility</span>
                    <p className={`font-bold ${result.marketData.volatility === 'High' ? 'text-red-400' : 'text-white'}`}>
                      {result.marketData.volatility}
                    </p>
                  </div>
                  <div className="col-span-2 border-t border-white/10 pt-2">
                    <span className="text-white/50">Forecast</span>
                    <p className="text-white">{result.marketData.forecast}</p>
                  </div>
                </div>
              </div>
            )}
            {summary && (
              <div className="space-y-2 text-xs text-white/70 font-mono">
                <div className="flex justify-between">
                  <span>Total Cells</span>
                  <span className="font-medium text-white">{summary.totalCells}</span>
                </div>
                <div className="flex justify-between">
                  <span>High Risk</span>
                  <span className="font-bold text-red-400">{summary.highRiskCells}</span>
                </div>
                {summary.mediumRiskCells !== undefined && (
                  <div className="flex justify-between">
                    <span>Medium Risk</span>
                    <span className="font-bold text-orange-400">{summary.mediumRiskCells}</span>
                  </div>
                )}
                {summary.lowRiskCells !== undefined && (
                  <div className="flex justify-between">
                    <span>Low Risk</span>
                    <span className="font-bold text-yellow-400">{summary.lowRiskCells}</span>
                  </div>
                )}
                {summary.safeCells !== undefined && (
                  <div className="flex justify-between">
                    <span>Safe</span>
                    <span className="font-bold text-green-400">{summary.safeCells}</span>
                  </div>
                )}
                <div className="flex justify-between border-t border-white/10 pt-2">
                  <span>Average Risk</span>
                  <span className="font-medium text-white">{summary.averageRisk}</span>
                </div>
                {summary.areaKm2 && (
                  <div className="flex justify-between">
                    <span>Area</span>
                    <span className="text-white">{summary.areaKm2} km²</span>
                  </div>
                )}
                {summary.imageCount !== undefined && (
                  <div className="flex justify-between">
                    <span>Images</span>
                    <span className="text-white">{summary.imageCount}</span>
                  </div>
                )}
              </div>
            )}

            {satelliteImages.length > 0 && (
              <div className="border-t border-white/10 pt-3">
                <ImageCarousel
                  images={satelliteImages}
                  isExpanded={isSourcesExpanded}
                  onToggle={() => setIsSourcesExpanded(!isSourcesExpanded)}
                  onViewLarge={handleViewLarge}
                />
              </div>
            )}

            <div>
              <h4 className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/50">Top Priority Zones</h4>
              {priorities.length > 0 ? (
                <div className="divide-y divide-white/10 text-xs text-white/70 font-mono">
                  {priorities.slice(0, 3).map((zone) => (
                    <div key={zone.id} className="py-2">
                      <div className="mb-1 flex items-start justify-between text-white">
                        <span className="font-medium">{zone.name}</span>
                        <span className={`font-bold ${zone.riskScore >= 75 ? 'text-red-400' :
                          zone.riskScore >= 60 ? 'text-orange-400' :
                            'text-yellow-400'
                          }`}>
                          {zone.riskScore}
                        </span>
                      </div>
                      {zone.factors && zone.factors.length > 0 && (
                        <div className="space-y-0.5 text-[11px] text-white/50">
                          {zone.factors.slice(0, 2).map((factor, idx) => (
                            <div key={idx} className="truncate">
                              {typeof factor === 'string' ? factor : factor.description || factor.name}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-xs text-white/40 font-mono">No priority zones identified.</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Image Viewer Modal - Outside fixed container */}
      {isModalOpen && (
        <ImageViewerModal
          images={satelliteImages}
          initialIndex={modalImageIndex}
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
        />
      )}
    </>
  );
}
