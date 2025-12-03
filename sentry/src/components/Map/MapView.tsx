'use client';

import dynamic from 'next/dynamic';
import type { MapViewContentProps } from '@/components/Map/MapViewContent';

const DynamicMap = dynamic<MapViewContentProps>(
  () => import('@/components/Map/MapViewContent').then((module) => module.MapViewContent),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-screen w-full items-center justify-center bg-[#1a1a1a] text-xs font-bold uppercase tracking-widest text-white/50 font-mono">
        Initializing Sentry Map...
      </div>
    ),
  }
);

export type MapViewProps = MapViewContentProps;

export function MapView(props: MapViewProps) {
  return <DynamicMap {...props} />;
}
