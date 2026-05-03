<template>
  <div class="feed-item">
    <div class="feed-ts">{{ nowStr(new Date(message.timestamp)) }}</div>
    <div class="bubble" :class="severityClass">{{ message.content }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { FeedMessage } from '@/core/types/agent';
import { nowStr } from '@/utils/time';

const props = defineProps<{
  message: FeedMessage;
}>();

const severityClass = computed(() => {
  if (props.message.severity === 'critical') return 'alert-bubble';
  if (props.message.severity === 'ok') return 'success-bubble';
  if (props.message.severity === 'warn') return 'warn-bubble';
  return '';
});
</script>
