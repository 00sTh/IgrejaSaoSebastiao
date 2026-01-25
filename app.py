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
            categoria TEXT,
            imagem_url TEXT NOT NULL,
            data_upload TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            ativo INTEGER DEFAULT 1
        )
    ''')

    # Migração: adicionar coluna categoria se não existir
    try:
        conn.execute('ALTER TABLE galeria ADD COLUMN categoria TEXT')
    except:
        pass  # Coluna já existe

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

    # Tabela de horários disponíveis para confissão
    conn.execute('''
        CREATE TABLE IF NOT EXISTS horarios_confissao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dia_semana TEXT NOT NULL,
            horario TEXT NOT NULL,
            ativo INTEGER DEFAULT 1
        )
    ''')

    # Tabela de agendamentos de confissão
    conn.execute('''
        CREATE TABLE IF NOT EXISTS agendamentos_confissao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            telefone TEXT NOT NULL,
            mes INTEGER NOT NULL,
            dia INTEGER NOT NULL,
            horario TEXT NOT NULL,
            observacoes TEXT,
            status TEXT DEFAULT 'pendente',
            data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabela de mensagens de contato
    conn.execute('''
        CREATE TABLE IF NOT EXISTS mensagens_contato (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            mensagem TEXT NOT NULL,
            lida INTEGER DEFAULT 0,
            data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
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

    # Inserir horários de confissão padrão
    confissao_default = [
        ('Terça-feira', '14:00'),
        ('Terça-feira', '15:00'),
        ('Terça-feira', '16:00'),
        ('Quarta-feira', '14:00'),
        ('Quarta-feira', '15:00'),
        ('Quarta-feira', '16:00'),
        ('Quinta-feira', '14:00'),
        ('Quinta-feira', '15:00'),
        ('Quinta-feira', '16:00'),
        ('Sexta-feira', '14:00'),
        ('Sexta-feira', '15:00'),
        ('Sexta-feira', '16:00'),
        ('Sábado', '09:00'),
        ('Sábado', '10:00'),
        ('Sábado', '11:00'),
    ]
    conn.executemany('INSERT INTO horarios_confissao (dia_semana, horario) VALUES (?, ?)', confissao_default)

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
    total_galeria = conn.execute('SELECT COUNT(*) as count FROM galeria').fetchone()['count']
    total_missas = conn.execute('SELECT COUNT(*) as count FROM horarios_missas WHERE ativo = 1').fetchone()['count']

    # Tentar buscar total_informacoes (pode não existir a tabela)
    try:
        total_informacoes = conn.execute('SELECT COUNT(*) as count FROM informacoes').fetchone()['count']
    except:
        total_informacoes = 0

    # Agendamentos pendentes
    try:
        agendamentos_pendentes = conn.execute(
            "SELECT COUNT(*) as count FROM agendamentos_confissao WHERE status = 'pendente'"
        ).fetchone()['count']
    except:
        agendamentos_pendentes = 0

    # Mensagens não lidas
    try:
        mensagens_nao_lidas = conn.execute(
            "SELECT COUNT(*) as count FROM mensagens_contato WHERE lida = 0"
        ).fetchone()['count']
    except:
        mensagens_nao_lidas = 0

    noticias_recentes = conn.execute(
        'SELECT * FROM noticias ORDER BY data_criacao DESC LIMIT 5'
    ).fetchall()

    conn.close()

    return render_template('admin_dashboard.html',
                         total_noticias=total_noticias,
                         total_fotos=total_galeria,
                         total_horarios=total_missas,
                         total_informacoes=total_informacoes,
                         agendamentos_pendentes=agendamentos_pendentes,
                         mensagens_nao_lidas=mensagens_nao_lidas,
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

@app.route('/admin/galeria/editar/<int:foto_id>', methods=['GET', 'POST'])
@app.route('/admin/galeria/editar', defaults={'foto_id': None}, methods=['GET', 'POST'])
@login_required
def admin_galeria_edit(foto_id=None):
    """Editar ou adicionar foto à galeria"""
    conn = get_db_connection()
    foto = None

    if foto_id:
        foto = conn.execute('SELECT * FROM galeria WHERE id = ?', (foto_id,)).fetchone()
        if not foto:
            conn.close()
            flash('Foto não encontrada.', 'error')
            return redirect(url_for('admin_galeria'))

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descricao = request.form.get('descricao', '').strip()
        categoria = request.form.get('categoria', '').strip()

        if not titulo:
            flash('Título é obrigatório.', 'error')
            return render_template('admin_galeria_edit.html', foto=foto)

        imagem_url = None
        if 'imagem' in request.files and request.files['imagem'].filename:
            imagem_url = save_uploaded_file(request.files['imagem'])
            if not imagem_url:
                flash('Erro ao fazer upload da imagem.', 'error')
                return render_template('admin_galeria_edit.html', foto=foto)
        elif not foto:
            flash('Imagem é obrigatória para nova foto.', 'error')
            return render_template('admin_galeria_edit.html', foto=foto)

        if foto:
            # Atualizar foto existente
            if imagem_url:
                conn.execute(
                    'UPDATE galeria SET titulo = ?, descricao = ?, categoria = ?, imagem_url = ? WHERE id = ?',
                    (titulo, descricao, categoria, imagem_url, foto_id)
                )
            else:
                conn.execute(
                    'UPDATE galeria SET titulo = ?, descricao = ?, categoria = ? WHERE id = ?',
                    (titulo, descricao, categoria, foto_id)
                )
            flash('Foto atualizada com sucesso!', 'success')
        else:
            # Nova foto
            conn.execute(
                'INSERT INTO galeria (titulo, descricao, categoria, imagem_url) VALUES (?, ?, ?, ?)',
                (titulo, descricao, categoria, imagem_url)
            )
            flash('Foto adicionada com sucesso!', 'success')

        conn.commit()
        conn.close()
        return redirect(url_for('admin_galeria'))

    conn.close()
    return render_template('admin_galeria_edit.html', foto=foto)


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


# ==================== ROTAS DE IMAGENS DO SITE ====================

@app.route('/admin/imagens-site')
@login_required
def admin_imagens_site():
    """Gerenciar imagens do site"""
    import time
    # Verificar se a imagem de confissão existe
    confession_bg_exists = os.path.exists(
        os.path.join(app.root_path, 'static', 'img', 'confession-background.jpg')
    )
    return render_template('admin_imagens_site.html',
                          confession_bg_exists=confession_bg_exists,
                          cache_bust=int(time.time()))


@app.route('/admin/imagens-site/upload', methods=['POST'])
@login_required
def admin_imagem_upload():
    """Upload de imagem do site"""
    if 'imagem' not in request.files:
        flash('Nenhuma imagem selecionada.', 'error')
        return redirect(url_for('admin_imagens_site'))

    file = request.files['imagem']
    imagem_nome = request.form.get('imagem_nome', '')

    if file.filename == '':
        flash('Nenhuma imagem selecionada.', 'error')
        return redirect(url_for('admin_imagens_site'))

    if not imagem_nome:
        flash('Tipo de imagem não especificado.', 'error')
        return redirect(url_for('admin_imagens_site'))

    # Validar extensão
    allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
    file_ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if file_ext not in allowed_extensions:
        flash('Formato de arquivo não suportado. Use PNG, JPG ou WEBP.', 'error')
        return redirect(url_for('admin_imagens_site'))

    try:
        # Determinar o nome final do arquivo mantendo a extensão original do destino
        dest_ext = imagem_nome.rsplit('.', 1)[-1].lower()
        dest_name = imagem_nome.rsplit('.', 1)[0]

        # Se a extensão do upload for diferente, converter para a extensão destino
        img_path = os.path.join(app.root_path, 'static', 'img', imagem_nome)

        # Salvar arquivo
        from PIL import Image
        img = Image.open(file.stream)

        # Converter para RGB se necessário (para salvar como JPG)
        if dest_ext in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Salvar com qualidade apropriada
        if dest_ext in ['jpg', 'jpeg']:
            img.save(img_path, 'JPEG', quality=90)
        elif dest_ext == 'png':
            img.save(img_path, 'PNG')
        elif dest_ext == 'webp':
            img.save(img_path, 'WEBP', quality=90)
        else:
            img.save(img_path)

        flash('Imagem atualizada com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao salvar imagem: {str(e)}', 'error')

    return redirect(url_for('admin_imagens_site'))


# ==================== ROTAS DE CONTEÚDO DO SITE (EDITOR AMIGÁVEL) ====================

@app.route('/admin/conteudo-site')
@login_required
def admin_conteudo_site():
    """Editor amigável de conteúdo do site"""
    conn = get_db_connection()

    # Carregar dados da tabela paroquia_info
    paroquia_info = conn.execute('SELECT secao, titulo FROM paroquia_info').fetchall()
    conn.close()

    # Converter para dicionário: secao -> titulo (valor)
    dados = {row['secao']: row['titulo'] for row in paroquia_info}

    return render_template('admin_conteudo_site.html', dados=dados)


@app.route('/admin/conteudo-site/salvar', methods=['POST'])
@login_required
def admin_conteudo_site_save():
    """Salvar alterações do conteúdo do site"""
    conn = get_db_connection()

    # Lista de campos que podem ser atualizados (correspondem à coluna 'secao')
    campos_permitidos = [
        'hero_titulo', 'hero_subtitulo', 'hero_botao',
        'sobre_titulo', 'sobre_texto',
        'horarios_titulo', 'missas_titulo', 'confissoes_titulo', 'confissoes_horarios',
        'secretaria_titulo', 'secretaria_horarios', 'secretaria_telefone', 'secretaria_email',
        'galeria_titulo',
        'historia_titulo', 'historia_texto', 'historia_marcos_titulo', 'historia_marcos',
        'localizacao_titulo', 'localizacao_endereco', 'localizacao_telefones',
        'localizacao_email', 'localizacao_mapa',
        'confissao_titulo', 'confissao_texto',
        'contato_titulo', 'contato_subtitulo', 'contato_texto',
        'rodape_texto', 'redes_facebook', 'redes_instagram', 'redes_whatsapp'
    ]

    for campo in campos_permitidos:
        valor = request.form.get(campo, '').strip()
        # Atualiza o campo na tabela paroquia_info (coluna 'titulo' contém o valor)
        conn.execute('UPDATE paroquia_info SET titulo = ? WHERE secao = ?', (valor, campo))

    conn.commit()
    conn.close()

    flash('Conteúdo do site atualizado com sucesso!', 'success')
    return redirect(url_for('admin_conteudo_site'))


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

# ==================== ROTAS DE FORMULÁRIOS PÚBLICOS ====================

import re
import socket

def validar_email(email):
    """
    Valida email de forma eficaz:
    1. Verifica formato com regex
    2. Verifica se o domínio existe (DNS)
    3. Bloqueia domínios temporários conhecidos
    """
    if not email or len(email) > 254:
        return False

    # Formato básico
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False

    # Extrair domínio
    dominio = email.split('@')[1].lower()

    # Lista de domínios temporários/descartáveis (bloquear)
    dominios_bloqueados = [
        'tempmail.com', 'throwaway.email', 'guerrillamail.com',
        'mailinator.com', '10minutemail.com', 'yopmail.com',
        'temp-mail.org', 'fakeinbox.com', 'trashmail.com',
        'tempail.com', 'mohmal.com', 'getnada.com'
    ]

    if dominio in dominios_bloqueados:
        return False

    # Verificar se o domínio existe (DNS)
    try:
        socket.gethostbyname(dominio)
        return True
    except socket.gaierror:
        # Domínio não existe
        return False

def validar_telefone(telefone):
    """
    Valida telefone brasileiro de forma eficaz:
    1. Verifica quantidade de dígitos (10-11)
    2. Verifica DDD válido (11-99)
    3. Verifica formato de celular (9 na frente) ou fixo
    """
    if not telefone:
        return False

    # Remove tudo que não é número
    numeros = re.sub(r'\D', '', telefone)

    # Deve ter 10 (fixo) ou 11 (celular) dígitos
    if len(numeros) < 10 or len(numeros) > 11:
        return False

    # DDDs válidos do Brasil (11-99, exceto alguns inválidos)
    ddd = int(numeros[:2])
    ddds_validos = [
        11, 12, 13, 14, 15, 16, 17, 18, 19,  # SP
        21, 22, 24,                           # RJ
        27, 28,                               # ES
        31, 32, 33, 34, 35, 37, 38,          # MG
        41, 42, 43, 44, 45, 46,              # PR
        47, 48, 49,                           # SC
        51, 53, 54, 55,                       # RS
        61,                                   # DF
        62, 64,                               # GO
        63,                                   # TO
        65, 66,                               # MT
        67,                                   # MS
        68,                                   # AC
        69,                                   # RO
        71, 73, 74, 75, 77,                  # BA
        79,                                   # SE
        81, 82, 83, 84, 85, 86, 87, 88, 89, # NE
        91, 92, 93, 94, 95, 96, 97, 98, 99  # Norte
    ]

    if ddd not in ddds_validos:
        return False

    # Se tem 11 dígitos, é celular e deve começar com 9
    if len(numeros) == 11:
        if numeros[2] != '9':
            return False

    # Se tem 10 dígitos, é fixo e NÃO deve começar com 9
    if len(numeros) == 10:
        if numeros[2] == '9':
            return False

    return True

def validar_nome_completo(nome):
    """Valida nome completo (pelo menos 2 palavras)"""
    partes = nome.strip().split()
    return len(partes) >= 2 and all(len(p) >= 2 for p in partes)


@app.route('/api/horarios-disponiveis', methods=['GET'])
def api_horarios_disponiveis():
    """Retorna horários disponíveis para uma data específica"""
    mes = request.args.get('mes', type=int)
    dia = request.args.get('dia', type=int)

    if not mes or not dia:
        return jsonify({'status': 'error', 'message': 'Mês e dia são obrigatórios'}), 400

    # Determinar dia da semana
    from datetime import date
    ano = date.today().year
    # Se o mês já passou, usa o próximo ano
    if mes < date.today().month or (mes == date.today().month and dia < date.today().day):
        ano += 1

    try:
        data_selecionada = date(ano, mes, dia)
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Data inválida'}), 400

    dias_semana = ['Segunda-feira', 'Terça-feira', 'Quarta-feira',
                   'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
    dia_semana = dias_semana[data_selecionada.weekday()]

    conn = get_db_connection()

    # Buscar horários disponíveis para este dia da semana
    horarios = conn.execute('''
        SELECT horario FROM horarios_confissao
        WHERE dia_semana = ? AND ativo = 1
        ORDER BY horario
    ''', (dia_semana,)).fetchall()

    # Buscar horários já agendados para esta data (que não foram cancelados)
    agendados = conn.execute('''
        SELECT horario FROM agendamentos_confissao
        WHERE mes = ? AND dia = ? AND status != 'cancelado'
    ''', (mes, dia)).fetchall()

    conn.close()

    horarios_ocupados = {a['horario'] for a in agendados}
    horarios_disponiveis = [
        h['horario'] for h in horarios
        if h['horario'] not in horarios_ocupados
    ]

    return jsonify({
        'status': 'success',
        'dia_semana': dia_semana,
        'horarios': horarios_disponiveis
    })


@app.route('/api/agendar-confissao', methods=['POST'])
def api_agendar_confissao():
    """API para agendamento de confissão com validações"""
    try:
        data = request.get_json() if request.is_json else request.form

        nome = data.get('nome', '').strip()
        email = data.get('email', '').strip()
        telefone = data.get('telefone', '').strip()
        mes = data.get('mes', '')
        dia = data.get('dia', '')
        horario = data.get('horario', '').strip()
        observacoes = data.get('observacoes', '').strip()

        # Validações de campos obrigatórios
        if not all([nome, email, telefone, mes, dia, horario]):
            return jsonify({
                'status': 'error',
                'message': 'Por favor, preencha todos os campos obrigatórios.'
            }), 400

        # Validar nome completo
        if not validar_nome_completo(nome):
            return jsonify({
                'status': 'error',
                'message': 'Por favor, informe seu nome completo (nome e sobrenome).'
            }), 400

        # Validar email
        if not validar_email(email):
            return jsonify({
                'status': 'error',
                'message': 'Por favor, informe um email válido.'
            }), 400

        # Validar telefone
        if not validar_telefone(telefone):
            return jsonify({
                'status': 'error',
                'message': 'Por favor, informe um telefone válido com DDD.'
            }), 400

        # Converter mes e dia para int
        try:
            mes = int(mes)
            dia = int(dia)
        except (ValueError, TypeError):
            return jsonify({
                'status': 'error',
                'message': 'Data inválida.'
            }), 400

        # Verificar se horário ainda está disponível
        conn = get_db_connection()
        existe = conn.execute('''
            SELECT id FROM agendamentos_confissao
            WHERE mes = ? AND dia = ? AND horario = ? AND status != 'cancelado'
        ''', (mes, dia, horario)).fetchone()

        if existe:
            conn.close()
            return jsonify({
                'status': 'error',
                'message': 'Este horário já foi reservado. Por favor, escolha outro.'
            }), 400

        # Salvar agendamento
        conn.execute('''
            INSERT INTO agendamentos_confissao
            (nome, email, telefone, mes, dia, horario, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (nome, email, telefone, mes, dia, horario, observacoes))
        conn.commit()
        conn.close()

        log_request("Novo agendamento de confissão", nome=nome, mes=mes, dia=dia, horario=horario)

        return jsonify({
            'status': 'success',
            'message': f'Agendamento confirmado para dia {dia}/{mes:02d} às {horario}. Entraremos em contato se necessário.'
        })

    except Exception as e:
        log_error("Erro ao agendar confissão", exception=e)
        return jsonify({
            'status': 'error',
            'message': 'Erro ao processar solicitação. Tente novamente.'
        }), 500


@app.route('/api/enviar-mensagem', methods=['POST'])
def api_enviar_mensagem():
    """API para envio de mensagem de contato"""
    try:
        data = request.get_json() if request.is_json else request.form

        nome = data.get('nome', '').strip()
        email = data.get('email', '').strip()
        mensagem = data.get('mensagem', '').strip()

        # Validações
        if not all([nome, email, mensagem]):
            return jsonify({
                'status': 'error',
                'message': 'Por favor, preencha todos os campos.'
            }), 400

        # Validar email
        if not validar_email(email):
            return jsonify({
                'status': 'error',
                'message': 'Por favor, informe um email válido.'
            }), 400

        # Validar tamanho mínimo do nome
        if len(nome) < 3:
            return jsonify({
                'status': 'error',
                'message': 'Por favor, informe seu nome completo.'
            }), 400

        # Validar tamanho mínimo da mensagem
        if len(mensagem) < 10:
            return jsonify({
                'status': 'error',
                'message': 'A mensagem deve ter pelo menos 10 caracteres.'
            }), 400

        # Salvar no banco
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO mensagens_contato (nome, email, mensagem)
            VALUES (?, ?, ?)
        ''', (nome, email, mensagem))
        conn.commit()
        conn.close()

        log_request("Nova mensagem de contato", nome=nome)

        return jsonify({
            'status': 'success',
            'message': 'Mensagem enviada com sucesso! Responderemos em breve.'
        })

    except Exception as e:
        log_error("Erro ao enviar mensagem", exception=e)
        return jsonify({
            'status': 'error',
            'message': 'Erro ao enviar mensagem. Tente novamente.'
        }), 500


# ==================== ROTAS ADMIN PARA AGENDAMENTOS E MENSAGENS ====================

@app.route('/admin/agendamentos')
@login_required
def admin_agendamentos():
    """Lista agendamentos de confissão"""
    conn = get_db_connection()
    agendamentos = conn.execute('''
        SELECT * FROM agendamentos_confissao
        ORDER BY data_criacao DESC
    ''').fetchall()
    conn.close()
    return render_template('admin_agendamentos.html', agendamentos=agendamentos)


@app.route('/admin/agendamentos/<int:agendamento_id>/status', methods=['POST'])
@login_required
def admin_agendamento_status(agendamento_id):
    """Atualizar status de agendamento"""
    novo_status = request.form.get('status', 'pendente')
    conn = get_db_connection()
    conn.execute('UPDATE agendamentos_confissao SET status = ? WHERE id = ?',
                (novo_status, agendamento_id))
    conn.commit()
    conn.close()
    flash(f'Status atualizado para: {novo_status}', 'success')
    return redirect(url_for('admin_agendamentos'))


@app.route('/admin/agendamentos/<int:agendamento_id>/editar', methods=['POST'])
@login_required
def admin_agendamento_edit(agendamento_id):
    """Editar agendamento de confissão"""
    nome = request.form.get('nome')
    email = request.form.get('email')
    telefone = request.form.get('telefone')
    mes = request.form.get('mes')
    dia = request.form.get('dia')
    horario = request.form.get('horario')
    observacoes = request.form.get('observacoes', '')

    if not all([nome, email, telefone, mes, dia, horario]):
        flash('Preencha todos os campos obrigatórios.', 'error')
        return redirect(url_for('admin_agendamentos'))

    conn = get_db_connection()
    conn.execute('''
        UPDATE agendamentos_confissao
        SET nome = ?, email = ?, telefone = ?, mes = ?, dia = ?, horario = ?, observacoes = ?
        WHERE id = ?
    ''', (nome, email, telefone, mes, dia, horario, observacoes, agendamento_id))
    conn.commit()
    conn.close()

    flash('Agendamento atualizado com sucesso.', 'success')
    return redirect(url_for('admin_agendamentos'))


@app.route('/admin/agendamentos/<int:agendamento_id>/deletar', methods=['POST'])
@login_required
def admin_agendamento_delete(agendamento_id):
    """Deletar agendamento"""
    conn = get_db_connection()
    conn.execute('DELETE FROM agendamentos_confissao WHERE id = ?', (agendamento_id,))
    conn.commit()
    conn.close()
    flash('Agendamento deletado.', 'success')
    return redirect(url_for('admin_agendamentos'))


# ==================== ROTAS ADMIN PARA HORÁRIOS DE CONFISSÃO ====================

@app.route('/admin/horarios-confissao')
@login_required
def admin_horarios_confissao():
    """Gerenciar horários disponíveis para confissão"""
    conn = get_db_connection()
    horarios = conn.execute('''
        SELECT * FROM horarios_confissao
        ORDER BY
            CASE dia_semana
                WHEN 'Domingo' THEN 1
                WHEN 'Segunda-feira' THEN 2
                WHEN 'Terça-feira' THEN 3
                WHEN 'Quarta-feira' THEN 4
                WHEN 'Quinta-feira' THEN 5
                WHEN 'Sexta-feira' THEN 6
                WHEN 'Sábado' THEN 7
            END,
            horario
    ''').fetchall()
    conn.close()

    # Organizar por dia da semana
    horarios_por_dia = {}
    for h in horarios:
        dia = h['dia_semana']
        if dia not in horarios_por_dia:
            horarios_por_dia[dia] = []
        horarios_por_dia[dia].append(h)

    return render_template('admin_horarios_confissao.html',
                          horarios=horarios,
                          horarios_por_dia=horarios_por_dia)


@app.route('/admin/horarios-confissao/adicionar', methods=['POST'])
@login_required
def admin_horario_confissao_add():
    """Adicionar novo horário de confissão"""
    dia_semana = request.form.get('dia_semana')
    horario = request.form.get('horario')

    if not dia_semana or not horario:
        flash('Preencha todos os campos.', 'error')
        return redirect(url_for('admin_horarios_confissao'))

    conn = get_db_connection()

    # Verificar se já existe
    existe = conn.execute('''
        SELECT id FROM horarios_confissao
        WHERE dia_semana = ? AND horario = ?
    ''', (dia_semana, horario)).fetchone()

    if existe:
        flash('Este horário já está cadastrado.', 'error')
    else:
        conn.execute('''
            INSERT INTO horarios_confissao (dia_semana, horario, ativo)
            VALUES (?, ?, 1)
        ''', (dia_semana, horario))
        conn.commit()
        flash(f'Horário {horario} adicionado para {dia_semana}.', 'success')

    conn.close()
    return redirect(url_for('admin_horarios_confissao'))


@app.route('/admin/horarios-confissao/<int:horario_id>/toggle', methods=['POST'])
@login_required
def admin_horario_confissao_toggle(horario_id):
    """Ativar/desativar horário de confissão"""
    conn = get_db_connection()
    horario = conn.execute('SELECT * FROM horarios_confissao WHERE id = ?', (horario_id,)).fetchone()

    if horario:
        novo_status = 0 if horario['ativo'] else 1
        conn.execute('UPDATE horarios_confissao SET ativo = ? WHERE id = ?', (novo_status, horario_id))
        conn.commit()
        status_texto = 'ativado' if novo_status else 'desativado'
        flash(f'Horário {status_texto}.', 'success')

    conn.close()
    return redirect(url_for('admin_horarios_confissao'))


@app.route('/admin/horarios-confissao/<int:horario_id>/deletar', methods=['POST'])
@login_required
def admin_horario_confissao_delete(horario_id):
    """Remover horário de confissão"""
    conn = get_db_connection()
    conn.execute('DELETE FROM horarios_confissao WHERE id = ?', (horario_id,))
    conn.commit()
    conn.close()
    flash('Horário removido.', 'success')
    return redirect(url_for('admin_horarios_confissao'))


@app.route('/admin/mensagens')
@login_required
def admin_mensagens():
    """Lista mensagens de contato"""
    conn = get_db_connection()
    mensagens = conn.execute('''
        SELECT * FROM mensagens_contato
        ORDER BY data_criacao DESC
    ''').fetchall()
    conn.close()
    return render_template('admin_mensagens.html', mensagens=mensagens)


@app.route('/admin/mensagens/<int:mensagem_id>/lida', methods=['POST'])
@login_required
def admin_mensagem_lida(mensagem_id):
    """Marcar mensagem como lida"""
    conn = get_db_connection()
    conn.execute('UPDATE mensagens_contato SET lida = 1 WHERE id = ?', (mensagem_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_mensagens'))


@app.route('/admin/mensagens/<int:mensagem_id>/deletar', methods=['POST'])
@login_required
def admin_mensagem_delete(mensagem_id):
    """Deletar mensagem"""
    conn = get_db_connection()
    conn.execute('DELETE FROM mensagens_contato WHERE id = ?', (mensagem_id,))
    conn.commit()
    conn.close()
    flash('Mensagem deletada.', 'success')
    return redirect(url_for('admin_mensagens'))


# ==================== INICIALIZAÇÃO ====================

if __name__ == '__main__':
    # Criar pasta de uploads
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Inicializar banco de dados
    init_db()

    # Executar aplicação
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
