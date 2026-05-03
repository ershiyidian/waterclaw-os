<template>
  <HudPanel panel-class="left-panel">
    <div class="panel-label">USV Fleet · Digital Twin</div>
    <UsvCard :usv="store.fleet['USV-01']" expanded />
    <UsvCard :usv="store.fleet['USV-02']" />
  </HudPanel>
</template>

<script setup lang="ts">
import HudPanel from '@/components/common/HudPanel.vue';
import { useRootStore } from '@/core/StateStore';
import UsvCard from './UsvCard.vue';

const store = useRootStore();
</script>
