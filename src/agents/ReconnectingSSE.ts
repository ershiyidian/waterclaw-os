export interface AgentEvent {
  id?: string;
  type: string;
  data: Record<string, unknown>;
}

export interface SSEOptions {
  onEvent: (event: AgentEvent) => void;
  onError?: (error: Error) => void;
  maxRetries?: number;
  baseDelay?: number;
  maxDelay?: number;
  signal?: AbortSignal;
}

export function parseSseChunk(buffer: string): { events: AgentEvent[]; rest: string } {
  const blocks = buffer.split(/\r?\n\r?\n/);
  const rest = blocks.pop() ?? '';
  const events: AgentEvent[] = [];

  for (const block of blocks) {
    let eventName = 'message';
    let eventId: string | undefined;
    const dataLines: string[] = [];
    block.split(/\r?\n/).forEach((line) => {
      if (line.startsWith('id:')) eventId = line.slice(3).trim();
      if (line.startsWith('event:')) eventName = line.slice(6).trim();
      if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
    });
    if (!dataLines.length) continue;
    try {
      events.push({ id: eventId, type: eventName, data: JSON.parse(dataLines.join('\n')) as Record<string, unknown> });
    } catch {
      events.push({ id: eventId, type: eventName, data: { content: dataLines.join('\n') } });
    }
  }

  return { events, rest };
}

export class ReconnectingSSE {
  private retryCount = 0;
  private abortController: AbortController | null = null;
  private lastEventId: string | null = null;
  private closed = false;

  constructor(
    private readonly url: string,
    private readonly options: SSEOptions,
  ) {}

  async connect(payload?: Record<string, unknown>, method: 'GET' | 'POST' = 'POST'): Promise<void> {
    this.closed = false;
    this.abortController = new AbortController();
    const headers: Record<string, string> = { Accept: 'text/event-stream' };
    if (method === 'POST') headers['Content-Type'] = 'application/json';
    if (this.lastEventId) headers['Last-Event-ID'] = this.lastEventId;
    const signal = this.composeSignal(this.abortController.signal, this.options.signal);

    try {
      const response = await fetch(this.url, {
        method,
        headers,
        body: method === 'POST' ? JSON.stringify(payload ?? {}) : undefined,
        signal,
      });
      if (!response.ok || !response.body) {
        const text = await response.text();
        throw new Error(`SSE HTTP ${response.status}: ${text}`);
      }
      await this.read(response.body);
    } catch (error) {
      if (this.closed || this.abortController.signal.aborted || this.options.signal?.aborted) return;
      this.options.onError?.(error instanceof Error ? error : new Error(String(error)));
      await this.reconnect(payload, method);
    }
  }

  close(): void {
    this.closed = true;
    this.abortController?.abort();
  }

  private async read(body: ReadableStream<Uint8Array>): Promise<void> {
    const reader = body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parsed = parseSseChunk(buffer);
      buffer = parsed.rest;
      parsed.events.forEach((event) => {
        if (event.id) this.lastEventId = event.id;
        this.options.onEvent(event);
        this.retryCount = 0;
      });
    }
    if (buffer.trim()) {
      parseSseChunk(`${buffer}\n\n`).events.forEach((event) => {
        if (event.id) this.lastEventId = event.id;
        this.options.onEvent(event);
      });
    }
  }

  private async reconnect(payload: Record<string, unknown> | undefined, method: 'GET' | 'POST'): Promise<void> {
    const maxRetries = this.options.maxRetries ?? 5;
    if (this.retryCount >= maxRetries) return;
    this.retryCount += 1;
    const baseDelay = this.options.baseDelay ?? 1000;
    const maxDelay = this.options.maxDelay ?? 30000;
    const delay = Math.min(baseDelay * 2 ** this.retryCount, maxDelay);
    await new Promise((resolve) => window.setTimeout(resolve, delay));
    if (!this.closed) await this.connect(payload, method);
  }

  private composeSignal(primary: AbortSignal, secondary?: AbortSignal): AbortSignal {
    if (!secondary) return primary;
    const controller = new AbortController();
    const abort = () => controller.abort();
    primary.addEventListener('abort', abort, { once: true });
    secondary.addEventListener('abort', abort, { once: true });
    return controller.signal;
  }
}
