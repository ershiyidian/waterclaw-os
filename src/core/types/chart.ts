export type ChartTab = 'water' | 'air' | 'flow' | 'health';

export interface SeriesBundle {
  times: string[];
  historical: Array<number | null>;
  prediction: Array<number | null>;
  predictionLow: Array<number | null>;
  predictionHigh: Array<number | null>;
  yesterday: Array<number | null>;
}

export interface AirSeriesBundle {
  times: string[];
  vocs: number[];
  pm25: number[];
  yesterdayVocs: number[];
}

export interface FlowSeriesBundle {
  times: string[];
  level: number[];
  velocity: number[];
}

export interface HealthSeriesBundle {
  times: string[];
  battery: number[];
  temperature: number[];
  linkLatency: number[];
}
