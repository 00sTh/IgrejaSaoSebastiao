import { Router } from 'express'
import type { Request, Response } from 'express'
import multer from 'multer'
import sanitizeHtml from 'sanitize-html'
import { sql, dbQuery } from '../../db'
import { uploadImage, MediaValidationError } from '../../lib/media'
import type { Galeria } from '../../types/index'

const router = Router()
import { config as appConfig } from '../../config'
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: appConfig.maxFileSize } })

function sanitize(text: string): string {
  return sanitizeHtml(text, { allowedTags: [], allowedAttributes: {} })
}

router.get('/', async (_req, res) => {
  const galeria = await dbQuery<Galeria>`SELECT * FROM galeria ORDER BY data_upload DESC`
  res.render('admin_galeria.html', { galeria })
})

router.get('/editar', (_req, res) => {
  res.render('admin_galeria_edit.html', { foto: null })
})

router.get('/editar/:id', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  const rows = await dbQuery<Galeria>`SELECT * FROM galeria WHERE id = ${id}`
  if (!rows[0]) {
    req.flash('error', 'Foto não encontrada.')
    return res.redirect('/admin/galeria')
  }
  res.render('admin_galeria_edit.html', { foto: rows[0] })
})

router.post('/editar', upload.single('imagem'), async (req, res) => { await saveFoto(req, res, null) })
router.post('/editar/:id', upload.single('imagem'), async (req, res) => { await saveFoto(req, res, parseInt(req.params.id, 10)) })

async function saveFoto(req: Request, res: Response, id: number | null): Promise<void> {
  const body = req.body as Record<string, string>
  const titulo = sanitize((body.titulo ?? '').trim())
  const descricao = sanitize((body.descricao ?? '').trim())
  const categoria = sanitize((body.categoria ?? '').trim())

  if (!titulo) {
    req.flash('error', 'Título é obrigatório.')
    res.redirect(id ? `/admin/galeria/editar/${id}` : '/admin/galeria/editar')
    return
  }

  let imagemUrl: string | null = null
  if (id) {
    const existing = await dbQuery<{ imagem_url: string }>`SELECT imagem_url FROM galeria WHERE id = ${id}`
    imagemUrl = existing[0]?.imagem_url ?? null
  }

  const file = (req as Request & { file?: Express.Multer.File }).file
  if (file) {
    try {
      imagemUrl = await uploadImage(file.buffer, file.originalname, file.mimetype)
    } catch (err) {
      if (err instanceof MediaValidationError) {
        req.flash('error', err.message)
        res.redirect(id ? `/admin/galeria/editar/${id}` : '/admin/galeria/editar')
        return
      }
    }
  } else if (!id) {
    req.flash('error', 'Imagem é obrigatória para nova foto.')
    res.redirect('/admin/galeria/editar')
    return
  }

  if (id) {
    if (imagemUrl && file) {
      await sql`UPDATE galeria SET titulo = ${titulo}, descricao = ${descricao || null}, categoria = ${categoria || null}, imagem_url = ${imagemUrl} WHERE id = ${id}`
    } else {
      await sql`UPDATE galeria SET titulo = ${titulo}, descricao = ${descricao || null}, categoria = ${categoria || null} WHERE id = ${id}`
    }
    req.flash('success', 'Foto atualizada com sucesso!')
  } else {
    await sql`INSERT INTO galeria (titulo, descricao, categoria, imagem_url) VALUES (${titulo}, ${descricao || null}, ${categoria || null}, ${imagemUrl})`
    req.flash('success', 'Foto adicionada com sucesso!')
  }
  res.redirect('/admin/galeria')
}

router.post('/deletar/:id', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  await sql`DELETE FROM galeria WHERE id = ${id}`
  req.flash('success', 'Foto deletada com sucesso!')
  res.redirect('/admin/galeria')
})

export default router
