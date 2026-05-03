<template>
  <div class="report-card">
    <div class="report-grade">III 类 · 达标</div>
    <div class="report-grid">
      <div v-for="row in rows" :key="row.key" class="report-row">
        <span>{{ row.key }}</span>
        <strong>{{ row.value }}</strong>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const rows = [
  { key: 'pH', value: '7.2' },
  { key: 'DO', value: '6.5 mg/L' },
  { key: '浊度', value: '42 NTU' },
  { key: 'NH3-N', value: '0.8 mg/L' },
  { key: 'CODMn', value: '4.2 mg/L' },
  { key: 'TDS', value: '385 mg/L' },
];
</script>

<style scoped>
.report-card {
  padding: 10px 12px;
  margin-top: 6px;
  background: var(--bg-inset);
  border-radius: 6px;
}

.report-grade {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  margin-bottom: 8px;
  color: var(--sem-ok);
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 4px;
  font-size: 13px;
  font-weight: 800;
}

.report-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
}

.report-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 3px 6px;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 3px;
  font-size: 11px;
}

.report-row span {
  color: var(--text-tertiary);
  font-family: var(--font-mono);
}

.report-row strong {
  color: var(--sem-ok);
  font-family: var(--font-mono);
}
</style>
