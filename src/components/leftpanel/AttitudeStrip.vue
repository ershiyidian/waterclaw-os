<template>
  <div class="attitude-wrap">
    <ArtificialHorizon :roll="attitude.roll" :pitch="attitude.pitch" />
    <div class="att-strip">
      <div class="att-cell">
        <span class="att-cell-key">ROLL</span>
        <span class="att-cell-val">{{ attitude.roll.toFixed(1) }}deg</span>
        <Sparkline :data="attitude.rollHistory" tone="info" />
      </div>
      <div class="att-cell">
        <span class="att-cell-key">PITCH</span>
        <span class="att-cell-val" :class="{ 'text-warn': Math.abs(attitude.pitch) > 5 }">{{ attitude.pitch.toFixed(1) }}deg</span>
        <Sparkline :data="attitude.pitchHistory" tone="warn" />
      </div>
      <div class="att-cell">
        <span class="att-cell-key">YAW ERR</span>
        <span class="att-cell-val">{{ attitude.yaw.toFixed(1) }}deg</span>
        <Sparkline :data="attitude.yawErrorHistory" tone="ai" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Sparkline from '@/components/common/Sparkline.vue';
import type { AttitudeState } from '@/core/types/usv';
import ArtificialHorizon from './twin/ArtificialHorizon.vue';

defineProps<{
  attitude: AttitudeState;
}>();
</script>

<style scoped>
.attitude-wrap {
  display: grid;
  grid-template-columns: 44px 1fr;
  gap: 6px;
  align-items: center;
}

.att-strip {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 3px;
}

.att-cell {
  min-width: 0;
  padding: 3px 0;
  text-align: center;
  background: var(--bg-inset);
  border-radius: 3px;
  font-family: var(--font-mono);
}

.att-cell-key {
  display: block;
  margin-bottom: 1px;
  color: var(--text-tertiary);
  font-size: 8px;
}

.att-cell-val {
  display: block;
  color: var(--text-primary);
  font-size: 10px;
  font-weight: 700;
}
</style>
