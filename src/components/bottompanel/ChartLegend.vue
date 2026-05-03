<template>
  <div class="chart-legend">
    <span><i class="real" /> 实测</span>
    <span><i class="pred" /> LSTM预测</span>
    <span><i class="ci" /> 95% CI</span>
    <span><i class="baseline" /> 昨日同期</span>
  </div>
</template>

<style scoped>
.chart-legend {
  display: flex;
  gap: 10px;
  color: var(--text-tertiary);
  font-family: var(--font-mono);
  font-size: 8px;
}

.chart-legend span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.chart-legend i {
  display: block;
  width: 12px;
  height: 2px;
  border-radius: 2px;
}

.real {
  background: var(--accent-blue);
}

.pred {
  background: var(--accent-indigo);
}

.ci {
  background: rgba(129, 140, 248, 0.35);
}

.baseline {
  background: rgba(148, 163, 184, 0.4);
}
</style>
