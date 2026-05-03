<template>
  <article class="usv-card" :class="[stateClass, { selected: usv.selected }]">
    <div class="usv-header">
      <span class="usv-id">
        <StatusDot :status="dotTone" pulse />
        {{ usv.id }}
      </span>
      <div class="usv-header-right">
        <span class="usv-mode" :class="modeClass">{{ usv.mode }}</span>
        <BatteryIndicator :pct="usv.battery.pct" />
      </div>
    </div>

    <div class="task-line">
      <div class="task-main">TASK {{ usv.task.label }} · {{ usv.task.segment }}</div>
      <div class="task-meta">Next WP {{ usv.task.nextWpDistanceM }}m · Remaining {{ usv.task.remainingWp }} · {{ Math.round(usv.task.progressPct) }}%</div>
      <div class="task-progress"><span :style="{ width: `${usv.task.progressPct}%` }" /></div>
    </div>

    <div v-if="expanded" class="twin-viewport">
      <FpvCanvas :usv-id="usv.id" :position="usv.position" :heading="usv.headingDeg" :speed="usv.speedMps" :yolo="usv.yolo" />
      <LidarBev :heading="usv.headingDeg" />
    </div>

    <AttitudeStrip v-if="expanded" :attitude="usv.attitude" />

    <button class="health-toggle" type="button" @click="healthOpen = !healthOpen">
      Health · {{ usv.battery.powerW }}W · {{ remainingText }} · {{ usv.battery.temperatureC }}C · cycle {{ usv.battery.cycles }}/{{ usv.battery.cycleLimit }}
    </button>
    <div v-if="healthOpen" class="health-grid">
      <span>Power</span><strong>{{ usv.battery.powerW }}W</strong>
      <span>Endurance</span><strong>{{ remainingText }}</strong>
      <span>Battery Temp</span><strong :class="{ 'text-warn': usv.battery.temperatureC > 50 }">{{ usv.battery.temperatureC }}C</strong>
      <span>Cycle</span><strong>{{ usv.battery.cycles }}/{{ usv.battery.cycleLimit }}</strong>
    </div>

    <SensorMatrix :sensors="usv.sensors" />
  </article>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import BatteryIndicator from '@/components/common/BatteryIndicator.vue';
import StatusDot from '@/components/common/StatusDot.vue';
import type { Severity } from '@/core/types/common';
import type { UsvState } from '@/core/types/usv';
import AttitudeStrip from './AttitudeStrip.vue';
import SensorMatrix from './SensorMatrix.vue';
import FpvCanvas from './twin/FpvCanvas.vue';
import LidarBev from './twin/LidarBev.vue';

const props = withDefaults(
  defineProps<{
    usv: UsvState;
    expanded?: boolean;
  }>(),
  {
    expanded: false,
  },
);

const healthOpen = ref(false);

const modeClass = computed(() => `mode-${props.usv.mode.toLowerCase()}`);
const stateClass = computed(() => {
  if (props.usv.mode === 'ESTOP') return 'crit-state';
  if (props.usv.mode === 'INTERCEPT' || props.usv.mode === 'SENTRY') return 'warn-state';
  return '';
});
const dotTone = computed<Severity>(() => {
  if (props.usv.mode === 'ESTOP') return 'critical';
  if (props.usv.mode === 'INTERCEPT') return 'warn';
  if (props.usv.mode === 'SENTRY') return 'ai';
  return 'ok';
});
const remainingText = computed(() => {
  const h = Math.floor(props.usv.battery.remainingMin / 60);
  const m = props.usv.battery.remainingMin % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
});
</script>

<style scoped>
.usv-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  cursor: default;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  transition: all 0.2s ease;
}

.usv-card:hover {
  background: var(--bg-card-hover);
  border-color: var(--border-medium);
}

.usv-card.selected {
  background: rgba(56, 189, 248, 0.06);
  border-color: var(--accent-blue);
}

.usv-card.warn-state {
  background: rgba(245, 158, 11, 0.05);
  border-color: var(--sem-warn);
}

.usv-card.crit-state {
  background: rgba(239, 68, 68, 0.05);
  border-color: var(--sem-critical);
}

.usv-header,
.usv-header-right {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.usv-id {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 800;
}

.usv-mode {
  padding: 1px 6px;
  text-transform: uppercase;
  border-radius: 3px;
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.mode-auto {
  color: var(--sem-ok);
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.mode-hold {
  color: var(--sem-info);
  background: rgba(56, 189, 248, 0.12);
  border: 1px solid rgba(56, 189, 248, 0.3);
}

.mode-intercept,
.mode-rtl {
  color: var(--sem-warn);
  background: rgba(245, 158, 11, 0.15);
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.mode-sentry {
  color: var(--sem-ai);
  background: rgba(129, 140, 248, 0.15);
  border: 1px solid rgba(129, 140, 248, 0.3);
}

.mode-estop {
  color: var(--sem-critical);
  background: rgba(239, 68, 68, 0.16);
  border: 1px solid rgba(239, 68, 68, 0.35);
}

.task-line {
  color: var(--text-tertiary);
  font-family: var(--font-mono);
  font-size: 10px;
  line-height: 1.4;
}

.task-main {
  color: var(--text-secondary);
}

.task-meta {
  margin-top: 1px;
}

.task-progress {
  height: 2px;
  margin-top: 5px;
  overflow: hidden;
  background: rgba(148, 163, 184, 0.11);
  border-radius: 2px;
}

.task-progress span {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, var(--accent-blue), var(--accent-indigo));
  border-radius: inherit;
  transition: width 0.35s ease;
}

.twin-viewport {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  height: 116px;
  padding: 1px;
  overflow: hidden;
  background: #000;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 4px;
}

.health-toggle {
  overflow: hidden;
  color: var(--text-tertiary);
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
  background: rgba(0, 0, 0, 0.16);
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
  padding: 4px 6px;
  font-family: var(--font-mono);
  font-size: 9px;
}

.health-grid {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 3px 10px;
  padding: 7px;
  background: var(--bg-inset);
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 9px;
}

.health-grid span {
  color: var(--text-tertiary);
}

.health-grid strong {
  color: var(--text-secondary);
}
</style>
