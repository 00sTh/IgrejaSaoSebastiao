import { Router } from 'express'
import { authenticate, auditLog } from '../lib/auth'
import { generateCsrfToken } from '../lib/csrf'
import { rateLimiter } from '../middleware/rate-limit'

const router = Router()

router.get('/admin', (req, res) => {
  if (req.session.logged_in) {
    res.redirect('/admin/dashboard')
    return
  }
  res.render('admin_login.html', { error: null, remaining_attempts: null })
})

router.post('/admin', async (req, res) => {
  const body = req.body as Record<string, string>
  const username = (body.username ?? '').trim()
  const password = body.password ?? ''
  const ip = req.ip ?? 'unknown'

  if (rateLimiter.isBlocked(ip)) {
    res.render('admin_login.html', {
      error: 'Muitas tentativas. Aguarde 15 minutos.',
      remaining_attempts: 0,
    })
    return
  }

  const { success, user, error } = await authenticate(username, password, ip)

  if (success && user) {
    req.session.logged_in = true
    req.session.user_id = user.id
    req.session.username = user.username
    req.session.role = user.role
    req.session.last_activity = new Date().toISOString()
    req.session.csrf_token = generateCsrfToken()

    await auditLog('login', user.id, 'user', user.id, undefined, undefined, ip)
    req.flash('success', 'Login realizado com sucesso!')
    res.redirect('/admin/dashboard')
  } else {
    res.render('admin_login.html', {
      error: error ?? 'Usuário ou senha incorretos.',
      remaining_attempts: rateLimiter.getRemainingAttempts(ip),
    })
  }
})

router.get('/logout', (req, res) => {
  const userId = req.session.user_id
  req.session.destroy(() => {
    if (userId) {
      auditLog('logout', userId, 'user', userId).catch(() => {})
    }
  })
  res.redirect('/')
})

export default router
