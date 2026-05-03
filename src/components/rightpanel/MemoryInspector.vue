<template>
  <div class="memory-inspector">
    <button class="memory-toggle" type="button" @click="open = !open">Memory Inspector</button>
    <div v-if="open" class="memory-body">
      <div class="memory-col">
        <strong>Short-term</strong>
        <div v-for="(value, key) in memory.shortTerm" :key="key" class="memory-row"><span>{{ key }}</span><em>{{ value }}</em></div>
      </div>
      <div class="memory-col">
        <strong>Long-term</strong>
        <div v-for="(value, key) in memory.longTerm" :key="key" class="memory-row"><span>{{ key }}</span><em>{{ value }}</em></div>
      </div>
      <div class="memory-col">
        <strong>Tools cache</strong>
        <div v-for="item in memory.toolCache" :key="item.key" class="memory-row"><span>{{ item.key }}</span><em>{{ item.value }}</em></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { MemoryState } from '@/core/types/agent';

defineProps<{
  memory: MemoryState;
}>();

const open = ref(false);
</script>

<style scoped>
.memory-inspector {
  border-top: 1px solid var(--border-subtle);
}

.memory-toggle {
  width: 100%;
  height: 24px;
  color: var(--text-tertiary);
  cursor: pointer;
  background: rgba(0, 0, 0, 0.12);
  border: none;
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 800;
}

.memory-body {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
  max-height: 180px;
  padding: 8px 14px;
  overflow-y: auto;
  background: rgba(0, 0, 0, 0.18);
}

.memory-col strong {
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 9px;
}

.memory-row {
  display: grid;
  grid-template-columns: 96px 1fr;
  gap: 6px;
  margin-top: 3px;
  color: var(--text-tertiary);
  font-family: var(--font-mono);
  font-size: 8px;
}

.memory-row em {
  color: var(--text-secondary);
  font-style: normal;
}
</style>
