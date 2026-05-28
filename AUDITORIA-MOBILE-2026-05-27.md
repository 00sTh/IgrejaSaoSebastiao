# Auditoria Mobile — Paróquia São Sebastião

- **Data:** 2026-05-27
- **URL auditada:** https://igreja-sao-sebastiao.vercel.app
- **Método:** Playwright (Chromium) navegando 9 rotas públicas em 4 viewports (iPhone SE 375×667, iPhone 14 Pro 390×844, Galaxy S23 360×780, iPad portrait 768×1024) = **36 combinações**
- **Screenshots brutos:** `docs/auditoria-mobile-2026-05-27/shots/` (40 PNGs full-page)
- **Dados brutos:** `docs/auditoria-mobile-2026-05-27/results.json`

---

## Sumário executivo

Site **responde 200 em todas as rotas, não tem overflow horizontal em nenhum viewport, viewport meta tag está correto, menu hamburger funciona, e os grids adaptam pra mobile**. A estrutura responsiva está bem feita. Os problemas estão em **3 áreas**: (1) **imagens externas bloqueadas pelo navegador**, (2) **mapa Google com width fixo cortando em celular**, e (3) **conteúdo vazio em produção** (notícias, galeria, confissões).

| Severidade | Qtd | Tempo estimado de fix |
|---|---|---|
| **P0** (quebra UX/função) | 5 | 4-6h |
| **P1** (degrada UX) | 6 | 4-5h |
| **P2** (polish) | 3 | 1-2h |

**Estado geral:** o site **funciona** no celular, mas **3 das suas principais seções estão mutiladas** visualmente: mapa cortado, comunidades sem fotos, santos sem retratos. O usuário que abre no celular ganha uma impressão de site incompleto.

---

## P0 — Críticos

### P0-1. Mapa Google cortado pela metade em celular
- **Rotas afetadas:** `/` (home, seção "Onde Nos Encontrar")
- **Viewports:** iPhone SE 375px, iPhone 14 Pro 390px, Galaxy S23 360px
- **Não afeta:** iPad 768px (aí o mapa cabe)
- **Causa:** `templates/index.html:320` tem `<iframe ... width="600" height="450">` hardcoded. O wrapper aplica `max-width:100%` mas o iframe ignora e renderiza 600px. Resultado: o card "Igreja Matriz de São Seba…" estoura cortado, e o pin não fica visível.
- **Evidência:** `docs/auditoria-mobile-2026-05-27/shots/FOCUS-map-iphone-se.png`
- **Fix:** envolver o iframe num wrapper com aspect-ratio CSS e dar `width:100%` no iframe.
  ```css
  .map-wrapper { position: relative; width: 100%; aspect-ratio: 4 / 3; }
  .map-wrapper iframe { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; }
  ```
  E no template trocar os atributos `width="600" height="450"` pra `width="100%" height="100%"`.

### P0-2. Imagens das comunidades não carregam (Blogger CDN bloqueado)
- **Rotas afetadas:** `/comunidades` (12 cards), `/` (cards de comunidade na home)
- **Causa:** as imagens estão hospedadas em `blogger.googleusercontent.com`. O Chrome bloqueia essas requisições com `net::ERR_BLOCKED_BY_ORB` (Opaque Response Blocking) porque a resposta não tem CORS/cross-origin headers compatíveis. **Acontece em todos os celulares** (e desktop tb, na real).
- **Evidência:** `docs/auditoria-mobile-2026-05-27/shots/iphone-se-comunidades.png` — vários cards mostram "Sem foto" / ícone placeholder
- **URLs falhando** (amostra):
  - `https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgZ_SSc05LPtBSCrxDl...`
  - `https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjd_xOu8aWinCp5...`
- **Fix:** migrar essas imagens pra Cloudinary (já está configurado em `src/lib/media.ts`). Baixar do Blogger e re-upload via `/admin/comunidades` ou via script.

### P0-3. Imagens dos santos não carregam (Wikipedia commons bloqueada)
- **Rotas afetadas:** `/santos`
- **Causa:** mesmo problema do P0-2, mas com `upload.wikimedia.org`. ORB bloqueia.
- **Evidência:** `docs/auditoria-mobile-2026-05-27/shots/iphone-se-santos.png` — alguns retratos faltando
- **URLs falhando** (amostra):
  - `https://upload.wikimedia.org/wikipedia/commons/3/3f/Therese_Lisieux.JPG`
  - `https://upload.wikimedia.org/wikipedia/commons/a/a7/Bernhard_Plockhorst_-_Good_Shephard.jpg`
- **Fix:** mesmo do P0-2 — baixar e re-hospedar no Cloudinary.

### P0-4. Página Notícias vazia em produção
- **Rotas afetadas:** `/noticias`
- **Causa:** banco de produção sem registros na tabela `noticias`. Página renderiza só hero + footer + botão "Voltar para o início" — sem empty state explicando que ainda não há notícias publicadas.
- **Evidência:** `docs/auditoria-mobile-2026-05-27/shots/iphone-se-noticias.png`
- **Fix duas opções:**
  - (a) **Cadastrar notícias** via `/admin/noticias` (mais provável a intenção)
  - (b) Adicionar empty state no template (`templates/noticias.html`) com mensagem amigável tipo "Em breve publicaremos as primeiras notícias da paróquia"

### P0-5. CSP viola inline event handlers em `/comunidades` e `/santos`
- **Causa:** `helmet.js` aplica `script-src-attr 'none'` (default seguro), mas os templates de comunidades/santos têm `onclick=` ou similar inline. Console:
  > `Executing inline event handler violates the following Content Security Policy directive 'script-src-attr 'none'`
- **Impacto real:** o handler **não é executado** — funcionalidades como abrir lightbox, fechar modal, ou clicar em card podem estar quebradas em produção. Cheque manualmente.
- **Fix:** remover os `onclick=` inline e mover pra `addEventListener` em script externo. Ou adicionar nonce/hash na CSP (não recomendado).

---

## P1 — Degrada UX

### P1-0. Hero "São Sebastião" fica minúsculo em celular ✅ **RESOLVIDO 2026-05-27**

**Solução aplicada:**
- Criada versão mobile dedicada `static/img/hero-background-mobile.jpg` (1000×1100, 63KB) — composição vertical com santo+cruz no topo e logo "PARÓQUIA SÃO SEBASTIÃO / PONTE NOVA - MG" embaixo, extraídos da imagem original com ImageMagick.
- CSS `static/style.css:356-362` atualizado: troca a imagem e o aspect-ratio dentro do media query `(max-aspect-ratio: 1280/727)`:
  ```css
  .hero-section::before {
    aspect-ratio: 1000 / 1100;  /* era 1280/727 */
    background: ... url('img/hero-background-mobile.jpg') ...;
  }
  ```

**Impacto medido (preview Playwright):**

| Viewport | Banner antes | Banner depois | Ganho |
|---|---|---|---|
| iPhone SE 375×667 | 213px | **412px** | +94% |
| iPhone 14 Pro 390×844 | 221px | **429px** | +94% |
| Galaxy S23 360×780 | 204px | **396px** | +94% |
| iPad portrait 768×1024 | 436px | 845px | +94% |

**Antes/depois:**
- ❌ Antes: `docs/auditoria-mobile-2026-05-27/shots/HERO-iphone-se.png` (santo minúsculo)
- ✅ Depois: `docs/auditoria-mobile-2026-05-27/shots/PREVIEW-iphone-se.png` (santo protagonista)

**Achado original abaixo (mantido pra referência):**


- **Rotas afetadas:** `/` (banner principal acima da dobra)
- **Viewports afetados:** todos com `aspect-ratio < 1280/727` (≈1.76), ou seja, **iPhone SE, iPhone 14 Pro, Galaxy S23, e até iPad portrait**
- **Causa técnica:** `static/style.css:339` define o hero com `background: ... no-repeat center 30%/cover` (modo cover, usado em desktop landscape). Mas em `@media (max-aspect-ratio: 1280 / 727)` (linha 345-371) ele vira "banner mode": `.hero-section::before` com `aspect-ratio: 1280/727` + `background-size: contain` + imagem original `hero-background.jpg` (1280×727, landscape).
- **Resultado visual:** a imagem do santo + nome "Paróquia São Sebastião" cabe inteira (graças ao `contain`), mas em altura mínima:
  - iPhone SE (375×667): banner com **213px de altura** — santo+texto ocupam ~120-180px de altura útil
  - Galaxy S23 (360×780): **204px** de altura
  - iPad portrait (768×1024): **436px** — tolerável
- **Evidência:**
  - `docs/auditoria-mobile-2026-05-27/shots/HERO-iphone-se.png` (santo pequeno)
  - `docs/auditoria-mobile-2026-05-27/shots/HERO-ipad-portrait.png` (ok)
- **Impacto:** primeira impressão do site no celular é fraca — a marca paroquial (santo + nome) é o elemento mais importante visualmente, e fica achatada num banner de 213px.
- **Fix recomendado (2 opções):**
  - **(a) Versão mobile dedicada da imagem:** criar `hero-background-mobile.jpg` em formato retrato (ex: 800×900) focando só no santo+nome, e usar `<picture>` ou troca por media query no CSS:
    ```css
    @media (max-aspect-ratio: 1280/727) {
      .hero-section::before {
        aspect-ratio: 4 / 5;   /* mais vertical */
        background-image: url('img/hero-background-mobile.jpg');
        background-size: cover;
      }
    }
    ```
  - **(b) Sem nova imagem, só CSS:** aumentar o aspect-ratio do banner em mobile (`aspect-ratio: 1 / 1` por exemplo) e cropar a imagem original com `background-size: cover` + `background-position: center`. Vai cortar laterais, mas o santo+nome (que estão no centro) ganham muito mais altura visual.

### P1-1. `Comunidade_acolhedora.jpg` é 671KB com overhead 6×
- **Rota:** `/` (hero secundário "Nossa Igreja em Imagens")
- **Métricas reais:**
  - Natural: 2048×1536px
  - Display em iPhone SE: 327×245px
  - Display em iPad: ~600×450px
  - Banda: **671KB** servidos pra mostrar 327×245
- **Impacto:** em 4G/3G lento, ~5s só pra essa imagem. Contribui pros 14s de carga da home.
- **Fix:** redimensionar pra 1024×768 e converter pra WebP (resultado esperado: ~80KB). Idealmente servir variantes via `<picture>` com `srcset` (mobile 600px / tablet 1200px).

### P1-2. Home demora 13-17s pra completar carga
- **Métricas (waitUntil: networkidle):**
  - iPhone SE: 14385ms
  - iPhone 14 Pro: 13220ms
  - Galaxy S23: 15711ms
  - iPad: 17808ms
- **Causa principal:** Google Maps tiles + Comunidade_acolhedora.jpg (671KB) + cold start serverless Vercel.
- **Fix:**
  - Otimizar a imagem (P1-1)
  - Considerar lazy loading do iframe do mapa (`loading="lazy"` já tá, mas o `networkidle` espera ele) — não afeta usuário real diretamente, mas o LCP fica feio
  - `loading="lazy"` em todas as imagens abaixo da dobra

### P1-3. Tap targets <44×44px (recomendação Apple HIG / WCAG 2.5.5)
- **Encontrados em todas as páginas:**
  - **Botão alternar tema (claro/escuro):** 36×36 — provavelmente no header
  - **Link "Contato" no footer:** 55×19 (altura crítica — 19px só)
  - **Link "Política de Privacidade" no footer:** 149×19
  - **CTA "Ver Horários das Missas" na home:** 201×43 (1px a menos que o mínimo)
  - **Link `contato@igrejasst.org`:** 181×32
  - **Filtro "Todas" na galeria:** 88×42
- **Fix:** aumentar `min-height: 44px` em botões e links de navegação. Adicionar `padding: 12px 0` em links de footer.

### P1-4. Confissões sem horários — empty state silencioso
- **Rota:** `/horarios` (seção "Confissões")
- **Evidência:** `docs/auditoria-mobile-2026-05-27/shots/iphone-se-horarios.png` — título "Confissões" aparece com seção vazia abaixo
- **Fix:** cadastrar em `/admin/horarios` ou adicionar mensagem "Agendar pelo telefone" no template.

### P1-5. Fontes <14px em texto secundário
- **Locais:** subtitle home (12.8px "Onde a Fé Encontra a Comunidad..."), badges "1 missa"/"2 missas" (12.8px), descrições padroeiros (12.8px), label "Sem foto" (12px)
- **Impacto:** legibilidade reduzida pra usuários com vista cansada (público típico da igreja inclui idosos)
- **Fix:** subir base pra 14px em mobile (`@media (max-width: 768px) { body { font-size: 16px } }`).

---

## P2 — Polish

### P2-1. Botão de tema dark/light é 36×36
- Tap target P1, mas como já está pegado no P1-3, listo aqui por completude.

### P2-2. Vídeos: empty state correto mas botão único
- Página `/videos` mostra "Nenhum vídeo publicado ainda" com botão "Voltar para o início" centralizado. OK funcional, mas falta um link "Visite nosso canal no YouTube" se houver canal.

### P2-3. iPad mostra 5 tap targets <44px (vs 3 no mobile)
- Em viewport maior alguns elementos ainda ficam pequenos. Provavelmente links de footer mais espaçados mas ainda com altura 19-22px.

---

## Top 5 quick wins (<30min cada, >50% do impacto)

1. **[P0-1] Tornar mapa responsivo** — 5 linhas de CSS + 1 atributo no iframe. Resolve quebra visual em 75% dos viewports.
2. **[P1-0] Aumentar o hero do São Sebastião em mobile** — opção (b) é só CSS: trocar `aspect-ratio: 1280/727` por `1/1` e `background-size: contain` por `cover` dentro do media query. Banner ganha o dobro de altura, santo fica protagonista.
3. **[P0-4] Adicionar empty state em /noticias** — 6 linhas de template Nunjucks. Resolve impressão de site quebrado.
4. **[P1-1] Reotimizar Comunidade_acolhedora.jpg** — `cwebp` ou `sharp` em CLI. Reduz home load em ~3s.
5. **[P1-3] CSS global `min-height: 44px` em botões/links de nav** — 3 linhas no `static/style.css`. Resolve 90% dos tap target failures.

---

## Performance — tempo de carga por viewport (waitUntil: networkidle)

| Rota | iPhone SE | iPhone 14 Pro | Galaxy S23 | iPad |
|---|---|---|---|---|
| `/` | 14385ms | 13220ms | 15711ms | 17808ms |
| `/noticias` | 1242ms | 1262ms | 1291ms | 1252ms |
| `/comunidades` | 8962ms | 8123ms | **20636ms** | 8768ms |
| `/santos` | 8341ms | 7644ms | 7464ms | 6131ms |
| `/galeria` | 1315ms | 1261ms | 1262ms | 1301ms |
| `/horarios` | 1273ms | 1254ms | 1242ms | 1269ms |
| `/videos` | 1257ms | 1233ms | 1253ms | 1229ms |
| `/termos-de-uso` | 1247ms | 1314ms | 1334ms | 1235ms |
| `/politica-de-privacidade` | 1374ms | 1235ms | 1259ms | 1250ms |

**Observação:** páginas leves (notícias, galeria, horários, vídeos, termos, privacidade) carregam em ~1.2s — excelente. O peso vem de imagens externas que tentam carregar e timeout (`comunidades`, `santos`) ou imagem grande (`/`).

---

## Recursos mais pesados (home)

| Tamanho | Tipo | URL |
|---|---|---|
| **671.3 KB** | image/jpeg | `/img/Comunidade_acolhedora.jpg` ⚠️ |
| 76.5 KB | image/jpeg | `/img/hero-background.jpg` |
| 41.0 KB | image/png | `/img/logo.png` |
| 35.3 KB | image/png | Google Maps tile (estático) |
| ~50 KB total | image/webp | Tiles vetoriais do mapa (8 arquivos) |

---

## O que NÃO foi testado

- **Rotas admin** (`/admin/*`) — atrás de Clerk; precisaria de credenciais
- **Formulário de contato** (`POST /api/enviar-mensagem`) — disparar envio de email real, evitado pra não poluir caixa
- **Modo dark/light** — botão presente, comportamento de toggle não testado em todos viewports
- **Interação real com mapa** — só captura visual; arrastar/zoom não foi testado
- **Cookies / consent banner** — se houver
- **Connection throttling 3G real** — usei carga em rede normal; números reais em 3G serão piores

---

## Coisas que funcionam bem (não tem o que arrumar)

- ✅ Zero overflow horizontal em **36 combinações testadas**
- ✅ Viewport meta tag presente em todos os templates
- ✅ Menu hamburger com `nav-toggle` funcional em mobile (`@media (max-width: 992px)`)
- ✅ Grids CSS com `minmax()` adaptam pra coluna única em mobile
- ✅ Imagens com `max-width: 100%; height: auto;` no CSS base
- ✅ Empty states corretos em `/galeria` e `/videos`
- ✅ CSS bem organizado: 1347 linhas, 5 breakpoints, variáveis CSS
- ✅ Skip link "Pular para o conteúdo principal" (acessibilidade)
- ✅ Logo e hero background otimizados (76KB, 41KB)
- ✅ Sem `<table>` no público — layouts em flex/grid
- ✅ Sem console errors graves de JavaScript (só CSP violations e imagens ORB)
