import type { Request, Response, NextFunction } from 'express'
import { getAuth } from '@clerk/express'
import { generateCsrfToken, getCsrfFromCookies } from '../lib/csrf'

export async function checkSession(req: Request, res: Response, next: NextFunction): Promise<void> {
  // Load current user from Clerk (only if keys configured)
  if (process.env.CLERK_PUBLISHABLE_KEY && process.env.CLERK_SECRET_KEY) {
    const { userId, sessionClaims } = getAuth(req)
    if (userId) {
      const metadata = sessionClaims?.metadata as { role?: string } | undefined
      res.locals.currentUser = {
        id: 0,
        username: (sessionClaims?.email as string) ?? userId,
        role: metadata?.role ?? 'viewer',
      }
    } else {
      res.locals.currentUser = null
    }
  } else {
    res.locals.currentUser = null
  }

  // CSRF token — double-submit cookie pattern (stateless, funciona em Vercel multi-instância)
  const existingToken = getCsrfFromCookies(req)
  const csrfToken = existingToken ?? generateCsrfToken()
  if (!existingToken) {
    res.cookie('csrf_token', csrfToken, {
      httpOnly: true,
      sameSite: 'lax',
      secure: process.env.NODE_ENV === 'production',
      maxAge: 8 * 60 * 60 * 1000, // 8h
    })
  }
  res.locals.csrfToken = csrfToken

  // Flash messages
  const flashMessages: Array<{ category: string; text: string }> = []
  for (const category of ['success', 'error', 'warning', 'info']) {
    const msgs = req.flash(category)
    for (const text of msgs) {
      flashMessages.push({ category, text })
    }
  }
  res.locals.messages = flashMessages

  next()
}
