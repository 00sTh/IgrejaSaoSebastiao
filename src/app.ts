import 'dotenv/config'
import express from 'express'
import helmet from 'helmet'
import session from 'express-session'
import flash from 'connect-flash'
import nunjucks from 'nunjucks'
import path from 'path'
import { clerkMiddleware } from '@clerk/express'
import { config } from './config'
import { initDb } from './db'
import { checkSession } from './middleware/session'
import { csrfProtect } from './middleware/csrf'
import { requestLogger } from './middleware/logger'
import { loginRequired } from './lib/auth'

// Route imports
import publicRoutes from './routes/public'
import authRoutes from './routes/auth'
import adminIndex from './routes/admin/index'
import adminNoticias from './routes/admin/noticias'
import adminHorarios from './routes/admin/horarios'
import adminGaleria from './routes/admin/galeria'
import adminInformacoes from './routes/admin/informacoes'
import adminConfiguracoes from './routes/admin/configuracoes'
import adminMensagens from './routes/admin/mensagens'
import adminConteudo from './routes/admin/conteudo'
import adminImagens from './routes/admin/imagens'
import adminComunidades from './routes/admin/comunidades'
import adminSantos from './routes/admin/santos'

const rootDir = path.resolve(__dirname, '..')

const app = express()

// ==================== SECURITY HEADERS ====================
app.use(
  helmet({
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        scriptSrc: [
          "'self'",
          "'unsafe-inline'", // Required for inline scripts in templates
          'https://cdnjs.cloudflare.com',
          'https://cdn.jsdelivr.net',
          'https://*.clerk.accounts.dev',
        ],
        styleSrc: [
          "'self'",
          "'unsafe-inline'",
          'https://fonts.googleapis.com',
          'https://cdnjs.cloudflare.com',
          'https://cdn.jsdelivr.net',
        ],
        fontSrc: [
          "'self'",
          'https://fonts.gstatic.com',
          'https://cdnjs.cloudflare.com',
          'data:',
        ],
        imgSrc: [
          "'self'",
          'data:',
          'https://res.cloudinary.com',
          'https:',
        ],
        connectSrc: [
          "'self'",
          'https://*.clerk.accounts.dev',
        ],
        frameSrc: [
          "'self'",
          'https://www.google.com',
          'https://*.clerk.accounts.dev',
        ],
        objectSrc: ["'none'"],
        upgradeInsecureRequests: process.env.NODE_ENV === 'production' ? [] : null,
      },
    },
    crossOriginEmbedderPolicy: false, // Required for Google Maps embeds
  })
)

// ==================== NUNJUCKS ====================
const env = nunjucks.configure(path.join(rootDir, 'templates'), {
  autoescape: true,
  express: app,
  watch: config.debug,
})

// Custom filters
env.addFilter('nl2br', (str: string) => {
  if (!str) return str
  return str.replace(/\n/g, '<br>')
})

env.addFilter('pipe_split', (str: string) => {
  if (!str) return []
  return str.split('|').map((s: string) => s.trim()).filter(Boolean)
})

env.addFilter('date_short', (val: unknown) => {
  if (!val) return ''
  return String(val).slice(0, 10)
})

// ==================== MIDDLEWARE ====================
app.use(express.urlencoded({ limit: '1mb', extended: true }))
app.use(express.json({ limit: '1mb' }))
app.use(express.static(path.join(rootDir, 'static')))

// Clerk middleware (only if keys are configured)
if (config.clerkPublishableKey && config.clerkSecretKey) {
  app.use(clerkMiddleware())
}

// Session (MemoryStore — only used for flash messages + CSRF, NOT for auth)
app.use(
  session({
    secret: config.secretKey,
    resave: false,
    saveUninitialized: false,
    cookie: {
      httpOnly: true,
      sameSite: 'lax',
      secure: process.env.NODE_ENV === 'production',
      maxAge: 8 * 60 * 60 * 1000, // 8 hours
    },
  })
)

app.use(flash())
app.use(requestLogger)
app.use(checkSession)  // populates res.locals.currentUser, csrfToken, messages
app.use(csrfProtect)   // validates CSRF on POST/PUT/DELETE

// Expose request.args (query params) to all templates — Jinja2 compat
app.use((req, res, next) => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const args: any = { ...req.query }
  args.get = (key: string, fallback: unknown = '') => args[key] ?? fallback
  res.locals.request = { args }
  next()
})

// ==================== ROUTES ====================
app.use('/', publicRoutes)
app.use('/', authRoutes)
app.use('/admin', loginRequired, adminIndex)
app.use('/admin/noticias', loginRequired, adminNoticias)
app.use('/admin/horarios', loginRequired, adminHorarios)
app.use('/admin/galeria', loginRequired, adminGaleria)
app.use('/admin/informacoes', loginRequired, adminInformacoes)
app.use('/admin/configuracoes', loginRequired, adminConfiguracoes)
app.use('/admin/mensagens', loginRequired, adminMensagens)
app.use('/admin/conteudo-site', loginRequired, adminConteudo)
app.use('/admin', loginRequired, adminImagens)
app.use('/admin/comunidades', loginRequired, adminComunidades)
app.use('/admin/santos', loginRequired, adminSantos)

// ==================== ERROR HANDLER ====================
app.use((_req, res) => {
  res.status(404).render('error.html', { error: 'Página não encontrada', code: 404 })
})

// ==================== START ====================
const port = config.port

initDb()
  .then(() => {
    app.listen(port, '0.0.0.0', () => {
      console.log(`✅ Servidor rodando em http://localhost:${port}`)
    })
  })
  .catch((err) => {
    console.error('Erro ao inicializar banco de dados:', err)
    process.exit(1)
  })

export default app
