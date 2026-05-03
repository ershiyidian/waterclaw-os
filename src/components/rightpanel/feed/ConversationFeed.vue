<template>
  <div ref="feedEl" class="feed">
    <template v-for="message in feed" :key="message.id">
      <UserBubble v-if="message.role === 'user'" :message="message" />
      <div v-else-if="message.role === 'tool_call' && toolCall(message.toolCallId)" class="feed-item">
        <div class="feed-ts">{{ nowStr(new Date(message.timestamp)) }}</div>
        <ToolCallCard :call="toolCall(message.toolCallId)!" @replay="$emit('replay', $event)" />
      </div>
      <div v-else-if="message.role === 'approval'" class="feed-item">
        <div class="feed-ts">{{ nowStr(new Date(message.timestamp)) }}</div>
        <ActionCard :approval="pendingApproval" @approve="$emit('approve', $event)" @reject="$emit('reject')" />
      </div>
      <AgentBubble v-else :message="message" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue';
import ToolCallCard from '@/components/common/ToolCallCard.vue';
import type { ApprovalAction, FeedMessage, ToolCall } from '@/core/types/agent';
import { nowStr } from '@/utils/time';
import ActionCard from '../reasoning/ActionCard.vue';
import AgentBubble from '../bubbles/AgentBubble.vue';
import UserBubble from '../bubbles/UserBubble.vue';

const props = defineProps<{
  feed: FeedMessage[];
  toolCalls: ToolCall[];
  pendingApproval: ApprovalAction | null;
}>();

defineEmits<{
  replay: [id: string];
  approve: [code?: string];
  reject: [];
}>();

const feedEl = ref<HTMLDivElement | null>(null);

function toolCall(id?: string): ToolCall | undefined {
  return props.toolCalls.find((item) => item.id === id);
}

watch(
  () => props.feed.length + props.toolCalls.length,
  async () => {
    await nextTick();
    if (feedEl.value) feedEl.value.scrollTop = feedEl.value.scrollHeight;
  },
);
</script>

<style>
.feed {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 12px;
  padding: 12px 14px;
  overflow-y: auto;
}

.feed-ts {
  margin-bottom: 2px;
  color: var(--text-tertiary);
  text-align: center;
  font-family: var(--font-mono);
  font-size: 9px;
}

.feed-item {
  opacity: 0;
  animation: feedSlide 0.35s ease-out forwards;
}

.bubble {
  padding: 10px 12px;
  font-size: 12px;
  line-height: 1.65;
  white-space: pre-wrap;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
}

.bubble.alert-bubble {
  background: rgba(239, 68, 68, 0.04);
  border-color: rgba(239, 68, 68, 0.35);
  border-left: 3px solid var(--sem-critical);
}

.bubble.success-bubble {
  background: rgba(16, 185, 129, 0.04);
  border-color: rgba(16, 185, 129, 0.35);
  border-left: 3px solid var(--sem-ok);
}

.bubble.warn-bubble {
  background: rgba(245, 158, 11, 0.04);
  border-color: rgba(245, 158, 11, 0.35);
  border-left: 3px solid var(--sem-warn);
}

.bubble.user-bubble {
  text-align: right;
  background: rgba(56, 189, 248, 0.06);
  border-color: rgba(56, 189, 248, 0.2);
}
</style>
