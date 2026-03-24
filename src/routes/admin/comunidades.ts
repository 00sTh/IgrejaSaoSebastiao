import { Router } from 'express'
import type { Request, Response } from 'express'
import multer from 'multer'
import sanitizeHtml from 'sanitize-html'
import { sql, dbQuery } from '../../db'
import { uploadImage, MediaValidationError } from '../../lib/media'
import type { Comunidade, ComunidadeHorario } from '../../types/index'

const router = Router()
import { config as appConfig } from '../../config'
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: appConfig.maxFileSize } })

function sanitize(text: string): string {
  return sanitizeHtml(text, { allowedTags: [], allowedAttributes: {} })
}

router.get('/', async (_req, res) => {
  const comunidades = await dbQuery<Comunidade>`SELECT * FROM comunidades ORDER BY ordem ASC, nome ASC`
  res.render('admin_comunidades.html', { comunidades })
})

router.get('/nova', (_req, res) => {
  res.render('admin_comunidade_edit.html', { comunidade: null, horarios: [] })
})

router.get('/editar/:id', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  const rows = await dbQuery<Comunidade>`SELECT * FROM comunidades WHERE id = ${id}`
  if (!rows[0]) {
    req.flash('error', 'Comunidade não encontrada.')
    return res.redirect('/admin/comunidades')
  }
  const horarios = await dbQuery<ComunidadeHorario>`
    SELECT * FROM comunidade_horarios WHERE comunidade_id = ${id} ORDER BY id ASC
  `
  res.render('admin_comunidade_edit.html', { comunidade: rows[0], horarios })
})

router.post('/nova', upload.single('imagem'), async (req, res) => { await saveComunidade(req, res, null) })
router.post('/editar/:id', upload.single('imagem'), async (req, res) => { await saveComunidade(req, res, parseInt(req.params.id, 10)) })

async function saveComunidade(req: Request, res: Response, id: number | null): Promise<void> {
  const body = req.body as Record<string, string>
  const nome = sanitize((body.nome ?? '').trim())
  const bairro = sanitize((body.bairro ?? '').trim())
  const descricao = sanitize((body.descricao ?? '').trim()) || null
  const endereco = sanitize((body.endereco ?? '').trim()) || null
  const mapa_url = sanitize((body.mapa_url ?? '').trim()) || null
  const ativo = body.ativo === 'on' || body.ativo === '1'
  const ordem = parseInt(body.ordem ?? '0', 10) || 0

  if (!nome || !bairro) {
    req.flash('error', 'Nome e bairro são obrigatórios.')
    res.redirect(id ? `/admin/comunidades/editar/${id}` : '/admin/comunidades/nova')
    return
  }

  let imagemUrl: string | null = null
  if (id) {
    const existing = await dbQuery<{ imagem_url: string | null }>`SELECT imagem_url FROM comunidades WHERE id = ${id}`
    imagemUrl = existing[0]?.imagem_url ?? null
  }

  const file = (req as Request & { file?: Express.Multer.File }).file
  if (file) {
    try {
      imagemUrl = await uploadImage(file.buffer, file.originalname, file.mimetype)
    } catch (err) {
      if (err instanceof MediaValidationError) {
        req.flash('error', err.message)
        res.redirect(id ? `/admin/comunidades/editar/${id}` : '/admin/comunidades/nova')
        return
      }
    }
  }

  if (id) {
    if (imagemUrl !== null && file) {
      await sql`UPDATE comunidades SET nome = ${nome}, bairro = ${bairro}, descricao = ${descricao}, endereco = ${endereco}, mapa_url = ${mapa_url}, ativo = ${ativo}, ordem = ${ordem}, imagem_url = ${imagemUrl} WHERE id = ${id}`
    } else {
      await sql`UPDATE comunidades SET nome = ${nome}, bairro = ${bairro}, descricao = ${descricao}, endereco = ${endereco}, mapa_url = ${mapa_url}, ativo = ${ativo}, ordem = ${ordem} WHERE id = ${id}`
    }
    req.flash('success', 'Comunidade atualizada com sucesso!')
  } else {
    await sql`INSERT INTO comunidades (nome, bairro, descricao, endereco, mapa_url, imagem_url, ativo, ordem) VALUES (${nome}, ${bairro}, ${descricao}, ${endereco}, ${mapa_url}, ${imagemUrl}, ${ativo}, ${ordem})`
    req.flash('success', 'Comunidade adicionada com sucesso!')
  }
  res.redirect('/admin/comunidades')
}

router.post('/deletar/:id', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  await sql`DELETE FROM comunidades WHERE id = ${id}`
  req.flash('success', 'Comunidade deletada com sucesso!')
  res.redirect('/admin/comunidades')
})

// Rotas de horários por comunidade
router.post('/editar/:id/horarios/novo', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  const body = req.body as Record<string, string>
  const tipo = sanitize((body.tipo ?? 'missa').trim())
  const titulo = sanitize((body.titulo ?? '').trim()) || null
  const dia_semana = sanitize((body.dia_semana ?? '').trim()) || null
  const horario = sanitize((body.horario ?? '').trim())
  const descricao = sanitize((body.descricao_horario ?? '').trim()) || null

  if (!horario) {
    req.flash('error', 'Horário é obrigatório.')
    return res.redirect(`/admin/comunidades/editar/${id}`)
  }

  await sql`
    INSERT INTO comunidade_horarios (comunidade_id, tipo, titulo, dia_semana, horario, descricao)
    VALUES (${id}, ${tipo}, ${titulo}, ${dia_semana}, ${horario}, ${descricao})
  `
  req.flash('success', 'Horário adicionado!')
  res.redirect(`/admin/comunidades/editar/${id}`)
})

router.post('/editar/:id/horarios/:horarioId/deletar', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  const horarioId = parseInt(req.params.horarioId, 10)
  await sql`DELETE FROM comunidade_horarios WHERE id = ${horarioId} AND comunidade_id = ${id}`
  req.flash('success', 'Horário removido.')
  res.redirect(`/admin/comunidades/editar/${id}`)
})

export default router
