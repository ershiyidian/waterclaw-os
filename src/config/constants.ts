import type { LatLngTuple } from '@/core/types/common';

export const MAP_CENTER: LatLngTuple = [31.2755918, 121.3875979];

export const TAOPU_RIVER_OSM_SOURCE = {
  osmWayId: 768410671,
  name: '桃浦河',
  tag: 'waterway=river',
  fetchedAt: '2026-05-03T09:06:05Z',
  source: 'OpenStreetMap Overpass API',
} as const;

export const RIVER_CORRIDOR_RADIUS_M = 32;

export const RIVER_PATH: LatLngTuple[] = [
  [31.26708, 121.3916897],
  [31.26771, 121.3914003],
  [31.2680638, 121.3911801],
  [31.2684759, 121.3909195],
  [31.2688867, 121.3907479],
  [31.2701339, 121.3901986],
  [31.2711829, 121.3897608],
  [31.2717185, 121.3894003],
  [31.2725034, 121.3890913],
  [31.2728189, 121.3889883],
  [31.273237, 121.3887823],
  [31.2738679, 121.3883618],
  [31.2742677, 121.38817],
  [31.2748436, 121.3879412],
  [31.2755918, 121.3875979],
  [31.2765367, 121.3871368],
  [31.2769236, 121.386958],
  [31.277235, 121.3868769],
  [31.2775884, 121.3868487],
  [31.2780132, 121.3869149],
  [31.280084, 121.3871475],
  [31.2803058, 121.3872326],
  [31.2814214, 121.3875644],
  [31.2816263, 121.3876156],
];

export const DRAIN_POINTS = [
  { id: 'DP-01', name: '排口A', pos: [31.2803058, 121.3872326] as LatLngTuple, enterprise: '桃浦北岸物流园' },
  { id: 'DP-02', name: '排口B', pos: [31.2775884, 121.3868487] as LatLngTuple, enterprise: '新杨泵站支渠' },
  { id: 'DP-03', name: '排口C', pos: [31.2728189, 121.3889883] as LatLngTuple, enterprise: '沪西精细化工三厂' },
  { id: 'DP-04', name: '排口D', pos: [31.2711829, 121.3897608] as LatLngTuple, enterprise: '真南工业仓储' },
  { id: 'DP-05', name: '排口E', pos: [31.2688867, 121.3907479] as LatLngTuple, enterprise: '市政雨水口' },
];

export const STATIONS = [
  { id: 'TP-01', pos: [31.2814214, 121.3875644] as LatLngTuple, classTarget: 'III' },
  { id: 'TP-02', pos: [31.2780132, 121.3869149] as LatLngTuple, classTarget: 'III' },
  { id: 'TP-03', pos: [31.2755918, 121.3875979] as LatLngTuple, classTarget: 'III' },
  { id: 'TP-04', pos: [31.2725034, 121.3890913] as LatLngTuple, classTarget: 'III' },
  { id: 'TP-05', pos: [31.2701339, 121.3901986] as LatLngTuple, classTarget: 'IV' },
];

export const BOOT_STEPS = [
  { label: 'Config registry loaded', pct: 8 },
  { label: 'State store schema validated', pct: 18 },
  { label: 'Leaflet GIS service READY', pct: 30 },
  { label: 'ECharts analytic renderer READY', pct: 42 },
  { label: 'MCP rack: backend status linked', pct: 56 },
  { label: 'Skill registry: 8 tools mounted', pct: 70 },
  { label: 'USV-01 handshake ACK', pct: 82 },
  { label: 'USV-02 handshake ACK', pct: 92 },
  { label: 'System nominal - entering main loop', pct: 100 },
];

export const SENSOR_KEYS = [
  ['DO', '溶解氧', '6.5 mg/L'],
  ['pH', '酸碱度', '7.2'],
  ['ORP', '氧化还原', '+186 mV'],
  ['EC', '电导率', '452 uS/cm'],
  ['Turb', '浊度', '42 NTU'],
  ['NH3N', '氨氮', '0.8 mg/L'],
  ['COD', 'CODMn', '4.2 mg/L'],
  ['Temp', '水温', '19.4 C'],
  ['VOCs', '挥发物', '0.7 mg/m3'],
  ['PM25', 'PM2.5', '33 ug/m3'],
] as const;
