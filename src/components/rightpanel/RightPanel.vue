<template>
  <HudPanel :panel-class="['right-panel', { 'awaiting-approval': store.agent.status === 'awaiting_approval' }]">
    <CopilotHeader :status="store.agent.status" :mission="store.agent.currentMission" :usage="store.agent.tokenUsage" />
    <McpRack :servers="store.mcp" />
    <ModeSwitcher :active="store.agent.mode" @change="store.setAgentMode" />

    <ConversationFeed
      v-if="store.agent.mode === 'conversation'"
      :feed="store.feed"
      :tool-calls="store.agent.toolCalls"
      :pending-approval="store.agent.pendingApproval"
      @approve="approvePending"
      @reject="rejectPending"
      @replay="replay"
    />
    <PlanTree v-else-if="store.agent.mode === 'plan'" :steps="store.agent.reactSteps" :tool-calls="store.agent.toolCalls" />
    <TraceTimeline v-else :tool-calls="store.agent.toolCalls" />

    <MemoryInspector :memory="store.agent.memory" />
    <CommandInput
      :show-reset="store.system.alertLevel !== 'normal'"
      @submit="handleSubmit"
      @gb="showGBReport"
      @fleet="showFleetStatus"
      @reset="reset"
    />
  </HudPanel>
</template>

<script setup lang="ts">
import HudPanel from '@/components/common/HudPanel.vue';
import { agentClient } from '@/agents/AgentClient';
import { useAgentCommands } from '@/composables/useAgentCommands';
import { useRootStore } from '@/core/StateStore';
import CommandInput from './input/CommandInput.vue';
import ConversationFeed from './feed/ConversationFeed.vue';
import CopilotHeader from './CopilotHeader.vue';
import McpRack from './McpRack.vue';
import MemoryInspector from './MemoryInspector.vue';
import ModeSwitcher from './ModeSwitcher.vue';
import PlanTree from './feed/PlanTree.vue';
import TraceTimeline from './feed/TraceTimeline.vue';

const store = useRootStore();
const agentCommands = useAgentCommands();

function handleSubmit(text: string): void {
  store.addFeed({ role: 'user', content: text });
  if (text.startsWith('/gb3838')) {
    void showGBReport().catch((error: unknown) => {
      const message = error instanceof Error ? error.message : String(error);
      store.addFeed({ role: 'assistant', severity: 'warn', content: `GB3838 请求失败：${message}` });
    });
    return;
  }
  void agentClient.sendMessage(text).catch((error: unknown) => {
    const message = error instanceof Error ? error.message : String(error);
    store.setAgentStatus('idle');
    store.addFeed({
      role: 'assistant',
      severity: 'warn',
      content: `Agent Host 调用失败：${message}。请确认后端已通过 Conda 环境启动，并检查 backend/.env 的模型供应商配置。`,
    });
  });
}

async function showGBReport(): Promise<void> {
  await agentCommands.execute('gb3838-report');
}

function showFleetStatus(): void {
  store.addFeed({
    role: 'assistant',
    severity: 'info',
    content:
      '艇群在线状态\n\n' +
      `USV-01 ■ ${store.fleet['USV-01'].mode} · ${store.fleet['USV-01'].battery.pct}% · ${store.fleet['USV-01'].task.segment}\n` +
      `USV-02 ■ ${store.fleet['USV-02'].mode} · ${store.fleet['USV-02'].battery.pct}% · ${store.fleet['USV-02'].task.segment}\n\n` +
      '通信链路正常，RTK 定位 FIXED，边缘推理队列未积压。',
  });
}

function reset(): void {
  store.resetIncidentProjection();
}

function approvePending(code?: string): void {
  void agentClient.approvePending(code).catch((error: unknown) => {
    const message = error instanceof Error ? error.message : String(error);
    store.addFeed({ role: 'system', severity: 'warn', content: `审批提交失败：${message}` });
  });
}

function rejectPending(): void {
  void agentClient.rejectPending().catch((error: unknown) => {
    const message = error instanceof Error ? error.message : String(error);
    store.addFeed({ role: 'system', severity: 'warn', content: `审批拒绝失败：${message}` });
  });
}

function replay(callId: string): void {
  const call = store.agent.toolCalls.find((item) => item.id === callId);
  if (!call) return;
  void agentClient.sendMessage(`Replay tool ${call.toolName} with args ${JSON.stringify(call.args)}`);
}
</script>
