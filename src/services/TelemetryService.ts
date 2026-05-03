import { ReconnectingSSE } from '@/agents/ReconnectingSSE';
import { useRootStore } from '@/core/StateStore';
import type { TelemetryState } from '@/core/types/telemetry';
import type { UsvState } from '@/core/types/usv';
import { pushBounded, randomBetween } from '@/utils/math';

export class TelemetryService {
  private missionTimer: number | null = null;
  private twinTimer: number | null = null;
  private telemetryStream: ReconnectingSSE | null = null;

  start(): void {
    const store = useRootStore();
    this.stop();

    this.missionTimer = window.setInterval(() => {
      store.setMissionTime(Math.floor((Date.now() - store.system.missionStartedAt) / 1000));
    }, 1000);

    this.telemetryStream = new ReconnectingSSE(`/api/agent/sessions/${encodeURIComponent(store.agent.sessionId)}/telemetry-stream`, {
      maxRetries: 10,
      onEvent: (event) => {
        if (event.type !== 'telemetry.snapshot') return;
        const telemetry = event.data.telemetry ?? event.data;
        store.setTelemetry(telemetry as TelemetryState);
      },
      onError: (error) => {
        store.addFeed({ role: 'system', severity: 'warn', content: `遥测流连接异常：${error.message}` });
      },
    });
    void this.telemetryStream.connect(undefined, 'GET');

    this.twinTimer = window.setInterval(() => {
      if (!store.system.isBooted || store.system.alertLevel === 'critical') return;
      const usv = store.fleet['USV-01'];
      const position = [
        usv.position[0] + (Math.random() - 0.5) * 0.00003,
        usv.position[1] + Math.random() * 0.00004,
      ] as [number, number];
      const heading = 145 + randomBetween(-2, 2);
      const now = Date.now();
      const next: Partial<UsvState> = {
        position,
        headingDeg: heading,
        speedMps: Number(randomBetween(1.05, 1.36).toFixed(2)),
        attitude: {
          roll: Number(randomBetween(-1.2, 1.2).toFixed(1)),
          pitch: Number(randomBetween(-1.8, 0.8).toFixed(1)),
          yaw: Number(heading.toFixed(1)),
          rollHistory: pushBounded(usv.attitude.rollHistory, { timestamp: now, value: randomBetween(-1.1, 1.1) }, 32),
          pitchHistory: pushBounded(usv.attitude.pitchHistory, { timestamp: now, value: randomBetween(-1.6, 0.8) }, 32),
          yawErrorHistory: pushBounded(usv.attitude.yawErrorHistory, { timestamp: now, value: randomBetween(-2.5, 2.5) }, 32),
        },
        yolo: {
          ...usv.yolo,
          confidence: Number(randomBetween(0.85, 0.9).toFixed(2)),
        },
        trail: pushBounded(usv.trail, position, 34),
      };
      store.updateUsv('USV-01', next);
    }, 1200);
  }

  stop(): void {
    [this.missionTimer, this.twinTimer].forEach((timer) => {
      if (timer) window.clearInterval(timer);
    });
    this.missionTimer = null;
    this.twinTimer = null;
    this.telemetryStream?.close();
    this.telemetryStream = null;
  }
}

export const telemetryService = new TelemetryService();
