<template>
  <HudPanel panel-class="top-bar">
    <BrandMark />
    <TelemetryStrip :telemetry="store.telemetry" />
    <MissionClock :seconds="store.system.missionTimeSec" />
    <HardControls @rtl="handleRtl" @estop="handleEstop" />
  </HudPanel>
</template>

<script setup lang="ts">
import HudPanel from '@/components/common/HudPanel.vue';
import { agentClient } from '@/agents/AgentClient';
import { useRootStore } from '@/core/StateStore';
import BrandMark from './BrandMark.vue';
import HardControls from './HardControls.vue';
import MissionClock from './MissionClock.vue';
import TelemetryStrip from './TelemetryStrip.vue';

const store = useRootStore();

function handleRtl(): void {
  store.addFeed({
    role: 'system',
    severity: 'warn',
    content: 'RTL 返航请求已提交后端审批。当前未写入控制总线，等待人工确认与后端回执。',
  });
  void agentClient.requestControl('rtl_usv', {
    usvs: ['USV-01', 'USV-02'],
    reason: '操作员从顶部硬控制区请求全艇 RTL 返航。',
  }).catch((error: unknown) => {
    const message = error instanceof Error ? error.message : String(error);
    store.addFeed({ role: 'system', severity: 'warn', content: `RTL 请求提交失败：${message}` });
  });
}

function handleEstop(): void {
  store.system.alertLevel = 'critical';
  store.addFeed({
    role: 'system',
    severity: 'critical',
    content: 'E-STOP 请求已提交后端安全控制通道。当前仅代表请求状态，未收到后端 ACK 前不宣称物理断电。',
  });
  void agentClient.requestControl('request_estop', {
    usvs: ['USV-01', 'USV-02'],
    reason: '操作员从顶部硬控制区请求 E-STOP 安全动作。',
  }).catch((error: unknown) => {
    const message = error instanceof Error ? error.message : String(error);
    store.addFeed({ role: 'system', severity: 'warn', content: `E-STOP 请求提交失败：${message}` });
  });
}
</script>
