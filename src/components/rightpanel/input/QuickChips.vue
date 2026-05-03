<template>
  <div class="chips">
    <button class="chip" type="button" @click="$emit('gb')">GB3838 实时评价</button>
    <button class="chip" type="button" @click="$emit('fleet')">艇群状态汇总</button>
    <button v-if="showReset" class="chip" type="button" @click="$emit('reset')">重置为常态巡航</button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  showReset: boolean;
}>();

defineEmits<{
  gb: [];
  fleet: [];
  reset: [];
}>();
</script>

<style scoped>
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 8px;
}

.chip {
  padding: 3px 8px;
  color: var(--text-tertiary);
  cursor: pointer;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  font-size: 9px;
  font-weight: 600;
  transition: all 0.15s ease;
}

.chip:hover {
  color: var(--accent-blue);
  border-color: var(--accent-blue);
}

</style>
