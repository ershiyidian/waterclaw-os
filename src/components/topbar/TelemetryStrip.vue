<template>
  <div class="telem-strip">
    <div class="telem-item has-popover">
      <span class="telem-key">GNSS RTK</span>
      <span class="telem-val">
        <StatusDot :status="rtkTone" pulse />
        {{ telemetry.rtk.status }} {{ telemetry.rtk.precisionCm.toFixed(1) }}cm · HDOP {{ telemetry.rtk.hdop.toFixed(2) }}
      </span>
      <div class="telemetry-popover sky-popover">
        <div class="popover-title">Satellite Skyplot</div>
        <svg class="skyplot" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r="52" />
          <circle cx="60" cy="60" r="34" />
          <circle cx="60" cy="60" r="17" />
          <line x1="8" y1="60" x2="112" y2="60" />
          <line x1="60" y1="8" x2="60" y2="112" />
          <circle
            v-for="sat in telemetry.rtk.skyPlot"
            :key="sat.id + sat.constellation"
            :cx="satXY(sat).x"
            :cy="satXY(sat).y"
            r="2.3"
            :fill="sat.cn0 > 42 ? '#10b981' : sat.cn0 > 34 ? '#38bdf8' : '#f59e0b'"
          />
        </svg>
        <div class="sat-counts">
          GPS {{ telemetry.rtk.satellites.gps }} / BDS {{ telemetry.rtk.satellites.bds }} / GAL {{ telemetry.rtk.satellites.gal }} / GLO {{ telemetry.rtk.satellites.glo }}
        </div>
      </div>
    </div>

    <div class="telem-item">
      <span class="telem-key">Data Link</span>
      <span class="telem-val">
        <StatusDot :status="linkTone" pulse />
        4G {{ telemetry.link.primary.rssiDbm }}dBm · {{ telemetry.link.heartbeatMs }}ms
      </span>
      <span class="telem-sub">BDS backup {{ telemetry.link.backup.online ? 'ONLINE' : 'OFFLINE' }} · loss {{ telemetry.link.primary.packetLossPct.toFixed(1) }}%</span>
    </div>

    <div class="telem-item">
      <span class="telem-key">Edge AI (Orin)</span>
      <span class="telem-val">
        <StatusDot status="ok" pulse />
        {{ telemetry.edge.fps }}/{{ telemetry.edge.targetFps }}FPS · {{ telemetry.edge.loadPct }}% · {{ telemetry.edge.temperatureC }}C
      </span>
      <span class="telem-sub">{{ telemetry.edge.model }} · Q {{ telemetry.edge.queueDepth }}/{{ telemetry.edge.queueCapacity }}</span>
    </div>

    <div class="telem-item weather-item" :class="{ warn: telemetry.weather.rainfallMm > 5 }">
      <span class="telem-key">Weather</span>
      <span class="telem-val">
        <svg class="wind-vane" viewBox="0 0 20 20" :style="{ transform: `rotate(${telemetry.weather.windDeg}deg)` }">
          <path d="M10 2 L13 10 L10 8 L7 10 Z" />
          <line x1="10" y1="8" x2="10" y2="18" />
        </svg>
        {{ telemetry.weather.windDirection }} {{ telemetry.weather.windSpeedMps.toFixed(1) }}m/s · {{ telemetry.weather.condition }}
      </span>
      <span class="telem-sub">{{ telemetry.weather.pressureHpa }}hPa · rain {{ telemetry.weather.rainfallMm.toFixed(1) }}mm · vis {{ telemetry.weather.visibilityKm.toFixed(1) }}km</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { Satellite, TelemetryState } from '@/core/types/telemetry';
import StatusDot from '@/components/common/StatusDot.vue';
import { LINK_LATENCY_CRITICAL_MS, LINK_LATENCY_WARN_MS } from '@/config/thresholds';

const props = defineProps<{
  telemetry: TelemetryState;
}>();

const rtkTone = computed(() => {
  if (props.telemetry.rtk.status === 'SINGLE') return 'critical';
  if (props.telemetry.rtk.status === 'FLOAT') return 'warn';
  return 'ok';
});

const linkTone = computed(() => {
  const latency = props.telemetry.link.heartbeatMs;
  if (latency > LINK_LATENCY_CRITICAL_MS) return 'critical';
  if (latency > LINK_LATENCY_WARN_MS) return 'warn';
  return 'ok';
});

function satXY(sat: Satellite): { x: number; y: number } {
  const radius = 52 * (1 - sat.elevation / 90);
  const rad = ((sat.azimuth - 90) * Math.PI) / 180;
  return { x: 60 + Math.cos(rad) * radius, y: 60 + Math.sin(rad) * radius };
}
</script>

<style scoped>
.telem-strip {
  display: flex;
  align-items: center;
  gap: 18px;
}

.telem-item {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 128px;
}

.telem-key {
  color: var(--text-tertiary);
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
}

.telem-val {
  display: flex;
  align-items: center;
  gap: 5px;
  color: var(--text-secondary);
  white-space: nowrap;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
}

.telem-sub {
  max-width: 190px;
  overflow: hidden;
  color: var(--text-tertiary);
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: var(--font-mono);
  font-size: 8px;
}

.weather-item.warn {
  padding: 2px 8px;
  border: 1px solid rgba(245, 158, 11, 0.35);
  border-radius: 4px;
}

.wind-vane {
  width: 15px;
  height: 15px;
  fill: none;
  stroke: var(--accent-blue);
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.5;
  transition: transform 0.4s ease;
}

.telemetry-popover {
  position: absolute;
  top: 44px;
  left: 0;
  z-index: 60;
  display: none;
  width: 178px;
  padding: 10px;
  background: rgba(10, 18, 36, 0.98);
  border: 1px solid var(--border-medium);
  border-radius: 6px;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.45);
}

.has-popover:hover .telemetry-popover {
  display: block;
}

.popover-title {
  margin-bottom: 6px;
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 800;
}

.skyplot {
  width: 120px;
  height: 120px;
  display: block;
  margin: 0 auto;
}

.skyplot circle,
.skyplot line {
  fill: none;
  stroke: rgba(148, 163, 184, 0.18);
  stroke-width: 1;
}

.sat-counts {
  margin-top: 6px;
  color: var(--text-tertiary);
  text-align: center;
  font-family: var(--font-mono);
  font-size: 9px;
}
</style>
