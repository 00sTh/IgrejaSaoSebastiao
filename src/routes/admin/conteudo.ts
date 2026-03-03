import { Router } from 'express'
import sanitizeHtml from 'sanitize-html'
import { sql, dbQuery } from '../../db'
import type { ParoquiaInfo } from '../../types/index'

const router = Router()

const ALLOWED_TAGS = ['b', 'i', 'u', 'p', 'br', 'a', 'ul', 'ol', 'li', 'h2', 'h3', 'blockquote', 'strong', 'em']
const ALLOWED_ATTRS = { a: ['href', 'title', 'target'] }

const CAMPOS_PERMITIDOS = [
  'hero_titulo', 'hero_subtitulo', 'hero_botao',
  'sobre_titulo', 'sobre_texto',
  'horarios_titulo', 'missas_titulo', 'confissoes_titulo', 'confissoes_horarios',
  'secretaria_titulo', 'secretaria_horarios', 'secretaria_telefone', 'secretaria_email',
  'galeria_titulo',
  'historia_titulo', 'historia_texto', 'historia_marcos_titulo', 'historia_marcos',
  'localizacao_titulo', 'localizacao_endereco', 'localizacao_telefones',
  'localizacao_email', 'localizacao_mapa',
  'confissao_titulo', 'confissao_texto',
  'contato_titulo', 'contato_subtitulo', 'contato_texto',
  'rodape_texto', 'redes_facebook', 'redes_instagram', 'redes_whatsapp',
]

router.get('/', async (_req, res) => {
  const rows = await dbQuery<Pick<ParoquiaInfo, 'secao' | 'titulo'>>`SELECT secao, titulo FROM paroquia_info`
  const dados: Record<string, string> = {}
  for (const row of rows) dados[row.secao] = row.titulo
  res.render('admin_conteudo_site.html', { dados })
})

router.post('/salvar', async (req, res) => {
  const body = req.body as Record<string, string>
  for (const campo of CAMPOS_PERMITIDOS) {
    const valor = sanitizeHtml((body[campo] ?? '').trim(), { allowedTags: ALLOWED_TAGS, allowedAttributes: ALLOWED_ATTRS })
    // Save to both titulo and conteudo so templates reading either column get the updated value
    await sql`UPDATE paroquia_info SET titulo = ${valor}, conteudo = ${valor} WHERE secao = ${campo}`
  }
  req.flash('success', 'Conteúdo do site atualizado com sucesso!')
  res.redirect('/admin/conteudo-site')
})

export default router
