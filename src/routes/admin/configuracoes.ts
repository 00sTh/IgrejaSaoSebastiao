import { Router } from 'express'
import { sql, dbQuery } from '../../db'
import type { Configuracao, Contato } from '../../types/index'

const ALLOWED_CONFIG_KEYS = new Set([
  'site_nome',
  'site_descricao',
  'endereco_completo',
  'mapa_latitude',
  'mapa_longitude',
])

const router = Router()

router.get('/', async (_req, res) => {
  const [configuracoes, contatos] = await Promise.all([
    dbQuery<Configuracao>`SELECT * FROM configuracoes`,
    dbQuery<Contato>`SELECT * FROM contatos ORDER BY ordem`,
  ])
  res.render('admin_configuracoes.html', { configuracoes, contatos })
})

router.post('/', async (req, res) => {
  const body = req.body as Record<string, string>
  for (const [key, valor] of Object.entries(body)) {
    if (key === 'csrf_token') continue
    if (!ALLOWED_CONFIG_KEYS.has(key)) continue
    await sql`UPDATE configuracoes SET valor = ${valor.trim()} WHERE chave = ${key}`
  }
  req.flash('success', 'Configurações atualizadas com sucesso!')
  res.redirect('/admin/configuracoes')
})

router.get('/contatos/editar/:id', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  const rows = await dbQuery<Contato>`SELECT * FROM contatos WHERE id = ${id}`
  if (!rows[0]) {
    req.flash('error', 'Contato não encontrado.')
    return res.redirect('/admin/configuracoes')
  }
  res.render('admin_contato_edit.html', { contato: rows[0] })
})

router.post('/contatos/editar/:id', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  const body = req.body as Record<string, string>
  const tipo = (body.tipo ?? '').trim()
  const valor = (body.valor ?? '').trim()
  const icone = (body.icone ?? '').trim()

  await sql`UPDATE contatos SET tipo = ${tipo}, valor = ${valor}, icone = ${icone || null} WHERE id = ${id}`
  req.flash('success', 'Contato atualizado com sucesso!')
  res.redirect('/admin/configuracoes')
})

export default router
