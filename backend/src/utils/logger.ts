export enum LogLevel {
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR',
  DEBUG = 'DEBUG',
}

function formatMessage(level: LogLevel, message: string, meta?: unknown): string {
  const timestamp = new Date().toISOString();
  const metaString = meta ? ` | ${JSON.stringify(meta)}` : '';
  return `[${timestamp}] [${level}] ${message}${metaString}`;
}

export const logger = {
  info: (message: string, meta?: unknown) => console.log(formatMessage(LogLevel.INFO, message, meta)),
  warn: (message: string, meta?: unknown) => console.warn(formatMessage(LogLevel.WARN, message, meta)),
  error: (message: string, meta?: unknown) => console.error(formatMessage(LogLevel.ERROR, message, meta)),
  debug: (message: string, meta?: unknown) => {
    if (process.env.DEBUG === 'true' || process.env.NODE_ENV === 'development') {
      console.debug(formatMessage(LogLevel.DEBUG, message, meta));
    }
  },
};
