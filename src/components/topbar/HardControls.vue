<template>
  <div class="ctrl-group">
    <button class="btn-rtl" type="button" @click="$emit('rtl')">RTL 返航</button>
    <button class="btn-estop" type="button" @click="$emit('estop')">E-STOP</button>
  </div>
</template>

<script setup lang="ts">
defineEmits<{
  rtl: [];
  estop: [];
}>();
</script>

<style scoped>
.ctrl-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-rtl,
.btn-estop {
  height: 30px;
  padding: 0 14px;
  cursor: pointer;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  transition: all 0.15s ease;
}

.btn-rtl {
  color: var(--text-primary);
  background: transparent;
  border: 1px solid var(--border-medium);
}

.btn-rtl:hover {
  color: var(--sem-warn);
  background: var(--bg-card-hover);
  border-color: var(--sem-warn);
}

.btn-estop {
  position: relative;
  overflow: hidden;
  color: #fff;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  background: linear-gradient(135deg, #991b1b, #7f1d1d);
  border: 1px solid #dc2626;
}

.btn-estop::before {
  position: absolute;
  inset: 0;
  content: "";
  background: repeating-linear-gradient(-45deg, transparent, transparent 4px, rgba(255, 255, 255, 0.06) 4px, rgba(255, 255, 255, 0.06) 8px);
}

.btn-estop:hover {
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.35);
  transform: scale(1.03);
}
</style>
