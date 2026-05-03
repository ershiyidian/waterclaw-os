<template>
  <div class="mini-output">
    <div v-if="status === 'running'" class="running-row">工具执行中...</div>
    <div v-else-if="error" class="error-row">{{ error }}</div>
    <template v-else-if="result">
      <div v-if="toolName === 'lstm_predict'" class="metric-output">
        <span class="metric-main text-crit">{{ get('peakNtu') }}</span>
        <span class="metric-label">NTU peak · {{ get('breachInMin') }}min breach</span>
      </div>
      <div v-else-if="toolName === 'run_kmeans'" class="cluster-output">
        <span class="cluster-title">{{ get('hotspot') }}</span>
        <div class="cluster-bubbles">
          <span
            v-for="(item, idx) in clusters"
            :key="idx"
            class="cluster-bubble"
            :style="{ width: `${item.r}px`, height: `${item.r}px`, left: `${item.x}%`, top: `${item.y}%` }"
          />
        </div>
      </div>
      <div v-else-if="toolName === 'eval_gb3838'" class="gb-output">
        <span class="grade">III 类 · 达标</span>
        <span>{{ get('summary') }}</span>
      </div>
      <div v-else-if="toolName === 'plan_dubins_path'" class="path-output">
        <span class="path-line" />
        <span>{{ get('lengthM') }}m · ETA {{ get('etaMin') }}min</span>
      </div>
      <div v-else class="summary-output">{{ get('summary') || JSON.stringify(result) }}</div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { ToolStatus } from '@/core/types/agent';

const props = defineProps<{
  toolName: string;
  result?: unknown;
  status: ToolStatus;
  error?: string;
}>();

function get(key: string): string {
  if (!props.result || typeof props.result !== 'object') return '';
  const value = (props.result as Record<string, unknown>)[key];
  return value == null ? '' : String(value);
}

const clusters = computed(() => {
  if (!props.result || typeof props.result !== 'object') return [];
  const value = (props.result as Record<string, unknown>).clusters;
  return Array.isArray(value) ? (value as Array<{ x: number; y: number; r: number }>) : [];
});
</script>

<style scoped>
.mini-output {
  min-height: 24px;
  color: var(--text-secondary);
  font-size: 10px;
}

.running-row {
  color: var(--sem-ai);
  font-family: var(--font-mono);
}

.error-row {
  color: var(--sem-critical);
  font-family: var(--font-mono);
}

.metric-output,
.gb-output,
.path-output {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.metric-main {
  font-family: var(--font-mono);
  font-size: 18px;
  font-weight: 800;
}

.metric-label,
.summary-output {
  color: var(--text-secondary);
}

.cluster-output {
  display: grid;
  grid-template-columns: 92px 1fr;
  gap: 8px;
  align-items: center;
}

.cluster-title {
  color: var(--sem-critical);
  font-weight: 700;
}

.cluster-bubbles {
  position: relative;
  height: 34px;
  background: rgba(0, 0, 0, 0.22);
  border-radius: 4px;
}

.cluster-bubble {
  position: absolute;
  border: 1px solid rgba(239, 68, 68, 0.65);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  background: rgba(239, 68, 68, 0.16);
}

.grade {
  flex-shrink: 0;
  padding: 2px 8px;
  color: var(--sem-ok);
  background: rgba(16, 185, 129, 0.14);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 4px;
  font-weight: 800;
}

.path-line {
  display: block;
  width: 86px;
  height: 26px;
  border-bottom: 1px dashed rgba(245, 158, 11, 0.7);
  border-left: 1px solid transparent;
  border-radius: 0 0 0 100%;
  transform: skewX(-18deg);
}
</style>
