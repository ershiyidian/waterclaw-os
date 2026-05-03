<template>
  <div v-if="visible" class="slash-menu">
    <div v-for="group in groups" :key="group.category" class="slash-group">
      <div class="slash-group-title">{{ group.category }}</div>
      <button v-for="cmd in group.commands" :key="cmd.command" type="button" class="slash-row" @click="$emit('select', cmd.command)">
        <span class="slash-command">{{ cmd.command }}</span>
        <span class="slash-label">{{ cmd.label }}</span>
        <span class="slash-params">{{ cmd.params }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { SLASH_COMMANDS } from '@/config/skills';

defineProps<{
  visible: boolean;
}>();

defineEmits<{
  select: [command: string];
}>();

const groups = computed(() => {
  const categories = [...new Set(SLASH_COMMANDS.map((cmd) => cmd.category))];
  return categories.map((category) => ({
    category,
    commands: SLASH_COMMANDS.filter((cmd) => cmd.category === category),
  }));
});
</script>

<style scoped>
.slash-menu {
  position: absolute;
  right: 14px;
  bottom: 84px;
  left: 14px;
  z-index: 90;
  max-height: 290px;
  padding: 10px;
  overflow-y: auto;
  background: rgba(10, 18, 36, 0.98);
  border: 1px solid var(--border-medium);
  border-radius: 7px;
  box-shadow: 0 14px 32px rgba(0, 0, 0, 0.5);
}

.slash-group + .slash-group {
  margin-top: 8px;
}

.slash-group-title {
  margin-bottom: 4px;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 1px;
  font-family: var(--font-mono);
  font-size: 8px;
  font-weight: 800;
}

.slash-row {
  display: grid;
  grid-template-columns: 78px 1fr auto;
  gap: 8px;
  width: 100%;
  padding: 6px;
  color: var(--text-secondary);
  text-align: left;
  cursor: pointer;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 4px;
  font-size: 10px;
}

.slash-row:hover {
  background: rgba(56, 189, 248, 0.06);
  border-color: rgba(56, 189, 248, 0.18);
}

.slash-command,
.slash-params {
  font-family: var(--font-mono);
}

.slash-command {
  color: var(--accent-blue);
  font-weight: 800;
}

.slash-params {
  color: var(--text-tertiary);
}
</style>
