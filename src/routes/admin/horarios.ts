import { Router } from 'express'
import type { Request, Response } from 'express'
import { sql, dbQuery } from '../../db'
import type { HorarioMissa } from '../../types/index'

const router = Router()

router.get('/', async (_req, res) => {
  const horarios = await dbQuery<HorarioMissa>`SELECT * FROM horarios_missas ORDER BY id`
  res.render('admin_horarios.html', { horarios })
})

router.get('/novo', (_req, res) => {
  res.render('admin_horario_edit.html', { horario: null })
})

router.get('/editar/:id', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  const rows = await dbQuery<HorarioMissa>`SELECT * FROM horarios_missas WHERE id = ${id}`
  res.render('admin_horario_edit.html', { horario: rows[0] ?? null })
})

async function saveHorario(req: Request, res: Response, id: number | null): Promise<void> {
  const body = req.body as Record<string, string>
  const dia_semana = (body.dia_semana ?? '').trim()
  const horario = (body.horario ?? '').trim()
  const tipo = (body.tipo ?? 'Missa').trim()
  const nome = (body.nome ?? '').trim()
  const ativo = body.ativo === 'on'

  if (!dia_semana || !horario) {
    req.flash('error', 'Dia da semana e horário são obrigatórios.')
    res.redirect(id ? `/admin/horarios/editar/${id}` : '/admin/horarios/novo')
    return
  }

  if (id) {
    await sql`UPDATE horarios_missas SET dia_semana = ${dia_semana}, horario = ${horario}, tipo = ${tipo}, nome = ${nome || null}, ativo = ${ativo} WHERE id = ${id}`
    req.flash('success', 'Horário atualizado com sucesso!')
  } else {
    await sql`INSERT INTO horarios_missas (dia_semana, horario, tipo, nome, ativo) VALUES (${dia_semana}, ${horario}, ${tipo}, ${nome || null}, ${ativo})`
    req.flash('success', 'Horário criado com sucesso!')
  }
  res.redirect('/admin/horarios')
}

router.post('/novo', async (req, res) => { await saveHorario(req, res, null) })
router.post('/editar/:id', async (req, res) => { await saveHorario(req, res, parseInt(req.params.id, 10)) })

router.post('/deletar/:id', async (req, res) => {
  const id = parseInt(req.params.id, 10)
  await sql`DELETE FROM horarios_missas WHERE id = ${id}`
  req.flash('success', 'Horário deletado com sucesso!')
  res.redirect('/admin/horarios')
})

export default router
