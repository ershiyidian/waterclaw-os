import { computed } from 'vue';
import { useRootStore } from '@/core/StateStore';

export function useAgentStore() {
  const root = useRootStore();
  return {
    agent: computed(() => root.agent),
    addReActStep: root.addReActStep,
    addToolCall: root.addToolCall,
    clearApproval: root.clearApproval,
    requestApproval: root.requestApproval,
    setAgentMode: root.setAgentMode,
    setAgentStatus: root.setAgentStatus,
    updateToolCall: root.updateToolCall,
  };
}
