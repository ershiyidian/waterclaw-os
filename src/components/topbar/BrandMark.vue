<template>
  <div class="brand">
    <div class="brand-mark">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
      </svg>
    </div>
    <span class="brand-text">WATERCLAW OS</span>
    <span class="brand-ver">v3.3 · 桃浦河网中枢</span>
  </div>
</template>

<style scoped>
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 250px;
}

.brand-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-indigo));
  border-radius: 6px;
}

.brand-mark svg {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: #fff;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 2.2;
}

.brand-text {
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.5px;
}

.brand-ver {
  padding-left: 10px;
  margin-left: 8px;
  color: var(--text-tertiary);
  border-left: 1px solid var(--border-subtle);
  font-family: var(--font-mono);
  font-size: 10px;
}
</style>
