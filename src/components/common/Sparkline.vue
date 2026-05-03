<template>
  <svg class="sparkline" viewBox="0 0 44 18" preserveAspectRatio="none" aria-hidden="true">
    <path class="sparkline-grid" d="M0 9 H44" />
    <polyline :points="points" :class="['sparkline-line', tone]" fill="none" />
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { TimeSeriesPoint } from '@/core/types/common';

const props = withDefaults(
  defineProps<{
    data: TimeSeriesPoint[];
    tone?: 'ok' | 'warn' | 'critical' | 'info' | 'ai';
  }>(),
  {
    tone: 'info',
  },
);

const points = computed(() => {
  if (!props.data.length) return '';
  const values = props.data.map((item) => item.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = Math.max(0.001, max - min);
  return props.data
    .map((item, index) => {
      const x = (index / Math.max(1, props.data.length - 1)) * 44;
      const y = 16 - ((item.value - min) / span) * 14;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');
});
</script>

<style scoped>
.sparkline {
  width: 44px;
  height: 18px;
  overflow: visible;
}

.sparkline-grid {
  stroke: rgba(148, 163, 184, 0.13);
  stroke-width: 1;
}

.sparkline-line {
  stroke-width: 1.35;
  vector-effect: non-scaling-stroke;
}

.sparkline-line.ok {
  stroke: var(--sem-ok);
}

.sparkline-line.warn {
  stroke: var(--sem-warn);
}

.sparkline-line.critical {
  stroke: var(--sem-critical);
}

.sparkline-line.info {
  stroke: var(--sem-info);
}

.sparkline-line.ai {
  stroke: var(--sem-ai);
}
</style>
