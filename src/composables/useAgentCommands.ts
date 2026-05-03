import { agentClient, type AgentTurnPayload } from '@/agents/AgentClient';
import { useRootStore } from '@/core/StateStore';
import type { UsvState } from '@/core/types/usv';

interface AgentCommand {
  id: string;
  label: string;
  buildPayload: () => AgentTurnPayload;
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

function basePayload(message: string, mission?: string): AgentTurnPayload {
  const store = useRootStore();
  return {
    message,
    mission: mission ?? store.agent.currentMission,
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
}

export function useAgentCommands() {
  const commands: Record<string, AgentCommand> = {
    'gb3838-report': {
      id: 'gb3838-report',
      label: 'GB3838 实时评价',
      buildPayload: () => basePayload('/gb3838', 'GB3838 III类水评价'),
    },
    'fleet-status': {
      id: 'fleet-status',
      label: '艇群状态核验',
      buildPayload: () => basePayload('/fleet-status 核验当前艇群、电量、链路和任务状态。'),
    },
  };

  async function execute(commandId: string): Promise<void> {
    const store = useRootStore();
    const command = commands[commandId];
    if (!command) throw new Error(`Unknown command: ${commandId}`);
    store.addFeed({ role: 'user', content: command.label });
    await agentClient.sendPrepared(command.buildPayload());
  }

  return { commands, execute };
}
