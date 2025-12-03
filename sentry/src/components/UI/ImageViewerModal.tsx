'use client';

import { useState, useEffect } from 'react';
import { SatelliteImage } from '@/lib/types';

interface ImageViewerModalProps {
  images: SatelliteImage[];
  initialIndex?: number;
  isOpen: boolean;
  onClose: () => void;
}

export function ImageViewerModal({ images, initialIndex = 0, isOpen, onClose }: ImageViewerModalProps) {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);

  useEffect(() => {
    setCurrentIndex(initialIndex);
  }, [initialIndex]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowLeft') handlePrev();
      if (e.key === 'ArrowRight') handleNext();
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, currentIndex, onClose]);

  if (!isOpen || images.length === 0) return null;

  const currentImage = images[currentIndex];

  const handlePrev = () => {
    setCurrentIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1));
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
  };

  const formatDate = (timestamp?: number) => {
    if (!timestamp) return 'Unknown';
    return new Date(timestamp).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" onClick={onClose}>
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/80" />

      {/* Close Button - Top Right */}
      <button
        onClick={onClose}
        className="absolute right-6 top-6 z-20 rounded-full bg-black/50 p-2 text-white hover:bg-black/80 border border-white/20"
        aria-label="Close"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
      </button>

      {/* Main Image Container - Centered */}
      <div
        className="relative z-10 mx-auto flex h-[90vh] w-[80vw] items-center justify-center overflow-hidden border border-white/20 bg-[#1a1a1a] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <img
          src={currentImage.url}
          alt={`Satellite image ${currentIndex + 1}`}
          className="h-full w-full object-contain"
        />

        {/* Navigation Arrows */}
        {images.length > 1 && (
          <>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handlePrev();
              }}
              className="absolute left-4 top-1/2 -translate-y-1/2 rounded-full bg-black/50 p-3 text-white shadow-lg hover:bg-black/80 border border-white/20"
              aria-label="Previous image"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M15 18l-6-6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleNext();
              }}
              className="absolute right-4 top-1/2 -translate-y-1/2 rounded-full bg-black/50 p-3 text-white shadow-lg hover:bg-black/80 border border-white/20"
              aria-label="Next image"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M9 18l6-6-6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </>
        )}

        {/* Bottom Info Bar */}
        <div className="absolute bottom-0 left-0 right-0 rounded-b-2xl bg-neutral-900/90 px-6 py-3 backdrop-blur-sm">
          <div className="flex items-center justify-between text-sm text-white">
            <div className="flex items-center gap-4">
              <span className="font-medium font-mono">{formatDate(currentImage.timestamp)}</span>
              <span className="text-white/40">•</span>
              <span className="text-white/60 font-mono">SENTINEL-2</span>
              {images.length > 1 && (
                <>
                  <span className="text-white/40">•</span>
                  <span className="text-white/60 font-mono">{currentIndex + 1} / {images.length}</span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
