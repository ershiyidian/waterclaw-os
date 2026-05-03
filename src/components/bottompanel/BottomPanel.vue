<template>
  <HudPanel panel-class="bottom-panel">
    <div class="chart-bar">
      <div class="panel-label chart-label">Analytics · LSTM Forecast</div>
      <ChartLegend />
      <ChartTabs :active="store.chart.activeTab" @change="store.setChartTab" />
    </div>
    <TimeSeriesChart :tab="store.chart.activeTab" :emergency-spike="store.chart.emergencySpike" />
  </HudPanel>
</template>

<script setup lang="ts">
import HudPanel from '@/components/common/HudPanel.vue';
import { useRootStore } from '@/core/StateStore';
import ChartLegend from './ChartLegend.vue';
import ChartTabs from './ChartTabs.vue';
import TimeSeriesChart from './TimeSeriesChart.vue';

const store = useRootStore();
</script>

<style scoped>
.chart-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
}

.chart-label {
  padding: 0;
  margin: 0;
  border: none;
}
</style>
