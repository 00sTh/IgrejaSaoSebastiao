import { Router } from 'express'
import type { Request, Response } from 'express'
import multer from 'multer'
import sanitizeHtml from 'sanitize-html'
import { sql, dbQuery } from '../../db'
import { uploadImage, MediaValidationError } from '../../lib/media'
import type { Comunidade } from '../../types/index'

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
  res.render('admin_comunidade_edit.html', { comunidade: null })
})

router.get('/editar/:id', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  const rows = await dbQuery<Comunidade>`SELECT * FROM comunidades WHERE id = ${id}`
  if (!rows[0]) {
    req.flash('error', 'Comunidade não encontrada.')
    return res.redirect('/admin/comunidades')
  }
  res.render('admin_comunidade_edit.html', { comunidade: rows[0] })
})

router.post('/nova', upload.single('imagem'), async (req, res) => { await saveComunidade(req, res, null) })
router.post('/editar/:id', upload.single('imagem'), async (req, res) => { await saveComunidade(req, res, parseInt(req.params.id, 10)) })

async function saveComunidade(req: Request, res: Response, id: number | null): Promise<void> {
  const body = req.body as Record<string, string>
  const nome = sanitize((body.nome ?? '').trim())
  const bairro = sanitize((body.bairro ?? '').trim())
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
      await sql`UPDATE comunidades SET nome = ${nome}, bairro = ${bairro}, ativo = ${ativo}, ordem = ${ordem}, imagem_url = ${imagemUrl} WHERE id = ${id}`
    } else {
      await sql`UPDATE comunidades SET nome = ${nome}, bairro = ${bairro}, ativo = ${ativo}, ordem = ${ordem} WHERE id = ${id}`
    }
    req.flash('success', 'Comunidade atualizada com sucesso!')
  } else {
    await sql`INSERT INTO comunidades (nome, bairro, imagem_url, ativo, ordem) VALUES (${nome}, ${bairro}, ${imagemUrl}, ${ativo}, ${ordem})`
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

export default router
