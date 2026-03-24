import { Router } from 'express'
import { z } from 'zod'
import { dbQuery, queryOne } from '../../db'

const router = Router()

interface Video {
  id: number
  titulo: string
  url_youtube: string
  descricao: string | null
  ativo: boolean
  ordem: number
  data_criacao: string
}

/** Converts any YouTube URL format to embed URL */
function toEmbedUrl(url: string): string {
  const shortMatch = url.match(/youtu\.be\/([a-zA-Z0-9_-]+)/)
  if (shortMatch) return `https://www.youtube.com/embed/${shortMatch[1]}`

  const longMatch = url.match(/[?&]v=([a-zA-Z0-9_-]+)/)
  if (longMatch) return `https://www.youtube.com/embed/${longMatch[1]}`

  if (url.includes('/embed/')) return url

  return url
}

router.get('/videos', async (_req, res) => {
  const videos = await dbQuery<Video>`SELECT * FROM videos ORDER BY ordem ASC, data_criacao DESC`
  res.render('admin_videos.html', { videos })
})

router.get('/videos/novo', (_req, res) => {
  res.render('admin_videos.html', { videos: [], form_mode: 'novo' })
})

router.get('/videos/:id/editar', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  if (isNaN(id)) { res.redirect('/admin/videos'); return }

  const video = await queryOne<Video>`SELECT * FROM videos WHERE id = ${id}`
  if (!video) { req.flash('error', 'Vídeo não encontrado'); res.redirect('/admin/videos'); return }

  const videos = await dbQuery<Video>`SELECT * FROM videos ORDER BY ordem ASC, data_criacao DESC`
  res.render('admin_videos.html', { videos, form_mode: 'editar', video_edit: video })
})

const VideoSchema = z.object({
  titulo: z.string().min(2, 'Título obrigatório').max(200),
  url_youtube: z.string().url('URL inválida').refine(
    (u) => u.includes('youtube.com') || u.includes('youtu.be'),
    { message: 'Deve ser uma URL do YouTube' }
  ),
  descricao: z.string().max(500).optional(),
  ordem: z.coerce.number().int().min(0).default(0),
})

router.post('/videos', async (req, res) => {
  const result = VideoSchema.safeParse(req.body)
  if (!result.success) {
    req.flash('error', result.error.issues[0]?.message ?? 'Dados inválidos')
    res.redirect('/admin/videos')
    return
  }
  const { titulo, url_youtube, descricao, ordem } = result.data
  const embedUrl = toEmbedUrl(url_youtube)
  await dbQuery`INSERT INTO videos (titulo, url_youtube, descricao, ordem) VALUES (${titulo}, ${embedUrl}, ${descricao ?? null}, ${ordem})`
  req.flash('success', 'Vídeo adicionado com sucesso!')
  res.redirect('/admin/videos')
})

router.post('/videos/:id', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  if (isNaN(id)) { res.redirect('/admin/videos'); return }

  const result = VideoSchema.safeParse(req.body)
  if (!result.success) {
    req.flash('error', result.error.issues[0]?.message ?? 'Dados inválidos')
    res.redirect(`/admin/videos/${id}/editar`)
    return
  }
  const { titulo, url_youtube, descricao, ordem } = result.data
  const embedUrl = toEmbedUrl(url_youtube)
  await dbQuery`UPDATE videos SET titulo = ${titulo}, url_youtube = ${embedUrl}, descricao = ${descricao ?? null}, ordem = ${ordem} WHERE id = ${id}`
  req.flash('success', 'Vídeo atualizado com sucesso!')
  res.redirect('/admin/videos')
})

router.post('/videos/:id/toggle', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  if (isNaN(id)) { res.redirect('/admin/videos'); return }
  await dbQuery`UPDATE videos SET ativo = NOT ativo WHERE id = ${id}`
  res.redirect('/admin/videos')
})

router.delete('/videos/:id', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  if (isNaN(id)) { res.status(400).json({ error: 'ID inválido' }); return }
  await dbQuery`DELETE FROM videos WHERE id = ${id}`
  res.json({ success: true })
})

export default router
