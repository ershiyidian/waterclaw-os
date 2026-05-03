<template>
  <div class="battery-wrap">
    <span class="battery-pct">{{ Math.round(pct) }}%</span>
    <div class="battery-shell">
      <div class="battery-fill" :style="{ width: `${pct}%`, background: color }" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  pct: number;
}>();

const color = computed(() => {
  if (props.pct < 20) return 'var(--sem-critical)';
  if (props.pct < 45) return 'var(--sem-warn)';
  return 'var(--sem-ok)';
});
</script>

<style scoped>
.battery-wrap {
  display: flex;
  align-items: center;
  gap: 5px;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
}

.battery-pct {
  min-width: 28px;
  text-align: right;
}

.battery-shell {
  position: relative;
  width: 22px;
  height: 10px;
  padding: 1px;
  border: 1px solid var(--text-tertiary);
  border-radius: 2px;
}

.battery-shell::after {
  position: absolute;
  top: 2px;
  right: -3px;
  width: 2px;
  height: 4px;
  content: "";
  background: var(--text-tertiary);
  border-radius: 0 1px 1px 0;
}

.battery-fill {
  height: 100%;
  border-radius: 1px;
  transition: width 0.5s ease, background 0.5s ease;
}
</style>
