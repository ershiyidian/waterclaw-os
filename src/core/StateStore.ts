import { defineStore } from 'pinia';
import { MAP_CENTER, SENSOR_KEYS } from '@/config/constants';
import { MCP_SERVERS } from '@/config/mcp-servers';
import type { AlertItem } from './types/alert';
import type { AgentMode, AgentStatus, ApprovalAction, ApprovalActionInput, FeedMessage, ReActStep, ToolCall } from './types/agent';
import type { ChartTab } from './types/chart';
import type { AlertLevel, LatLngTuple } from './types/common';
import type { McpServerStatus } from './types/mcp';
import type { TelemetryState } from './types/telemetry';
import type { SensorCell, UsvMode, UsvState } from './types/usv';

function id(prefix: string): string {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

function makeHistory(seed: number): Array<{ timestamp: number; value: number }> {
  const now = Date.now();
  return Array.from({ length: 28 }, (_, i) => ({
    timestamp: now - (28 - i) * 1000,
    value: seed + Math.sin(i * 0.45) * 1.5 + Math.random() * 0.5,
  }));
}

function makeSensors(offset = 0): SensorCell[] {
  return SENSOR_KEYS.map(([key, label, value], index) => ({
    key,
    label,
    value,
    lastCalDays: 2 + ((index + offset) % 7),
    driftPct: Number((0.6 + ((index + offset) % 4) * 0.7).toFixed(1)),
    status: index === 4 && offset > 0 ? 'warn' : 'ok',
  }));
}

function makeInitialTelemetry(): TelemetryState {
  return {
    rtk: {
      status: 'FIXED',
      precisionCm: 1.2,
      hdop: 0.8,
      satellites: { gps: 12, bds: 8, gal: 6, glo: 3 },
      skyPlot: Array.from({ length: 22 }, (_, i) => ({
        id: `${i + 1}`,
        constellation: (['GPS', 'BDS', 'GAL', 'GLO'] as const)[i % 4],
        azimuth: (i * 47) % 360,
        elevation: 18 + ((i * 13) % 68),
        cn0: 28 + ((i * 7) % 22),
      })),
    },
    link: {
      primary: { name: '4G', rssiDbm: -67, latencyMs: 17, packetLossPct: 0.2 },
      backup: { name: 'BDS-SMS', online: true, latencyMs: 780 },
      heartbeatMs: 17,
    },
    edge: {
      loadPct: 42,
      temperatureC: 54,
      fps: 28,
      targetFps: 30,
      model: 'YOLOv8s-water-v2.3',
      queueDepth: 0,
      queueCapacity: 16,
    },
    weather: {
      windDirection: '东南',
      windDeg: 130,
      windSpeedMps: 2.4,
      pressureHpa: 1017,
      rainfallMm: 0,
      visibilityKm: 8.6,
      condition: '晴',
    },
  };
}

function makeInitialFleet(): Record<string, UsvState> {
  return {
    'USV-01': {
      id: 'USV-01',
      selected: true,
      mode: 'AUTO',
      position: [31.2755918, 121.3875979],
      speedMps: 1.2,
      headingDeg: 145,
      battery: { pct: 85, powerW: 412, remainingMin: 167, temperatureC: 38, cycles: 187, cycleLimit: 2000 },
      attitude: {
        roll: 0.2,
        pitch: -1.1,
        yaw: 145,
        rollHistory: makeHistory(0),
        pitchHistory: makeHistory(-1),
        yawErrorHistory: makeHistory(1),
      },
      task: {
        label: '桃浦河中段常规巡航',
        segment: 'WP3 -> WP4',
        nextWpDistanceM: 127,
        remainingWp: 5,
        progressPct: 38,
      },
      sensors: makeSensors(0),
      trail: [
        [31.2765367, 121.3871368],
        [31.2769236, 121.386958],
        [31.2755918, 121.3875979],
      ],
      yolo: {
        label: 'Plastic',
        confidence: 0.89,
        locked: false,
        box: { top: 48, left: 38, width: 28, height: 32 },
      },
    },
    'USV-02': {
      id: 'USV-02',
      selected: false,
      mode: 'HOLD',
      position: [31.2803058, 121.3872326],
      speedMps: 0.1,
      headingDeg: 90,
      battery: { pct: 92, powerW: 96, remainingMin: 221, temperatureC: 34, cycles: 121, cycleLimit: 2000 },
      attitude: {
        roll: -0.1,
        pitch: 0.2,
        yaw: 90,
        rollHistory: makeHistory(0),
        pitchHistory: makeHistory(0),
        yawErrorHistory: makeHistory(0),
      },
      task: {
        label: 'DP-01 排口蹲守定点监测',
        segment: 'DP-01 station keep',
        nextWpDistanceM: 0,
        remainingWp: 1,
        progressPct: 100,
      },
      sensors: makeSensors(2),
      trail: [
        [31.2814214, 121.3875644],
        [31.2803058, 121.3872326],
      ],
      yolo: {
        label: 'Riverbank',
        confidence: 0.76,
        locked: false,
        box: { top: 40, left: 52, width: 24, height: 28 },
      },
    },
  };
}

export const useRootStore = defineStore('root', {
  state: () => ({
    system: {
      isBooted: false,
      missionStartedAt: Date.now(),
      missionTimeSec: 0,
      theme: 'dark',
      alertLevel: 'normal' as AlertLevel,
      debugOpen: false,
    },
    fleet: makeInitialFleet(),
    alerts: [] as AlertItem[],
    telemetry: makeInitialTelemetry(),
    chart: {
      activeTab: 'water' as ChartTab,
      emergencySpike: false,
      selectedRange: null as [number, number] | null,
    },
    agent: {
      sessionId: `wc-${Date.now().toString(36)}`,
      mode: 'conversation' as AgentMode,
      status: 'idle' as AgentStatus,
      currentMission: '桃浦河常态巡航 / Routine Patrol',
      tokenUsage: { input: 2400, output: 1800, costCny: 0.08 },
      pendingApproval: null as ApprovalAction | null,
      reactSteps: [] as ReActStep[],
      toolCalls: [] as ToolCall[],
      memory: {
        shortTerm: {
          active_reach: 'TP-01 ~ TP-05',
          current_alert: 'none',
          patrol_policy: 'III类水目标，5分钟滚动评价',
        },
        longTerm: {
          'DP-03_history': '过去30天3次夜间浊度异常，2次与化工园雨水井相关',
          'USV-01_profile': '高速采样艇，适合上游拦截和近岸视觉确认',
          'USV-02_profile': '低速续航艇，适合断面哨位和长时间蹲守',
        },
        toolCache: [
          { key: 'gb3838:TP-03:last5min', value: 'III类达标', updatedAt: Date.now() - 90_000 },
          { key: 'weather:taopu:now', value: '东南风2级，无降雨', updatedAt: Date.now() - 70_000 },
        ],
      },
    },
    mcp: MCP_SERVERS.map((server) => ({ ...server })) as McpServerStatus[],
    feed: [] as FeedMessage[],
    map: {
      center: MAP_CENTER as LatLngTuple,
      zoom: 16,
      focusTarget: null as LatLngTuple | null,
      activeLayers: ['river-route', 'drain-points', 'stations', 'usv'] as string[],
      emergencyDrainId: null as string | null,
      spreadVisible: false,
      blockadeVisible: false,
      clusterVisible: false,
    },
  }),
  actions: {
    markBooted() {
      this.system.isBooted = true;
      this.agent.status = 'idle';
      this.addFeed({
        role: 'assistant',
        severity: 'info',
        content:
          '系统自检完成。监测区域：桃浦河段 TP-01 ~ TP-05，覆盖排口 DP-01 ~ DP-05。USV-01 自主巡航，USV-02 在 DP-01 定点蹲守。前端 AgentClient、后端 Agent Host、MCP Rack 与 Skill Registry 已进入待命状态。',
      });
    },
    setMissionTime(seconds: number) {
      this.system.missionTimeSec = seconds;
    },
    setChartTab(tab: ChartTab) {
      this.chart.activeTab = tab;
    },
    setAgentMode(mode: AgentMode) {
      this.agent.mode = mode;
    },
    setAgentStatus(status: AgentStatus) {
      this.agent.status = status;
    },
    setTelemetry(next: TelemetryState) {
      this.telemetry = next;
    },
    updateUsv(idValue: string, patch: Partial<UsvState>) {
      this.fleet[idValue] = { ...this.fleet[idValue], ...patch };
    },
    setUsvMode(idValue: string, mode: UsvMode) {
      this.fleet[idValue].mode = mode;
    },
    setUsvPosition(idValue: string, position: LatLngTuple, headingDeg?: number, trail?: LatLngTuple[]) {
      const usv = this.fleet[idValue];
      usv.position = position;
      if (typeof headingDeg === 'number') usv.headingDeg = headingDeg;
      if (trail) usv.trail = trail;
    },
    addFeed(message: Omit<FeedMessage, 'id' | 'timestamp'>) {
      this.feed.push({ id: id('msg'), timestamp: Date.now(), ...message });
    },
    addAlert(alert: Omit<AlertItem, 'id' | 'createdAt' | 'status'>) {
      this.alerts.unshift({ id: id('alert'), createdAt: Date.now(), status: 'open', ...alert });
      this.system.alertLevel = alert.level;
    },
    addReActStep(step: Omit<ReActStep, 'id'>) {
      this.agent.reactSteps.push({ id: id('react'), ...step });
    },
    updateReActStep(stepId: string, patch: Partial<ReActStep>) {
      const step = this.agent.reactSteps.find((item) => item.id === stepId);
      if (step) Object.assign(step, patch);
    },
    addToolCall(call: Omit<ToolCall, 'id' | 'startedAt'> & { id?: string; startedAt?: number }) {
      const idValue = call.id ?? id('tool');
      this.agent.toolCalls.push({ ...call, id: idValue, startedAt: call.startedAt ?? Date.now() });
      this.addFeed({ role: 'tool_call', toolCallId: idValue });
      return idValue;
    },
    updateToolCall(callId: string, patch: Partial<ToolCall>) {
      const call = this.agent.toolCalls.find((item) => item.id === callId);
      if (call) Object.assign(call, patch);
    },
    requestApproval(action: ApprovalActionInput) {
      const approval: ApprovalAction = { ...action, id: action.id ?? id('approval'), requestedAt: action.requestedAt ?? Date.now() };
      this.agent.pendingApproval = approval;
      this.agent.status = 'awaiting_approval';
      this.addFeed({ role: 'approval', approvalId: approval.id });
      return approval.id;
    },
    clearApproval() {
      this.agent.pendingApproval = null;
      this.agent.status = 'idle';
    },
    updateMcp(serverId: string, patch: Partial<McpServerStatus>) {
      const server = this.mcp.find((item) => item.id === serverId);
      if (server) Object.assign(server, patch);
    },
    replaceMcp(servers: McpServerStatus[]) {
      this.mcp = servers.map((server) => ({ ...server }));
    },
    registerMcpCall(serverId: string) {
      const server = this.mcp.find((item) => item.id === serverId);
      if (!server) return;
      server.callCount += 1;
      server.lastCallAt = Date.now();
      server.status = 'calling';
      setTimeout(() => {
        if (server.status === 'calling') server.status = 'connected';
      }, 600);
    },
    setBlockadeVisible(visible: boolean) {
      this.map.blockadeVisible = visible;
    },
    resetIncidentProjection() {
      this.system.alertLevel = 'normal';
      this.chart.emergencySpike = false;
      this.map.emergencyDrainId = null;
      this.map.focusTarget = MAP_CENTER;
      this.map.clusterVisible = false;
      this.map.spreadVisible = false;
      this.map.blockadeVisible = false;
      this.agent.currentMission = '桃浦河常态巡航 / Routine Patrol';
      this.agent.status = 'idle';
      this.agent.pendingApproval = null;
      this.agent.reactSteps = [];
      this.agent.toolCalls = [];
      this.agent.memory.shortTerm.current_alert = 'none';
      this.fleet = makeInitialFleet();
      this.addFeed({ role: 'system', severity: 'ok', content: '事件已归档，系统恢复常态巡航模式。' });
    },
  },
});
