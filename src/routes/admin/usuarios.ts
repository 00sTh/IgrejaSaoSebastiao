import { Router } from 'express'
import type { Request, Response } from 'express'
import { config } from '../../config'

const router = Router()

const CLERK_API = 'https://api.clerk.com/v1'

async function clerkGet(path: string) {
  const r = await fetch(`${CLERK_API}${path}`, {
    headers: { Authorization: `Bearer ${config.clerkSecretKey}` },
  })
  return r.json()
}

async function clerkPatch(path: string, body: unknown) {
  const r = await fetch(`${CLERK_API}${path}`, {
    method: 'PATCH',
    headers: {
      Authorization: `Bearer ${config.clerkSecretKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
  return r.json()
}

router.get('/', async (_req: Request, res: Response) => {
  try {
    const data = await clerkGet('/users?limit=100') as { id: string; first_name: string; last_name: string; email_addresses: { email_address: string }[]; public_metadata: { role?: string }; created_at: number }[]
    const admins = Array.isArray(data)
      ? data.filter((u) => u.public_metadata?.role === 'admin')
      : []
    res.render('admin_usuarios.html', { admins, error: null })
  } catch (err) {
    console.error('Erro ao listar usuários Clerk:', err)
    res.render('admin_usuarios.html', { admins: [], error: 'Erro ao carregar usuários.' })
  }
})

router.post('/definir-admin', async (req: Request, res: Response) => {
  const { email, acao } = req.body as { email?: string; acao?: string }

  if (!email || !['adicionar', 'remover'].includes(acao ?? '')) {
    req.flash('error', 'Dados inválidos.')
    return res.redirect('/admin/usuarios')
  }

  try {
    const data = await clerkGet(`/users?email_address=${encodeURIComponent(email)}&limit=1`) as { id: string; public_metadata: Record<string, unknown> }[]
    if (!Array.isArray(data) || !data.length) {
      req.flash('error', `Usuário "${email}" não encontrado no Clerk.`)
      return res.redirect('/admin/usuarios')
    }

    const user = data[0]
    const newMeta = { ...user.public_metadata, role: acao === 'adicionar' ? 'admin' : null }
    await clerkPatch(`/users/${user.id}`, { public_metadata: newMeta })

    req.flash('success', acao === 'adicionar'
      ? `Role "admin" adicionado para ${email}.`
      : `Role "admin" removido de ${email}.`)
  } catch (err) {
    console.error('Erro ao atualizar role Clerk:', err)
    req.flash('error', 'Erro ao atualizar permissão.')
  }

  res.redirect('/admin/usuarios')
})

export default router
