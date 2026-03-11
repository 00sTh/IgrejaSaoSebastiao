import { getAuth } from '@clerk/express'
import { sql } from '../db'
import type { Request, Response, NextFunction } from 'express'

/** Express middleware — requires Clerk-authenticated session with admin role */
export function loginRequired(req: Request, res: Response, next: NextFunction): void {
  // If Clerk keys not configured, block admin access
  if (!process.env.CLERK_PUBLISHABLE_KEY || !process.env.CLERK_SECRET_KEY) {
    res.status(503).render('error.html', { error: 'Admin desabilitado — configure CLERK_PUBLISHABLE_KEY e CLERK_SECRET_KEY no .env', code: 503 })
    return
  }

  const { userId, sessionClaims } = getAuth(req)

  if (!userId) {
    res.redirect('/sign-in')
    return
  }

  const metadata = sessionClaims?.metadata as { role?: string } | undefined
  if (metadata?.role !== 'admin') {
    res.status(403).render('error.html', { error: 'Acesso negado. Você não tem permissão de administrador.', code: 403 })
    return
  }

  next()
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
