<template>
  <article class="tool-card" :class="[call.status, call.riskLevel]">
    <header class="tool-head">
      <div class="tool-title">
        <component :is="icon" :size="14" />
        <span>{{ call.toolName }}</span>
      </div>
      <div class="tool-status">
        <span class="tool-status-dot" :class="call.status" />
        <span>{{ statusText }}</span>
        <span v-if="call.durationMs" class="tool-duration">{{ call.durationMs }}ms</span>
        <button v-if="call.replayable" class="tool-replay" type="button" title="Replay" @click="$emit('replay', call.id)">
          <RefreshCw :size="12" />
        </button>
      </div>
    </header>

    <button class="tool-io-toggle" type="button" @click="expanded = !expanded">
      <ChevronRight :class="{ expanded }" :size="12" />
      Input
    </button>
    <pre v-if="expanded" class="tool-json">{{ formattedArgs }}</pre>

    <div class="tool-output">
      <MiniOutput :tool-name="call.toolName" :result="call.result" :status="call.status" :error="call.error" />
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { Activity, BarChart3, ChevronRight, ClipboardCheck, Map, RadioTower, RefreshCw, Send, ShieldAlert } from 'lucide-vue-next';
import type { ToolCall } from '@/core/types/agent';
import MiniOutput from './ToolMiniOutput.vue';

const props = defineProps<{
  call: ToolCall;
}>();

defineEmits<{
  replay: [id: string];
}>();

const expanded = ref(false);

const formattedArgs = computed(() => JSON.stringify(props.call.args, null, 2));

const statusText = computed(() => {
  if (props.call.status === 'running') return 'Running';
  if (props.call.status === 'success') return 'Success';
  if (props.call.status === 'failed') return 'Failed';
  if (props.call.status === 'awaiting_approval') return 'Approval';
  return 'Pending';
});

const icon = computed(() => {
  if (props.call.category === 'analytics') return BarChart3;
  if (props.call.category === 'reports') return ClipboardCheck;
  if (props.call.category === 'fleet') return RadioTower;
  if (props.call.category === 'emergency') return ShieldAlert;
  if (props.call.category === 'communications') return Send;
  if (props.call.toolName.includes('path')) return Map;
  return Activity;
});
</script>

<style scoped>
.tool-card {
  padding: 9px 10px;
  margin-top: 8px;
  background: rgba(10, 18, 36, 0.84);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
}

.tool-card.critical {
  border-color: rgba(239, 68, 68, 0.32);
}

.tool-card.success {
  border-color: rgba(16, 185, 129, 0.28);
}

.tool-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.tool-title,
.tool-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
}

.tool-title {
  color: var(--text-primary);
}

.tool-status {
  color: var(--text-tertiary);
}

.tool-status-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--text-tertiary);
}

.tool-status-dot.running {
  background: var(--sem-ai);
  animation: miniBlink 1s ease-in-out infinite;
}

.tool-status-dot.success {
  background: var(--sem-ok);
}

.tool-status-dot.failed {
  background: var(--sem-critical);
}

.tool-duration {
  color: var(--text-tertiary);
}

.tool-replay {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 18px;
  cursor: pointer;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
}

.tool-io-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  color: var(--text-tertiary);
  cursor: pointer;
  background: transparent;
  border: none;
  font-family: var(--font-mono);
  font-size: 9px;
}

.tool-io-toggle svg {
  transition: transform 0.15s ease;
}

.tool-io-toggle svg.expanded {
  transform: rotate(90deg);
}

.tool-json {
  max-height: 120px;
  padding: 7px;
  margin-top: 5px;
  overflow: auto;
  color: #a5b4fc;
  background: rgba(0, 0, 0, 0.24);
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 10px;
  line-height: 1.55;
}

.tool-output {
  margin-top: 7px;
}
</style>
