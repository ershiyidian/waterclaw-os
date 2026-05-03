<template>
  <div class="lidar-cell">
    <div class="lidar-grid">
      <div class="range-ring r1"><span>50m</span></div>
      <div class="range-ring r2"><span>20m</span></div>
      <div class="range-ring r3"><span>10m</span></div>
      <div class="range-ring r4"><span>5m</span></div>
      <div class="lidar-sweep" />
      <div class="ownship" :style="{ transform: `translate(-50%, -50%) rotate(${heading}deg)` }" />
      <div class="prediction-line" :style="{ transform: `rotate(${heading}deg)` }" />
      <span
        v-for="dot in dots"
        :key="dot.id"
        class="lidar-dot"
        :style="{ left: `${dot.x}%`, top: `${dot.y}%`, width: `${dot.s}px`, height: `${dot.s}px`, background: dot.color, animationDelay: `${dot.delay}s` }"
      />
      <svg class="obstacle-layer" viewBox="0 0 100 100" preserveAspectRatio="none">
        <polygon points="62,31 75,38 72,52 58,48 54,38" />
      </svg>
      <div class="obstacle-tag">obstacle 8m @045</div>
    </div>
    <div class="twin-cell-label">LiDAR 32L · BEV</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  heading: number;
}>();

const dots = Array.from({ length: 34 }, (_, i) => {
  const dist = (i * 17) % 48;
  const near = dist < 18;
  return {
    id: i,
    x: 12 + ((i * 19) % 76),
    y: 13 + ((i * 23) % 74),
    s: near ? 3 : 2,
    delay: (i % 8) * 0.17,
    color: near ? 'rgba(239,68,68,0.72)' : dist < 34 ? 'rgba(245,158,11,0.62)' : 'rgba(56,189,248,0.62)',
  };
});
</script>

<style scoped>
.lidar-cell {
  position: relative;
  overflow: hidden;
  background: #070d18;
  border-radius: 3px;
}

.lidar-grid {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.range-ring {
  position: absolute;
  border: 1px solid rgba(56, 189, 248, 0.09);
  border-radius: 50%;
}

.range-ring span {
  position: absolute;
  right: 2px;
  bottom: 48%;
  color: rgba(148, 163, 184, 0.38);
  font-family: var(--font-mono);
  font-size: 6px;
}

.r1 {
  width: 84%;
  height: 84%;
}

.r2 {
  width: 60%;
  height: 60%;
}

.r3 {
  width: 38%;
  height: 38%;
}

.r4 {
  width: 18%;
  height: 18%;
}

.lidar-sweep {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 50%;
  height: 2px;
  background: linear-gradient(90deg, rgba(56, 189, 248, 0.55), transparent);
  transform-origin: left center;
  animation: lidarSpin 2.5s linear infinite;
}

.ownship {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-right: 5px solid transparent;
  border-bottom: 14px solid var(--accent-blue);
  border-left: 5px solid transparent;
  filter: drop-shadow(0 0 5px rgba(56, 189, 248, 0.5));
  transform-origin: center 70%;
}

.prediction-line {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 1px;
  height: 38%;
  border-left: 1px dashed rgba(255, 255, 255, 0.45);
  transform-origin: top center;
}

.lidar-dot {
  position: absolute;
  border-radius: 50%;
  animation: dotFlicker 2s ease-in-out infinite;
}

.obstacle-layer {
  position: absolute;
  inset: 0;
}

.obstacle-layer polygon {
  fill: rgba(245, 158, 11, 0.12);
  stroke: rgba(245, 158, 11, 0.7);
  stroke-width: 1;
}

.obstacle-tag {
  position: absolute;
  top: 28%;
  right: 4%;
  padding: 1px 3px;
  color: #020617;
  background: var(--sem-warn);
  border-radius: 2px;
  font-family: var(--font-mono);
  font-size: 6.5px;
  font-weight: 800;
}

.twin-cell-label {
  position: absolute;
  bottom: 3px;
  left: 4px;
  z-index: 4;
  color: rgba(255, 255, 255, 0.35);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-family: var(--font-mono);
  font-size: 7px;
  font-weight: 700;
}
</style>
