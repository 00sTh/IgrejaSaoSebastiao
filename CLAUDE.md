# CLAUDE.md

Site e painel administrativo da Igreja São Sebastião (Ponte Nova/MG). Portuguese (pt-BR) codebase.

> **Atenção:** o projeto foi migrado de Flask/Python para **Express.js + TypeScript**. Os arquivos `app.py`, `config.py`, `core/`, `middleware/` (Python) e `venv/` são legados e **não são usados**. Todo o código ativo está em `src/`.

## Stack

- **Runtime:** Node.js (via nvm)
- **Framework:** Express.js + TypeScript
- **Templates:** Nunjucks (`templates/`)
- **Banco:** Neon PostgreSQL (`@neondatabase/serverless`)
- **Auth:** Clerk (`@clerk/express`) — login via Clerk Account Portal, role admin em `publicMetadata`
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
# Admin: http://localhost:5000/admin (requer login Clerk com role admin)
```

## Estrutura principal (`src/`)

```
src/
  app.ts                  # Entry point + helmet CSP + Clerk + session + rotas
  config.ts               # Zod env validation (SECRET_KEY, CLERK_* obrigatórias)
  db.ts                   # initDb(), dbQuery<T>, queryOne<T>, sql tagged template, seeds
  lib/
    auth.ts               # loginRequired (Clerk-based), auditLog()
    mailer.ts             # sendReplyEmail(), sendNewMessageNotification()
    media.ts              # uploadImage() via Cloudinary
    cache.ts              # cache simples em memória
    csrf.ts               # geração de token CSRF
  middleware/
    session.ts            # checkSession — popula res.locals via Clerk + flash + CSRF
    csrf.ts               # csrfProtect — valida CSRF em POST/PUT/DELETE
    rate-limit.ts         # mensagemRateLimitMiddleware (5/15min)
    logger.ts             # requestLogger estruturado
  routes/
    public.ts             # GET /, /noticias, /noticias/:id, /comunidades, /santos, POST /api/enviar-mensagem
    auth.ts               # GET /sign-in, /admin (redirect Clerk), /logout
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
      santos.ts           # CRUD /admin/santos
  types/index.ts          # Interfaces TypeScript + augmentations express-session/Express.Locals
```

## Auth (Clerk)

- **Middleware:** `clerkMiddleware()` adicionado em app.ts ANTES das rotas
- **loginRequired:** usa `getAuth(req)` para verificar `userId` e `sessionClaims.metadata.role === 'admin'`
- **Session:** express-session com MemoryStore (apenas para flash messages + CSRF, NÃO para auth)
- **Configuração Clerk Dashboard:**
  1. Criar app "Igreja São Sebastião"
  2. Em Configure → Sessions → Customize session token: `{ "metadata": "{{user.public_metadata}}" }`
  3. Criar user admin → Public metadata: `{ "role": "admin" }`
  4. Copiar `CLERK_PUBLISHABLE_KEY` e `CLERK_SECRET_KEY` para `.env`

## Padrão DB (Neon)

- `dbQuery<T>` — tagged template literal, retorna `Promise<T[]>`
- `queryOne<T>` — retorna `T | null`
- PostgreSQL: SERIAL PRIMARY KEY, BOOLEAN DEFAULT TRUE/FALSE, TIMESTAMPTZ DEFAULT NOW()
- Schema criado em `initDb()` com `CREATE TABLE IF NOT EXISTS`
- **Tabelas:** noticias, horarios_missas, paroquia_info, galeria, contatos, configuracoes, mensagens_contato, users, audit_log, session, comunidades, **santos**
- **Seeds:** santos (padroeiros + jovens) e comunidades reais de Ponte Nova inseridos condicionalmente

## Env vars obrigatórias

| Var | Uso |
|---|---|
| `DATABASE_URL` | Neon PostgreSQL connection string |
| `SECRET_KEY` | Segredo de sessão (mín. 32 chars) |
| `CLERK_PUBLISHABLE_KEY` | Chave pública Clerk (pk_...) |
| `CLERK_SECRET_KEY` | Chave secreta Clerk (sk_...) |

## Env vars opcionais (mas recomendadas em prod)

| Var | Uso |
|---|---|
| `CLOUDINARY_CLOUD_NAME` / `_API_KEY` / `_API_SECRET` | Upload de imagens |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` / `SMTP_FROM` | Emails (reply + notificação) |
| `SITE_URL` | URL pública (usado no link do email de notificação) |
| `PORT` | Porta (padrão: 5000) |

## Páginas públicas

| Rota | Template | Descrição |
|------|----------|-----------|
| `/` | `index.html` | Homepage com seções |
| `/noticias` | `noticias.html` | Grid de notícias |
| `/noticias/:id` | `noticia.html` | Notícia individual |
| `/comunidades` | `comunidades.html` | Grid de comunidades |
| `/santos` | `santos.html` | Santos padroeiros + jovens por categoria |

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
3. `CLERK_PUBLISHABLE_KEY` / `CLERK_SECRET_KEY` — keys do Clerk Dashboard
4. `CLOUDINARY_*` — para upload de imagens funcionar
5. `SMTP_*` + `SITE_URL` — para emails funcionarem

> **Atenção:** arquivos em `static/uploads/` NÃO persistem no Vercel (serverless). Todas as imagens devem estar no Cloudinary.

## Gotchas

- `paroquia_info.secao` é UNIQUE — use `ON CONFLICT (secao) DO NOTHING` em inserts
- CSRF: rotas `/api/*` são isentas; todas as outras POST/PUT/DELETE precisam do token (apenas para users autenticados)
- Auth é 100% Clerk — NÃO há mais bcryptjs, connect-pg-simple, ou login por username/senha
- Tabela `users` mantida para FK do `audit_log`, mas auth é via Clerk
- `database.db` na raiz é legado do Flask — ignorar
- Santos sem imagem mostram placeholder com ícone de cruz
- Comunidades seed: Bom Pastor (Copacabana), São Geraldo, Vila Alvarenga
