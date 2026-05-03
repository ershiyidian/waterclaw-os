import type { SkillCategory, ToolCall } from '@/core/types/agent';
import type { McpServerStatus } from '@/core/types/mcp';
import type { TelemetryState } from '@/core/types/telemetry';
import type { UsvState } from '@/core/types/usv';
import { useRootStore } from '@/core/StateStore';
import { ReconnectingSSE, type AgentEvent } from './ReconnectingSSE';

export interface AgentTurnPayload {
  message: string;
  mission: string;
  alert_level: string;
  telemetry: TelemetryState;
  fleet: Array<{
    id: string;
    mode: string;
    battery_pct: number;
    task: string;
    segment: string;
    position: number[];
    speed_mps: number;
    heading_deg: number;
  }>;
  memory: unknown;
  recent_messages: Array<{
    role: string;
    content?: string;
    severity?: string;
    timestamp: number;
  }>;
}

interface BackendApproval {
  id: string;
  title: string;
  description: string;
  riskLevel: 'safe' | 'confirm' | 'critical';
  autoCancelSeconds: number;
  requestedAt: number;
  command: string;
  payload: Record<string, unknown>;
  requiresHoldMs?: number;
  requiresCode?: boolean;
}

type ControlAction = 'rtl_usv' | 'request_estop';

interface StreamOptions {
  signal?: AbortSignal;
}

function usvSnapshot(usv: UsvState): AgentTurnPayload['fleet'][number] {
  return {
    id: usv.id,
    mode: usv.mode,
    battery_pct: usv.battery.pct,
    task: usv.task.label,
    segment: usv.task.segment,
    position: usv.position,
    speed_mps: usv.speedMps,
    heading_deg: usv.headingDeg,
  };
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' ? (value as Record<string, unknown>) : {};
}

export class AgentClient {
  async sendMessage(message: string): Promise<void> {
    const store = useRootStore();
    const payload: AgentTurnPayload = {
      message,
      mission: store.agent.currentMission,
      alert_level: store.system.alertLevel,
      telemetry: store.telemetry,
      fleet: Object.values(store.fleet).map(usvSnapshot),
      memory: store.agent.memory,
      recent_messages: store.feed.slice(-8).map((item) => ({
        role: item.role,
        content: item.content,
        severity: item.severity,
        timestamp: item.timestamp,
      })),
    };
    await this.sendPrepared(payload);
  }

  async sendPrepared(payload: AgentTurnPayload): Promise<void> {
    const store = useRootStore();
    await this.stream(`/api/agent/sessions/${encodeURIComponent(store.agent.sessionId)}/turn`, payload as unknown as Record<string, unknown>);
  }

  async approvePending(code = ''): Promise<void> {
    const store = useRootStore();
    const approval = store.agent.pendingApproval;
    if (!approval) return;
    await this.stream(`/api/agent/sessions/${encodeURIComponent(store.agent.sessionId)}/approvals/${encodeURIComponent(approval.id)}/approve`, {
      code,
    });
  }

  async rejectPending(): Promise<void> {
    const store = useRootStore();
    const approval = store.agent.pendingApproval;
    if (!approval) return;
    await this.stream(`/api/agent/sessions/${encodeURIComponent(store.agent.sessionId)}/approvals/${encodeURIComponent(approval.id)}/reject`, {
      reason: 'operator rejected',
    });
  }

  async requestControl(action: ControlAction, args: { usvs: string[]; reason: string }): Promise<void> {
    const store = useRootStore();
    await this.stream(`/api/agent/sessions/${encodeURIComponent(store.agent.sessionId)}/control/request`, {
      action,
      ...args,
    });
  }

  async refreshMcpStatus(): Promise<void> {
    const store = useRootStore();
    const response = await fetch('/api/agent/mcp/status');
    if (!response.ok) return;
    const data = (await response.json()) as { servers?: McpServerStatus[] };
    if (Array.isArray(data.servers)) store.replaceMcp(data.servers);
  }

  private async stream(url: string, payload: Record<string, unknown>, options: StreamOptions = {}): Promise<void> {
    const stream = new ReconnectingSSE(url, {
      signal: options.signal,
      maxRetries: 5,
      onEvent: (event) => this.applyEvent(event),
      onError: (error) => {
        const store = useRootStore();
        store.addFeed({ role: 'system', severity: 'warn', content: `SSE 连接中断，正在尝试重连：${error.message}` });
      },
    });
    await stream.connect(payload, 'POST');
  }

  private applyEvent(event: AgentEvent): void {
    const store = useRootStore();
    const traceId = event.data._trace_id;
    if (typeof traceId === 'string') console.debug('[WaterClaw trace]', traceId, event.type);
    if (event.type === 'state.patch') {
      const agent = asRecord(event.data.agent);
      if (typeof agent.status === 'string') store.setAgentStatus(agent.status as never);
      if (typeof agent.currentMission === 'string') store.agent.currentMission = agent.currentMission;
      return;
    }
    if (event.type === 'usage.patch') {
      const usage = asRecord(event.data.tokenUsage);
      store.agent.tokenUsage.input = Number(usage.input ?? store.agent.tokenUsage.input);
      store.agent.tokenUsage.output = Number(usage.output ?? store.agent.tokenUsage.output);
      store.agent.tokenUsage.costCny = Number(usage.costCny ?? store.agent.tokenUsage.costCny);
      return;
    }
    if (event.type === 'mcp.status') {
      const servers = event.data.servers;
      if (Array.isArray(servers)) store.replaceMcp(servers as McpServerStatus[]);
      return;
    }
    if (event.type === 'react.step') {
      store.addReActStep({
        thought: String(event.data.thought ?? ''),
        action: typeof event.data.action === 'string' ? event.data.action : undefined,
        observation: typeof event.data.observation === 'string' ? event.data.observation : undefined,
        status: (event.data.status as never) ?? 'success',
      });
      return;
    }
    if (event.type === 'tool.started') {
      const call = asRecord(event.data.call);
      const status = String(call.status ?? 'running');
      store.addToolCall({
        id: String(call.id),
        toolName: String(call.toolName),
        category: String(call.category ?? 'analytics') as SkillCategory,
        status: (['pending', 'running', 'success', 'failed', 'awaiting_approval'].includes(status) ? status : 'running') as never,
        args: asRecord(call.args),
        riskLevel: (call.riskLevel as never) ?? 'safe',
        replayable: Boolean(call.replayable),
        mcpServer: typeof call.mcpServer === 'string' ? call.mcpServer : undefined,
      });
      return;
    }
    if (event.type === 'tool.finished') {
      store.updateToolCall(String(event.data.callId), {
        status: 'success',
        result: event.data.result,
        endedAt: Date.now(),
        durationMs: Number(event.data.durationMs ?? 0),
      } satisfies Partial<ToolCall>);
      return;
    }
    if (event.type === 'tool.failed') {
      store.updateToolCall(String(event.data.callId), {
        status: 'failed',
        error: String(event.data.error ?? 'Tool failed'),
        endedAt: Date.now(),
        durationMs: Number(event.data.durationMs ?? 0),
      });
      return;
    }
    if (event.type === 'tool.awaiting_approval') {
      store.updateToolCall(String(event.data.callId), { status: 'awaiting_approval' });
      return;
    }
    if (event.type === 'approval.required') {
      const approval = event.data.approval as BackendApproval;
      const exists = store.agent.pendingApproval?.id === approval.id || store.feed.some((item) => item.approvalId === approval.id);
      if (exists) return;
      store.requestApproval({
        id: approval.id,
        title: approval.title,
        description: approval.description,
        riskLevel: approval.riskLevel,
        autoCancelSeconds: approval.autoCancelSeconds,
        requestedAt: approval.requestedAt,
        command: approval.command,
        payload: approval.payload,
        requiresHoldMs: approval.requiresHoldMs,
        requiresCode: Boolean(approval.requiresCode),
      });
      return;
    }
    if (event.type === 'approval.resolved') {
      const status = String(event.data.status ?? '');
      if (status === 'failed') {
        store.setAgentStatus('awaiting_approval');
        store.addFeed({
          role: 'system',
          severity: 'warn',
          content: `审批失败：${String(event.data.error ?? '未知错误')}。控制动作未执行。`,
        });
      } else {
        store.clearApproval();
      }
      return;
    }
    if (event.type === 'message.delta') return;
    if (event.type === 'message.final') {
      const content = String(event.data.content ?? '').trim();
      if (content) {
        store.addFeed({
          role: (event.data.role as never) ?? 'assistant',
          severity: (event.data.severity as never) ?? 'ai',
          content,
        });
      }
    }
    if (event.type === 'telemetry.snapshot') {
      const telemetry = event.data.telemetry ?? event.data;
      store.setTelemetry(telemetry as TelemetryState);
    }
  }

}

export const agentClient = new AgentClient();
