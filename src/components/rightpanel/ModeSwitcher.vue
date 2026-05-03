<template>
  <div class="mode-switcher">
    <button v-for="item in modes" :key="item.id" type="button" :class="{ active: active === item.id }" @click="$emit('change', item.id)">
      {{ item.label }}
    </button>
  </div>
</template>

<script setup lang="ts">
import type { AgentMode } from '@/core/types/agent';

defineProps<{
  active: AgentMode;
}>();

defineEmits<{
  change: [mode: AgentMode];
}>();

const modes: Array<{ id: AgentMode; label: string }> = [
  { id: 'conversation', label: 'Conversation' },
  { id: 'plan', label: 'Plan' },
  { id: 'trace', label: 'Trace' },
];
</script>

<style scoped>
.mode-switcher {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
  padding: 8px 14px;
  border-bottom: 1px solid var(--border-subtle);
}

.mode-switcher button {
  height: 24px;
  color: var(--text-tertiary);
  cursor: pointer;
  background: rgba(30, 41, 59, 0.28);
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 700;
}

.mode-switcher button.active {
  color: var(--accent-blue);
  background: rgba(56, 189, 248, 0.08);
  border-color: rgba(56, 189, 248, 0.26);
}
</style>
