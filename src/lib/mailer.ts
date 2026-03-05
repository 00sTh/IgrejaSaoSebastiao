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

export async function sendNewMessageNotification(
  nome: string,
  email: string,
  mensagem: string
): Promise<boolean> {
  const transporter = createTransport()
  if (!transporter) return false

  const adminEmail = config.smtp.from

  const html = `
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
  <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #3B5F6C;">Nova mensagem recebida</h2>
    <p>Uma nova mensagem foi enviada pelo formulário do site.</p>
    <table style="width:100%; border-collapse: collapse; margin: 16px 0;">
      <tr><td style="padding: 8px; background:#f5f5f5; font-weight:600; width:120px;">Nome</td><td style="padding: 8px;">${nome}</td></tr>
      <tr><td style="padding: 8px; background:#f5f5f5; font-weight:600;">E-mail</td><td style="padding: 8px;"><a href="mailto:${email}">${email}</a></td></tr>
      <tr><td style="padding: 8px; background:#f5f5f5; font-weight:600; vertical-align:top;">Mensagem</td><td style="padding: 8px;">${mensagem}</td></tr>
    </table>
    <a href="${process.env.SITE_URL ?? 'http://localhost:5000'}/admin/mensagens" style="display:inline-block; background:#3B5F6C; color:#fff; padding:10px 20px; border-radius:6px; text-decoration:none; font-weight:600;">Ver no painel admin</a>
  </div>
</body>
</html>`

  try {
    await transporter.sendMail({
      from: config.smtp.from,
      to: adminEmail,
      subject: `Nova mensagem de ${nome} — Igreja São Sebastião`,
      html,
    })
    return true
  } catch {
    return false
  }
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
