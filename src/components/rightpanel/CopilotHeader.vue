<template>
  <div class="copilot-head">
    <div class="agent-avatar" :class="status">
      <div class="agent-ring" />
      <Bot :size="16" />
    </div>
    <div class="copilot-copy">
      <div class="copilot-title">WaterClaw AI Copilot</div>
      <div class="copilot-sub">Mission: {{ mission }}</div>
    </div>
    <div class="token-meter">
      {{ ((usage.input + usage.output) / 1000).toFixed(1) }}k tokens · ¥{{ usage.costCny.toFixed(2) }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { Bot } from 'lucide-vue-next';
import type { AgentStatus, TokenUsage } from '@/core/types/agent';

defineProps<{
  status: AgentStatus;
  mission: string;
  usage: TokenUsage;
}>();
</script>

<style scoped>
.copilot-head {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  padding: 12px 14px 10px;
  border-bottom: 1px solid var(--border-subtle);
}

.agent-avatar {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  color: var(--sem-ai);
  background: linear-gradient(135deg, rgba(129, 140, 248, 0.15), rgba(56, 189, 248, 0.1));
  border: 1px solid rgba(129, 140, 248, 0.35);
  border-radius: 8px;
}

.agent-ring {
  position: absolute;
  inset: -4px;
  border: 1px solid transparent;
  border-top-color: rgba(129, 140, 248, 0.75);
  border-radius: 10px;
  opacity: 0;
}

.agent-avatar.thinking .agent-ring,
.agent-avatar.tool_call .agent-ring {
  opacity: 1;
  animation: agentRing 1.1s linear infinite;
}

.agent-avatar.awaiting_approval {
  color: var(--sem-warn);
  border-color: rgba(245, 158, 11, 0.5);
}

.agent-avatar.awaiting_approval .agent-ring {
  opacity: 1;
  border-top-color: var(--sem-warn);
  animation: agentRing 1.8s linear infinite;
}

.copilot-copy {
  min-width: 0;
}

.copilot-title {
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 800;
}

.copilot-sub {
  overflow: hidden;
  color: var(--text-tertiary);
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: var(--font-mono);
  font-size: 9px;
}

.token-meter {
  padding: 2px 7px;
  color: var(--text-tertiary);
  white-space: nowrap;
  background: rgba(0, 0, 0, 0.18);
  border: 1px solid var(--border-subtle);
  border-radius: 999px;
  font-family: var(--font-mono);
  font-size: 9px;
}
</style>
