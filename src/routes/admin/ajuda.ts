import { Router } from 'express'

const router = Router()

router.get('/', (_req, res) => {
  res.render('admin_ajuda.html')
})

export default router
