<template>
  <div class="input-zone">
    <SlashMenu :visible="showSlash" @select="selectCommand" />
    <div class="cmd-wrap">
      <span class="cmd-caret">&gt;</span>
      <input
        v-model="value"
        class="cmd-input"
        type="text"
        placeholder="输入指令或自然语言提问..."
        @keydown.enter="submit"
        @keydown.esc="showSlash = false"
        @input="showSlash = value.startsWith('/')"
      />
    </div>
    <QuickChips @gb="$emit('gb')" @fleet="$emit('fleet')" @reset="$emit('reset')" :show-reset="showReset" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import QuickChips from './QuickChips.vue';
import SlashMenu from './SlashMenu.vue';

defineProps<{
  showReset: boolean;
}>();

const emit = defineEmits<{
  submit: [text: string];
  gb: [];
  fleet: [];
  reset: [];
}>();

const value = ref('');
const showSlash = ref(false);

function submit(): void {
  const text = value.value.trim();
  if (!text) return;
  value.value = '';
  showSlash.value = false;
  emit('submit', text);
}

function selectCommand(command: string): void {
  value.value = `${command} `;
  showSlash.value = false;
}
</script>

<style scoped>
.input-zone {
  position: relative;
  padding: 12px 14px;
  background: rgba(0, 0, 0, 0.15);
  border-top: 1px solid var(--border-subtle);
}

.cmd-wrap {
  display: flex;
  align-items: center;
  padding: 0 10px;
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  transition: border-color 0.2s ease;
}

.cmd-wrap:focus-within {
  border-color: var(--sem-ai);
}

.cmd-caret {
  margin-right: 6px;
  color: var(--sem-ai);
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 800;
}

.cmd-input {
  flex: 1;
  padding: 9px 0;
  color: var(--text-primary);
  background: transparent;
  border: none;
  outline: none;
  font-size: 12px;
}

.cmd-input::placeholder {
  color: var(--text-tertiary);
}
</style>
