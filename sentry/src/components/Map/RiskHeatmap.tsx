'use client';

import { useMemo, useCallback } from 'react';
import type { GeoJsonObject } from 'geojson';
import { GeoJSON } from 'react-leaflet';
import type { GeoJsonFeatureCollection } from '@/lib/types';
import { RISK_LEVEL_COLORS } from '@/lib/constants';

export type RiskFeatureProperties = {
  riskScore?: number;
  [key: string]: unknown;
};

type RiskFeature = {
  properties?: RiskFeatureProperties;
};

interface RiskHeatmapProps {
  data: GeoJsonFeatureCollection | null;
  displayThreshold: number;
  onSelectZone?: (feature: RiskFeatureProperties) => void;
}

export function RiskHeatmap({ data, displayThreshold, onSelectZone }: RiskHeatmapProps) {
  if (!data) {
    return null;
  }

  const filtered = useMemo(() => {
    if (!data) return null;
    return {
      ...data,
      features: data.features.filter((feature) => {
        const riskScore = getRiskScore(feature);
        return Number.isFinite(riskScore) && riskScore >= displayThreshold;
      }),
    };
  }, [data, displayThreshold]);

  const styleFunction = useCallback((feature: any) => {
    const riskScore = getRiskScore(feature);
    const riskLevel = getRiskLevel(riskScore);
    return {
      color: riskOutlineForLevel(riskLevel),
      weight: 1,
      fillColor: riskFillForLevel(riskLevel),
      fillOpacity: 0.55,
    };
  }, []);

  if (!filtered || filtered.features.length === 0) {
    return null;
  }

  return (
    <GeoJSON
      key={`${displayThreshold}-${filtered.features.length}`}
      data={filtered as unknown as GeoJsonObject}
      style={styleFunction}
      eventHandlers={{
        click: (event) => {
          const properties = (event.propagatedFrom.feature as RiskFeature | undefined)?.properties;
          onSelectZone?.(properties ?? {});
        },
      }}
    />
  );
}

function getRiskScore(feature: unknown): number {
  if (feature && typeof feature === 'object') {
    const candidate = feature as RiskFeature;
    const raw = candidate.properties?.riskScore;
    const numeric = typeof raw === 'number' ? raw : Number(raw ?? 0);
    return Number.isFinite(numeric) ? numeric : 0;
  }
  return 0;
}

function getRiskLevel(score: number): 'safe' | 'low' | 'medium' | 'high' {
  if (score >= 80) return 'high';
  if (score >= 60) return 'medium';
  if (score >= 40) return 'low';
  return 'safe';
}

function riskFillForLevel(level: ReturnType<typeof getRiskLevel>) {
  return RISK_LEVEL_COLORS[level];
}

function riskOutlineForLevel(level: ReturnType<typeof getRiskLevel>) {
  switch (level) {
    case 'high':
      return '#C81E1E';
    case 'medium':
      return '#EA9A3B';
    case 'low':
      return '#D4B010';
    default:
      return '#2F8F5B';
  }
}
