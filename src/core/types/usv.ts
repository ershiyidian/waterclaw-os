import type { LatLngTuple, Severity, TimeSeriesPoint } from './common';

export type UsvMode = 'AUTO' | 'HOLD' | 'INTERCEPT' | 'SENTRY' | 'RTL' | 'ESTOP';

export interface BatteryState {
  pct: number;
  powerW: number;
  remainingMin: number;
  temperatureC: number;
  cycles: number;
  cycleLimit: number;
}

export interface AttitudeState {
  roll: number;
  pitch: number;
  yaw: number;
  rollHistory: TimeSeriesPoint[];
  pitchHistory: TimeSeriesPoint[];
  yawErrorHistory: TimeSeriesPoint[];
}

export interface TaskState {
  label: string;
  segment: string;
  nextWpDistanceM: number;
  remainingWp: number;
  progressPct: number;
}

export interface SensorCell {
  key: string;
  label: string;
  value: string;
  lastCalDays: number;
  driftPct: number;
  status: Severity;
}

export interface UsvState {
  id: string;
  selected: boolean;
  mode: UsvMode;
  position: LatLngTuple;
  speedMps: number;
  headingDeg: number;
  battery: BatteryState;
  attitude: AttitudeState;
  task: TaskState;
  sensors: SensorCell[];
  trail: LatLngTuple[];
  yolo: {
    label: string;
    confidence: number;
    locked: boolean;
    box: {
      top: number;
      left: number;
      width: number;
      height: number;
    };
  };
}
