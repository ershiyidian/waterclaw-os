import L from 'leaflet';
import type { LatLngTuple } from '@/core/types/common';

export function createSpreadCircle(center: LatLngTuple): L.Circle {
  return L.circle(center, {
    radius: 90,
    color: 'rgba(239,68,68,0.35)',
    fillColor: 'rgba(239,68,68,0.08)',
    fillOpacity: 0.5,
    weight: 1,
    dashArray: '4,4',
  });
}
