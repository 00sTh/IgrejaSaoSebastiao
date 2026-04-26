import { Router } from 'express'
import { z } from 'zod'
import { sql, dbQuery, queryOne } from '../db'
import { mensagemRateLimitMiddleware } from '../middleware/rate-limit'
import { sendNewMessageNotification } from '../lib/mailer'
import type { Noticia, HorarioMissa, HorarioConfissao, ParoquiaInfo, Galeria, Contato, Configuracao, Comunidade, ComunidadeHorario, Santo } from '../types/index'

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
  const horarios = await dbQuery<ComunidadeHorario>`
    SELECT * FROM comunidade_horarios WHERE ativo = TRUE ORDER BY comunidade_id, id
  `
  const horariosMap: Record<number, ComunidadeHorario[]> = {}
  for (const h of horarios) {
    if (!horariosMap[h.comunidade_id]) horariosMap[h.comunidade_id] = []
    horariosMap[h.comunidade_id].push(h)
  }
  const comunidadesComHorarios = comunidades.map(c => ({ ...c, horarios: horariosMap[c.id] ?? [] }))
  res.render('comunidades.html', { comunidades: comunidadesComHorarios })
})

// ==================== SANTOS ====================

router.get('/santos', async (_req, res) => {
  const santos = await dbQuery<Santo>`SELECT * FROM santos WHERE ativo = TRUE ORDER BY ordem ASC, nome ASC`
  const jovens = santos.filter(s => s.categoria === 'jovem')
  const padroeiros = santos.filter(s => s.categoria === 'padroeiro')
  const outros = santos.filter(s => s.categoria === 'outros')
  res.render('santos.html', { santos, jovens, padroeiros, outros })
})

// ==================== GALERIA ====================

router.get('/galeria', async (req, res) => {
  const page = Math.max(1, parseInt((req.query.page as string) || '1', 10))
  const categoria = ((req.query.categoria as string) || '').trim()
  const perPage = 20
  const offset = (page - 1) * perPage

  const [fotos, totalRows, categoriasRows] = await Promise.all([
    categoria
      ? dbQuery<Galeria>`SELECT * FROM galeria WHERE ativo = TRUE AND categoria = ${categoria} ORDER BY data_upload DESC LIMIT ${perPage} OFFSET ${offset}`
      : dbQuery<Galeria>`SELECT * FROM galeria WHERE ativo = TRUE ORDER BY data_upload DESC LIMIT ${perPage} OFFSET ${offset}`,
    categoria
      ? dbQuery<{ count: string }>`SELECT COUNT(*) as count FROM galeria WHERE ativo = TRUE AND categoria = ${categoria}`
      : dbQuery<{ count: string }>`SELECT COUNT(*) as count FROM galeria WHERE ativo = TRUE`,
    dbQuery<{ categoria: string }>`SELECT DISTINCT categoria FROM galeria WHERE ativo = TRUE AND categoria IS NOT NULL ORDER BY categoria`,
  ])

  const totalPages = Math.ceil(Number(totalRows[0]?.count ?? 0) / perPage)
  res.render('galeria.html', {
    fotos,
    categorias: categoriasRows.map(c => c.categoria),
    categoria_atual: categoria,
    current_page: page,
    total_pages: totalPages,
  })
})

// ==================== HORÁRIOS ====================

router.get('/horarios', async (_req, res) => {
  const diasOrdem = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
  const [missas, confissoes] = await Promise.all([
    dbQuery<HorarioMissa>`SELECT * FROM horarios_missas WHERE ativo = TRUE ORDER BY id`,
    dbQuery<HorarioConfissao>`SELECT * FROM horarios_confissao WHERE ativo = TRUE ORDER BY
      CASE dia_semana WHEN 'Domingo' THEN 0 WHEN 'Segunda-feira' THEN 1 WHEN 'Terça-feira' THEN 2
        WHEN 'Quarta-feira' THEN 3 WHEN 'Quinta-feira' THEN 4 WHEN 'Sexta-feira' THEN 5
        WHEN 'Sábado' THEN 6 ELSE 7 END, horario ASC`,
  ])
  const missasPorDia: Record<string, HorarioMissa[]> = {}
  for (const m of missas) {
    if (!missasPorDia[m.dia_semana]) missasPorDia[m.dia_semana] = []
    missasPorDia[m.dia_semana].push(m)
  }
  res.render('horarios.html', { missas, confissoes, missas_por_dia: missasPorDia, dias_ordem: diasOrdem })
})

// ==================== VÍDEOS ====================

router.get('/videos', async (_req, res) => {
  const videos = await dbQuery<Video>`SELECT * FROM videos WHERE ativo = TRUE ORDER BY ordem ASC, data_criacao DESC`
  res.render('videos.html', { videos })
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
    // Honeypot: bots preenchem campo oculto "website", humanos deixam vazio
    if ((req.body as Record<string, string>).website) {
      res.json({ status: 'success', message: 'Mensagem enviada com sucesso! Responderemos em breve.' })
      return
    }

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

// ==================== SEO ====================

router.get('/robots.txt', (req, res) => {
  const siteUrl = (res.locals.site_url as string) || `${req.protocol}://${req.get('host')}`
  res.type('text/plain').send(
    `User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /api/\n\nSitemap: ${siteUrl}/sitemap.xml`
  )
})

router.get('/sitemap.xml', async (_req, res) => {
  const siteUrl = res.locals.site_url as string
  const noticias = await dbQuery<{ id: number; data_criacao: string }>`
    SELECT id, data_criacao FROM noticias ORDER BY data_criacao DESC
  `
  const staticUrls = [
    { loc: '/', changefreq: 'weekly', priority: '1.0' },
    { loc: '/noticias', changefreq: 'daily', priority: '0.9' },
    { loc: '/comunidades', changefreq: 'monthly', priority: '0.8' },
    { loc: '/santos', changefreq: 'monthly', priority: '0.8' },
    { loc: '/galeria', changefreq: 'weekly', priority: '0.8' },
    { loc: '/horarios', changefreq: 'weekly', priority: '0.8' },
    { loc: '/videos', changefreq: 'weekly', priority: '0.7' },
    { loc: '/termos-de-uso', changefreq: 'yearly', priority: '0.3' },
    { loc: '/politica-de-privacidade', changefreq: 'yearly', priority: '0.3' },
  ]
  const urlElements = [
    ...staticUrls.map(u =>
      `  <url><loc>${siteUrl}${u.loc}</loc><changefreq>${u.changefreq}</changefreq><priority>${u.priority}</priority></url>`
    ),
    ...noticias.map(n =>
      `  <url><loc>${siteUrl}/noticias/${n.id}</loc><lastmod>${String(n.data_criacao).slice(0, 10)}</lastmod><changefreq>never</changefreq><priority>0.7</priority></url>`
    ),
  ]
  res.type('application/xml').send(
    `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urlElements.join('\n')}\n</urlset>`
  )
})

export default router
