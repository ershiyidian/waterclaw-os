<template>
  <div class="horizon">
    <div class="horizon-disc" :style="{ transform: `rotate(${-roll}deg) translateY(${pitch * 0.6}px)` }">
      <div class="sky" />
      <div class="ground" />
      <div class="horizon-line" />
    </div>
    <div class="horizon-aircraft" />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  roll: number;
  pitch: number;
}>();
</script>

<style scoped>
.horizon {
  position: relative;
  width: 40px;
  height: 40px;
  overflow: hidden;
  background: #020617;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 50%;
}

.horizon-disc {
  position: absolute;
  inset: -20%;
  transition: transform 0.35s ease;
}

.sky,
.ground {
  position: absolute;
  left: 0;
  right: 0;
  height: 50%;
}

.sky {
  top: 0;
  background: linear-gradient(180deg, rgba(56, 189, 248, 0.55), rgba(56, 189, 248, 0.18));
}

.ground {
  bottom: 0;
  background: linear-gradient(180deg, rgba(120, 83, 38, 0.54), rgba(88, 55, 28, 0.4));
}

.horizon-line {
  position: absolute;
  top: 50%;
  left: 8%;
  right: 8%;
  height: 1px;
  background: rgba(255, 255, 255, 0.45);
}

.horizon-aircraft {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 22px;
  height: 1px;
  background: var(--sem-warn);
  transform: translate(-50%, -50%);
}

.horizon-aircraft::before,
.horizon-aircraft::after {
  position: absolute;
  top: 0;
  width: 5px;
  height: 1px;
  content: "";
  background: var(--sem-warn);
}

.horizon-aircraft::before {
  left: -2px;
  transform: rotate(35deg);
}

.horizon-aircraft::after {
  right: -2px;
  transform: rotate(-35deg);
}
</style>
