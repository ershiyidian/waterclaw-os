<template>
  <div v-if="visible" id="boot-overlay" :class="{ 'fade-out': fading }">
    <div class="boot-logo">
      <svg viewBox="0 0 24 24">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
      </svg>
    </div>
    <div class="boot-title">WATERCLAW OS</div>
    <div class="boot-log">
      <div v-for="line in lines" :key="line" class="boot-line" v-html="line" />
    </div>
    <div class="boot-bar-track">
      <div class="boot-bar-fill" :style="{ width: `${pct}%` }" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { BOOT_STEPS } from '@/config/constants';

const emit = defineEmits<{
  done: [];
}>();

const visible = ref(true);
const fading = ref(false);
const pct = ref(0);
const lines = ref<string[]>([]);

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

onMounted(async () => {
  for (const step of BOOT_STEPS) {
    lines.value.push(`${step.label} <span class="boot-ok">OK</span>`);
    if (lines.value.length > 4) lines.value.shift();
    pct.value = step.pct;
    await sleep(310);
  }
  await sleep(380);
  fading.value = true;
  await sleep(600);
  visible.value = false;
  emit('done');
});
</script>

<style scoped>
#boot-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
  justify-content: center;
  background: var(--bg-base);
  transition: opacity 0.6s ease;
}

#boot-overlay.fade-out {
  pointer-events: none;
  opacity: 0;
}

.boot-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-indigo));
  border-radius: 12px;
  animation: bootPulse 1.5s ease-in-out infinite;
}

.boot-logo svg {
  width: 24px;
  height: 24px;
  fill: none;
  stroke: #fff;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 2.2;
}

.boot-title {
  color: var(--text-primary);
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 1px;
}

.boot-log {
  min-height: 60px;
  color: var(--text-tertiary);
  text-align: center;
  font-family: var(--font-mono);
  font-size: 11px;
  line-height: 1.8;
}

.boot-line {
  opacity: 0;
  animation: bootLineIn 0.3s ease-out forwards;
}

:deep(.boot-ok) {
  color: var(--sem-ok);
}

.boot-bar-track {
  width: 240px;
  height: 3px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 2px;
}

.boot-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent-blue), var(--accent-indigo));
  border-radius: 2px;
  transition: width 0.3s ease;
}
</style>
