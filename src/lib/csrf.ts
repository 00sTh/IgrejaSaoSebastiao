import crypto from 'crypto'

export function generateCsrfToken(): string {
  return crypto.randomBytes(32).toString('hex')
}

export function validateCsrfToken(sessionToken: string | undefined, requestToken: string | undefined): boolean {
  if (!sessionToken || !requestToken) return false
  return sessionToken === requestToken
}
