type Handler<T = unknown> = (payload: T) => void;

export enum AppEvent {
  TELEMETRY_TICK = 'TELEMETRY_TICK',
  USV_STATE_CHANGED = 'USV_STATE_CHANGED',
  ALERT_RAISED = 'ALERT_RAISED',
  ALERT_RESOLVED = 'ALERT_RESOLVED',
  AGENT_THINKING_START = 'AGENT_THINKING_START',
  AGENT_TOOL_INVOKED = 'AGENT_TOOL_INVOKED',
  AGENT_TOOL_COMPLETED = 'AGENT_TOOL_COMPLETED',
  AGENT_REQUESTS_APPROVAL = 'AGENT_REQUESTS_APPROVAL',
  USER_APPROVED = 'USER_APPROVED',
  USER_REJECTED = 'USER_REJECTED',
  MAP_FOCUS_REQUESTED = 'MAP_FOCUS_REQUESTED',
  CHART_RANGE_CHANGED = 'CHART_RANGE_CHANGED',
  MCP_CONNECTION_CHANGED = 'MCP_CONNECTION_CHANGED',
}

class EventBus {
  private handlers = new Map<AppEvent, Set<Handler>>();

  on<T>(event: AppEvent, handler: Handler<T>): () => void {
    const set = this.handlers.get(event) ?? new Set<Handler>();
    set.add(handler as Handler);
    this.handlers.set(event, set);
    return () => set.delete(handler as Handler);
  }

  emit<T>(event: AppEvent, payload: T): void {
    const set = this.handlers.get(event);
    if (!set) return;
    set.forEach((handler) => handler(payload));
  }
}

export const eventBus = new EventBus();
