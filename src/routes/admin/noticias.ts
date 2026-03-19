import { Router } from 'express'
import type { Request, Response } from 'express'
import multer from 'multer'
import sanitizeHtml from 'sanitize-html'
import { sql, dbQuery } from '../../db'
import { uploadImage, MediaValidationError } from '../../lib/media'
import type { Noticia } from '../../types/index'

const router = Router()
import { config as appConfig } from '../../config'
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: appConfig.maxFileSize } })

const ALLOWED_TAGS = ['b', 'i', 'u', 'p', 'br', 'a', 'ul', 'ol', 'li', 'h2', 'h3', 'blockquote', 'strong', 'em']
const ALLOWED_ATTRS = { a: ['href', 'title', 'target'] }

function sanitize(html: string): string {
  return sanitizeHtml(html, { allowedTags: ALLOWED_TAGS, allowedAttributes: ALLOWED_ATTRS })
}

router.get('/', async (_req, res) => {
  const noticias = await dbQuery<Noticia>`SELECT * FROM noticias ORDER BY data_criacao DESC`
  res.render('admin_noticias.html', { noticias })
})

router.get('/nova', (_req, res) => {
  res.render('admin_noticia_edit.html', { noticia: null })
})

router.get('/editar/:id', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  const rows = await dbQuery<Noticia>`SELECT * FROM noticias WHERE id = ${id}`
  if (!rows[0]) {
    req.flash('error', 'Notícia não encontrada.')
    return res.redirect('/admin/noticias')
  }
  res.render('admin_noticia_edit.html', { noticia: rows[0] })
})

router.post('/nova', upload.single('imagem'), async (req, res) => {
  await saveNoticia(req, res, null)
})

router.post('/editar/:id', upload.single('imagem'), async (req, res) => {
  await saveNoticia(req, res, parseInt(req.params.id, 10))
})

async function saveNoticia(req: Request, res: Response, id: number | null): Promise<void> {
  const body = req.body as Record<string, string>
  const titulo = (body.titulo ?? '').trim()
  const subtitulo = (body.subtitulo ?? '').trim()
  const conteudo = sanitize((body.conteudo ?? '').trim())
  const tipo = body.tipo ?? 'Notícia'

  if (!titulo || !conteudo) {
    req.flash('error', 'Título e conteúdo são obrigatórios.')
    res.redirect(id ? `/admin/noticias/editar/${id}` : '/admin/noticias/nova')
    return
  }

  let imagemUrl: string | null = null
  if (id) {
    const existing = await dbQuery<{ imagem_url: string | null }>`SELECT imagem_url FROM noticias WHERE id = ${id}`
    imagemUrl = existing[0]?.imagem_url ?? null
  }

  const file = (req as Request & { file?: Express.Multer.File }).file
  if (file) {
    try {
      imagemUrl = await uploadImage(file.buffer, file.originalname, file.mimetype)
    } catch (err) {
      if (err instanceof MediaValidationError) {
        req.flash('error', err.message)
        res.redirect(id ? `/admin/noticias/editar/${id}` : '/admin/noticias/nova')
        return
      }
    }
  }

  if (id) {
    await sql`UPDATE noticias SET titulo = ${titulo}, subtitulo = ${subtitulo || null}, conteudo = ${conteudo}, imagem_url = ${imagemUrl}, tipo = ${tipo} WHERE id = ${id}`
    req.flash('success', 'Notícia atualizada com sucesso!')
  } else {
    await sql`INSERT INTO noticias (titulo, subtitulo, conteudo, imagem_url, tipo) VALUES (${titulo}, ${subtitulo || null}, ${conteudo}, ${imagemUrl}, ${tipo})`
    req.flash('success', 'Notícia criada com sucesso!')
  }

  res.redirect('/admin/noticias')
}

router.post('/deletar/:id', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  await sql`DELETE FROM noticias WHERE id = ${id}`
  req.flash('success', 'Notícia deletada com sucesso!')
  res.redirect('/admin/noticias')
})

export default router
