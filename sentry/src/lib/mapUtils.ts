'use client';

import type { LatLng } from './types';

export interface PolygonMetrics {
  points: number;
  areaSqKm: number;
  perimeterKm: number;
}

const EARTH_RADIUS_METERS = 6_371_000;

const toRadians = (degrees: number) => (degrees * Math.PI) / 180;

const haversineDistance = (a: LatLng, b: LatLng) => {
  const lat1 = toRadians(a.lat);
  const lat2 = toRadians(b.lat);
  const deltaLat = lat2 - lat1;
  const deltaLng = toRadians(b.lng - a.lng);

  const sinLat = Math.sin(deltaLat / 2);
  const sinLng = Math.sin(deltaLng / 2);

  const h = sinLat * sinLat + Math.cos(lat1) * Math.cos(lat2) * sinLng * sinLng;
  const c = 2 * Math.atan2(Math.sqrt(h), Math.sqrt(Math.max(0, 1 - h)));
  return EARTH_RADIUS_METERS * c;
};

export function calculatePolygonMetrics(polygon?: LatLng[] | null): PolygonMetrics | null {
  if (!polygon || polygon.length < 3) {
    return null;
  }

  const centroidLat = polygon.reduce((sum, point) => sum + point.lat, 0) / polygon.length;
  const cosLat = Math.cos(toRadians(centroidLat));

  const projected = polygon.map((point) => ({
    x: toRadians(point.lng) * EARTH_RADIUS_METERS * cosLat,
    y: toRadians(point.lat) * EARTH_RADIUS_METERS,
  }));

  let areaAccumulator = 0;
  let perimeterMeters = 0;

  for (let index = 0; index < polygon.length; index += 1) {
    const current = projected[index];
    const next = projected[(index + 1) % projected.length];
    areaAccumulator += current.x * next.y - next.x * current.y;

    const currentLatLng = polygon[index];
    const nextLatLng = polygon[(index + 1) % polygon.length];
    perimeterMeters += haversineDistance(currentLatLng, nextLatLng);
  }

  const areaSqMeters = Math.abs(areaAccumulator) / 2;

  return {
    points: polygon.length,
    areaSqKm: areaSqMeters / 1_000_000,
    perimeterKm: perimeterMeters / 1_000,
  };
}
