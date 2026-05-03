import type { Severity } from './common';

export type AgentStatus = 'idle' | 'thinking' | 'tool_call' | 'awaiting_approval';
export type AgentMode = 'conversation' | 'plan' | 'trace';
export type ToolStatus = 'pending' | 'running' | 'success' | 'failed' | 'awaiting_approval';
export type SkillCategory = 'analytics' | 'perception' | 'reports' | 'fleet' | 'emergency' | 'communications';
export type RiskLevel = 'safe' | 'confirm' | 'critical';

export interface TokenUsage {
  input: number;
  output: number;
  costCny: number;
}

export interface ToolCall {
  id: string;
  toolName: string;
  category: SkillCategory;
  status: ToolStatus;
  startedAt: number;
  endedAt?: number;
  durationMs?: number;
  args: Record<string, unknown>;
  result?: unknown;
  error?: string;
  mcpServer?: string;
  riskLevel: RiskLevel;
  replayable: boolean;
}

export interface ReActStep {
  id: string;
  thought: string;
  action?: string;
  observation?: string;
  status: ToolStatus;
}

export interface ApprovalAction {
  id: string;
  title: string;
  description: string;
  riskLevel: RiskLevel;
  autoCancelSeconds: number;
  requestedAt: number;
  command: string;
  payload: Record<string, unknown>;
  requiresHoldMs?: number;
  requiresCode?: boolean;
}

export type ApprovalActionInput = Omit<ApprovalAction, 'id' | 'requestedAt'> & {
  id?: string;
  requestedAt?: number;
};

export interface MemoryState {
  shortTerm: Record<string, string>;
  longTerm: Record<string, string>;
  toolCache: Array<{
    key: string;
    value: string;
    updatedAt: number;
  }>;
}

export interface AgentState {
  sessionId: string;
  mode: AgentMode;
  status: AgentStatus;
  currentMission: string;
  tokenUsage: TokenUsage;
  pendingApproval: ApprovalAction | null;
  reactSteps: ReActStep[];
  toolCalls: ToolCall[];
  memory: MemoryState;
}

export type MessageRole = 'user' | 'assistant' | 'system' | 'tool_call' | 'mcp_resource_read' | 'approval';

export interface FeedMessage {
  id: string;
  role: MessageRole;
  timestamp: number;
  content?: string;
  severity?: Severity;
  toolCallId?: string;
  approvalId?: string;
  report?: Record<string, unknown>;
}

export interface SkillDefinition<I = Record<string, unknown>, O = unknown> {
  name: string;
  label: string;
  category: SkillCategory;
  description: string;
  parameters: Record<string, unknown>;
  requiredMcp: string[];
  riskLevel: RiskLevel;
  execute(args: I, ctx: ToolContext): Promise<O>;
}

export interface ToolContext {
  now: () => number;
  getMcp: (serverId: string) => unknown;
}
