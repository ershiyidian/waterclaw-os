import L from 'leaflet';
import type { LatLngTuple } from '@/core/types/common';

export function createFovSector(center: LatLngTuple, heading: number): L.Polygon {
  const radius = 0.0012;
  const spread = 26;
  const points: LatLngTuple[] = [center];
  for (let a = heading - spread; a <= heading + spread; a += 4) {
    const rad = (a * Math.PI) / 180;
    points.push([center[0] + Math.cos(rad) * radius * 0.6, center[1] + Math.sin(rad) * radius]);
  }
  return L.polygon(points, {
    color: 'rgba(56,189,248,0.2)',
    fillColor: 'rgba(56,189,248,0.06)',
    fillOpacity: 0.6,
    weight: 1,
  });
}
