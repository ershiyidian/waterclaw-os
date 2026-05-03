import { computed } from 'vue';
import { useRootStore } from '@/core/StateStore';

export function useSystemStore() {
  const root = useRootStore();
  return {
    system: computed(() => root.system),
    markBooted: root.markBooted,
    setMissionTime: root.setMissionTime,
  };
}
