import { computed } from 'vue';
import { useRootStore } from '@/core/StateStore';

export function useMapStore() {
  const root = useRootStore();
  return {
    map: computed(() => root.map),
    resetIncidentProjection: root.resetIncidentProjection,
    setBlockadeVisible: root.setBlockadeVisible,
  };
}
