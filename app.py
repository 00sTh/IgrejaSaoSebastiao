"""
Sistema de Gerenciamento - Igreja São Sebastião
Sistema completo com painel administrativo editável
v2.0 - Com Middleware de Logging e Autenticação Segura
"""
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, g
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import shutil
from config import Config

# Importar middlewares
from middleware.logger import AppLogger, log_request, log_error, log_action
from middleware.auth import (
    AuthManager, login_required, role_required, permission_required,
    Permissions, RateLimiter
)

app = Flask(__name__)
app.config.from_object(Config)
app.config['DATABASE_PATH'] = Config.DATABASE_PATH
app.secret_key = Config.SECRET_KEY

# Inicializar middlewares
AppLogger.setup(app)
AuthManager.setup(app)

# Inicializar CRUD Engine
from core.routes import init_crud_routes
init_crud_routes(app)

# Configurações
UPLOAD_FOLDER = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS

# ==================== FUNÇÕES DE BANCO DE DADOS ====================

def get_db_connection():
    """Cria conexão com o banco de dados"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa o banco de dados com todas as tabelas"""
    conn = get_db_connection()

    # Tabela de notícias e eventos
    conn.execute('''
        CREATE TABLE IF NOT EXISTS noticias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            subtitulo TEXT,
            conteudo TEXT NOT NULL,
            imagem_url TEXT,
            tipo TEXT NOT NULL DEFAULT 'Notícia',
            data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabela de horários de missas
    conn.execute('''
        CREATE TABLE IF NOT EXISTS horarios_missas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dia_semana TEXT NOT NULL,
            horario TEXT NOT NULL,
            tipo TEXT,
            ativo INTEGER DEFAULT 1
        )
    ''')

    # Tabela de informações da paróquia
    conn.execute('''
        CREATE TABLE IF NOT EXISTS paroquia_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            secao TEXT NOT NULL UNIQUE,
            titulo TEXT NOT NULL,
            conteudo TEXT NOT NULL,
            ordem INTEGER DEFAULT 0
        )
    ''')

    # Tabela de galeria de fotos
    conn.execute('''
        CREATE TABLE IF NOT EXISTS galeria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT,
            imagem_url TEXT NOT NULL,
            data_upload TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            ativo INTEGER DEFAULT 1
        )
    ''')

    # Tabela de contatos
    conn.execute('''
        CREATE TABLE IF NOT EXISTS contatos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            valor TEXT NOT NULL,
            icone TEXT,
            ordem INTEGER DEFAULT 0
        )
    ''')

    # Tabela de configurações gerais
    conn.execute('''
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL,
            descricao TEXT
        )
    ''')

    # Inserir dados iniciais se não existirem
    insert_initial_data(conn)

    # Garantir que todas as seções existam (migração)
    ensure_all_sections_exist(conn)

    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado com sucesso!")

def insert_initial_data(conn):
    """Insere dados iniciais nas tabelas"""

    # Verificar se já existem dados
    existing = conn.execute('SELECT COUNT(*) as count FROM configuracoes').fetchone()
    if existing['count'] > 0:
        return

    # Inserir horários de missas padrão
    missas_default = [
        ('Segunda-feira', '07:00', 'Missa'),
        ('Terça-feira', '07:00', 'Missa'),
        ('Quarta-feira', '07:00', 'Missa'),
        ('Quinta-feira', '07:00', 'Missa'),
        ('Sexta-feira', '07:00', 'Missa'),
        ('Sábado', '19:00', 'Missa'),
        ('Domingo', '08:00', 'Missa'),
        ('Domingo', '19:00', 'Missa'),
    ]
    conn.executemany('INSERT INTO horarios_missas (dia_semana, horario, tipo) VALUES (?, ?, ?)', missas_default)

    # Inserir informações da paróquia padrão
    paroquia_default = [
        ('hero_titulo', 'Igreja São Sebastião', 'Título principal do banner'),
        ('hero_subtitulo', 'Onde a Fé Encontra a Comunidade em Ponte Nova', 'Subtítulo do banner'),
        ('hero_botao', 'Ver Horários das Missas', 'Texto do botão do banner'),
        ('sobre_titulo', 'Seja Bem-Vindo à Nossa Comunidade!', 'Título da seção Sobre'),
        ('sobre_texto', 'A Igreja São Sebastião tem sido um farol de fé e esperança para a comunidade de Ponte Nova por décadas. Convidamos você a fazer parte de nossa família, a encontrar consolo na palavra e a fortalecer sua espiritualidade.', 'Texto da seção Sobre'),
        ('horarios_titulo', 'Horários Importantes', 'Título da seção de horários'),
        ('missas_titulo', 'Missas', 'Título do card de missas'),
        ('confissoes_titulo', 'Confissões', 'Título do card de confissões'),
        ('confissoes_horarios', 'Terça a Sexta: 14h às 17h|Sábado: 9h às 12h', 'Horários de confissão (separados por |)'),
        ('secretaria_titulo', 'Secretaria', 'Título do card da secretaria'),
        ('secretaria_horarios', 'Segunda a Sexta: 13h às 18h', 'Horário da secretaria'),
        ('secretaria_telefone', '(31) 3295-1379', 'Telefone da secretaria'),
        ('secretaria_email', 'contato@igrejasst.org', 'Email da secretaria'),
        ('galeria_titulo', 'Nossa Igreja em Imagens', 'Título da seção galeria'),
        ('historia_titulo', 'Nossa História e Legado', 'Título da seção história'),
        ('historia_texto', '<p>Fundada em [Ano de Fundação], a Igreja São Sebastião tem uma rica história de serviço e evangelização. Desde sua construção, este santuário tem sido um ponto de encontro para gerações de fiéis, testemunhando momentos de alegria, consolo e renovação da fé.</p><p>Nossa paróquia cresceu junto com a cidade de Ponte Nova, adaptando-se aos desafios e celebrando as vitórias. Pessoas dedicadas, desde os primeiros padres até os voluntários de hoje, construíram um legado de amor e acolhimento que continua a inspirar.</p>', 'Texto da história'),
        ('historia_marcos_titulo', 'Principais Marcos', 'Título dos marcos históricos'),
        ('historia_marcos', '[Ano]: Fundação da paróquia|[Ano]: Início da construção da atual igreja|[Ano]: Inauguração e primeira missa solene|[Ano]: Lançamento de importantes projetos sociais', 'Marcos históricos (separados por |)'),
        ('localizacao_titulo', 'Onde Nos Encontrar', 'Título da seção localização'),
        ('localizacao_endereco', 'Praça Getúlio Vargas, 92 - Centro Histórico, Pte. Nova - MG, 35430-003', 'Endereço completo'),
        ('localizacao_telefones', '(31) 98888-6796 / (31) 3881-1401', 'Telefones'),
        ('localizacao_email', 'contato@igrejasst.org', 'Email'),
        ('localizacao_mapa', 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3739.1906006479735!2d-42.911577723851245!3d-20.41623625363568!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0xa497026b4d46e1%3A0x5d64af00395326ce!2sIgreja%20Matriz%20de%20S%C3%A3o%20Sebasti%C3%A3o%20-%20Ponte%20Nova!5e0!3m2!1spt-BR!2sbr!4v1757269101938!5m2!1spt-BR!2sbr', 'URL do mapa embed'),
        ('confissao_titulo', 'Agendamento de Confissão com o Padre', 'Título do formulário de confissão'),
        ('confissao_texto', '<p>O Sacramento da Confissão é um momento de graça e reconciliação com Deus e com a Igreja. Para facilitar seu acesso a este momento especial, oferecemos a possibilidade de agendamento online.</p><p><strong>Importante:</strong> Este formulário é para <strong>solicitação de agendamento</strong>. Nossa secretaria entrará em contato para <strong>confirmar</strong> a data e hora, bem como quaisquer detalhes necessários. Sua privacidade e o sigilo sacramental são garantidos.</p>', 'Texto informativo sobre confissão'),
        ('contato_titulo', 'Entre em Contato', 'Título da seção contato'),
        ('contato_subtitulo', 'Estamos Prontos para Ajudar', 'Subtítulo da seção contato'),
        ('contato_texto', 'Tem dúvidas, sugestões ou precisa de mais informações? Fale conosco!', 'Texto da seção contato'),
        ('rodape_texto', 'Igreja São Sebastião. Todos os direitos reservados.', 'Texto do rodapé'),
        ('redes_facebook', '#', 'Link do Facebook'),
        ('redes_instagram', '#', 'Link do Instagram'),
        ('redes_whatsapp', '#', 'Link do WhatsApp'),
    ]
    for i, (secao, titulo, conteudo) in enumerate(paroquia_default):
        conn.execute('INSERT INTO paroquia_info (secao, titulo, conteudo, ordem) VALUES (?, ?, ?, ?)',
                    (secao, titulo, conteudo, i))

    # Inserir contatos padrão
    contatos_default = [
        ('telefone', '(31) 0000-0000', 'fas fa-phone', 1),
        ('email', 'contato@igrejasaosebastiao.com.br', 'fas fa-envelope', 2),
        ('endereco', 'Rua São Sebastião, 123 - Ponte Nova/MG', 'fas fa-map-marker-alt', 3),
    ]
    conn.executemany('INSERT INTO contatos (tipo, valor, icone, ordem) VALUES (?, ?, ?, ?)', contatos_default)

    # Inserir configurações gerais
    config_default = [
        ('site_nome', 'Igreja São Sebastião', 'Nome do site'),
        ('site_descricao', 'Onde a Fé Encontra a Comunidade', 'Descrição do site'),
        ('endereco_completo', 'Rua São Sebastião, 123 - Centro, Ponte Nova/MG', 'Endereço completo'),
        ('mapa_latitude', '-20.4169', 'Latitude para o mapa'),
        ('mapa_longitude', '-42.9089', 'Longitude para o mapa'),
    ]
    conn.executemany('INSERT INTO configuracoes (chave, valor, descricao) VALUES (?, ?, ?)', config_default)

def ensure_all_sections_exist(conn):
    """Garante que todas as seções necessárias existam no banco"""
    required_sections = [
        ('hero_titulo', 'Igreja São Sebastião', 'Título principal do banner'),
        ('hero_subtitulo', 'Onde a Fé Encontra a Comunidade em Ponte Nova', 'Subtítulo do banner'),
        ('hero_botao', 'Ver Horários das Missas', 'Texto do botão do banner'),
        ('sobre_titulo', 'Seja Bem-Vindo à Nossa Comunidade!', 'Título da seção Sobre'),
        ('sobre_texto', 'A Igreja São Sebastião tem sido um farol de fé e esperança para a comunidade de Ponte Nova por décadas.', 'Texto da seção Sobre'),
        ('horarios_titulo', 'Horários Importantes', 'Título da seção de horários'),
        ('missas_titulo', 'Missas', 'Título do card de missas'),
        ('confissoes_titulo', 'Confissões', 'Título do card de confissões'),
        ('confissoes_horarios', 'Terça a Sexta: 14h às 17h|Sábado: 9h às 12h', 'Horários de confissão'),
        ('secretaria_titulo', 'Secretaria', 'Título do card da secretaria'),
        ('secretaria_horarios', 'Segunda a Sexta: 13h às 18h', 'Horário da secretaria'),
        ('secretaria_telefone', '(31) 3295-1379', 'Telefone da secretaria'),
        ('secretaria_email', 'contato@igrejasst.org', 'Email da secretaria'),
        ('galeria_titulo', 'Nossa Igreja em Imagens', 'Título da seção galeria'),
        ('historia_titulo', 'Nossa História e Legado', 'Título da seção história'),
        ('historia_texto', '<p>Fundada em [Ano], a Igreja São Sebastião tem uma rica história.</p>', 'Texto da história'),
        ('historia_marcos_titulo', 'Principais Marcos', 'Título dos marcos históricos'),
        ('historia_marcos', '[Ano]: Fundação da paróquia|[Ano]: Construção da igreja|[Ano]: Inauguração', 'Marcos históricos'),
        ('localizacao_titulo', 'Onde Nos Encontrar', 'Título da seção localização'),
        ('localizacao_endereco', 'Praça Getúlio Vargas, 92 - Centro, Ponte Nova - MG', 'Endereço'),
        ('localizacao_telefones', '(31) 98888-6796 / (31) 3881-1401', 'Telefones'),
        ('localizacao_email', 'contato@igrejasst.org', 'Email'),
        ('localizacao_mapa', 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3739.19!2d-42.91!3d-20.41!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0xa497026b4d46e1%3A0x5d64af00395326ce!2sIgreja%20Matriz%20de%20S%C3%A3o%20Sebasti%C3%A3o!5e0!3m2!1spt-BR!2sbr', 'URL do mapa'),
        ('confissao_titulo', 'Agendamento de Confissão com o Padre', 'Título do formulário'),
        ('confissao_texto', '<p>O Sacramento da Confissão é um momento de graça.</p>', 'Texto informativo'),
        ('contato_titulo', 'Entre em Contato', 'Título da seção contato'),
        ('contato_subtitulo', 'Estamos Prontos para Ajudar', 'Subtítulo'),
        ('contato_texto', 'Tem dúvidas? Fale conosco!', 'Texto'),
        ('rodape_texto', 'Igreja São Sebastião. Todos os direitos reservados.', 'Rodapé'),
        ('redes_facebook', '#', 'Link do Facebook'),
        ('redes_instagram', '#', 'Link do Instagram'),
        ('redes_whatsapp', '#', 'Link do WhatsApp'),
    ]

    for i, (secao, titulo, conteudo) in enumerate(required_sections):
        existing = conn.execute('SELECT id FROM paroquia_info WHERE secao = ?', (secao,)).fetchone()
        if not existing:
            conn.execute('INSERT INTO paroquia_info (secao, titulo, conteudo, ordem) VALUES (?, ?, ?, ?)',
                        (secao, titulo, conteudo, i))
    conn.commit()

# ==================== DECORADORES ====================
# login_required, role_required e permission_required
# são importados do middleware.auth

# ==================== FUNÇÕES AUXILIARES ====================

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, folder='uploads', use_pipeline=True):
    """
    Salva arquivo enviado e retorna o caminho.

    Args:
        file: Arquivo do request
        folder: Pasta destino (ignorado se use_pipeline=True)
        use_pipeline: Se True, usa o MediaPipeline com resize automático

    Returns:
        URL do arquivo salvo (versão medium se pipeline, original caso contrário)
    """
    if not file or not file.filename:
        return None

    if use_pipeline:
        # Usar o novo pipeline de mídia
        try:
            from core.media import process_upload, MediaValidationError
            result = process_upload(file, convert_to_webp=True)
            return result.primary_url  # Retorna URL da versão medium
        except MediaValidationError as e:
            log_error(f"Erro na validação de upload: {e}")
            return None
        except Exception as e:
            log_error(f"Erro no pipeline de mídia", exception=e)
            # Fallback para método antigo
            pass

    # Método antigo (fallback)
    if allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{timestamp}{ext}"

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)
        return url_for('static', filename=f'uploads/{filename}')

    return None

def backup_database():
    """Cria backup do banco de dados"""
    try:
        backup_folder = 'backups'
        os.makedirs(backup_folder, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"{backup_folder}/database_backup_{timestamp}.db"

        shutil.copy2(Config.DATABASE_PATH, backup_file)
        return backup_file
    except Exception as e:
        print(f"Erro ao criar backup: {e}")
        return None

# ==================== ROTAS PÚBLICAS ====================

@app.route('/')
def index():
    """Página inicial"""
    conn = get_db_connection()

    # Buscar notícias e eventos
    noticias = conn.execute(
        'SELECT * FROM noticias ORDER BY data_criacao DESC LIMIT 5'
    ).fetchall()

    # Buscar horários de missas
    horarios = conn.execute(
        'SELECT * FROM horarios_missas WHERE ativo = 1 ORDER BY id'
    ).fetchall()

    # Buscar informações da paróquia
    info_paroquia = {}
    infos = conn.execute('SELECT * FROM paroquia_info ORDER BY ordem').fetchall()
    for info in infos:
        info_paroquia[info['secao']] = {'titulo': info['titulo'], 'conteudo': info['conteudo']}

    # Buscar galeria
    galeria = conn.execute(
        'SELECT * FROM galeria WHERE ativo = 1 ORDER BY data_upload DESC LIMIT 12'
    ).fetchall()

    # Buscar contatos
    contatos = conn.execute(
        'SELECT * FROM contatos ORDER BY ordem'
    ).fetchall()

    # Buscar configurações
    configs = conn.execute('SELECT * FROM configuracoes').fetchall()
    config_dict = {config['chave']: config['valor'] for config in configs}

    conn.close()

    is_admin = session.get('logged_in', False)

    return render_template('index.html',
                         noticias=noticias,
                         horarios=horarios,
                         info_paroquia=info_paroquia,
                         galeria=galeria,
                         contatos=contatos,
                         configs=config_dict,
                         is_admin=is_admin)

# ==================== ROTAS DE AUTENTICAÇÃO ====================

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    """Login do administrador - Com autenticação segura"""
    # Se já está logado, redireciona
    if session.get('logged_in'):
        return redirect(url_for('admin_dashboard'))

    error = None
    remaining_attempts = None

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        ip_address = request.remote_addr

        # Verificar rate limiting
        if RateLimiter.is_blocked(ip_address):
            error = 'Muitas tentativas. Aguarde 15 minutos.'
            log_request("Login bloqueado - rate limit", level='warning', ip=ip_address)
        else:
            # Autenticar com o novo sistema
            success, user, auth_error = AuthManager.authenticate(
                username, password, ip_address
            )

            if success and user:
                AuthManager.create_session(user)
                AuthManager.audit_log('login', 'user', user['id'])
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                error = auth_error or 'Usuário ou senha incorretos.'
                remaining_attempts = RateLimiter.get_remaining_attempts(ip_address)

    return render_template('admin_login.html',
                          error=error,
                          remaining_attempts=remaining_attempts)

@app.route('/logout')
def logout():
    """Logout do administrador"""
    if session.get('user_id'):
        AuthManager.audit_log('logout', 'user', session.get('user_id'))
    AuthManager.logout()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('index'))

# ==================== ROTAS DO PAINEL ADMIN ====================

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Dashboard do administrador"""
    conn = get_db_connection()

    # Estatísticas
    total_noticias = conn.execute('SELECT COUNT(*) as count FROM noticias').fetchone()['count']
    total_galeria = conn.execute('SELECT COUNT(*) as count FROM galeria WHERE ativo = 1').fetchone()['count']
    total_missas = conn.execute('SELECT COUNT(*) as count FROM horarios_missas WHERE ativo = 1').fetchone()['count']

    noticias_recentes = conn.execute(
        'SELECT * FROM noticias ORDER BY data_criacao DESC LIMIT 5'
    ).fetchall()

    conn.close()

    return render_template('admin_dashboard.html',
                         total_noticias=total_noticias,
                         total_galeria=total_galeria,
                         total_missas=total_missas,
                         noticias_recentes=noticias_recentes)

# ==================== ROTAS DE NOTÍCIAS ====================

@app.route('/admin/noticias')
@login_required
def admin_noticias():
    """Lista todas as notícias"""
    conn = get_db_connection()
    noticias = conn.execute('SELECT * FROM noticias ORDER BY data_criacao DESC').fetchall()
    conn.close()
    return render_template('admin_noticias.html', noticias=noticias)

@app.route('/admin/noticias/nova', methods=['GET', 'POST'])
@app.route('/admin/noticias/editar/<int:post_id>', methods=['GET', 'POST'])
@login_required
def admin_noticia_edit(post_id=None):
    """Criar ou editar notícia"""
    conn = get_db_connection()
    noticia = None

    if post_id:
        noticia = conn.execute('SELECT * FROM noticias WHERE id = ?', (post_id,)).fetchone()
        if not noticia:
            conn.close()
            flash('Notícia não encontrada.', 'error')
            return redirect(url_for('admin_noticias'))

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        subtitulo = request.form.get('subtitulo', '').strip()
        conteudo = request.form.get('conteudo', '').strip()
        tipo = request.form.get('tipo', 'Notícia')

        if not titulo or not conteudo:
            conn.close()
            flash('Título e conteúdo são obrigatórios.', 'error')
            return render_template('admin_noticia_edit.html', noticia=noticia)

        # Processar imagem
        imagem_url = noticia['imagem_url'] if noticia else None
        if 'imagem' in request.files and request.files['imagem'].filename:
            imagem_url = save_uploaded_file(request.files['imagem'])

        if post_id:
            conn.execute(
                'UPDATE noticias SET titulo = ?, subtitulo = ?, conteudo = ?, imagem_url = ?, tipo = ? WHERE id = ?',
                (titulo, subtitulo, conteudo, imagem_url, tipo, post_id)
            )
            flash('Notícia atualizada com sucesso!', 'success')
        else:
            conn.execute(
                'INSERT INTO noticias (titulo, subtitulo, conteudo, imagem_url, tipo) VALUES (?, ?, ?, ?, ?)',
                (titulo, subtitulo, conteudo, imagem_url, tipo)
            )
            flash('Notícia criada com sucesso!', 'success')

        conn.commit()
        conn.close()
        return redirect(url_for('admin_noticias'))

    conn.close()
    return render_template('admin_noticia_edit.html', noticia=noticia)

@app.route('/admin/noticias/deletar/<int:post_id>', methods=['POST'])
@login_required
def admin_noticia_delete(post_id):
    """Deletar notícia"""
    conn = get_db_connection()
    conn.execute('DELETE FROM noticias WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    flash('Notícia deletada com sucesso!', 'success')
    return redirect(url_for('admin_noticias'))

# ==================== ROTAS DE HORÁRIOS ====================

@app.route('/admin/horarios')
@login_required
def admin_horarios():
    """Lista horários de missas"""
    conn = get_db_connection()
    horarios = conn.execute('SELECT * FROM horarios_missas ORDER BY id').fetchall()
    conn.close()
    return render_template('admin_horarios.html', horarios=horarios)

@app.route('/admin/horarios/novo', methods=['GET', 'POST'])
@app.route('/admin/horarios/editar/<int:horario_id>', methods=['GET', 'POST'])
@login_required
def admin_horario_edit(horario_id=None):
    """Criar ou editar horário de missa"""
    conn = get_db_connection()
    horario = None

    if horario_id:
        horario = conn.execute('SELECT * FROM horarios_missas WHERE id = ?', (horario_id,)).fetchone()

    if request.method == 'POST':
        dia_semana = request.form.get('dia_semana', '').strip()
        horario_time = request.form.get('horario', '').strip()
        tipo = request.form.get('tipo', 'Missa').strip()
        ativo = 1 if request.form.get('ativo') == 'on' else 0

        if not dia_semana or not horario_time:
            conn.close()
            flash('Dia da semana e horário são obrigatórios.', 'error')
            return render_template('admin_horario_edit.html', horario=horario)

        if horario_id:
            conn.execute(
                'UPDATE horarios_missas SET dia_semana = ?, horario = ?, tipo = ?, ativo = ? WHERE id = ?',
                (dia_semana, horario_time, tipo, ativo, horario_id)
            )
            flash('Horário atualizado com sucesso!', 'success')
        else:
            conn.execute(
                'INSERT INTO horarios_missas (dia_semana, horario, tipo, ativo) VALUES (?, ?, ?, ?)',
                (dia_semana, horario_time, tipo, ativo)
            )
            flash('Horário criado com sucesso!', 'success')

        conn.commit()
        conn.close()
        return redirect(url_for('admin_horarios'))

    conn.close()
    return render_template('admin_horario_edit.html', horario=horario)

@app.route('/admin/horarios/deletar/<int:horario_id>', methods=['POST'])
@login_required
def admin_horario_delete(horario_id):
    """Deletar horário"""
    conn = get_db_connection()
    conn.execute('DELETE FROM horarios_missas WHERE id = ?', (horario_id,))
    conn.commit()
    conn.close()
    flash('Horário deletado com sucesso!', 'success')
    return redirect(url_for('admin_horarios'))

# ==================== ROTAS DE INFORMAÇÕES ====================

@app.route('/admin/informacoes')
@login_required
def admin_informacoes():
    """Lista informações da paróquia"""
    conn = get_db_connection()
    informacoes = conn.execute('SELECT * FROM paroquia_info ORDER BY ordem').fetchall()
    conn.close()
    return render_template('admin_informacoes.html', informacoes=informacoes)

@app.route('/admin/informacoes/editar/<int:info_id>', methods=['GET', 'POST'])
@login_required
def admin_informacao_edit(info_id):
    """Editar informação da paróquia"""
    conn = get_db_connection()
    informacao = conn.execute('SELECT * FROM paroquia_info WHERE id = ?', (info_id,)).fetchone()

    if not informacao:
        conn.close()
        flash('Informação não encontrada.', 'error')
        return redirect(url_for('admin_informacoes'))

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        conteudo = request.form.get('conteudo', '').strip()

        if not titulo or not conteudo:
            conn.close()
            flash('Título e conteúdo são obrigatórios.', 'error')
            return render_template('admin_informacao_edit.html', informacao=informacao)

        conn.execute(
            'UPDATE paroquia_info SET titulo = ?, conteudo = ? WHERE id = ?',
            (titulo, conteudo, info_id)
        )
        conn.commit()
        conn.close()
        flash('Informação atualizada com sucesso!', 'success')
        return redirect(url_for('admin_informacoes'))

    conn.close()
    return render_template('admin_informacao_edit.html', informacao=informacao)

# ==================== ROTAS DE GALERIA ====================

@app.route('/admin/galeria')
@login_required
def admin_galeria():
    """Lista fotos da galeria"""
    conn = get_db_connection()
    galeria = conn.execute('SELECT * FROM galeria ORDER BY data_upload DESC').fetchall()
    conn.close()
    return render_template('admin_galeria.html', galeria=galeria)

@app.route('/admin/galeria/nova', methods=['GET', 'POST'])
@login_required
def admin_galeria_nova():
    """Adicionar foto à galeria"""
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descricao = request.form.get('descricao', '').strip()

        if not titulo:
            flash('Título é obrigatório.', 'error')
            return render_template('admin_galeria_edit.html')

        if 'imagem' not in request.files or not request.files['imagem'].filename:
            flash('Imagem é obrigatória.', 'error')
            return render_template('admin_galeria_edit.html')

        imagem_url = save_uploaded_file(request.files['imagem'])
        if not imagem_url:
            flash('Erro ao fazer upload da imagem.', 'error')
            return render_template('admin_galeria_edit.html')

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO galeria (titulo, descricao, imagem_url) VALUES (?, ?, ?)',
            (titulo, descricao, imagem_url)
        )
        conn.commit()
        conn.close()
        flash('Foto adicionada com sucesso!', 'success')
        return redirect(url_for('admin_galeria'))

    return render_template('admin_galeria_edit.html')

@app.route('/admin/galeria/deletar/<int:foto_id>', methods=['POST'])
@login_required
def admin_galeria_delete(foto_id):
    """Deletar foto da galeria"""
    conn = get_db_connection()
    conn.execute('DELETE FROM galeria WHERE id = ?', (foto_id,))
    conn.commit()
    conn.close()
    flash('Foto deletada com sucesso!', 'success')
    return redirect(url_for('admin_galeria'))

# ==================== ROTAS DE CONFIGURAÇÕES ====================

@app.route('/admin/configuracoes', methods=['GET', 'POST'])
@login_required
def admin_configuracoes():
    """Editar configurações gerais"""
    conn = get_db_connection()

    if request.method == 'POST':
        # Atualizar cada configuração
        for key in request.form:
            valor = request.form.get(key, '').strip()
            conn.execute(
                'UPDATE configuracoes SET valor = ? WHERE chave = ?',
                (valor, key)
            )

        conn.commit()
        flash('Configurações atualizadas com sucesso!', 'success')

    configuracoes = conn.execute('SELECT * FROM configuracoes').fetchall()
    contatos = conn.execute('SELECT * FROM contatos ORDER BY ordem').fetchall()
    conn.close()

    return render_template('admin_configuracoes.html',
                         configuracoes=configuracoes,
                         contatos=contatos)

@app.route('/admin/contatos/editar/<int:contato_id>', methods=['GET', 'POST'])
@login_required
def admin_contato_edit(contato_id):
    """Editar contato"""
    conn = get_db_connection()
    contato = conn.execute('SELECT * FROM contatos WHERE id = ?', (contato_id,)).fetchone()

    if not contato:
        conn.close()
        flash('Contato não encontrado.', 'error')
        return redirect(url_for('admin_configuracoes'))

    if request.method == 'POST':
        tipo = request.form.get('tipo', '').strip()
        valor = request.form.get('valor', '').strip()
        icone = request.form.get('icone', '').strip()

        conn.execute(
            'UPDATE contatos SET tipo = ?, valor = ?, icone = ? WHERE id = ?',
            (tipo, valor, icone, contato_id)
        )
        conn.commit()
        conn.close()
        flash('Contato atualizado com sucesso!', 'success')
        return redirect(url_for('admin_configuracoes'))

    conn.close()
    return render_template('admin_contato_edit.html', contato=contato)

# ==================== ROTAS DE BACKUP ====================

@app.route('/admin/backup', methods=['POST'])
@login_required
def admin_backup():
    """Criar backup do banco de dados"""
    backup_file = backup_database()
    if backup_file:
        flash(f'Backup criado com sucesso: {backup_file}', 'success')
    else:
        flash('Erro ao criar backup.', 'error')
    return redirect(url_for('admin_dashboard'))

# ==================== API ROUTES ====================

@app.route('/api/update_content', methods=['POST'])
@login_required
@permission_required(Permissions.NOTICIAS_UPDATE)
def api_update_content():
    """API para atualização de conteúdo inline - SEGURA"""
    data = request.get_json()

    if not data:
        return jsonify({'status': 'error', 'message': 'Dados inválidos'}), 400

    post_id = data.get('id')
    field = data.get('field')
    new_value = data.get('value')

    if not all([post_id, field, new_value is not None]):
        return jsonify({'status': 'error', 'message': 'Dados incompletos'}), 400

    # WHITELIST de campos permitidos (previne SQL injection)
    ALLOWED_FIELDS = {
        'titulo': 'titulo',
        'conteudo': 'conteudo',
        'subtitulo': 'subtitulo'
    }

    if field not in ALLOWED_FIELDS:
        log_request("Tentativa de atualizar campo inválido", level='warning', field=field)
        return jsonify({'status': 'error', 'message': 'Campo inválido'}), 400

    # Validar que post_id é inteiro
    try:
        post_id = int(post_id)
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'ID inválido'}), 400

    try:
        conn = get_db_connection()

        # Buscar valor antigo para auditoria
        old_record = conn.execute(
            'SELECT * FROM noticias WHERE id = ?', (post_id,)
        ).fetchone()

        if not old_record:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Registro não encontrado'}), 404

        old_value = old_record[field]

        # Query segura usando o nome da coluna do whitelist
        safe_field = ALLOWED_FIELDS[field]
        conn.execute(
            f'UPDATE noticias SET {safe_field} = ? WHERE id = ?',
            (new_value, post_id)
        )
        conn.commit()
        conn.close()

        # Registrar auditoria
        AuthManager.audit_log(
            action='update_inline',
            entity_type='noticias',
            entity_id=post_id,
            old_value={field: old_value},
            new_value={field: new_value}
        )

        log_request(f"Conteúdo atualizado via API", noticia_id=post_id, field=field)
        return jsonify({'status': 'success', 'message': f'Campo {field} atualizado'})

    except Exception as e:
        log_error("Erro ao atualizar conteúdo via API", exception=e, post_id=post_id)
        # NÃO expor detalhes do erro ao cliente
        return jsonify({
            'status': 'error',
            'message': 'Erro interno. Tente novamente.',
            'request_id': getattr(g, 'request_id', 'unknown')
        }), 500

# ==================== INICIALIZAÇÃO ====================

if __name__ == '__main__':
    # Criar pasta de uploads
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Inicializar banco de dados
    init_db()

    # Executar aplicação
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
