import { Router } from 'express'
import { dbQuery } from '../../db'

const router = Router()

router.get('/dashboard', async (_req, res) => {
  const [
    noticiasCount,
    galeriaCount,
    missasCount,
    agendamentosCount,
    mensagensCount,
    noticiasRecentes,
  ] = await Promise.all([
    dbQuery<{ count: string }>`SELECT COUNT(*) as count FROM noticias`,
    dbQuery<{ count: string }>`SELECT COUNT(*) as count FROM galeria`,
    dbQuery<{ count: string }>`SELECT COUNT(*) as count FROM horarios_missas WHERE ativo = TRUE`,
    dbQuery<{ count: string }>`SELECT COUNT(*) as count FROM agendamentos_confissao WHERE status = 'pendente'`,
    dbQuery<{ count: string }>`SELECT COUNT(*) as count FROM mensagens_contato WHERE lida = FALSE`,
    dbQuery`SELECT * FROM noticias ORDER BY data_criacao DESC LIMIT 5`,
  ])

  res.render('admin_dashboard.html', {
    total_noticias: Number(noticiasCount[0]?.count ?? 0),
    total_fotos: Number(galeriaCount[0]?.count ?? 0),
    total_horarios: Number(missasCount[0]?.count ?? 0),
    total_informacoes: 0,
    agendamentos_pendentes: Number(agendamentosCount[0]?.count ?? 0),
    mensagens_nao_lidas: Number(mensagensCount[0]?.count ?? 0),
    noticias_recentes: noticiasRecentes,
  })
})

export default router
