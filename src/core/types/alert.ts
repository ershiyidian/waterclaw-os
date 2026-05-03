import type { AlertLevel, LatLngTuple } from './common';

export interface AlertItem {
  id: string;
  level: AlertLevel;
  title: string;
  source: string;
  location?: LatLngTuple;
  createdAt: number;
  status: 'open' | 'acknowledged' | 'resolved';
  description: string;
}
