import { Router } from 'express'
import { z } from 'zod'
import { sql, dbQuery } from '../db'
import { mensagemRateLimitMiddleware } from '../middleware/rate-limit'
import type { Noticia, HorarioMissa, ParoquiaInfo, Galeria, Contato, Configuracao } from '../types/index'

const router = Router()

// ==================== HOME ====================

router.get('/', async (req, res) => {
  const [noticias, horarios, infos, galeria, contatos, configs] = await Promise.all([
    dbQuery<Noticia>`SELECT * FROM noticias ORDER BY data_criacao DESC LIMIT 5`,
    dbQuery<HorarioMissa>`SELECT * FROM horarios_missas WHERE ativo = TRUE ORDER BY id`,
    dbQuery<ParoquiaInfo>`SELECT * FROM paroquia_info ORDER BY ordem`,
    dbQuery<Galeria>`SELECT * FROM galeria WHERE ativo = TRUE ORDER BY data_upload DESC LIMIT 12`,
    dbQuery<Contato>`SELECT * FROM contatos ORDER BY ordem`,
    dbQuery<Configuracao>`SELECT * FROM configuracoes`,
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
    is_admin: req.session.logged_in ?? false,
  })
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

    res.json({ status: 'success', message: 'Mensagem enviada com sucesso! Responderemos em breve.' })
  } catch (err) {
    console.error('Erro ao enviar mensagem:', err)
    res.status(500).json({ status: 'error', message: 'Erro ao enviar mensagem. Tente novamente.' })
  }
})

export default router
