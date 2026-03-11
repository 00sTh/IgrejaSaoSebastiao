import { neon } from '@neondatabase/serverless'
import { config } from './config'

const sql = neon(config.databaseUrl)

export { sql }

/** Typed tagged template literal for queries — returns T[] */
export function dbQuery<T = Record<string, unknown>>(
  strings: TemplateStringsArray,
  ...values: unknown[]
): Promise<T[]> {
  return sql(strings, ...values) as unknown as Promise<T[]>
}

/** Single-row typed query */
export async function queryOne<T = Record<string, unknown>>(
  strings: TemplateStringsArray,
  ...values: unknown[]
): Promise<T | null> {
  const rows = await (sql(strings, ...values) as unknown as Promise<T[]>)
  return rows[0] ?? null
}

export async function initDb(): Promise<void> {
  // Tabela de notícias
  await sql`
    CREATE TABLE IF NOT EXISTS noticias (
      id SERIAL PRIMARY KEY,
      titulo TEXT NOT NULL,
      subtitulo TEXT,
      conteudo TEXT NOT NULL,
      imagem_url TEXT,
      tipo TEXT NOT NULL DEFAULT 'Notícia',
      data_criacao TIMESTAMPTZ DEFAULT NOW()
    )
  `

  // Tabela de horários de missas
  await sql`
    CREATE TABLE IF NOT EXISTS horarios_missas (
      id SERIAL PRIMARY KEY,
      dia_semana TEXT NOT NULL,
      horario TEXT NOT NULL,
      tipo TEXT,
      nome TEXT,
      ativo BOOLEAN DEFAULT TRUE
    )
  `

  // Tabela de informações da paróquia
  await sql`
    CREATE TABLE IF NOT EXISTS paroquia_info (
      id SERIAL PRIMARY KEY,
      secao TEXT NOT NULL UNIQUE,
      titulo TEXT NOT NULL,
      conteudo TEXT NOT NULL,
      ordem INTEGER DEFAULT 0
    )
  `

  // Tabela de galeria de fotos
  await sql`
    CREATE TABLE IF NOT EXISTS galeria (
      id SERIAL PRIMARY KEY,
      titulo TEXT NOT NULL,
      descricao TEXT,
      categoria TEXT,
      imagem_url TEXT NOT NULL,
      data_upload TIMESTAMPTZ DEFAULT NOW(),
      ativo BOOLEAN DEFAULT TRUE
    )
  `

  // Tabela de contatos
  await sql`
    CREATE TABLE IF NOT EXISTS contatos (
      id SERIAL PRIMARY KEY,
      tipo TEXT NOT NULL,
      valor TEXT NOT NULL,
      icone TEXT,
      ordem INTEGER DEFAULT 0
    )
  `

  // Tabela de configurações gerais
  await sql`
    CREATE TABLE IF NOT EXISTS configuracoes (
      chave TEXT PRIMARY KEY,
      valor TEXT NOT NULL,
      descricao TEXT
    )
  `

  // Tabela de mensagens de contato
  await sql`
    CREATE TABLE IF NOT EXISTS mensagens_contato (
      id SERIAL PRIMARY KEY,
      nome TEXT NOT NULL,
      email TEXT NOT NULL,
      mensagem TEXT NOT NULL,
      lida BOOLEAN DEFAULT FALSE,
      resposta TEXT,
      data_resposta TIMESTAMPTZ,
      data_criacao TIMESTAMPTZ DEFAULT NOW()
    )
  `

  // Tabela de usuários (mantida para audit_log FK, mas auth é via Clerk)
  await sql`
    CREATE TABLE IF NOT EXISTS users (
      id SERIAL PRIMARY KEY,
      username TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL,
      email TEXT,
      role TEXT NOT NULL DEFAULT 'viewer',
      is_active BOOLEAN DEFAULT TRUE,
      created_at TIMESTAMPTZ DEFAULT NOW(),
      last_login TIMESTAMPTZ,
      failed_attempts INTEGER DEFAULT 0
    )
  `

  // Tabela de audit log
  await sql`
    CREATE TABLE IF NOT EXISTS audit_log (
      id SERIAL PRIMARY KEY,
      user_id INTEGER,
      action TEXT NOT NULL,
      entity_type TEXT,
      entity_id INTEGER,
      old_value TEXT,
      new_value TEXT,
      ip_address TEXT,
      created_at TIMESTAMPTZ DEFAULT NOW(),
      FOREIGN KEY (user_id) REFERENCES users(id)
    )
  `

  // Session store table (for flash messages/CSRF)
  await sql`
    CREATE TABLE IF NOT EXISTS "session" (
      "sid" varchar NOT NULL COLLATE "default",
      "sess" json NOT NULL,
      "expire" timestamp(6) NOT NULL,
      CONSTRAINT "session_pkey" PRIMARY KEY ("sid") NOT DEFERRABLE INITIALLY IMMEDIATE
    )
  `

  await sql`
    CREATE INDEX IF NOT EXISTS "IDX_session_expire" ON "session" ("expire")
  `

  // Tabela de comunidades
  await sql`
    CREATE TABLE IF NOT EXISTS comunidades (
      id SERIAL PRIMARY KEY,
      nome TEXT NOT NULL,
      bairro TEXT NOT NULL,
      imagem_url TEXT,
      ativo BOOLEAN DEFAULT TRUE,
      ordem INTEGER DEFAULT 0,
      data_criacao TIMESTAMPTZ DEFAULT NOW()
    )
  `

  // Tabela de santos
  await sql`
    CREATE TABLE IF NOT EXISTS santos (
      id SERIAL PRIMARY KEY,
      nome TEXT NOT NULL,
      descricao TEXT,
      imagem_url TEXT,
      categoria TEXT NOT NULL DEFAULT 'outros',
      dia_festa TEXT,
      ativo BOOLEAN DEFAULT TRUE,
      ordem INTEGER DEFAULT 0,
      data_criacao TIMESTAMPTZ DEFAULT NOW()
    )
  `

  // Adicionar coluna descricao em comunidades (seguro se já existir)
  await sql`ALTER TABLE comunidades ADD COLUMN IF NOT EXISTS descricao TEXT`
  await sql`
    DO $$ BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'comunidades_nome_unique') THEN
        ALTER TABLE comunidades ADD CONSTRAINT comunidades_nome_unique UNIQUE (nome);
      END IF;
    END $$
  `

  // Performance indexes
  await sql`CREATE INDEX IF NOT EXISTS idx_noticias_created ON noticias(data_criacao)`
  await sql`CREATE INDEX IF NOT EXISTS idx_mensagens_lida ON mensagens_contato(lida)`
  await sql`CREATE INDEX IF NOT EXISTS idx_comunidades_ordem ON comunidades(ordem, nome)`
  await sql`CREATE INDEX IF NOT EXISTS idx_santos_categoria_ordem ON santos(categoria, ordem, nome)`

  await insertInitialData()
  console.log('✅ Banco de dados inicializado com sucesso!')
}

async function insertInitialData(): Promise<void> {
  // Verificar se já existem dados
  const existing = await queryOne<{ count: string }>`
    SELECT COUNT(*) as count FROM configuracoes
  `
  if (existing && parseInt(existing.count) > 0) {
    await insertSantosIfEmpty()
    await insertComunidadesIfEmpty()
    await fixComunidadesData()
    await updateHistoryData()
    await updateSantosImages()
    return
  }

  // Horários de missas padrão
  const missas = [
    ['Segunda-feira', '07:00', 'Missa'],
    ['Terça-feira', '07:00', 'Missa'],
    ['Quarta-feira', '07:00', 'Missa'],
    ['Quinta-feira', '07:00', 'Missa'],
    ['Sexta-feira', '07:00', 'Missa'],
    ['Sábado', '19:00', 'Missa'],
    ['Domingo', '08:00', 'Missa'],
    ['Domingo', '19:00', 'Missa'],
  ]
  for (const [dia, horario, tipo] of missas) {
    await sql`INSERT INTO horarios_missas (dia_semana, horario, tipo) VALUES (${dia}, ${horario}, ${tipo})`
  }

  // Informações da paróquia
  const paroquiaDefault: [string, string, string][] = [
    ['hero_titulo', 'Igreja São Sebastião', 'Título principal do banner'],
    ['hero_subtitulo', 'Onde a Fé Encontra a Comunidade em Ponte Nova', 'Subtítulo do banner'],
    ['hero_botao', 'Ver Horários das Missas', 'Texto do botão do banner'],
    ['sobre_titulo', 'Seja Bem-Vindo à Nossa Comunidade!', 'Título da seção Sobre'],
    ['sobre_texto', 'A Igreja São Sebastião tem sido um farol de fé e esperança para a comunidade de Ponte Nova por décadas.', 'Texto da seção Sobre'],
    ['horarios_titulo', 'Horários Importantes', 'Título da seção de horários'],
    ['missas_titulo', 'Missas', 'Título do card de missas'],
    ['confissoes_titulo', 'Confissões', 'Título do card de confissões'],
    ['confissoes_horarios', 'Terça a Sexta: 14h às 17h|Sábado: 9h às 12h', 'Horários de confissão (separados por |)'],
    ['secretaria_titulo', 'Secretaria', 'Título do card da secretaria'],
    ['secretaria_horarios', 'Segunda a Sexta: 13h às 18h', 'Horário da secretaria'],
    ['secretaria_telefone', '(31) 3295-1379', 'Telefone da secretaria'],
    ['secretaria_email', 'contato@igrejasst.org', 'Email da secretaria'],
    ['galeria_titulo', 'Nossa Igreja em Imagens', 'Título da seção galeria'],
    ['historia_titulo', 'Nossa História e Legado', 'Título da seção história'],
    ['historia_texto', '<p>Fundada em [Ano], a Igreja São Sebastião tem uma rica história de serviço.</p>', 'Texto da história'],
    ['historia_marcos_titulo', 'Principais Marcos', 'Título dos marcos históricos'],
    ['historia_marcos', '[Ano]: Fundação da paróquia|[Ano]: Construção da igreja|[Ano]: Inauguração', 'Marcos históricos'],
    ['localizacao_titulo', 'Onde Nos Encontrar', 'Título da seção localização'],
    ['localizacao_endereco', 'Praça Getúlio Vargas, 92 - Centro Histórico, Pte. Nova - MG, 35430-003', 'Endereço completo'],
    ['localizacao_telefones', '(31) 98888-6796 / (31) 3881-1401', 'Telefones'],
    ['localizacao_email', 'contato@igrejasst.org', 'Email'],
    ['localizacao_mapa', 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3739.19!2d-42.91!3d-20.41!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0xa497026b4d46e1%3A0x5d64af00395326ce!2sIgreja%20Matriz%20de%20S%C3%A3o%20Sebasti%C3%A3o!5e0!3m2!1spt-BR!2sbr', 'URL do mapa'],
    ['confissao_titulo', 'Agendamento de Confissão com o Padre', 'Título do formulário'],
    ['confissao_texto', '<p>O Sacramento da Confissão é um momento de graça e reconciliação.</p>', 'Texto informativo'],
    ['contato_titulo', 'Entre em Contato', 'Título da seção contato'],
    ['contato_subtitulo', 'Estamos Prontos para Ajudar', 'Subtítulo'],
    ['contato_texto', 'Tem dúvidas, sugestões ou precisa de mais informações? Fale conosco!', 'Texto'],
    ['rodape_texto', 'Igreja São Sebastião. Todos os direitos reservados.', 'Rodapé'],
    ['redes_facebook', '#', 'Link do Facebook'],
    ['redes_instagram', '#', 'Link do Instagram'],
    ['redes_whatsapp', '#', 'Link do WhatsApp'],
  ]
  for (let i = 0; i < paroquiaDefault.length; i++) {
    const [secao, titulo, conteudo] = paroquiaDefault[i]
    await sql`
      INSERT INTO paroquia_info (secao, titulo, conteudo, ordem)
      VALUES (${secao}, ${titulo}, ${conteudo}, ${i})
      ON CONFLICT (secao) DO NOTHING
    `
  }

  // Contatos padrão
  await sql`INSERT INTO contatos (tipo, valor, icone, ordem) VALUES ('telefone', '(31) 0000-0000', 'fas fa-phone', 1)`
  await sql`INSERT INTO contatos (tipo, valor, icone, ordem) VALUES ('email', 'contato@igrejasaosebastiao.com.br', 'fas fa-envelope', 2)`
  await sql`INSERT INTO contatos (tipo, valor, icone, ordem) VALUES ('endereco', 'Rua São Sebastião, 123 - Ponte Nova/MG', 'fas fa-map-marker-alt', 3)`

  // Configurações gerais
  await sql`INSERT INTO configuracoes (chave, valor, descricao) VALUES ('site_nome', 'Igreja São Sebastião', 'Nome do site')`
  await sql`INSERT INTO configuracoes (chave, valor, descricao) VALUES ('site_descricao', 'Onde a Fé Encontra a Comunidade', 'Descrição do site')`
  await sql`INSERT INTO configuracoes (chave, valor, descricao) VALUES ('endereco_completo', 'Rua São Sebastião, 123 - Centro, Ponte Nova/MG', 'Endereço completo')`
  await sql`INSERT INTO configuracoes (chave, valor, descricao) VALUES ('mapa_latitude', '-20.4169', 'Latitude para o mapa')`
  await sql`INSERT INTO configuracoes (chave, valor, descricao) VALUES ('mapa_longitude', '-42.9089', 'Longitude para o mapa')`

  await insertSantosIfEmpty()
  await insertComunidadesIfEmpty()
  await fixComunidadesData()
  await updateHistoryData()
  await updateSantosImages()
}

async function insertSantosIfEmpty(): Promise<void> {
  const count = await queryOne<{ count: string }>`SELECT COUNT(*) as count FROM santos`
  if (count && parseInt(count.count) > 0) return

  // Santos Padroeiros
  const padroeiros: [string, string, string, number][] = [
    ['São Sebastião', 'Padroeiro da Paróquia e da cidade de Ponte Nova. Soldado romano que se converteu ao cristianismo e foi martirizado no século III por defender a fé cristã. É invocado contra pestes e epidemias.', '20 de janeiro', 1],
    ['Bom Pastor', 'Padroeiro da Comunidade no bairro Copacabana. Jesus Cristo é o Bom Pastor que conhece suas ovelhas e dá a vida por elas, símbolo do amor e cuidado divino pela comunidade.', '4º Domingo da Páscoa', 2],
    ['Nossa Senhora', 'Mãe de Jesus Cristo, venerada em toda a paróquia sob diversos títulos. Intercessora dos fiéis e modelo de fé, obediência e amor a Deus.', '15 de agosto', 3],
    ['São Judas Tadeu', 'Um dos doze Apóstolos de Jesus, primo do Senhor. É o padroeiro das causas impossíveis e situações desesperadoras, muito venerado no Brasil.', '28 de outubro', 4],
  ]
  for (const [nome, descricao, dia, ordem] of padroeiros) {
    await sql`INSERT INTO santos (nome, descricao, categoria, dia_festa, ordem) VALUES (${nome}, ${descricao}, 'padroeiro', ${dia}, ${ordem})`
  }

  // Santos Jovens
  const jovens: [string, string, string, number][] = [
    ['Beato Carlo Acutis', 'Jovem italiano beatificado em 2020, conhecido como o "padroeiro da internet". Documentou milagres eucarísticos pelo mundo em um site. Faleceu aos 15 anos de leucemia, oferecendo seu sofrimento pela Igreja.', '12 de outubro', 1],
    ['Santa Teresinha do Menino Jesus', 'Carmelita francesa e Doutora da Igreja, conhecida pela "pequena via" — fazer as coisas simples do dia a dia com grande amor. Entrou no Carmelo aos 15 anos e faleceu aos 24.', '1 de outubro', 2],
    ['São Domingos Sávio', 'Aluno de São João Bosco, viveu uma vida de santidade extraordinária desde a infância. Faleceu aos 14 anos. Seu lema era "Antes morrer do que pecar".', '6 de maio', 3],
    ['Santa Maria Goretti', 'Mártir da pureza, assassinada aos 11 anos ao resistir a uma tentativa de violência. Antes de morrer, perdoou seu agressor, que posteriormente se converteu.', '6 de julho', 4],
    ['São Tarcísio', 'Jovem mártir dos primeiros séculos do cristianismo, morto ao proteger a Eucaristia de profanação. É o padroeiro dos coroinhas e da primeira comunhão.', '15 de agosto', 5],
  ]
  for (const [nome, descricao, dia, ordem] of jovens) {
    await sql`INSERT INTO santos (nome, descricao, categoria, dia_festa, ordem) VALUES (${nome}, ${descricao}, 'jovem', ${dia}, ${ordem})`
  }
}

async function insertComunidadesIfEmpty(): Promise<void> {
  const existing = await dbQuery<{ nome: string }>`SELECT nome FROM comunidades`
  const existingNames = new Set(existing.map(c => c.nome))

  const comunidades: [string, string, string, number][] = [
    ['Comunidade Bom Pastor', 'Dioguinho', 'Padroeiro: Bom Pastor — celebração em 8 de dezembro', 1],
    ['Comunidade São Geraldo', 'São Geraldo', 'Padroeiro: São Sebastião — Eucaristia: 2ª quarta-feira, 19h30', 2],
    ['Comunidade Vila Alvarenga', 'Vila Alvarenga', 'Padroeira: Nossa Senhora de Fátima — Eucaristia: 1ª quarta-feira, 19h30', 3],
    ['Comunidade Bom Fim', 'Bom Fim', 'Padroeiro: São José — inaugurada em 2005', 4],
    ['Comunidade Central', 'Centro', 'Padroeiro: Santo Expedito — Eucaristia: 19 de abril', 5],
    ['Comunidade Copacabana', 'Copacabana', 'Padroeira: Nossa Senhora Aparecida — Eucaristia: 1ª terça-feira, 19h30', 6],
    ['Comunidade Esplanada', 'Esplanada', 'Padroeiro: Santo Cristóvão — Eucaristia: 3º domingo, 9h', 7],
    ['Comunidade Fazenda da Serra', 'Fazenda da Serra', 'Padroeiro: São Judas Tadeu — Eucaristia: 2ª quinta-feira, 19h30', 8],
    ['Comunidade Massangano', 'Massangano', 'Padroeiro: São José — Eucaristia: 3ª terça-feira, 19h30', 9],
    ['Comunidade Morro Grande', 'Morro Grande', 'Padroeira: Nossa Senhora Aparecida — Eucaristia: 3ª terça-feira, 18h', 10],
    ['Comunidade Rosário', 'Rosário', 'Padroeira: Nossa Senhora do Rosário — festa em 7 de outubro', 11],
    ['Comunidade Santa Helena', 'Santa Helena', 'Padroeira: Santa Helena — Eucaristia: 3ª quinta-feira de cada mês', 12],
    ['Comunidade Santa Tereza', 'Santa Tereza', 'Padroeira: Santa Luzia — Eucaristia: 1ª terça-feira do mês', 13],
    ['Comunidade Vau Açu', 'Vau Açu', 'Padroeiro: São Sebastião — Eucaristia: 1º domingo do mês', 14],
  ]

  for (const [nome, bairro, descricao, ordem] of comunidades) {
    await sql`INSERT INTO comunidades (nome, bairro, descricao, ordem) VALUES (${nome}, ${bairro}, ${descricao}, ${ordem}) ON CONFLICT (nome) DO NOTHING`
  }
}

async function fixComunidadesData(): Promise<void> {
  // Corrige o seed antigo que colocou Bom Pastor no bairro Copacabana (errado)
  await sql`
    UPDATE comunidades
    SET bairro = 'Dioguinho',
        descricao = 'Padroeiro: Bom Pastor — celebração em 8 de dezembro'
    WHERE nome = 'Comunidade Bom Pastor' AND bairro = 'Copacabana'
  `
  // Adiciona descricao nas comunidades antigas que ficaram sem
  await sql`
    UPDATE comunidades SET descricao = 'Padroeiro: São Sebastião — Eucaristia: 2ª quarta-feira, 19h30'
    WHERE nome = 'Comunidade São Geraldo' AND (descricao IS NULL OR descricao = '')
  `
  await sql`
    UPDATE comunidades SET descricao = 'Padroeira: Nossa Senhora de Fátima — Eucaristia: 1ª quarta-feira, 19h30'
    WHERE nome = 'Comunidade Vila Alvarenga' AND (descricao IS NULL OR descricao = '')
  `
  // Adiciona foto da Comunidade Bom Fim (única disponível online)
  await sql`
    UPDATE comunidades SET imagem_url = 'https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEi3p54V4kE25DCLXmZk-FV6NPm7OdhSIr2s1fTva2JMI51v5E3-5CqIoWGNPVgeF7uRXM_XqKZLP0z_L3j4vbyua5MkdgNpHGXFVGGcCNo15_sqiDHtejH49dv8gBozVfJuz1NSVq1HIlYX/s1600/BOM+FIM.jpg'
    WHERE nome = 'Comunidade Bom Fim' AND imagem_url IS NULL
  `
  // Remove duplicatas exatas por nome (mantém o de menor id)
  await sql`
    DELETE FROM comunidades WHERE id NOT IN (
      SELECT MIN(id) FROM comunidades GROUP BY nome
    )
  `
}

async function updateSantosImages(): Promise<void> {
  const images: [string, string][] = [
    ['São Sebastião',                'https://upload.wikimedia.org/wikipedia/commons/e/e0/Guido_Reni_-_Saint_Sebastian_-_Google_Art_Project_%2827740148%29.jpg'],
    ['Bom Pastor',                   'https://upload.wikimedia.org/wikipedia/commons/a/a7/Bernhard_Plockhorst_-_Good_Shephard.jpg'],
    ['Nossa Senhora',                'https://upload.wikimedia.org/wikipedia/commons/1/13/Bartolom%C3%A9_Esteban_Perez_Murillo_-_Immaculate_Conception_-_WGA16380.jpg'],
    ['São Judas Tadeu',              'https://upload.wikimedia.org/wikipedia/commons/0/02/El_Greco_-_Apostle_St_Thaddeus_%28Jude%29_-_WGA10601.jpg'],
    ['Beato Carlo Acutis',           'https://upload.wikimedia.org/wikipedia/pt/7/78/Carlo_Acutis.jpg'],
    ['Santa Teresinha do Menino Jesus', 'https://upload.wikimedia.org/wikipedia/commons/3/3f/Therese_Lisieux.JPG'],
    ['São Domingos Sávio',           'https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Life_of_Dominic_Savio_%28page_6_crop%29.jpg/500px-Life_of_Dominic_Savio_%28page_6_crop%29.jpg'],
    ['Santa Maria Goretti',          'https://upload.wikimedia.org/wikipedia/commons/5/5f/Photograph_of_Saint_Maria_Goretti%2C_1902.jpg'],
    ['São Tarcísio',                 'https://upload.wikimedia.org/wikipedia/commons/a/ae/Saint_Tarcisius_MET_DP167090.jpg'],
  ]
  for (const [nome, url] of images) {
    await sql`UPDATE santos SET imagem_url = ${url} WHERE nome = ${nome} AND imagem_url IS NULL`
  }
}

async function updateHistoryData(): Promise<void> {
  // Corrige historia_texto: conteudo deve ter o HTML, titulo deve ser o rótulo
  const hist = await queryOne<{ conteudo: string }>`SELECT conteudo FROM paroquia_info WHERE secao = 'historia_texto'`
  if (hist && (hist.conteudo === 'Texto da história' || hist.conteudo.includes('[Ano]'))) {
    const historiaHtml = `<p>A Paróquia de São Sebastião de Ponte Nova, MG, tem suas raízes no século XVIII. Em <strong>1770</strong>, o fundador do arraial, Padre João do Monte de Medeiros, recebeu autorização do Bispado de Mariana e ergueu a primeira capelinha às margens do Rio Piranga.</p><p>Com o crescimento da população, Ponte Nova desmembrou-se da Freguesia de Furquim e foi elevada à condição de <strong>Paróquia pelo decreto da Regência em 14 de julho de 1832</strong>. Em <strong>1860</strong>, o Padre José Miguel Martins Chaves construiu um novo templo de estilo colonial, com torres de 12 metros e arquitetura regional mineira.</p><p>No dia <strong>23 de outubro de 1915</strong>, um grande incêndio destruiu a Igreja por completo. O projeto de reconstrução foi encomendado ao padre-arquiteto Frederico Vienkein. A nova Matriz, em estilo <strong>neogótico</strong> com estrutura de concreto armado, planta cruciforme e belos vitrais, foi consagrada em <strong>26 de abril de 1926</strong> pelo bispo D. Helvécio Gomes de Oliveira.</p><p>Em reconhecimento ao seu valor histórico, artístico e cultural, a Igreja foi <strong>tombada como patrimônio histórico municipal pelo Decreto nº 11.219/2019</strong>.</p>`
    await sql`UPDATE paroquia_info SET titulo = 'Nossa História', conteudo = ${historiaHtml} WHERE secao = 'historia_texto'`
  }

  // Corrige historia_marcos
  const marcos = await queryOne<{ conteudo: string }>`SELECT conteudo FROM paroquia_info WHERE secao = 'historia_marcos'`
  if (marcos && (marcos.conteudo === 'Marcos históricos' || marcos.conteudo.includes('[Ano]'))) {
    const marcosTexto = '1770: Fundação da primeira capelinha pelo Pe. João do Monte de Medeiros|1832: Elevação à Paróquia pelo decreto da Regência Imperial (14 de julho)|1860: Construção de novo templo colonial pelo Pe. José Miguel Martins Chaves|1915: Grande incêndio destrói a Igreja em 23 de outubro|1926: Consagração da atual Matriz neogótica (26 de abril), pelo bispo D. Helvécio|2019: Tombamento como patrimônio histórico municipal — Decreto nº 11.219'
    await sql`UPDATE paroquia_info SET titulo = 'Principais Marcos', conteudo = ${marcosTexto} WHERE secao = 'historia_marcos'`
  }
}
