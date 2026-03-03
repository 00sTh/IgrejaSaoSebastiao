import bcrypt from 'bcryptjs'
import { sql, queryOne } from '../db'
import { rateLimiter } from '../middleware/rate-limit'
import type { Request, Response, NextFunction } from 'express'
import type { User, SessionUser } from '../types/index'

export const SESSION_LIFETIME_MS = 8 * 60 * 60 * 1000 // 8 hours

export async function authenticate(
  username: string,
  password: string,
  ipAddress?: string
): Promise<{ success: boolean; user: SessionUser | null; error: string | null }> {
  // Rate limit check
  if (ipAddress && rateLimiter.isBlocked(ipAddress)) {
    return { success: false, user: null, error: 'Muitas tentativas. Aguarde 15 minutos.' }
  }

  const user = await queryOne<User>`
    SELECT * FROM users WHERE username = ${username} AND is_active = TRUE
  `

  if (!user) {
    if (ipAddress) rateLimiter.recordAttempt(ipAddress, false)
    return { success: false, user: null, error: 'Usuário ou senha incorretos.' }
  }

  const valid = bcrypt.compareSync(password, user.password_hash)
  if (!valid) {
    if (ipAddress) rateLimiter.recordAttempt(ipAddress, false)
    await sql`UPDATE users SET failed_attempts = failed_attempts + 1 WHERE id = ${user.id}`
    return { success: false, user: null, error: 'Usuário ou senha incorretos.' }
  }

  // Success
  if (ipAddress) rateLimiter.recordAttempt(ipAddress, true)
  await sql`UPDATE users SET last_login = NOW(), failed_attempts = 0 WHERE id = ${user.id}`

  return {
    success: true,
    user: { id: user.id, username: user.username, role: user.role },
    error: null,
  }
}

export async function auditLog(
  action: string,
  userId?: number,
  entityType?: string,
  entityId?: number,
  oldValue?: unknown,
  newValue?: unknown,
  ipAddress?: string
): Promise<void> {
  try {
    await sql`
      INSERT INTO audit_log (user_id, action, entity_type, entity_id, old_value, new_value, ip_address)
      VALUES (
        ${userId ?? null},
        ${action},
        ${entityType ?? null},
        ${entityId ?? null},
        ${oldValue ? JSON.stringify(oldValue) : null},
        ${newValue ? JSON.stringify(newValue) : null},
        ${ipAddress ?? null}
      )
    `
  } catch {
    // Never let audit log failures break main operations
  }
}

/** Express middleware — requires authenticated session */
export function loginRequired(req: Request, res: Response, next: NextFunction): void {
  if (!req.session.logged_in) {
    req.flash('error', 'Você precisa estar logado para acessar esta página.')
    res.redirect('/admin')
    return
  }
  next()
}
