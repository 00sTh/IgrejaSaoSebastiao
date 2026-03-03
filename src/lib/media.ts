import { v2 as cloudinary } from 'cloudinary'
import { config } from '../config'

cloudinary.config({
  cloud_name: config.cloudinary.cloudName,
  api_key: config.cloudinary.apiKey,
  api_secret: config.cloudinary.apiSecret,
})

const ALLOWED_MIME = new Set(['image/jpeg', 'image/png', 'image/gif', 'image/webp'])
const MAX_SIZE = config.maxFileSize

export class MediaValidationError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'MediaValidationError'
  }
}

export async function uploadImage(buffer: Buffer, originalName: string, mimetype: string): Promise<string> {
  if (!ALLOWED_MIME.has(mimetype)) {
    throw new MediaValidationError('Formato de arquivo não suportado. Use PNG, JPG, GIF ou WEBP.')
  }
  if (buffer.length > MAX_SIZE) {
    throw new MediaValidationError(`Arquivo muito grande. Máximo ${MAX_SIZE / 1024 / 1024}MB.`)
  }

  return new Promise((resolve, reject) => {
    const stream = cloudinary.uploader.upload_stream(
      { folder: 'igrejasaosebastiao', resource_type: 'image' },
      (error, result) => {
        if (error || !result) return reject(error ?? new Error('Upload falhou'))
        resolve(result.secure_url)
      }
    )
    stream.end(buffer)
  })
}

export async function deleteImage(publicId: string): Promise<void> {
  await cloudinary.uploader.destroy(publicId)
}
