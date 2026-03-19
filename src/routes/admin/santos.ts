import { Router } from 'express'
import type { Request, Response } from 'express'
import multer from 'multer'
import sanitizeHtml from 'sanitize-html'
import { sql, dbQuery } from '../../db'
import { uploadImage, MediaValidationError } from '../../lib/media'
import type { Santo } from '../../types/index'

const router = Router()
import { config as appConfig } from '../../config'
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: appConfig.maxFileSize } })

function sanitize(text: string): string {
  return sanitizeHtml(text, { allowedTags: [], allowedAttributes: {} })
}

router.get('/', async (_req, res) => {
  const santos = await dbQuery<Santo>`SELECT * FROM santos ORDER BY categoria ASC, ordem ASC, nome ASC`
  res.render('admin_santos.html', { santos })
})

router.get('/novo', (_req, res) => {
  res.render('admin_santo_edit.html', { santo: null })
})

router.get('/editar/:id', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  const rows = await dbQuery<Santo>`SELECT * FROM santos WHERE id = ${id}`
  if (!rows[0]) {
    req.flash('error', 'Santo não encontrado.')
    return res.redirect('/admin/santos')
  }
  res.render('admin_santo_edit.html', { santo: rows[0] })
})

router.post('/novo', upload.single('imagem'), async (req, res) => { await saveSanto(req, res, null) })
router.post('/editar/:id', upload.single('imagem'), async (req, res) => { await saveSanto(req, res, parseInt(req.params.id, 10)) })

async function saveSanto(req: Request, res: Response, id: number | null): Promise<void> {
  const body = req.body as Record<string, string>
  const nome = sanitize((body.nome ?? '').trim())
  const descricao = sanitize((body.descricao ?? '').trim()) || null
  const categoria = body.categoria ?? 'outros'
  const dia_festa = sanitize((body.dia_festa ?? '').trim()) || null
  const ativo = body.ativo === 'on' || body.ativo === '1'
  const ordem = parseInt(body.ordem ?? '0', 10) || 0

  if (!nome) {
    req.flash('error', 'Nome é obrigatório.')
    res.redirect(id ? `/admin/santos/editar/${id}` : '/admin/santos/novo')
    return
  }

  if (!['jovem', 'padroeiro', 'outros'].includes(categoria)) {
    req.flash('error', 'Categoria inválida.')
    res.redirect(id ? `/admin/santos/editar/${id}` : '/admin/santos/novo')
    return
  }

  let imagemUrl: string | null = null
  if (id) {
    const existing = await dbQuery<{ imagem_url: string | null }>`SELECT imagem_url FROM santos WHERE id = ${id}`
    imagemUrl = existing[0]?.imagem_url ?? null
  }

  const file = (req as Request & { file?: Express.Multer.File }).file
  if (file) {
    try {
      imagemUrl = await uploadImage(file.buffer, file.originalname, file.mimetype)
    } catch (err) {
      if (err instanceof MediaValidationError) {
        req.flash('error', err.message)
        res.redirect(id ? `/admin/santos/editar/${id}` : '/admin/santos/novo')
        return
      }
    }
  }

  if (id) {
    if (imagemUrl !== null && file) {
      await sql`UPDATE santos SET nome = ${nome}, descricao = ${descricao}, categoria = ${categoria}, dia_festa = ${dia_festa}, ativo = ${ativo}, ordem = ${ordem}, imagem_url = ${imagemUrl} WHERE id = ${id}`
    } else {
      await sql`UPDATE santos SET nome = ${nome}, descricao = ${descricao}, categoria = ${categoria}, dia_festa = ${dia_festa}, ativo = ${ativo}, ordem = ${ordem} WHERE id = ${id}`
    }
    req.flash('success', 'Santo atualizado com sucesso!')
  } else {
    await sql`INSERT INTO santos (nome, descricao, imagem_url, categoria, dia_festa, ativo, ordem) VALUES (${nome}, ${descricao}, ${imagemUrl}, ${categoria}, ${dia_festa}, ${ativo}, ${ordem})`
    req.flash('success', 'Santo adicionado com sucesso!')
  }
  res.redirect('/admin/santos')
}

router.post('/deletar/:id', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  await sql`DELETE FROM santos WHERE id = ${id}`
  req.flash('success', 'Santo deletado com sucesso!')
  res.redirect('/admin/santos')
})

export default router
