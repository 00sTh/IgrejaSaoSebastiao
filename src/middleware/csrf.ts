import type { Request, Response, NextFunction } from 'express'
import { validateCsrfToken } from '../lib/csrf'

// Routes exempt from CSRF (public APIs)
const EXEMPT_PATHS = ['/api/agendar-confissao', '/api/enviar-mensagem']

export function csrfProtect(req: Request, res: Response, next: NextFunction): void {
  if (!['POST', 'PUT', 'DELETE'].includes(req.method)) {
    next()
    return
  }

  if (EXEMPT_PATHS.includes(req.path)) {
    next()
    return
  }

  // Only enforce CSRF for authenticated admin sessions
  if (!res.locals.currentUser) {
    next()
    return
  }

  const token = req.is('json')
    ? req.headers['x-csrf-token'] as string | undefined
    : (req.body as Record<string, string>)?.csrf_token

  if (!validateCsrfToken(req.session.csrf_token, token)) {
    res.status(403).render('error.html', { error: 'CSRF token inválido', code: 403 })
    return
  }

  next()
}
