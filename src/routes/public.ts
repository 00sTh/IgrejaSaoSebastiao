import { Router } from 'express'
import { z } from 'zod'
import { sql, dbQuery, queryOne } from '../db'
import { mensagemRateLimitMiddleware } from '../middleware/rate-limit'
import { sendNewMessageNotification } from '../lib/mailer'
import type { Noticia, HorarioMissa, ParoquiaInfo, Galeria, Contato, Configuracao, Comunidade, Santo } from '../types/index'

interface Video {
  id: number
  titulo: string
  url_youtube: string
  descricao: string | null
  ativo: boolean
  ordem: number
}

const router = Router()

// ==================== HOME ====================

router.get('/', async (req, res) => {
  const [noticias, horarios, infos, galeria, contatos, configs, videos] = await Promise.all([
    dbQuery<Noticia>`SELECT * FROM noticias ORDER BY data_criacao DESC LIMIT 5`,
    dbQuery<HorarioMissa>`SELECT * FROM horarios_missas WHERE ativo = TRUE ORDER BY id`,
    dbQuery<ParoquiaInfo>`SELECT * FROM paroquia_info ORDER BY ordem`,
    dbQuery<Galeria>`SELECT * FROM galeria WHERE ativo = TRUE ORDER BY data_upload DESC LIMIT 12`,
    dbQuery<Contato>`SELECT * FROM contatos ORDER BY ordem`,
    dbQuery<Configuracao>`SELECT * FROM configuracoes`,
    dbQuery<Video>`SELECT * FROM videos WHERE ativo = TRUE ORDER BY ordem ASC, data_criacao DESC LIMIT 6`,
  ])

  // Build infoParoquia with .get() method to stay compatible with Jinja2-style templates in Nunjucks
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const infoParoquia: any = {}
  for (const info of infos) {
    const inner: any = { titulo: info.titulo, conteudo: info.conteudo }
    inner.get = (key: string, fallback: unknown = '') => inner[key] ?? fallback
    infoParoquia[info.secao] = inner
  }
  const emptyGetable: any = {}
  emptyGetable.get = (_k: string, fb: unknown = '') => fb
  infoParoquia.get = (key: string, fallback: unknown = emptyGetable) => {
    const val = infoParoquia[key]
    return val !== undefined ? val : fallback
  }

  const configDict: Record<string, string> = {}
  for (const c of configs) {
    configDict[c.chave] = c.valor
  }

  res.render('index.html', {
    noticias,
    horarios,
    info_paroquia: infoParoquia,
    galeria,
    contatos,
    configs: configDict,
    videos,
    is_admin: res.locals.currentUser?.role === 'admin',
  })
})

// ==================== NOTÍCIAS ====================

router.get('/noticias', async (_req, res) => {
  const noticias = await dbQuery<Noticia>`SELECT * FROM noticias ORDER BY data_criacao DESC`
  res.render('noticias.html', { noticias })
})

router.get('/noticias/:id', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  if (isNaN(id)) {
    res.status(404).render('error.html', { error: 'Notícia não encontrada', code: 404 })
    return
  }

  const noticia = await queryOne<Noticia>`SELECT * FROM noticias WHERE id = ${id}`
  if (!noticia) {
    res.status(404).render('error.html', { error: 'Notícia não encontrada', code: 404 })
    return
  }

  const recentes = await dbQuery<Noticia>`
    SELECT id, titulo, data_criacao FROM noticias WHERE id != ${id} ORDER BY data_criacao DESC LIMIT 5
  `
  res.render('noticia.html', { noticia, recentes })
})

// ==================== COMUNIDADES ====================

router.get('/comunidades', async (_req, res) => {
  const comunidades = await dbQuery<Comunidade>`
    SELECT * FROM comunidades WHERE ativo = TRUE ORDER BY ordem ASC, nome ASC
  `
  res.render('comunidades.html', { comunidades })
})

// ==================== SANTOS ====================

router.get('/santos', async (_req, res) => {
  const santos = await dbQuery<Santo>`SELECT * FROM santos WHERE ativo = TRUE ORDER BY ordem ASC, nome ASC`
  const jovens = santos.filter(s => s.categoria === 'jovem')
  const padroeiros = santos.filter(s => s.categoria === 'padroeiro')
  const outros = santos.filter(s => s.categoria === 'outros')
  res.render('santos.html', { santos, jovens, padroeiros, outros })
})

// ==================== PÁGINAS LEGAIS ====================

router.get('/termos-de-uso', (_req, res) => {
  res.render('termos.html')
})

router.get('/politica-de-privacidade', (_req, res) => {
  res.render('privacidade.html')
})

// ==================== PUBLIC APIs ====================

const MensagemSchema = z.object({
  nome: z.string().min(3, 'Nome deve ter pelo menos 3 caracteres').max(100),
  email: z.string().email('Email inválido').max(254).refine(
    (email) => {
      const blockedDomains = [
        'tempmail.com', 'throwaway.email', 'guerrillamail.com',
        'mailinator.com', '10minutemail.com', 'yopmail.com',
        'temp-mail.org', 'fakeinbox.com', 'trashmail.com',
      ]
      const domain = email.split('@')[1]?.toLowerCase()
      return domain ? !blockedDomains.includes(domain) : false
    },
    { message: 'Por favor, informe um email válido.' }
  ),
  mensagem: z.string().min(10, 'A mensagem deve ter pelo menos 10 caracteres').max(2000),
})

router.post('/api/enviar-mensagem', mensagemRateLimitMiddleware, async (req, res) => {
  try {
    const result = MensagemSchema.safeParse(req.body)
    if (!result.success) {
      const firstError = result.error.issues[0]?.message ?? 'Dados inválidos.'
      res.status(400).json({ status: 'error', message: firstError })
      return
    }

    const { nome, email, mensagem } = result.data
    await sql`INSERT INTO mensagens_contato (nome, email, mensagem) VALUES (${nome}, ${email}, ${mensagem})`

    // Notifica o admin por email (silencioso se SMTP não configurado)
    sendNewMessageNotification(nome, email, mensagem).catch(() => {})

    res.json({ status: 'success', message: 'Mensagem enviada com sucesso! Responderemos em breve.' })
  } catch (err) {
    console.error('Erro ao enviar mensagem:', err)
    res.status(500).json({ status: 'error', message: 'Erro ao enviar mensagem. Tente novamente.' })
  }
})

export default router
