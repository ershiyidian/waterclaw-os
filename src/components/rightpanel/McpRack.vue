<template>
  <div class="mcp-rack">
    <div class="rack-head">
      <span>Active Contexts</span>
      <span>{{ servers.length }} MCP</span>
    </div>
    <div class="mcp-scroll">
      <McpPill v-for="server in servers" :key="server.id" :server="server" />
    </div>
  </div>
</template>

<script setup lang="ts">
import McpPill from '@/components/common/McpPill.vue';
import type { McpServerStatus } from '@/core/types/mcp';

defineProps<{
  servers: McpServerStatus[];
}>();
</script>

<style scoped>
.mcp-rack {
  padding: 9px 14px;
  border-bottom: 1px solid var(--border-subtle);
}

.rack-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 7px;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 1px;
  font-family: var(--font-mono);
  font-size: 8px;
  font-weight: 800;
}

.mcp-scroll {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 2px;
}
</style>
