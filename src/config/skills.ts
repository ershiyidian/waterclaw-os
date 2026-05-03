import type { SkillCategory } from '@/core/types/agent';

export interface SlashCommand {
  command: string;
  label: string;
  category: SkillCategory;
  description: string;
  params: string;
}

export const SLASH_COMMANDS: SlashCommand[] = [
  { command: '/predict', label: 'LSTM时序预测', category: 'analytics', description: '预测指定站点未来水质趋势', params: 'station horizon' },
  { command: '/cluster', label: 'K-means异常聚类', category: 'analytics', description: '请求后端 Agent Host 评估是否需要聚类工具', params: 'k features' },
  { command: '/correlate', label: '多变量相关性', category: 'analytics', description: '分析水气双域指标相关性', params: 'window variables' },
  { command: '/gb3838', label: 'GB3838评价报告', category: 'reports', description: '生成国标分级报告', params: 'station target_class' },
  { command: '/dispatch', label: '派遣USV', category: 'fleet', description: '向MAVLink总线发送航行计划', params: 'usv target mission' },
  { command: '/recall', label: '召回USV', category: 'fleet', description: '召回艇群返回基站', params: 'scope' },
  { command: '/sentry', label: '建立监测哨位', category: 'fleet', description: '在下游断面建立扩散监测', params: 'usv station' },
  { command: '/escalate', label: '上报市水务局', category: 'emergency', description: '生成并推送一级预警工单', params: 'incident_id channel' },
];
