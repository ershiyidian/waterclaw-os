export const GB3838_TURBIDITY_BANDS = [
  { name: 'I', from: 0, to: 20, color: 'rgba(16,185,129,0.08)' },
  { name: 'II', from: 20, to: 50, color: 'rgba(52,211,153,0.08)' },
  { name: 'III', from: 50, to: 100, color: 'rgba(56,189,248,0.07)' },
  { name: 'IV', from: 100, to: 180, color: 'rgba(245,158,11,0.07)' },
  { name: 'V', from: 180, to: 320, color: 'rgba(239,68,68,0.07)' },
];

export const GB3838_LIMITS = {
  ph: { min: 6, max: 9 },
  dissolvedOxygen: { min: 5, unit: 'mg/L' },
  nh3n: { max: 1, unit: 'mg/L' },
  codMn: { max: 6, unit: 'mg/L' },
  turbidity: { max: 100, unit: 'NTU' },
};

export const LINK_LATENCY_WARN_MS = 200;
export const LINK_LATENCY_CRITICAL_MS = 500;
export const BATTERY_TEMP_WARN_C = 50;
export const PITCH_WARN_DEG = 5;
export const YAW_ERROR_WARN_DEG = 10;
