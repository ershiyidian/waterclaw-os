<template>
  <button
    class="confirm-button"
    :class="riskLevel"
    type="button"
    @pointerdown="start"
    @pointerup="cancel"
    @pointerleave="cancel"
    @click.prevent
  >
    <span class="confirm-fill" :style="{ width: `${progress}%` }" />
    <span class="confirm-label">{{ labelText }}</span>
  </button>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { RiskLevel } from '@/core/types/agent';

const props = withDefaults(
  defineProps<{
    riskLevel?: RiskLevel;
    holdMs?: number;
    label?: string;
  }>(),
  {
    riskLevel: 'confirm',
    holdMs: 1800,
    label: '长按批准',
  },
);

const emit = defineEmits<{
  confirm: [];
}>();

const progress = ref(0);
let raf = 0;
let started = 0;

const labelText = computed(() => (progress.value > 0 ? `${props.label} ${Math.round(progress.value)}%` : props.label));

function start(): void {
  started = performance.now();
  const tick = (now: number) => {
    progress.value = Math.min(100, ((now - started) / props.holdMs) * 100);
    if (progress.value >= 100) {
      cancel();
      emit('confirm');
      return;
    }
    raf = requestAnimationFrame(tick);
  };
  raf = requestAnimationFrame(tick);
}

function cancel(): void {
  if (raf) cancelAnimationFrame(raf);
  raf = 0;
  if (progress.value < 100) progress.value = 0;
}
</script>

<style scoped>
.confirm-button {
  position: relative;
  flex: 1;
  height: 32px;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid rgba(56, 189, 248, 0.35);
  border-radius: var(--radius-sm);
  background: rgba(56, 189, 248, 0.12);
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 800;
}

.confirm-button.critical {
  border-color: rgba(239, 68, 68, 0.55);
  background:
    repeating-linear-gradient(-45deg, rgba(239, 68, 68, 0.12), rgba(239, 68, 68, 0.12) 4px, rgba(127, 29, 29, 0.18) 4px, rgba(127, 29, 29, 0.18) 8px),
    rgba(239, 68, 68, 0.14);
}

.confirm-fill {
  position: absolute;
  inset: 0 auto 0 0;
  width: 0%;
  background: rgba(56, 189, 248, 0.35);
  transition: width 0.05s linear;
}

.confirm-button.critical .confirm-fill {
  background: rgba(239, 68, 68, 0.38);
}

.confirm-label {
  position: relative;
  z-index: 1;
}
</style>
