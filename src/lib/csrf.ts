import crypto from 'crypto'
import type { Request } from 'express'

export function generateCsrfToken(): string {
  return crypto.randomBytes(32).toString('hex')
}

export function validateCsrfToken(sessionToken: string | undefined, requestToken: string | undefined): boolean {
  if (!sessionToken || !requestToken) return false
  if (sessionToken.length !== requestToken.length) return false
  return crypto.timingSafeEqual(Buffer.from(sessionToken), Buffer.from(requestToken))
}

export function getCsrfFromCookies(req: Request): string | undefined {
  const header = req.headers.cookie ?? ''
  for (const part of header.split(';')) {
    const [k, ...v] = part.trim().split('=')
    if (k?.trim() === 'csrf_token') return decodeURIComponent(v.join('='))
  }
  return undefined
}
