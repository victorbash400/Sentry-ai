'use client';

import { useState } from 'react';
import { SatelliteImage } from '@/lib/types';

interface ImageCarouselProps {
  images: SatelliteImage[];
  isExpanded: boolean;
  onToggle: () => void;
  onViewLarge?: (index: number) => void;
}

export function ImageCarousel({ images, isExpanded, onToggle, onViewLarge }: ImageCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0);

  if (images.length === 0) return null;

  const handlePrev = () => {
    setCurrentIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1));
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
  };

  const formatDate = (timestamp?: number) => {
    if (!timestamp) return 'Unknown date';
    return new Date(timestamp).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div>
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between text-[10px] font-semibold uppercase tracking-[0.18em] text-white/50 hover:text-white transition"
      >
        <span>Satellite Sources ({images.length})</span>
        <span className="text-xs">{isExpanded ? '−' : '+'}</span>
      </button>

      {isExpanded && (
        <div className="mt-2 space-y-2">
          <div className="relative aspect-video overflow-hidden border border-white/10 bg-black/20">
            <img
              src={images[currentIndex].url}
              alt={`Satellite image ${currentIndex + 1}`}
              className="h-full w-full object-cover"
            />

            {/* Expand Button */}
            {onViewLarge && (
              <button
                onClick={() => onViewLarge(currentIndex)}
                className="absolute right-2 top-2 rounded-lg bg-black/50 p-1.5 text-white hover:bg-black/70"
                aria-label="View large"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M2 9v5h5M14 7V2H9M14 14L9 9M2 2l5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            )}

            {images.length > 1 && (
              <>
                <button
                  onClick={handlePrev}
                  className="absolute left-2 top-1/2 -translate-y-1/2 rounded-full bg-black/50 p-1.5 text-white hover:bg-black/70"
                  aria-label="Previous image"
                >
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <path d="M8 2L4 6L8 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </button>
                <button
                  onClick={handleNext}
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full bg-black/50 p-1.5 text-white hover:bg-black/70"
                  aria-label="Next image"
                >
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <path d="M4 2L8 6L4 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </button>
              </>
            )}

            <div className="absolute bottom-2 left-1/2 -translate-x-1/2 rounded-full bg-black/50 px-2 py-0.5 text-[10px] text-white">
              {currentIndex + 1} / {images.length}
            </div>
          </div>

          <div className="text-[11px] text-white/60 font-mono">
            <div className="flex justify-between">
              <span className="uppercase tracking-wide">Captured</span>
              <span className="text-white">{formatDate(images[currentIndex].timestamp)}</span>
            </div>
            <div className="mt-0.5 truncate text-[10px] text-white/30">
              {images[currentIndex].id.split('/').pop()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
