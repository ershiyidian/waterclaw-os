<template>
  <div class="sensor-matrix">
    <div v-for="sensor in sensors" :key="sensor.key" class="sensor-cell" :class="sensor.status">
      <span class="sensor-square" />
      <span class="sensor-key">{{ sensor.key }}</span>
      <div class="sensor-popover">
        <div class="sensor-title">{{ sensor.label }}</div>
        <div class="sensor-value">{{ sensor.value }}</div>
        <div class="sensor-line">Last Cal: {{ sensor.lastCalDays }}天前</div>
        <div class="sensor-line">Drift +{{ sensor.driftPct.toFixed(1) }}%</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SensorCell } from '@/core/types/usv';

defineProps<{
  sensors: SensorCell[];
}>();
</script>

<style scoped>
.sensor-matrix {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 4px;
}

.sensor-cell {
  position: relative;
  display: flex;
  align-items: center;
  gap: 3px;
  min-width: 0;
  padding: 3px 4px;
  color: var(--text-tertiary);
  background: rgba(0, 0, 0, 0.18);
  border: 1px solid var(--border-subtle);
  border-radius: 3px;
  font-family: var(--font-mono);
  font-size: 8px;
}

.sensor-square {
  width: 5px;
  height: 5px;
  flex-shrink: 0;
  border-radius: 1px;
  background: var(--sem-ok);
  box-shadow: 0 0 5px rgba(16, 185, 129, 0.45);
}

.sensor-cell.warn .sensor-square {
  background: var(--sem-warn);
  box-shadow: 0 0 5px rgba(245, 158, 11, 0.45);
}

.sensor-cell.critical .sensor-square {
  background: var(--sem-critical);
  box-shadow: 0 0 5px rgba(239, 68, 68, 0.45);
}

.sensor-key {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sensor-popover {
  position: absolute;
  bottom: 24px;
  left: 0;
  z-index: 80;
  display: none;
  width: 150px;
  padding: 8px;
  background: rgba(10, 18, 36, 0.98);
  border: 1px solid var(--border-medium);
  border-radius: 5px;
  box-shadow: 0 10px 22px rgba(0, 0, 0, 0.4);
}

.sensor-cell:hover .sensor-popover {
  display: block;
}

.sensor-title {
  color: var(--text-primary);
  font-size: 10px;
  font-weight: 800;
}

.sensor-value {
  margin: 3px 0;
  color: var(--accent-blue);
  font-size: 12px;
  font-weight: 800;
}

.sensor-line {
  color: var(--text-tertiary);
  line-height: 1.5;
}
</style>
