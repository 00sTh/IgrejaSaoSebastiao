# CLAUDE.md

Site e painel administrativo da Igreja São Sebastião (Ponte Nova/MG). Portuguese (pt-BR) codebase.

> **Atenção:** o projeto foi migrado de Flask/Python para **Express.js + TypeScript**. Os arquivos `app.py`, `config.py`, `core/`, `middleware/` (Python) e `venv/` são legados e **não são usados**. Todo o código ativo está em `src/`.

## Stack

- **Runtime:** Node.js (via nvm)
- **Framework:** Express.js + TypeScript
- **Templates:** Nunjucks (`templates/`)
- **Banco:** Neon PostgreSQL (`@neondatabase/serverless`)
- **Auth:** express-session + connect-pg-simple (sessões no Postgres)
- **Upload:** Cloudinary (`src/lib/media.ts`)
- **Email:** Nodemailer (`src/lib/mailer.ts`)
- **Segurança:** helmet.js, CSRF próprio, rate-limit, sanitize-html, Zod

## Comandos

```bash
# Instalar dependências
source /home/sth/.nvm/nvm.sh
pnpm install

# Dev (com hot reload)
pnpm dev

# Produção
pnpm start

# Verificar TypeScript
npx tsc --noEmit

# Acesso
# Site:  http://localhost:5000
# Admin: http://localhost:5000/admin
```

## Estrutura principal (`src/`)

```
src/
  app.ts                  # Entry point + helmet CSP + session + rotas
  config.ts               # Zod env validation (SECRET_KEY obrigatória, min 32 chars)
  db.ts                   # initDb(), dbQuery<T>, queryOne<T>, sql tagged template
  lib/
    auth.ts               # authenticate(), auditLog(), loginRequired middleware
    mailer.ts             # sendReplyEmail(), sendNewMessageNotification()
    media.ts              # uploadImage() via Cloudinary
    cache.ts              # cache simples em memória
    csrf.ts               # geração de token CSRF
  middleware/
    session.ts            # checkSession — popula res.locals.currentUser, csrfToken, messages
    csrf.ts               # csrfProtect — valida CSRF em POST/PUT/DELETE
    rate-limit.ts         # loginLimiter (5/5min), mensagemRateLimitMiddleware (5/15min)
    logger.ts             # requestLogger estruturado
  routes/
    public.ts             # GET /, /noticias, /noticias/:id, /comunidades, POST /api/enviar-mensagem
    auth.ts               # GET/POST /login, POST /logout
    admin/
      index.ts            # /admin/dashboard
      noticias.ts         # CRUD /admin/noticias
      horarios.ts         # CRUD /admin/horarios
      galeria.ts          # CRUD /admin/galeria
      informacoes.ts      # CRUD /admin/informacoes
      configuracoes.ts    # /admin/configuracoes
      mensagens.ts        # /admin/mensagens (lista + resposta por email)
      conteudo.ts         # /admin/conteudo-site
      imagens.ts          # /admin/banco-imagens
      comunidades.ts      # CRUD /admin/comunidades
  types/index.ts          # Interfaces TypeScript + augmentations express-session/Express.Locals
```

## Padrão DB (Neon)

- `dbQuery<T>` — tagged template literal, retorna `Promise<T[]>`
- `queryOne<T>` — retorna `T | null`
- PostgreSQL: SERIAL PRIMARY KEY, BOOLEAN DEFAULT TRUE/FALSE, TIMESTAMPTZ DEFAULT NOW()
- Schema criado em `initDb()` com `CREATE TABLE IF NOT EXISTS`

## Env vars obrigatórias

| Var | Uso |
|---|---|
| `DATABASE_URL` | Neon PostgreSQL connection string |
| `SECRET_KEY` | Segredo de sessão (mín. 32 chars) |

## Env vars opcionais (mas recomendadas em prod)

| Var | Uso |
|---|---|
| `ADMIN_USERNAME` | Usuário admin inicial (padrão: `admin`) |
| `ADMIN_PASSWORD` | Senha admin inicial |
| `CLOUDINARY_CLOUD_NAME` / `_API_KEY` / `_API_SECRET` | Upload de imagens |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` / `SMTP_FROM` | Emails (reply + notificação) |
| `SITE_URL` | URL pública (usado no link do email de notificação) |
| `PORT` | Porta (padrão: 5000) |

## Templates Nunjucks

- Filtros customizados: `nl2br`, `pipe_split` (split por `|`), `date_short`
- Flash messages via `res.locals.messages = [{category, text}]`
- `info_paroquia.get('chave', {}).get('titulo')` — conteúdo curto
- `info_paroquia.get('chave', {}).get('conteudo')` — conteúdo longo (HTML)
- Campos separados por `|` usam filtro `pipe_split` (ex: `confissoes_horarios`, `historia_marcos`)

## Deploy (Vercel)

`vercel.json` já configurado. Env vars a configurar:
1. `DATABASE_URL` — Neon connection string (pooled)
2. `SECRET_KEY` — string aleatória ≥ 32 chars
3. `ADMIN_USERNAME` / `ADMIN_PASSWORD` — credenciais admin
4. `CLOUDINARY_*` — para upload de imagens funcionar
5. `SMTP_*` + `SITE_URL` — para emails funcionarem

> **Atenção:** arquivos em `static/uploads/` NÃO persistem no Vercel (serverless). Todas as imagens devem estar no Cloudinary.

## Gotchas

- `paroquia_info.secao` é UNIQUE — use `ON CONFLICT (secao) DO NOTHING` em inserts
- CSRF: rotas `/api/*` são isentas; todas as outras POST/PUT/DELETE precisam do token
- Sessões ficam na tabela `session` do Postgres (criada pelo `initDb()`)
- `database.db` na raiz é legado do Flask — ignorar
