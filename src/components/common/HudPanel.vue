<template>
  <section class="hud-panel" :class="panelClass">
    <slot />
  </section>
</template>

<script setup lang="ts">
defineProps<{
  panelClass?: string | Array<string | Record<string, boolean>> | Record<string, boolean>;
}>();
</script>
