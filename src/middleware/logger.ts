import winston from 'winston'
import DailyRotateFile from 'winston-daily-rotate-file'
import type { Request, Response, NextFunction } from 'express'
import fs from 'fs'
import path from 'path'

// Em serverless (Vercel/Lambda) o filesystem é read-only — usar /tmp para logs
const logsDir = process.env.VERCEL ? '/tmp/logs' : 'logs'
fs.mkdirSync(logsDir, { recursive: true })

const transports: winston.transport[] = [
  new winston.transports.Console({
    format: winston.format.combine(winston.format.colorize(), winston.format.simple()),
  }),
]

if (!process.env.VERCEL) {
  transports.push(
    new DailyRotateFile({
      filename: path.join(logsDir, 'app-%DATE%.log'),
      datePattern: 'YYYY-MM-DD',
      maxFiles: '14d',
    })
  )
}

export const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports,
})

export function requestLogger(req: Request, res: Response, next: NextFunction): void {
  const start = Date.now()
  res.on('finish', () => {
    logger.info('request', {
      method: req.method,
      path: req.path,
      status: res.statusCode,
      ms: Date.now() - start,
      ip: req.ip,
    })
  })
  next()
}
