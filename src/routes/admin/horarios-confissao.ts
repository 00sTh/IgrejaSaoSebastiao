import { Router } from 'express'
import { z } from 'zod'
import { dbQuery } from '../../db'

const router = Router()

interface HorarioConfissao {
  id: number
  dia_semana: string
  horario: string
  ativo: boolean
}

const DIAS_ORDEM = ['Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado']

router.get('/horarios-confissao', async (_req, res) => {
  const horarios = await dbQuery<HorarioConfissao>`
    SELECT * FROM horarios_confissao ORDER BY
      CASE dia_semana
        WHEN 'Domingo' THEN 0 WHEN 'Segunda-feira' THEN 1 WHEN 'Terça-feira' THEN 2
        WHEN 'Quarta-feira' THEN 3 WHEN 'Quinta-feira' THEN 4 WHEN 'Sexta-feira' THEN 5
        WHEN 'Sábado' THEN 6 ELSE 7 END,
      horario ASC
  `

  const horariosPorDia: Record<string, HorarioConfissao[]> = {}
  for (const h of horarios) {
    if (!horariosPorDia[h.dia_semana]) horariosPorDia[h.dia_semana] = []
    horariosPorDia[h.dia_semana].push(h)
  }

  res.render('admin_horarios_confissao.html', { horarios, horarios_por_dia: horariosPorDia })
})

const HorarioSchema = z.object({
  dia_semana: z.enum(['Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado']),
  horario: z.string().regex(/^\d{2}:\d{2}$/, 'Horário inválido (use HH:MM)'),
})

router.post('/horarios-confissao/adicionar', async (req, res) => {
  const result = HorarioSchema.safeParse(req.body)
  if (!result.success) {
    req.flash('error', result.error.issues[0]?.message ?? 'Dados inválidos')
    res.redirect('/admin/horarios-confissao')
    return
  }
  const { dia_semana, horario } = result.data
  await dbQuery`INSERT INTO horarios_confissao (dia_semana, horario) VALUES (${dia_semana}, ${horario})`
  req.flash('success', 'Horário de confissão adicionado com sucesso!')
  res.redirect('/admin/horarios-confissao')
})

router.post('/horarios-confissao/:id/toggle', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  if (isNaN(id)) { res.redirect('/admin/horarios-confissao'); return }
  await dbQuery`UPDATE horarios_confissao SET ativo = NOT ativo WHERE id = ${id}`
  req.flash('success', 'Status atualizado!')
  res.redirect('/admin/horarios-confissao')
})

router.post('/horarios-confissao/:id/deletar', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  if (isNaN(id)) { res.redirect('/admin/horarios-confissao'); return }
  await dbQuery`DELETE FROM horarios_confissao WHERE id = ${id}`
  req.flash('success', 'Horário removido com sucesso!')
  res.redirect('/admin/horarios-confissao')
})

export { DIAS_ORDEM }
export default router
