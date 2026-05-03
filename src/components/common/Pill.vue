<template>
  <span class="pill" :class="tone">
    <slot />
  </span>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    tone?: 'ok' | 'warn' | 'critical' | 'info' | 'ai' | 'muted';
  }>(),
  {
    tone: 'muted',
  },
);
</script>

<style scoped>
.pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-height: 18px;
  padding: 1px 7px;
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.4px;
  border: 1px solid var(--border-subtle);
  border-radius: 999px;
}

.pill.ok {
  color: var(--sem-ok);
  background: rgba(16, 185, 129, 0.12);
  border-color: rgba(16, 185, 129, 0.28);
}

.pill.warn {
  color: var(--sem-warn);
  background: rgba(245, 158, 11, 0.12);
  border-color: rgba(245, 158, 11, 0.28);
}

.pill.critical {
  color: var(--sem-critical);
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.28);
}

.pill.info {
  color: var(--sem-info);
  background: rgba(56, 189, 248, 0.1);
  border-color: rgba(56, 189, 248, 0.26);
}

.pill.ai {
  color: var(--sem-ai);
  background: rgba(129, 140, 248, 0.12);
  border-color: rgba(129, 140, 248, 0.28);
}

.pill.muted {
  color: var(--text-tertiary);
  background: rgba(30, 41, 59, 0.45);
}
</style>
