import type { AirSeriesBundle, FlowSeriesBundle, HealthSeriesBundle, SeriesBundle } from '@/core/types/chart';
import { GB3838_TURBIDITY_BANDS } from '@/config/thresholds';

function timeLabels(points = 96): string[] {
  const base = new Date();
  base.setHours(base.getHours() - 8);
  return Array.from({ length: points }, (_, i) => {
    const d = new Date(base.getTime() + i * 5 * 60_000);
    return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  });
}

export function generateWaterData(spike = false): SeriesBundle {
  const times = timeLabels();
  const nowIndex = 54;
  const historical: Array<number | null> = [];
  const prediction: Array<number | null> = [];
  const predictionLow: Array<number | null> = [];
  const predictionHigh: Array<number | null> = [];
  const yesterday: Array<number | null> = [];

  for (let i = 0; i < times.length; i += 1) {
    const baseline = 38 + Math.sin(i * 0.16) * 8 + Math.cos(i * 0.07) * 3;
    const noise = Math.sin(i * 1.7) * 2.2;
    const yBase = 34 + Math.sin((i - 8) * 0.14) * 6;
    yesterday.push(Number((yBase + Math.cos(i * 0.3) * 2).toFixed(1)));
    if (i <= nowIndex) {
      historical.push(Number((baseline + noise).toFixed(1)));
      prediction.push(i === nowIndex ? Number((baseline + noise).toFixed(1)) : null);
      predictionLow.push(null);
      predictionHigh.push(null);
      continue;
    }
    historical.push(null);
    const ramp = spike ? Math.pow(i - nowIndex, 2) * 0.62 : Math.sin(i * 0.15) * 4;
    const pred = baseline + ramp;
    prediction.push(Number(pred.toFixed(1)));
    predictionLow.push(Number((pred - 8 - Math.random() * 4).toFixed(1)));
    predictionHigh.push(Number((pred + 8 + Math.random() * 5).toFixed(1)));
  }

  return { times, historical, prediction, predictionLow, predictionHigh, yesterday };
}

export function generateAirData(): AirSeriesBundle {
  const times = timeLabels();
  return {
    times,
    vocs: times.map((_, i) => Number((0.7 + Math.sin(i * 0.2) * 0.26 + Math.random() * 0.25).toFixed(2))),
    pm25: times.map((_, i) => Math.round(26 + Math.sin(i * 0.11) * 8 + Math.random() * 12)),
    yesterdayVocs: times.map((_, i) => Number((0.62 + Math.sin((i - 8) * 0.18) * 0.18).toFixed(2))),
  };
}

export function generateFlowData(): FlowSeriesBundle {
  const times = timeLabels();
  return {
    times,
    level: times.map((_, i) => Number((2.4 + Math.sin(i * 0.06) * 0.12 + Math.random() * 0.03).toFixed(2))),
    velocity: times.map((_, i) => Number((0.42 + Math.cos(i * 0.08) * 0.08 + Math.random() * 0.03).toFixed(2))),
  };
}

export function generateHealthData(): HealthSeriesBundle {
  const times = timeLabels();
  return {
    times,
    battery: times.map((_, i) => Number((96 - i * 0.11 + Math.sin(i * 0.3) * 0.4).toFixed(1))),
    temperature: times.map((_, i) => Number((35 + Math.sin(i * 0.12) * 3 + Math.random()).toFixed(1))),
    linkLatency: times.map((_, i) => Math.round(28 + Math.sin(i * 0.27) * 8 + Math.random() * 12)),
  };
}

const axisStyle = {
  axisLine: { lineStyle: { color: 'rgba(100,116,139,0.3)' } },
  axisLabel: { fontSize: 9, color: '#64748b' },
};

export function waterOption(data: SeriesBundle) {
  const markAreas = GB3838_TURBIDITY_BANDS.map((band) => [
    { yAxis: band.from, itemStyle: { color: band.color } },
    { yAxis: band.to, label: { show: true, formatter: band.name, color: 'rgba(148,163,184,0.32)', fontSize: 9 } },
  ]);
  let nowIndex = 0;
  for (let i = data.historical.length - 1; i >= 0; i -= 1) {
    if (data.historical[i] !== null) {
      nowIndex = i;
      break;
    }
  }
  return {
    backgroundColor: 'transparent',
    animationDuration: 500,
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10,18,36,0.94)',
      borderColor: 'rgba(56,189,248,0.3)',
      textStyle: { color: '#f1f5f9', fontSize: 11, fontFamily: 'Inter' },
    },
    brush: {
      toolbox: ['lineX', 'clear'],
      xAxisIndex: 0,
      brushStyle: { color: 'rgba(56,189,248,0.12)', borderColor: 'rgba(56,189,248,0.45)' },
    },
    toolbox: {
      right: 4,
      top: -4,
      iconStyle: { borderColor: 'rgba(148,163,184,0.45)' },
      emphasis: { iconStyle: { borderColor: '#38bdf8' } },
      feature: { brush: { type: ['lineX', 'clear'] } },
    },
    legend: {
      top: 0,
      right: 34,
      textStyle: { color: '#64748b', fontSize: 9 },
      itemWidth: 12,
      itemHeight: 2,
      data: ['实测浊度', 'LSTM预测', '95% CI', '昨日同期'],
    },
    grid: { top: 26, bottom: 36, left: 38, right: 16 },
    dataZoom: [
      { type: 'inside', xAxisIndex: 0, filterMode: 'none' },
      {
        type: 'slider',
        height: 14,
        bottom: 4,
        borderColor: 'rgba(148,163,184,0.16)',
        backgroundColor: 'rgba(2,6,23,0.3)',
        dataBackground: { lineStyle: { color: 'rgba(56,189,248,0.25)' }, areaStyle: { color: 'rgba(56,189,248,0.06)' } },
        fillerColor: 'rgba(56,189,248,0.08)',
        handleStyle: { color: '#38bdf8' },
        textStyle: { color: '#64748b', fontSize: 8 },
      },
    ],
    xAxis: {
      type: 'category',
      data: data.times,
      ...axisStyle,
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      name: 'NTU',
      min: 0,
      max: 320,
      nameTextStyle: { fontSize: 9, color: '#64748b' },
      axisLabel: { fontSize: 9, color: '#64748b' },
      splitLine: { lineStyle: { color: 'rgba(148,163,184,0.06)', type: 'dashed' } },
    },
    series: [
      {
        name: 'CI-Lo',
        type: 'line',
        data: data.predictionLow,
        lineStyle: { opacity: 0 },
        symbol: 'none',
        stack: 'ci',
        areaStyle: { opacity: 0 },
        tooltip: { show: false },
      },
      {
        name: '95% CI',
        type: 'line',
        data: data.predictionHigh,
        lineStyle: { opacity: 0 },
        symbol: 'none',
        stack: 'ci',
        areaStyle: { color: 'rgba(129,140,248,0.14)' },
      },
      {
        name: '昨日同期',
        type: 'line',
        data: data.yesterday,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: 'rgba(148,163,184,0.32)', width: 1 },
      },
      {
        name: '实测浊度',
        type: 'line',
        data: data.historical,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#38BDF8', width: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(56,189,248,0.15)' },
              { offset: 1, color: 'rgba(56,189,248,0)' },
            ],
          },
        },
        markArea: { silent: true, data: markAreas },
        markPoint: {
          symbolSize: 28,
          label: { fontSize: 8 },
          data: [
            { type: 'max', name: 'Max' },
            { type: 'min', name: 'Min' },
          ],
        },
      },
      {
        name: 'LSTM预测',
        type: 'line',
        data: data.prediction,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#818CF8', width: 2, type: 'dashed' },
        markLine: {
          symbol: 'none',
          label: { formatter: 'NOW', color: '#38bdf8', fontSize: 9 },
          lineStyle: { color: 'rgba(56,189,248,0.55)', type: 'dashed' },
          data: [{ xAxis: data.times[nowIndex] }],
        },
      },
      {
        name: 'III类限值',
        type: 'line',
        data: data.times.map(() => 100),
        symbol: 'none',
        lineStyle: { color: 'rgba(239,68,68,0.45)', width: 1, type: 'dotted' },
      },
    ],
  };
}

export function airOption(data: AirSeriesBundle) {
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(10,18,36,0.94)', borderColor: 'rgba(52,211,153,0.3)', textStyle: { color: '#f1f5f9', fontSize: 11 } },
    legend: { top: 0, right: 0, textStyle: { color: '#64748b', fontSize: 9 }, itemWidth: 12, itemHeight: 2 },
    grid: { top: 24, bottom: 36, left: 38, right: 46 },
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 14, bottom: 4, textStyle: { color: '#64748b', fontSize: 8 } }],
    xAxis: { type: 'category', data: data.times, ...axisStyle, splitLine: { show: false } },
    yAxis: [
      { type: 'value', name: 'mg/m3', nameTextStyle: { fontSize: 9, color: '#64748b' }, axisLabel: { fontSize: 9, color: '#64748b' }, splitLine: { lineStyle: { color: 'rgba(148,163,184,0.06)', type: 'dashed' } } },
      { type: 'value', name: 'ug/m3', nameTextStyle: { fontSize: 9, color: '#64748b' }, axisLabel: { fontSize: 9, color: '#64748b' }, splitLine: { show: false } },
    ],
    series: [
      { name: '昨日VOCs', type: 'line', data: data.yesterdayVocs, smooth: true, symbol: 'none', lineStyle: { color: 'rgba(148,163,184,0.28)', width: 1 } },
      { name: 'VOCs', type: 'line', data: data.vocs, smooth: true, symbol: 'none', yAxisIndex: 0, lineStyle: { color: '#34D399', width: 2 }, areaStyle: { color: 'rgba(52,211,153,0.1)' } },
      { name: 'PM2.5', type: 'bar', data: data.pm25, yAxisIndex: 1, barWidth: 3, itemStyle: { color: 'rgba(245,158,11,0.35)', borderRadius: [1, 1, 0, 0] } },
    ],
  };
}

export function flowOption(data: FlowSeriesBundle) {
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(10,18,36,0.94)', textStyle: { color: '#f1f5f9', fontSize: 11 } },
    legend: { top: 0, right: 0, textStyle: { color: '#64748b', fontSize: 9 }, itemWidth: 12, itemHeight: 2 },
    grid: { top: 24, bottom: 36, left: 38, right: 46 },
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 14, bottom: 4, textStyle: { color: '#64748b', fontSize: 8 } }],
    xAxis: { type: 'category', data: data.times, ...axisStyle },
    yAxis: [
      { type: 'value', name: 'm', axisLabel: { fontSize: 9, color: '#64748b' }, splitLine: { lineStyle: { color: 'rgba(148,163,184,0.06)', type: 'dashed' } } },
      { type: 'value', name: 'm/s', axisLabel: { fontSize: 9, color: '#64748b' }, splitLine: { show: false } },
    ],
    series: [
      { name: '水位', type: 'line', data: data.level, smooth: true, symbol: 'none', lineStyle: { color: '#38bdf8', width: 2 }, areaStyle: { color: 'rgba(56,189,248,0.1)' } },
      { name: '流速', type: 'line', yAxisIndex: 1, data: data.velocity, smooth: true, symbol: 'none', lineStyle: { color: '#f59e0b', width: 2 } },
    ],
  };
}

export function healthOption(data: HealthSeriesBundle) {
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(10,18,36,0.94)', textStyle: { color: '#f1f5f9', fontSize: 11 } },
    legend: { top: 0, right: 0, textStyle: { color: '#64748b', fontSize: 9 }, itemWidth: 12, itemHeight: 2 },
    grid: { top: 24, bottom: 36, left: 38, right: 46 },
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 14, bottom: 4, textStyle: { color: '#64748b', fontSize: 8 } }],
    xAxis: { type: 'category', data: data.times, ...axisStyle },
    yAxis: [
      { type: 'value', name: '%/C', axisLabel: { fontSize: 9, color: '#64748b' }, splitLine: { lineStyle: { color: 'rgba(148,163,184,0.06)', type: 'dashed' } } },
      { type: 'value', name: 'ms', axisLabel: { fontSize: 9, color: '#64748b' }, splitLine: { show: false } },
    ],
    series: [
      { name: '电量', type: 'line', data: data.battery, smooth: true, symbol: 'none', lineStyle: { color: '#34d399', width: 2 } },
      { name: '电池温度', type: 'line', data: data.temperature, smooth: true, symbol: 'none', lineStyle: { color: '#f59e0b', width: 2 } },
      { name: '链路延迟', type: 'bar', yAxisIndex: 1, data: data.linkLatency, barWidth: 3, itemStyle: { color: 'rgba(129,140,248,0.45)' } },
    ],
  };
}
