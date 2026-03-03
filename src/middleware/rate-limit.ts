import type { RequestHandler } from 'express'

interface Attempt {
  timestamp: number
}

class RateLimiter {
  private attempts = new Map<string, Attempt[]>()

  constructor(
    private maxAttempts: number,
    private windowMs: number,
    private blockMs: number,
  ) {}

  isBlocked(ip: string): boolean {
    this.cleanup()
    const list = this.attempts.get(ip) ?? []
    if (list.length >= this.maxAttempts) {
      const last = list[list.length - 1].timestamp
      if (Date.now() - last < this.blockMs) return true
    }
    return false
  }

  recordAttempt(ip: string, success: boolean): void {
    this.cleanup()
    if (success) {
      this.attempts.delete(ip)
      return
    }
    const list = this.attempts.get(ip) ?? []
    list.push({ timestamp: Date.now() })
    this.attempts.set(ip, list)
  }

  getRemainingAttempts(ip: string): number {
    this.cleanup()
    const used = this.attempts.get(ip)?.length ?? 0
    return Math.max(0, this.maxAttempts - used)
  }

  private cleanup(): void {
    const cutoff = Date.now() - this.windowMs
    for (const [ip, list] of this.attempts) {
      const fresh = list.filter(a => a.timestamp > cutoff)
      if (fresh.length === 0) this.attempts.delete(ip)
      else this.attempts.set(ip, fresh)
    }
  }
}

export function createRateLimiter(
  maxAttempts: number,
  windowMs: number,
  blockMs: number,
): { limiter: RateLimiter; middleware: RequestHandler } {
  const limiter = new RateLimiter(maxAttempts, windowMs, blockMs)

  const middleware: RequestHandler = (req, res, next) => {
    const ip = req.ip ?? 'unknown'
    if (limiter.isBlocked(ip)) {
      res.status(429).json({ status: 'error', message: 'Muitas tentativas. Tente novamente em alguns minutos.' })
      return
    }
    limiter.recordAttempt(ip, false)
    next()
  }

  return { limiter, middleware }
}

// Login rate limiter: 5 attempts / 5 min window / 15 min block
export const loginRateLimiter = new RateLimiter(5, 5 * 60 * 1000, 15 * 60 * 1000)

// Alias for backward compatibility (used by auth.ts)
export const rateLimiter = loginRateLimiter

// Message rate limiter: 5 messages / 15 min / 15 min block
export const { middleware: mensagemRateLimitMiddleware } = createRateLimiter(5, 15 * 60 * 1000, 15 * 60 * 1000)
