<template>
  <div class="feed">
    <div class="plan-summary">
      <strong>Plan Tree</strong>
      <span>{{ steps.length }} ReAct steps · {{ toolCalls.length }} tool calls</span>
    </div>
    <ReActBlock v-for="step in steps" :key="step.id" :step="step" />
    <div v-if="!steps.length" class="empty-state">等待 Agent 进入推理流程。</div>
  </div>
</template>

<script setup lang="ts">
import type { ReActStep, ToolCall } from '@/core/types/agent';
import ReActBlock from '../reasoning/ReActBlock.vue';

defineProps<{
  steps: ReActStep[];
  toolCalls: ToolCall[];
}>();
</script>

<style scoped>
.plan-summary {
  display: flex;
  justify-content: space-between;
  padding: 8px 10px;
  color: var(--text-tertiary);
  background: rgba(0, 0, 0, 0.18);
  border: 1px solid var(--border-subtle);
  border-radius: 5px;
  font-family: var(--font-mono);
  font-size: 10px;
}

.plan-summary strong {
  color: var(--text-primary);
}

.empty-state {
  padding: 24px 10px;
  color: var(--text-tertiary);
  text-align: center;
  font-family: var(--font-mono);
  font-size: 10px;
}
</style>
