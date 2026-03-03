import { Router } from 'express'
import { sql, dbQuery } from '../../db'
import { sendReplyEmail } from '../../lib/mailer'
import type { Mensagem } from '../../types/index'

const router = Router()

router.get('/', async (_req, res) => {
  const mensagens = await dbQuery<Mensagem>`SELECT * FROM mensagens_contato ORDER BY data_criacao DESC`
  res.render('admin_mensagens.html', { mensagens })
})

router.post('/:id/lida', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  await sql`UPDATE mensagens_contato SET lida = TRUE WHERE id = ${id}`
  res.redirect('/admin/mensagens')
})

router.post('/:id/deletar', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  await sql`DELETE FROM mensagens_contato WHERE id = ${id}`
  req.flash('success', 'Mensagem deletada.')
  res.redirect('/admin/mensagens')
})

router.get('/:id/responder', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  const rows = await dbQuery<Mensagem>`SELECT * FROM mensagens_contato WHERE id = ${id}`
  if (!rows[0]) {
    req.flash('error', 'Mensagem não encontrada.')
    return res.redirect('/admin/mensagens')
  }
  res.render('admin_mensagem_responder.html', { mensagem: rows[0] })
})

router.post('/:id/responder', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  const body = req.body as Record<string, string>
  const resposta = (body.resposta ?? '').trim()

  if (!resposta) {
    req.flash('error', 'A resposta não pode estar vazia.')
    return res.redirect(`/admin/mensagens/${id}/responder`)
  }

  const rows = await dbQuery<Mensagem>`SELECT * FROM mensagens_contato WHERE id = ${id}`
  const mensagem = rows[0]
  if (!mensagem) {
    req.flash('error', 'Mensagem não encontrada.')
    return res.redirect('/admin/mensagens')
  }

  await sql`
    UPDATE mensagens_contato
    SET resposta = ${resposta}, data_resposta = NOW(), lida = TRUE
    WHERE id = ${id}
  `

  const emailEnviado = await sendReplyEmail(mensagem.email, mensagem.nome, mensagem.mensagem, resposta)

  if (emailEnviado) {
    req.flash('success', 'Resposta enviada com sucesso por email!')
  } else {
    req.flash('warning', 'Resposta salva! Configure SMTP para enviar por email.')
  }

  res.redirect('/admin/mensagens')
})

export default router
