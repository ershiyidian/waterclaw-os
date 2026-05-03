import type { LatLngTuple } from '@/core/types/common';

const EARTH_RADIUS_M = 6_371_000;
const METERS_PER_DEGREE_LAT = 111_320;

export function bearing(p1: LatLngTuple, p2: LatLngTuple): number {
  const dLng = ((p2[1] - p1[1]) * Math.PI) / 180;
  const lat1 = (p1[0] * Math.PI) / 180;
  const lat2 = (p2[0] * Math.PI) / 180;
  const y = Math.sin(dLng) * Math.cos(lat2);
  const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLng);
  return ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360;
}

export function quadBezier(p0: LatLngTuple, p1: LatLngTuple, p2: LatLngTuple, t: number): LatLngTuple {
  const u = 1 - t;
  return [
    u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
    u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1],
  ];
}

export function makeBezierPath(start: LatLngTuple, ctrl: LatLngTuple, end: LatLngTuple, steps = 50): LatLngTuple[] {
  return Array.from({ length: steps + 1 }, (_, i) => quadBezier(start, ctrl, end, i / steps));
}

export function distanceMeters(p1: LatLngTuple, p2: LatLngTuple): number {
  const dLat = ((p2[0] - p1[0]) * Math.PI) / 180;
  const dLng = ((p2[1] - p1[1]) * Math.PI) / 180;
  const lat1 = (p1[0] * Math.PI) / 180;
  const lat2 = (p2[0] * Math.PI) / 180;
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  return 2 * EARTH_RADIUS_M * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function toLocalMeters(point: LatLngTuple, origin: LatLngTuple): [number, number] {
  const latScale = METERS_PER_DEGREE_LAT;
  const lngScale = METERS_PER_DEGREE_LAT * Math.cos((origin[0] * Math.PI) / 180);
  return [(point[1] - origin[1]) * lngScale, (point[0] - origin[0]) * latScale];
}

function fromLocalMeters(point: [number, number], origin: LatLngTuple): LatLngTuple {
  const latScale = METERS_PER_DEGREE_LAT;
  const lngScale = METERS_PER_DEGREE_LAT * Math.cos((origin[0] * Math.PI) / 180);
  return [origin[0] + point[1] / latScale, origin[1] + point[0] / lngScale];
}

function nearestPointOnSegment(point: LatLngTuple, start: LatLngTuple, end: LatLngTuple): LatLngTuple {
  const p = toLocalMeters(point, point);
  const a = toLocalMeters(start, point);
  const b = toLocalMeters(end, point);
  const ab: [number, number] = [b[0] - a[0], b[1] - a[1]];
  const abLenSq = ab[0] ** 2 + ab[1] ** 2;
  if (abLenSq === 0) return start;
  const t = Math.max(0, Math.min(1, ((p[0] - a[0]) * ab[0] + (p[1] - a[1]) * ab[1]) / abLenSq));
  return fromLocalMeters([a[0] + t * ab[0], a[1] + t * ab[1]], point);
}

export interface NearestPathResult {
  point: LatLngTuple;
  distanceM: number;
  segmentIndex: number;
}

export function nearestPointOnPath(point: LatLngTuple, path: LatLngTuple[]): NearestPathResult {
  if (path.length === 0) {
    return { point, distanceM: Number.POSITIVE_INFINITY, segmentIndex: -1 };
  }
  if (path.length === 1) {
    return { point: path[0], distanceM: distanceMeters(point, path[0]), segmentIndex: 0 };
  }

  return path.slice(0, -1).reduce<NearestPathResult>(
    (best, start, index) => {
      const candidate = nearestPointOnSegment(point, start, path[index + 1]);
      const distanceM = distanceMeters(point, candidate);
      return distanceM < best.distanceM ? { point: candidate, distanceM, segmentIndex: index } : best;
    },
    { point: path[0], distanceM: Number.POSITIVE_INFINITY, segmentIndex: -1 },
  );
}
