<template>
  <div class="mcp-pill" :class="[server.status, server.permission]">
    <StatusDot :status="statusTone" :pulse="server.status === 'calling'" />
    <component :is="icon" :size="13" />
    <span class="mcp-name">{{ server.name }}</span>
    <span class="mcp-count">x{{ server.callCount }}</span>
    <div class="mcp-popover">
      <div class="mcp-pop-title">{{ server.name }}</div>
      <div class="mcp-line">{{ server.endpoint }}</div>
      <div class="mcp-grid">
        <span>resources</span><strong>{{ server.capabilities.resources }}</strong>
        <span>tools</span><strong>{{ server.capabilities.tools }}</strong>
        <span>prompts</span><strong>{{ server.capabilities.prompts }}</strong>
        <span>latency</span><strong>{{ server.latencyMs }}ms</strong>
        <span>scope</span><strong>{{ server.permission }}</strong>
      </div>
      <div class="mcp-desc">{{ server.description }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Bot, CloudSun, Database, Globe2, Map, RadioTower, Server, Zap } from 'lucide-vue-next';
import type { McpServerStatus } from '@/core/types/mcp';
import StatusDot from './StatusDot.vue';

const props = defineProps<{
  server: McpServerStatus;
}>();

const icon = computed(() => {
  if (props.server.icon === 'database') return Database;
  if (props.server.icon === 'stream') return Zap;
  if (props.server.icon === 'bus') return RadioTower;
  if (props.server.icon === 'map') return Map;
  if (props.server.icon === 'weather') return CloudSun;
  if (props.server.icon === 'llm') return Bot;
  if (props.server.icon === 'api') return Globe2;
  return Server;
});

const statusTone = computed(() => {
  if (props.server.status === 'offline') return 'critical';
  if (props.server.status === 'degraded') return 'warn';
  if (props.server.status === 'calling') return 'ai';
  return 'ok';
});
</script>

<style scoped>
.mcp-pill {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 24px;
  padding: 0 8px;
  color: var(--text-secondary);
  white-space: nowrap;
  background: rgba(30, 41, 59, 0.45);
  border: 1px solid var(--border-subtle);
  border-radius: 999px;
  font-family: var(--font-mono);
  font-size: 9px;
}

.mcp-pill.calling {
  color: var(--sem-ai);
  border-color: rgba(129, 140, 248, 0.4);
  box-shadow: 0 0 16px rgba(129, 140, 248, 0.12);
}

.mcp-pill.read-write {
  border-color: rgba(245, 158, 11, 0.26);
}

.mcp-name {
  font-weight: 700;
}

.mcp-count {
  padding-left: 4px;
  color: var(--text-tertiary);
  border-left: 1px solid var(--border-subtle);
}

.mcp-popover {
  position: absolute;
  top: 30px;
  left: 0;
  z-index: 50;
  display: none;
  width: 260px;
  padding: 10px;
  background: rgba(10, 18, 36, 0.98);
  border: 1px solid var(--border-medium);
  border-radius: 6px;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.45);
}

.mcp-pill:hover .mcp-popover {
  display: block;
}

.mcp-pop-title {
  color: var(--text-primary);
  font-size: 11px;
  font-weight: 800;
}

.mcp-line {
  margin: 4px 0 8px;
  overflow: hidden;
  color: var(--text-tertiary);
  text-overflow: ellipsis;
}

.mcp-grid {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 3px 8px;
}

.mcp-grid span {
  color: var(--text-tertiary);
}

.mcp-grid strong {
  color: var(--text-secondary);
}

.mcp-desc {
  margin-top: 8px;
  color: var(--text-secondary);
  line-height: 1.5;
  white-space: normal;
}
</style>
