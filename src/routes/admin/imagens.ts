import { Router } from 'express'
import multer from 'multer'
import path from 'path'
import fs from 'fs'
import { uploadImage, MediaValidationError } from '../../lib/media'

const router = Router()
const upload = multer({ storage: multer.memoryStorage() })

router.get('/imagens-site', (_req, res) => {
  const confessionBgExists = fs.existsSync(
    path.join(process.cwd(), 'static', 'img', 'confession-background.jpg')
  )
  res.render('admin_imagens_site.html', {
    confession_bg_exists: confessionBgExists,
    cache_bust: Date.now(),
  })
})

router.post('/imagens-site/upload', upload.single('imagem'), async (req, res) => {
  const file = (req as typeof req & { file?: Express.Multer.File }).file
  if (!file) {
    req.flash('error', 'Nenhuma imagem selecionada.')
    return res.redirect('/admin/imagens-site')
  }

  const body = req.body as Record<string, string>
  const imagemNome = body.imagem_nome ?? ''

  if (!imagemNome) {
    req.flash('error', 'Tipo de imagem não especificado.')
    return res.redirect('/admin/imagens-site')
  }

  try {
    await uploadImage(file.buffer, imagemNome, file.mimetype)
    req.flash('success', 'Imagem atualizada com sucesso!')
  } catch (err) {
    if (err instanceof MediaValidationError) {
      req.flash('error', err.message)
    } else {
      req.flash('error', 'Erro ao salvar imagem.')
    }
  }

  res.redirect('/admin/imagens-site')
})

router.get('/banco-imagens', (_req, res) => {
  const imagens: Array<{
    nome: string
    pasta: string
    url: string
    tamanho: number
    tamanho_fmt: string
    data: string
    data_sort: string
  }> = []

  const collectImages = (dir: string, pasta: string) => {
    if (!fs.existsSync(dir)) return
    try {
      for (const file of fs.readdirSync(dir)) {
        if (!/\.(jpg|jpeg|png|gif|webp)$/i.test(file)) continue
        const filepath = path.join(dir, file)
        const stat = fs.statSync(filepath)
        const relPath = path.relative(path.join(process.cwd(), 'static'), filepath)
        const tamanho = stat.size
        const modificado = stat.mtime
        imagens.push({
          nome: file,
          pasta,
          url: '/' + relPath.replace(/\\/g, '/'),
          tamanho,
          tamanho_fmt: tamanho < 1048576 ? `${(tamanho / 1024).toFixed(1)} KB` : `${(tamanho / 1048576).toFixed(1)} MB`,
          data: modificado.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }),
          data_sort: modificado.toISOString(),
        })
      }
    } catch { /* ignore */ }
  }

  const uploadDir = path.join(process.cwd(), 'static', 'uploads')
  for (const pasta of ['', 'medium', 'large', 'thumb', 'original']) {
    collectImages(pasta ? path.join(uploadDir, pasta) : uploadDir, pasta || 'raiz')
  }
  collectImages(path.join(process.cwd(), 'static', 'img'), 'img')

  imagens.sort((a, b) => b.data_sort.localeCompare(a.data_sort))
  res.render('admin_banco_imagens.html', { imagens })
})

router.post('/backup', (req, res) => {
  req.flash('info', 'Backup do banco de dados deve ser feito pelo painel do Neon.')
  res.redirect('/admin/dashboard')
})

export default router
