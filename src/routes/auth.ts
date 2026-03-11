import { Router } from 'express'
import { getAuth } from '@clerk/express'

const router = Router()

// Clerk Account Portal redirect
router.get('/sign-in', (req, res) => {
  const { userId } = getAuth(req)
  if (userId) {
    res.redirect('/admin/dashboard')
    return
  }
  res.render('admin_login.html')
})

// Legacy /admin login route — redirect to Clerk
router.get('/admin', (req, res) => {
  const { userId, sessionClaims } = getAuth(req)
  if (userId) {
    const metadata = sessionClaims?.metadata as { role?: string } | undefined
    if (metadata?.role === 'admin') {
      res.redirect('/admin/dashboard')
      return
    }
  }
  res.redirect('/sign-in')
})

// Logout via Clerk
router.get('/logout', (_req, res) => {
  res.redirect('/')
})

export default router
