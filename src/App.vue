<template>
  <main class="app-shell">
    <MapContainer />
    <TopBar />
    <LeftPanel />
    <BottomPanel />
    <RightPanel />
    <BootSequence v-if="!store.system.isBooted" @done="onBootDone" />
  </main>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import { agentClient } from '@/agents/AgentClient';
import BottomPanel from '@/components/bottompanel/BottomPanel.vue';
import BootSequence from '@/components/boot/BootSequence.vue';
import LeftPanel from '@/components/leftpanel/LeftPanel.vue';
import MapContainer from '@/components/map/MapContainer.vue';
import RightPanel from '@/components/rightpanel/RightPanel.vue';
import TopBar from '@/components/topbar/TopBar.vue';
import { useRootStore } from '@/core/StateStore';
import { telemetryService } from '@/services/TelemetryService';

const store = useRootStore();

function onBootDone(): void {
  store.markBooted();
  telemetryService.start();
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'l') {
    store.system.debugOpen = !store.system.debugOpen;
  }
  if (event.key === 'Escape' && store.agent.pendingApproval) {
    store.clearApproval();
  }
}

onMounted(() => {
  void agentClient.refreshMcpStatus();
  window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  telemetryService.stop();
  window.removeEventListener('keydown', handleKeydown);
});
</script>
