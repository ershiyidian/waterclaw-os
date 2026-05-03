export type ConnectionStatus = 'connected' | 'degraded' | 'offline' | 'calling';
export type McpPermission = 'read-only' | 'read-write' | 'restricted';

export interface McpCapabilities {
  resources: number;
  tools: number;
  prompts: number;
}

export interface McpServerStatus {
  id: string;
  name: string;
  icon: 'database' | 'stream' | 'api' | 'bus' | 'map' | 'weather' | 'llm';
  endpoint: string;
  status: ConnectionStatus;
  permission: McpPermission;
  capabilities: McpCapabilities;
  callCount: number;
  latencyMs: number;
  lastCallAt: number | null;
  description: string;
}

export interface McpResource {
  uri: string;
  name: string;
  mimeType: string;
}

export interface McpAdapter {
  serverId: string;
  endpoint: string;
  status: ConnectionStatus;
  capabilities: McpCapabilities;
  connect(): Promise<void>;
  listResources(): Promise<McpResource[]>;
  readResource(uri: string): Promise<unknown>;
  callTool(name: string, args: Record<string, unknown>): Promise<unknown>;
}
