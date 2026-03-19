import { Router } from 'express'
import { createClerkClient } from '@clerk/express'
import { config } from '../../config'

const router = Router()

function getClerk() {
  return createClerkClient({ secretKey: config.clerkSecretKey })
}

router.get('/', async (_req, res) => {
  try {
    const clerk = getClerk()
    // Fetch up to 100 users and filter those with admin role
    const { data: allUsers } = await clerk.users.getUserList({ limit: 100 })
    const admins = allUsers.filter(
      (u) => (u.publicMetadata as { role?: string })?.role === 'admin'
    )
    res.render('admin_usuarios.html', { admins, error: null, success: null })
  } catch (err) {
    console.error('Erro ao listar usuários Clerk:', err)
    res.render('admin_usuarios.html', { admins: [], error: 'Erro ao carregar usuários.', success: null })
  }
})

router.post('/definir-admin', async (req, res) => {
  const { email, acao } = req.body as { email?: string; acao?: string }

  if (!email || !['adicionar', 'remover'].includes(acao ?? '')) {
    req.flash('error', 'Dados inválidos.')
    return res.redirect('/admin/usuarios')
  }

  try {
    const clerk = getClerk()
    const { data: found } = await clerk.users.getUserList({ emailAddress: [email] })
    if (!found.length) {
      req.flash('error', `Usuário com email "${email}" não encontrado no Clerk.`)
      return res.redirect('/admin/usuarios')
    }

    const user = found[0]
    const role = acao === 'adicionar' ? 'admin' : null

    await clerk.users.updateUser(user.id, {
      publicMetadata: { ...user.publicMetadata, role },
    })

    const msg = acao === 'adicionar'
      ? `Role "admin" adicionado para ${email}.`
      : `Role "admin" removido de ${email}.`
    req.flash('success', msg)
  } catch (err) {
    console.error('Erro ao atualizar role Clerk:', err)
    req.flash('error', 'Erro ao atualizar permissão. Verifique os logs.')
  }

  res.redirect('/admin/usuarios')
})

export default router
