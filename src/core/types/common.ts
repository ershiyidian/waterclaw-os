export type Severity = 'ok' | 'info' | 'warn' | 'critical' | 'ai';

export type AlertLevel = 'normal' | 'caution' | 'critical';

export type LatLngTuple = [number, number];

export interface TimeSeriesPoint {
  timestamp: number;
  value: number;
}

export interface KeyValueRow {
  key: string;
  value: string | number;
  unit?: string;
  status?: Severity;
}
