<template>
  <div class="feed">
    <div v-for="call in toolCalls" :key="call.id" class="trace-row">
      <span class="trace-dot" :class="call.status" />
      <div class="trace-body">
        <div class="trace-title">{{ call.toolName }}</div>
        <div class="trace-meta">{{ call.mcpServer || 'local' }} · {{ call.durationMs ?? 0 }}ms · {{ call.riskLevel }}</div>
      </div>
      <span class="trace-time">{{ nowStr(new Date(call.startedAt)) }}</span>
    </div>
    <div v-if="!toolCalls.length" class="empty-state">暂无执行轨迹。</div>
  </div>
</template>

<script setup lang="ts">
import type { ToolCall } from '@/core/types/agent';
import { nowStr } from '@/utils/time';

defineProps<{
  toolCalls: ToolCall[];
}>();
</script>

<style scoped>
.trace-row {
  display: grid;
  grid-template-columns: 10px 1fr auto;
  gap: 8px;
  align-items: start;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-subtle);
}

.trace-dot {
  width: 7px;
  height: 7px;
  margin-top: 5px;
  border-radius: 50%;
  background: var(--text-tertiary);
}

.trace-dot.running {
  background: var(--sem-ai);
}

.trace-dot.success {
  background: var(--sem-ok);
}

.trace-dot.failed {
  background: var(--sem-critical);
}

.trace-title {
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 800;
}

.trace-meta,
.trace-time,
.empty-state {
  color: var(--text-tertiary);
  font-family: var(--font-mono);
  font-size: 9px;
}

.empty-state {
  padding: 24px 10px;
  text-align: center;
}
</style>
