<template>
  <div v-if="approval" class="action-card">
    <div class="action-head">
      <span class="text-warn">HITL</span>
      <strong>{{ approval.title }}</strong>
      <span class="countdown">{{ remaining }}s</span>
    </div>
    <div class="action-desc">{{ approval.description }}</div>
    <div v-if="approval.requiresCode" class="code-row">
      <span>2FA</span>
      <input v-model="code" inputmode="numeric" maxlength="8" placeholder="输入审批码" />
    </div>
    <div class="action-btns">
      <ConfirmButton :risk-level="approval.riskLevel" :hold-ms="approval.requiresHoldMs ?? 1800" label="长按批准" @confirm="approve" />
      <button class="btn-dismiss" type="button" @click="$emit('reject')">忽略</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import ConfirmButton from '@/components/common/ConfirmButton.vue';
import type { ApprovalAction } from '@/core/types/agent';

const props = defineProps<{
  approval: ApprovalAction | null;
}>();

const emit = defineEmits<{
  approve: [code?: string];
  reject: [];
}>();

const now = ref(Date.now());
const code = ref('');
let timer = 0;

const remaining = computed(() => {
  if (!props.approval) return 0;
  const elapsed = Math.floor((now.value - props.approval.requestedAt) / 1000);
  return Math.max(0, props.approval.autoCancelSeconds - elapsed);
});

function approve(): void {
  if (props.approval?.requiresCode && !code.value.trim()) return;
  emit('approve', code.value.trim());
}

onMounted(() => {
  timer = window.setInterval(() => {
    now.value = Date.now();
    if (props.approval && remaining.value <= 0) emit('reject');
  }, 1000);
});

onUnmounted(() => window.clearInterval(timer));
</script>

<style scoped>
.action-card {
  padding: 10px 12px;
  margin-top: 8px;
  background: rgba(10, 18, 36, 0.92);
  border: 1px solid rgba(245, 158, 11, 0.34);
  border-radius: 6px;
}

.action-head {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 7px;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
}

.action-head span:first-child,
.countdown {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 800;
}

.countdown {
  color: var(--text-tertiary);
}

.action-desc {
  margin-bottom: 10px;
  color: var(--text-secondary);
  font-size: 11px;
  line-height: 1.6;
}

.code-row {
  display: grid;
  grid-template-columns: 36px 1fr;
  gap: 6px;
  align-items: center;
  margin-bottom: 10px;
  font-family: var(--font-mono);
  font-size: 10px;
}

.code-row span {
  color: var(--text-tertiary);
}

.code-row input {
  height: 28px;
  padding: 0 8px;
  color: var(--text-primary);
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
  outline: none;
  font-family: var(--font-mono);
}

.code-row input:focus {
  border-color: var(--sem-warn);
}

.action-btns {
  display: flex;
  gap: 8px;
}

.btn-dismiss {
  flex: 1;
  height: 32px;
  color: var(--text-secondary);
  cursor: pointer;
  background: transparent;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  font-size: 11px;
}

.btn-dismiss:hover {
  background: var(--bg-card);
}
</style>
