<template>
  <div class="bubble alert-bubble">
    <strong class="text-crit">{{ title }}</strong>
    <div class="alert-content"><slot /></div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
}>();
</script>

<style scoped>
.alert-content {
  margin-top: 5px;
}
</style>
