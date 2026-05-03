<template>
  <div class="mission-clock">
    <span class="clock-key">Mission Clock</span>
    <span class="clock-value">{{ formatDuration(seconds) }}</span>
  </div>
</template>

<script setup lang="ts">
import { formatDuration } from '@/utils/time';

defineProps<{
  seconds: number;
}>();
</script>

<style scoped>
.mission-clock {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 96px;
  padding: 0 10px;
  border-left: 1px solid var(--border-subtle);
}

.clock-key {
  color: var(--text-tertiary);
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
}

.clock-value {
  color: var(--accent-blue);
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 800;
}
</style>
