import 'dotenv/config'
import { z } from 'zod'

const envSchema = z.object({
  DATABASE_URL: z.string().min(1, 'DATABASE_URL é obrigatória'),
  SECRET_KEY: z.string().min(32, 'SECRET_KEY deve ter no mínimo 32 caracteres'),
  PORT: z.string().optional(),
  UPLOAD_FOLDER: z.string().optional(),
  MAX_FILE_SIZE: z.string().optional(),
  ADMIN_USERNAME: z.string().optional(),
  ADMIN_PASSWORD: z.string().optional(),
  DEBUG: z.string().optional(),
  CLOUDINARY_CLOUD_NAME: z.string().optional(),
  CLOUDINARY_API_KEY: z.string().optional(),
  CLOUDINARY_API_SECRET: z.string().optional(),
  SMTP_HOST: z.string().optional(),
  SMTP_PORT: z.string().optional(),
  SMTP_USER: z.string().optional(),
  SMTP_PASS: z.string().optional(),
  SMTP_FROM: z.string().optional(),
  NODE_ENV: z.string().optional(),
})

const parsed = envSchema.safeParse(process.env)

if (!parsed.success) {
  console.error('❌ Variáveis de ambiente inválidas:')
  for (const [field, errors] of Object.entries(parsed.error.flatten().fieldErrors)) {
    console.error(`  ${field}: ${(errors as string[]).join(', ')}`)
  }
  process.exit(1)
}

const env = parsed.data

// Warn about missing optional-but-recommended vars
const warnIfMissing = (key: string, label: string) => {
  if (!env[key as keyof typeof env]) {
    console.warn(`⚠️  ${key} não configurado — ${label}`)
  }
}
warnIfMissing('ADMIN_USERNAME', 'use a env ADMIN_USERNAME para definir o usuário admin')
warnIfMissing('ADMIN_PASSWORD', 'use a env ADMIN_PASSWORD para definir a senha admin')
warnIfMissing('CLOUDINARY_CLOUD_NAME', 'upload de imagens desabilitado')

export const config = {
  secretKey: env.SECRET_KEY,
  port: parseInt(env.PORT ?? '5000', 10),

  databaseUrl: env.DATABASE_URL,

  uploadFolder: env.UPLOAD_FOLDER ?? 'static/uploads',
  maxFileSize: parseInt(env.MAX_FILE_SIZE ?? '10485760', 10),
  allowedExtensions: new Set(['png', 'jpg', 'jpeg', 'gif', 'webp']),

  adminUsername: env.ADMIN_USERNAME ?? 'admin',
  adminPassword: env.ADMIN_PASSWORD ?? '',

  debug: env.DEBUG?.toLowerCase() === 'true',

  cloudinary: {
    cloudName: env.CLOUDINARY_CLOUD_NAME ?? '',
    apiKey: env.CLOUDINARY_API_KEY ?? '',
    apiSecret: env.CLOUDINARY_API_SECRET ?? '',
  },

  smtp: {
    host: env.SMTP_HOST ?? '',
    port: parseInt(env.SMTP_PORT ?? '587', 10),
    user: env.SMTP_USER ?? '',
    pass: env.SMTP_PASS ?? '',
    from: env.SMTP_FROM ?? 'noreply@igrejasaosebastiao.com.br',
  },
} as const
