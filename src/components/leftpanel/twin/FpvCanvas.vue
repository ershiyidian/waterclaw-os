<template>
  <div class="fpv-cell">
    <div class="fpv-scene" :style="{ transform: `translateX(${(heading - 145) * 0.12}px)` }">
      <div class="fpv-horizon" />
      <div class="fpv-water" />
      <div class="fpv-bank-l" />
      <div class="fpv-bank-r" />
      <div class="fpv-glint" />
      <div class="fpv-crosshair" />
    </div>
    <div class="fpv-hud">
      {{ usvId }} | {{ timecode }} | {{ position[0].toFixed(4) }}N {{ position[1].toFixed(4) }}E | HDG {{ Math.round(heading) }} | SPD {{ speed.toFixed(1) }}m/s
    </div>
    <div class="rec-code"><span /> REC {{ timecode }}</div>
    <div
      class="yolo-box"
      :class="{ locked: yolo.locked, unstable: yolo.confidence < 0.7 }"
      :style="{ top: `${yolo.box.top}%`, left: `${yolo.box.left}%`, width: `${yolo.box.width}%`, height: `${yolo.box.height}%` }"
    >
      <div class="yolo-corner tl" />
      <div class="yolo-corner tr" />
      <div class="yolo-corner bl" />
      <div class="yolo-corner br" />
      <div class="yolo-tag">{{ yolo.label }} {{ Math.round(yolo.confidence * 100) }}%</div>
    </div>
    <div class="twin-cell-label">YOLO V8 · VIS</div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue';
import type { LatLngTuple } from '@/core/types/common';
import type { UsvState } from '@/core/types/usv';
import { formatTimecode } from '@/utils/time';

defineProps<{
  usvId: string;
  position: LatLngTuple;
  heading: number;
  speed: number;
  yolo: UsvState['yolo'];
}>();

const timecode = ref(formatTimecode());
let timer = 0;
let frame = 0;

onMounted(() => {
  timer = window.setInterval(() => {
    frame = (frame + 1) % 30;
    timecode.value = formatTimecode(Date.now(), frame);
  }, 120);
});

onUnmounted(() => window.clearInterval(timer));
</script>

<style scoped>
.fpv-cell {
  position: relative;
  overflow: hidden;
  background: #070d18;
  border-radius: 3px;
}

.fpv-scene {
  position: absolute;
  inset: -2px;
  background: linear-gradient(180deg, #0c1a2e 0%, #0a1628 40%, #061020 60%, #081828 100%);
  animation: fpvBob 4s ease-in-out infinite;
  transition: transform 0.35s ease;
}

.fpv-horizon {
  position: absolute;
  top: 42%;
  right: 0;
  left: 0;
  height: 1px;
  background: rgba(56, 189, 248, 0.2);
}

.fpv-water {
  position: absolute;
  inset: 43% 0 0;
  background:
    repeating-linear-gradient(0deg, rgba(56, 189, 248, 0.04) 0, transparent 1px, transparent 6px),
    linear-gradient(180deg, #081422, #050e1a);
  animation: waterShift 3s ease-in-out infinite;
}

.fpv-bank-l,
.fpv-bank-r {
  position: absolute;
  top: 32%;
  height: 12%;
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.66), rgba(30, 41, 59, 0.22));
}

.fpv-bank-l {
  left: 0;
  width: 15%;
}

.fpv-bank-r {
  right: 0;
  width: 18%;
}

.fpv-glint {
  position: absolute;
  top: 40%;
  left: 0;
  width: 40%;
  height: 80%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.14), transparent);
  animation: fpvGlint 3.4s ease-in-out infinite;
}

.fpv-crosshair {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 20px;
  height: 20px;
  transform: translate(-50%, -50%);
}

.fpv-crosshair::before,
.fpv-crosshair::after {
  position: absolute;
  content: "";
  background: rgba(56, 189, 248, 0.3);
}

.fpv-crosshair::before {
  top: 0;
  left: 50%;
  width: 1px;
  height: 100%;
  transform: translateX(-50%);
}

.fpv-crosshair::after {
  top: 50%;
  left: 0;
  width: 100%;
  height: 1px;
  transform: translateY(-50%);
}

.fpv-hud {
  position: absolute;
  top: 3px;
  left: 4px;
  z-index: 4;
  max-width: calc(100% - 8px);
  overflow: hidden;
  color: rgba(226, 232, 240, 0.78);
  text-shadow: 0 1px 1px #000, 0 0 2px #000;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: var(--font-mono);
  font-size: 6.8px;
  font-weight: 700;
}

.rec-code {
  position: absolute;
  right: 4px;
  bottom: 3px;
  z-index: 4;
  display: flex;
  align-items: center;
  gap: 3px;
  color: rgba(255, 255, 255, 0.55);
  font-family: var(--font-mono);
  font-size: 6.8px;
}

.rec-code span {
  width: 5px;
  height: 5px;
  background: var(--sem-critical);
  border-radius: 50%;
  animation: miniBlink 1s ease-in-out infinite;
}

.yolo-box {
  position: absolute;
  z-index: 5;
  border: none;
  animation: yoloJitter 0.22s steps(2, end) infinite;
  transition: all 0.4s ease;
}

.yolo-corner {
  position: absolute;
  width: 6px;
  height: 6px;
  border-color: var(--sem-warn);
  border-style: solid;
}

.yolo-box.locked .yolo-corner {
  border-color: var(--sem-critical);
  filter: drop-shadow(0 0 4px rgba(239, 68, 68, 0.7));
}

.yolo-box.unstable .yolo-corner {
  border-style: dashed;
}

.yolo-corner.tl {
  top: 0;
  left: 0;
  border-width: 1px 0 0 1px;
}

.yolo-corner.tr {
  top: 0;
  right: 0;
  border-width: 1px 1px 0 0;
}

.yolo-corner.bl {
  bottom: 0;
  left: 0;
  border-width: 0 0 1px 1px;
}

.yolo-corner.br {
  right: 0;
  bottom: 0;
  border-width: 0 1px 1px 0;
}

.yolo-tag {
  position: absolute;
  top: -13px;
  left: 0;
  padding: 1px 3px;
  color: #000;
  white-space: nowrap;
  background: var(--sem-warn);
  border-radius: 1px;
  font-family: var(--font-mono);
  font-size: 7px;
  font-weight: 800;
}

.yolo-box.locked .yolo-tag {
  color: #fff;
  background: var(--sem-critical);
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
