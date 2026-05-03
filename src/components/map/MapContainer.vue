<template>
  <div ref="mapEl" class="map-foundation" />
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { onMounted, onUnmounted, watch } from 'vue';
import { useRootStore } from '@/core/StateStore';
import { mapService } from '@/services/MapService';

const store = useRootStore();
const mapEl = ref<HTMLDivElement | null>(null);

onMounted(() => {
  if (mapEl.value) mapService.init(mapEl.value);
});

onUnmounted(() => {
  mapService.destroy();
});

watch(
  () => [
    store.fleet['USV-01'].position,
    store.fleet['USV-01'].headingDeg,
    store.fleet['USV-02'].position,
    store.fleet['USV-02'].headingDeg,
    store.map.emergencyDrainId,
    store.map.spreadVisible,
    store.map.clusterVisible,
    store.map.blockadeVisible,
    store.map.focusTarget,
  ],
  () => mapService.sync(),
  { deep: true },
);
</script>
