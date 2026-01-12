"""
Sistema de Gerenciamento - Igreja São Sebastião
Sistema completo com painel administrativo editável
"""
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import shutil
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

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
        ('hero', 'Igreja São Sebastião', 'Onde a Fé Encontra a Comunidade em Ponte Nova'),
        ('sobre', 'Sobre a Paróquia', 'A Igreja São Sebastião é uma comunidade de fé dedicada a servir e acolher todos em Ponte Nova.'),
        ('historia', 'Nossa História', 'Fundada em [ano], a Igreja São Sebastião tem uma rica história de serviço à comunidade.'),
        ('missao', 'Nossa Missão', 'Levar a palavra de Deus e servir nossa comunidade com amor e dedicação.'),
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

# ==================== DECORADORES ====================

def login_required(f):
    """Decorator para proteger rotas que requerem autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Você precisa estar logado para acessar esta página.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== FUNÇÕES AUXILIARES ====================

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, folder='uploads'):
    """Salva arquivo enviado e retorna o caminho"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Adicionar timestamp para evitar conflitos
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
    """Login do administrador"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Usuário ou senha incorretos.', 'error')
            return render_template('admin_login.html', error='Usuário ou senha incorretos.')

    return render_template('admin_login.html')

@app.route('/logout')
def logout():
    """Logout do administrador"""
    session.clear()
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
def api_update_content():
    """API para atualização de conteúdo inline"""
    data = request.get_json()
    post_id = data.get('id')
    field = data.get('field')
    new_value = data.get('value')

    if not all([post_id, field, new_value]):
        return jsonify({'status': 'error', 'message': 'Dados incompletos'}), 400

    if field not in ['titulo', 'conteudo', 'subtitulo']:
        return jsonify({'status': 'error', 'message': 'Campo inválido'}), 400

    try:
        conn = get_db_connection()
        query = f"UPDATE noticias SET {field} = ? WHERE id = ?"
        conn.execute(query, (new_value, post_id))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': f'Campo {field} atualizado'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ==================== INICIALIZAÇÃO ====================

if __name__ == '__main__':
    # Criar pasta de uploads
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Inicializar banco de dados
    init_db()

    # Executar aplicação
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
