import { neon } from '@neondatabase/serverless'
import { config } from './config'
import bcrypt from 'bcryptjs'

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

  // Tabela de usuários
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

  // Session store table (connect-pg-simple)
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

  // Performance indexes
  await sql`CREATE INDEX IF NOT EXISTS idx_noticias_created ON noticias(data_criacao)`
  await sql`CREATE INDEX IF NOT EXISTS idx_mensagens_lida ON mensagens_contato(lida)`
  await sql`CREATE INDEX IF NOT EXISTS idx_comunidades_ordem ON comunidades(ordem, nome)`

  await insertInitialData()
  console.log('✅ Banco de dados inicializado com sucesso!')
}

async function insertInitialData(): Promise<void> {
  // Verificar se já existem dados
  const existing = await queryOne<{ count: string }>`
    SELECT COUNT(*) as count FROM configuracoes
  `
  if (existing && parseInt(existing.count) > 0) return

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

  // Criar admin padrão
  const adminCount = await queryOne<{ count: string }>`SELECT COUNT(*) as count FROM users`
  if (!adminCount || parseInt(adminCount.count) === 0) {
    const hash = bcrypt.hashSync(config.adminPassword, 12)
    await sql`
      INSERT INTO users (username, password_hash, email, role)
      VALUES (${config.adminUsername}, ${hash}, 'admin@igreja.local', 'super_admin')
    `
    console.log('! Usuário admin padrão criado. ALTERE A SENHA!')
  }
}
