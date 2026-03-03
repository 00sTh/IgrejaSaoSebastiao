import nodemailer from 'nodemailer'
import { config } from '../config'

function createTransport() {
  if (!config.smtp.host || !config.smtp.user || !config.smtp.pass) return null

  return nodemailer.createTransport({
    host: config.smtp.host,
    port: config.smtp.port,
    secure: config.smtp.port === 465,
    auth: { user: config.smtp.user, pass: config.smtp.pass },
  })
}

export async function sendReplyEmail(
  to: string,
  nome: string,
  mensagemOriginal: string,
  resposta: string
): Promise<boolean> {
  const transporter = createTransport()
  if (!transporter) return false

  const html = `
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
  <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #3B5F6C;">Igreja São Sebastião</h2>
    <p>Olá <strong>${nome}</strong>,</p>
    <p>Obrigado por entrar em contato conosco.</p>
    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
      <p style="color: #666; margin: 0 0 10px 0;"><strong>Sua mensagem:</strong></p>
      <p style="margin: 0; font-style: italic;">"${mensagemOriginal}"</p>
    </div>
    <div style="background: #e8f4f8; padding: 15px; border-radius: 8px; border-left: 4px solid #3B5F6C;">
      <p style="color: #3B5F6C; margin: 0 0 10px 0;"><strong>Nossa resposta:</strong></p>
      <p style="margin: 0;">${resposta}</p>
    </div>
    <p style="margin-top: 30px;">Atenciosamente,<br><strong>Igreja São Sebastião</strong></p>
  </div>
</body>
</html>`

  try {
    await transporter.sendMail({
      from: config.smtp.from,
      to,
      subject: 'Re: Contato - Igreja São Sebastião',
      html,
    })
    return true
  } catch {
    return false
  }
}
