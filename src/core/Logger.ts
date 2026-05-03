export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogRecord {
  level: LogLevel;
  scope: string;
  message: string;
  timestamp: number;
  data?: unknown;
}

class Logger {
  private ring: LogRecord[] = [];
  private max = 1000;

  log(level: LogLevel, scope: string, message: string, data?: unknown): void {
    const record: LogRecord = { level, scope, message, timestamp: Date.now(), data };
    this.ring.push(record);
    if (this.ring.length > this.max) this.ring.shift();
    const method = level === 'debug' ? 'debug' : level;
    console[method](`[${scope}] ${message}`, data ?? '');
  }

  debug(scope: string, message: string, data?: unknown): void {
    this.log('debug', scope, message, data);
  }

  info(scope: string, message: string, data?: unknown): void {
    this.log('info', scope, message, data);
  }

  warn(scope: string, message: string, data?: unknown): void {
    this.log('warn', scope, message, data);
  }

  error(scope: string, message: string, data?: unknown): void {
    this.log('error', scope, message, data);
  }

  recent(): LogRecord[] {
    return [...this.ring];
  }
}

export const logger = new Logger();
