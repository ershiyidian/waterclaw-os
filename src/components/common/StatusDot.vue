<template>
  <span class="status-dot" :class="[status, { pulse }]" />
</template>

<script setup lang="ts">
import type { Severity } from '@/core/types/common';

withDefaults(
  defineProps<{
    status?: Severity;
    pulse?: boolean;
  }>(),
  {
    status: 'ok',
    pulse: false,
  },
);
</script>
