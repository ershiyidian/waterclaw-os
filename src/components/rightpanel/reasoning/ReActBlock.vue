<template>
  <article class="react-block" :class="step.status">
    <div class="react-line thought"><span>Thought</span>{{ step.thought }}</div>
    <div v-if="step.action" class="react-line action"><span>Action</span><code>{{ step.action }}</code></div>
    <div v-if="step.observation" class="react-line observation"><span>Observation</span>{{ step.observation }}</div>
  </article>
</template>

<script setup lang="ts">
import type { ReActStep } from '@/core/types/agent';

defineProps<{
  step: ReActStep;
}>();
</script>

<style scoped>
.react-block {
  padding: 8px 9px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border-subtle);
  border-radius: 5px;
}

.react-block + .react-block {
  margin-top: 7px;
}

.react-line {
  display: grid;
  grid-template-columns: 74px 1fr;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 11px;
  line-height: 1.55;
}

.react-line + .react-line {
  margin-top: 4px;
}

.react-line span {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 800;
}

.thought span {
  color: var(--sem-ai);
}

.action span {
  color: var(--sem-info);
}

.observation span {
  color: var(--sem-ok);
}

code {
  color: #bfdbfe;
  font-family: var(--font-mono);
  font-size: 10px;
}
</style>
