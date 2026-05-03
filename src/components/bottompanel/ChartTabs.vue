<template>
  <div class="chart-tabs">
    <button v-for="tab in tabs" :key="tab.id" class="chart-tab" :class="{ active: active === tab.id }" type="button" @click="$emit('change', tab.id)">
      {{ tab.label }}
    </button>
  </div>
</template>

<script setup lang="ts">
import type { ChartTab } from '@/core/types/chart';

defineProps<{
  active: ChartTab;
}>();

defineEmits<{
  change: [tab: ChartTab];
}>();

const tabs: Array<{ id: ChartTab; label: string }> = [
  { id: 'water', label: '水质 浊度/DO' },
  { id: 'air', label: '逸散气体 VOCs/PM2.5' },
  { id: 'flow', label: '流量水位' },
  { id: 'health', label: '设备健康' },
];
</script>

<style scoped>
.chart-tabs {
  display: flex;
  gap: 6px;
}

.chart-tab {
  padding: 3px 8px;
  color: var(--text-tertiary);
  cursor: pointer;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font-size: 10px;
  font-weight: 600;
  transition: all 0.15s ease;
}

.chart-tab:hover {
  color: var(--text-secondary);
}

.chart-tab.active {
  color: var(--accent-blue);
  background: rgba(56, 189, 248, 0.08);
  border-color: rgba(56, 189, 248, 0.2);
}
</style>
