<template>
  <div ref="chartEl" class="chart-area" />
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import * as echarts from 'echarts';
import type { ECharts } from 'echarts';
import type { ChartTab } from '@/core/types/chart';
import { airOption, flowOption, generateAirData, generateFlowData, generateHealthData, generateWaterData, healthOption, waterOption } from '@/services/ChartService';

const props = defineProps<{
  tab: ChartTab;
  emergencySpike: boolean;
}>();

const chartEl = ref<HTMLDivElement | null>(null);
let chart: ECharts | null = null;

const waterData = computed(() => generateWaterData(props.emergencySpike));
const airData = generateAirData();
const flowData = generateFlowData();
const healthData = generateHealthData();

function currentOption() {
  if (props.tab === 'air') return airOption(airData);
  if (props.tab === 'flow') return flowOption(flowData);
  if (props.tab === 'health') return healthOption(healthData);
  return waterOption(waterData.value);
}

function render(notMerge = true): void {
  if (!chart) return;
  chart.setOption(currentOption(), notMerge);
}

onMounted(() => {
  if (!chartEl.value) return;
  chart = echarts.init(chartEl.value);
  render();
  window.addEventListener('resize', resize);
});

onUnmounted(() => {
  window.removeEventListener('resize', resize);
  chart?.dispose();
  chart = null;
});

watch(() => [props.tab, props.emergencySpike] as const, () => render(true));

function resize(): void {
  chart?.resize();
}
</script>

<style scoped>
.chart-area {
  width: 100%;
  height: calc(100% - 30px);
}
</style>
