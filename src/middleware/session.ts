import type { Request, Response, NextFunction } from 'express'
import { SESSION_LIFETIME_MS } from '../lib/auth'
import { generateCsrfToken } from '../lib/csrf'
import { queryOne } from '../db'
import type { User } from '../types/index'

export async function checkSession(req: Request, res: Response, next: NextFunction): Promise<void> {
  // Check session expiry
  if (req.session.logged_in) {
    const lastActivity = req.session.last_activity
    if (lastActivity) {
      const elapsed = Date.now() - new Date(lastActivity).getTime()
      if (elapsed > SESSION_LIFETIME_MS) {
        req.session.destroy(() => {})
        req.flash('warning', 'Sua sessão expirou. Faça login novamente.')
        res.redirect('/admin')
        return
      }
    }
    req.session.last_activity = new Date().toISOString()
  }

  // Load current user
  if (req.session.user_id) {
    const user = await queryOne<User>`SELECT * FROM users WHERE id = ${req.session.user_id}`
    res.locals.currentUser = user
      ? { id: user.id, username: user.username, role: user.role }
      : null
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
