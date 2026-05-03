export type RtkFixStatus = 'FIXED' | 'FLOAT' | 'SINGLE';

export interface Satellite {
  id: string;
  constellation: 'GPS' | 'BDS' | 'GAL' | 'GLO';
  azimuth: number;
  elevation: number;
  cn0: number;
}

export interface RtkTelemetry {
  status: RtkFixStatus;
  precisionCm: number;
  hdop: number;
  satellites: {
    gps: number;
    bds: number;
    gal: number;
    glo: number;
  };
  skyPlot: Satellite[];
}

export interface LinkTelemetry {
  primary: {
    name: '4G';
    rssiDbm: number;
    latencyMs: number;
    packetLossPct: number;
  };
  backup: {
    name: 'BDS-SMS';
    online: boolean;
    latencyMs: number;
  };
  heartbeatMs: number;
}

export interface EdgeTelemetry {
  loadPct: number;
  temperatureC: number;
  fps: number;
  targetFps: number;
  model: string;
  queueDepth: number;
  queueCapacity: number;
}

export interface WeatherTelemetry {
  windDirection: string;
  windDeg: number;
  windSpeedMps: number;
  pressureHpa: number;
  rainfallMm: number;
  visibilityKm: number;
  condition: string;
}

export interface TelemetryState {
  rtk: RtkTelemetry;
  link: LinkTelemetry;
  edge: EdgeTelemetry;
  weather: WeatherTelemetry;
}
