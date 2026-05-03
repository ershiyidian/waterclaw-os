<template>
  <div class="feed-item">
    <div class="feed-ts">{{ nowStr(new Date(message.timestamp)) }}</div>
    <div class="bubble user-bubble"><strong>&gt;</strong> {{ message.content }}</div>
  </div>
</template>

<script setup lang="ts">
import type { FeedMessage } from '@/core/types/agent';
import { nowStr } from '@/utils/time';

defineProps<{
  message: FeedMessage;
}>();
</script>
