import type { Request, Response, NextFunction } from 'express'
import { getAuth } from '@clerk/express'
import { generateCsrfToken } from '../lib/csrf'

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

  // CSRF token
  if (!req.session.csrf_token) {
    req.session.csrf_token = generateCsrfToken()
  }
  res.locals.csrfToken = req.session.csrf_token

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
