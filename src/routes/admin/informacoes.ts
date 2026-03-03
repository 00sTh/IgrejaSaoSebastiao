import { Router } from 'express'
import sanitizeHtml from 'sanitize-html'
import { sql, dbQuery } from '../../db'
import type { ParoquiaInfo } from '../../types/index'

const router = Router()

const ALLOWED_TAGS = ['b', 'i', 'u', 'p', 'br', 'a', 'ul', 'ol', 'li', 'h2', 'h3', 'blockquote', 'strong', 'em']
const ALLOWED_ATTRS = { a: ['href', 'title', 'target'] }

function sanitize(html: string): string {
  return sanitizeHtml(html, { allowedTags: ALLOWED_TAGS, allowedAttributes: ALLOWED_ATTRS })
}

router.get('/', async (_req, res) => {
  const informacoes = await dbQuery<ParoquiaInfo>`SELECT * FROM paroquia_info ORDER BY ordem`
  res.render('admin_informacoes.html', { informacoes })
})

router.get('/editar/:id', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  const rows = await dbQuery<ParoquiaInfo>`SELECT * FROM paroquia_info WHERE id = ${id}`
  if (!rows[0]) {
    req.flash('error', 'Informação não encontrada.')
    return res.redirect('/admin/informacoes')
  }
  res.render('admin_informacao_edit.html', { informacao: rows[0] })
})

router.post('/editar/:id', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  const body = req.body as Record<string, string>
  const titulo = sanitize((body.titulo ?? '').trim())
  const conteudo = sanitize((body.conteudo ?? '').trim())

  if (!titulo || !conteudo) {
    req.flash('error', 'Título e conteúdo são obrigatórios.')
    return res.redirect(`/admin/informacoes/editar/${id}`)
  }

  await sql`UPDATE paroquia_info SET titulo = ${titulo}, conteudo = ${conteudo} WHERE id = ${id}`
  req.flash('success', 'Informação atualizada com sucesso!')
  res.redirect('/admin/informacoes')
})

export default router
