import { computed } from 'vue';
import { useRootStore } from '@/core/StateStore';

export function useFleetStore() {
  const root = useRootStore();
  return {
    fleet: computed(() => root.fleet),
    setUsvMode: root.setUsvMode,
    setUsvPosition: root.setUsvPosition,
    updateUsv: root.updateUsv,
  };
}
