export interface Noticia {
  id: number
  titulo: string
  subtitulo: string | null
  conteudo: string
  imagem_url: string | null
  tipo: string
  data_criacao: string
}

export interface HorarioMissa {
  id: number
  dia_semana: string
  horario: string
  tipo: string | null
  nome: string | null
  ativo: boolean
}

export interface ParoquiaInfo {
  id: number
  secao: string
  titulo: string
  conteudo: string
  ordem: number
}

export interface Galeria {
  id: number
  titulo: string
  descricao: string | null
  categoria: string | null
  imagem_url: string
  data_upload: string
  ativo: boolean
}

export interface Contato {
  id: number
  tipo: string
  valor: string
  icone: string | null
  ordem: number
}

export interface Configuracao {
  chave: string
  valor: string
  descricao: string | null
}

export interface Agendamento {
  id: number
  nome: string
  email: string
  telefone: string
  mes: number
  dia: number
  horario: string
  observacoes: string | null
  status: string
  data_criacao: string
}

export interface Mensagem {
  id: number
  nome: string
  email: string
  mensagem: string
  lida: boolean
  resposta: string | null
  data_resposta: string | null
  data_criacao: string
}

export interface HorarioConfissao {
  id: number
  dia_semana: string
  horario: string
  ativo: boolean
}

export interface Comunidade {
  id: number
  nome: string
  bairro: string
  descricao: string | null
  endereco: string | null
  mapa_url: string | null
  imagem_url: string | null
  ativo: boolean
  ordem: number
  data_criacao: string
}

export interface ComunidadeHorario {
  id: number
  comunidade_id: number
  tipo: string
  titulo: string | null
  dia_semana: string | null
  data_especifica: string | null
  horario: string
  descricao: string | null
  ativo: boolean
}

export interface Santo {
  id: number
  nome: string
  descricao: string | null
  imagem_url: string | null
  categoria: string       // 'jovem' | 'padroeiro' | 'outros'
  dia_festa: string | null
  ativo: boolean
  ordem: number
  data_criacao: string
}

export interface User {
  id: number
  username: string
  password_hash: string
  email: string | null
  role: string
  is_active: boolean
  created_at: string
  last_login: string | null
  failed_attempts: number
}

export interface SessionUser {
  id: number
  username: string
  role: string
}

// Express session augmentation (only flash + CSRF now, auth is via Clerk)
declare module 'express-session' {
  interface SessionData {
    csrf_token?: string
  }
}

// Express locals augmentation
declare global {
  namespace Express {
    interface Locals {
      currentUser: SessionUser | null
      csrfToken: string
      messages: Array<{ category: string; text: string }>
    }
  }
}
