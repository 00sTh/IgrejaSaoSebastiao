# app.py
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
# Chave secreta para gerenciar sessões (MUDE ISSO EM PRODUÇÃO!)
app.secret_key = 'sua_chave_secreta_aqui_12345' 

# app.py (Corrigido e Completo - Insira esta rota)

# 1. Rota de Login
# app.py: 1. Rota de Login (CORRIGIDA - APENAS LÓGICA DE LOGIN)

# app.py: 1. Rota de Login (CORRIGIDA - SEM LÓGICA DE CONTEÚDO)

@app.route('/admin', methods=('GET', 'POST'))
def admin_login():
	if request.method == 'POST':
		# APENAS VARIÁVEIS DE LOGIN AQUI, COM 8 ESPAÇOS DE INDENTAÇÃO
		username = request.form['username']
		password = request.form['password'] 
		
		if username == 'admin' and password == '123':
			session['logged_in'] = True
			return redirect(url_for('admin_dashboard'))
		else:
			return render_template('admin_login.html', error='Usuário ou senha incorretos.')
			
	# Este retorno deve estar com 4 ESPAÇOS de indentação (alinhado com o 'if')
	return render_template('admin_login.html')
# Configurações de Upload
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



# --- Funções de Banco de Dados ---

def get_db_connection():
	# Cria a conexão com o banco de dados SQLite
	conn = sqlite3.connect('database.db')
	conn.row_factory = sqlite3.Row # Permite acessar colunas por nome
	return conn

# app.py: Modifique a função init_db()

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS noticias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            subtitulo TEXT,
            conteudo TEXT NOT NULL,
            imagem_url TEXT,
            tipo TEXT NOT NULL DEFAULT 'Notícia',  
            data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    ''') # Certifique-se de que NÃO há nenhum caractere extra AQUI
    conn.commit()
    conn.close()
    print("Banco de dados inicializado com sucesso!")
	
# Crie a pasta de uploads se não existir
if not os.path.exists(UPLOAD_FOLDER):
	os.makedirs(UPLOAD_FOLDER)

# Inicializa o banco de dados ao iniciar o app
init_db()

# Função auxiliar para verificar tipo de arquivo
def allowed_file(filename):
	return '.' in filename and \
		   filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- ROTAS DE BACK-END ---

# Rota para a página inicial (Front-end)
# app.py (Modificação na Rota index

# Rota para a página inicial (Front-end)
@app.route('/')
def index():
	conn = get_db_connection()
	noticias = conn.execute('SELECT * FROM noticias ORDER BY data_criacao DESC LIMIT 5').fetchall()
	conn.close()
	
	# ADICIONAR ESTA LINHA: 
	is_admin = session.get('logged_in', False)
	
	# PASSAR PARA O TEMPLATE:
	return render_template('index.html', noticias=noticias, is_admin=is_admin)

# --- ROTAS DO PAINEL DE ADMINISTRAÇÃO ---

# 1. Rota de Login
# app.py (Adicionar esta nova rota em qualquer lugar após as definições das outras rotas)

@app.route('/api/update_content', methods=['POST'])
def update_content():
	# Verifica se o usuário está logado
	if not session.get('logged_in'):
		return {'status': 'error', 'message': 'Não Autorizado'}, 401

	# Pega os dados enviados pelo JavaScript (JSON)
	data = request.get_json()
	post_id = data.get('id')
	field = data.get('field') # Ex: 'titulo' ou 'conteudo'
	new_value = data.get('value')
	
	if not all([post_id, field, new_value]):
		return {'status': 'error', 'message': 'Dados incompletos'}, 400

	if field not in ['titulo', 'conteudo', 'subtitulo']:
		return {'status': 'error', 'message': 'Campo inválido'}, 400

	try:
		conn = get_db_connection()
		# Usa um PLACEHOLDER (?) para evitar ataques de SQL Injection
		query = f"UPDATE noticias SET {field} = ? WHERE id = ?"
		conn.execute(query, (new_value, post_id))
		conn.commit()
		conn.close()
		
		return {'status': 'success', 'message': f'Campo {field} atualizado com sucesso.'}
	except Exception as e:
		# Em caso de erro, desfaz a operação e retorna o erro
		conn.close()
		print(f"Erro ao atualizar conteúdo: {e}")
		return {'status': 'error', 'message': 'Erro no servidor'}, 500

# 2. Rota de Logout
@app.route('/logout')
def logout():
	session.pop('logged_in', None)
	return redirect(url_for('admin_login'))

# 3. Rota de Dashboard (READ)
@app.route('/admin/dashboard')
def admin_dashboard():
	# Protege a rota: só acessa se estiver logado
	if not session.get('logged_in'):
		return redirect(url_for('admin_login'))

	conn = get_db_connection()
	noticias = conn.execute('SELECT * FROM noticias ORDER BY data_criacao DESC').fetchall()
	conn.close()
	return render_template('admin_dashboard.html', noticias=noticias)

# app.py: 4. Rota para Criação/Edição de Notícia (CORREÇÃO FINAL DE INDENTAÇÃO)

# Em app.py: Encontre e substitua TODA a função admin_edit (ou a lógica do POST dela)

# app.py: Rota para Criação/Edição de Notícia (CORREÇÃO FINAL)

@app.route('/admin/edit/', defaults={'post_id': None}, methods=('GET', 'POST'))
@app.route('/admin/edit/<int:post_id>', methods=('GET', 'POST'))
def admin_edit(post_id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))

    noticia = None
    
    # 1. LÓGICA DO GET (SE FOR EDIÇÃO)
    if post_id:
        conn = get_db_connection()
        noticia = conn.execute('SELECT * FROM noticias WHERE id = ?', (post_id,)).fetchone()
        conn.close() # <--- CONEXÃO FECHADA APÓS O FETCH!

    # 2. LÓGICA DO POST (SALVAMENTO)
    if request.method == 'POST':
        # Usando .get() para evitar o KeyError de 'conteudo'
        titulo = request.form.get('titulo')
        subtitulo = request.form.get('subtitulo')
        conteudo = request.form.get('conteudo') 
        tipo = request.form.get('tipo', 'Notícia') 

        # ... Lógica de Imagem ...
        imagem_url = noticia['imagem_url'] if noticia else None
        
        if 'imagem' in request.files and request.files['imagem'].filename != '':
            file = request.files['imagem']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                imagem_url = url_for('static', filename=f'uploads/{filename}')

        # Validação simples
        if not titulo or not conteudo:
            # Retorna para o formulário com o erro
            # O ideal é usar Flash messages, mas para simplicidade, vamos redirecionar ou mostrar erro.
            return 'Erro: Título e Conteúdo são obrigatórios.', 400

        # === INÍCIO DA INTERAÇÃO COM O BANCO DE DADOS ===
        conn = get_db_connection() 

        if post_id:
            # UPDATE
            conn.execute('UPDATE noticias SET titulo = ?, subtitulo = ?, conteudo = ?, imagem_url = ?, tipo = ? WHERE id = ?',
                         (titulo, subtitulo, conteudo, imagem_url, tipo, post_id))
        else:
            # CREATE
            conn.execute('INSERT INTO noticias (titulo, subtitulo, conteudo, imagem_url, tipo) VALUES (?, ?, ?, ?, ?)',
                         (titulo, subtitulo, conteudo, imagem_url, tipo))
            
        conn.commit()
        conn.close() # <--- CONEXÃO FECHADA APÓS O SAVE!
        return redirect(url_for('admin_dashboard'))

    # 3. RENDERIZAÇÃO DO TEMPLATE (GET - Nova ou Edição)
    # NÃO HÁ conn.close() AQUI, pois nenhuma conexão foi aberta neste caminho (apenas a de fetch, que já foi fechada acima).
    return render_template('admin_edit.html', noticia=noticia)

# ... (restante do app.py) ...
		
		
# 5. Rota para Deletar Notícia (DELETE)
@app.route('/admin/delete/<int:post_id>', methods=('POST',))
def admin_delete(post_id):
	if not session.get('logged_in'):
		return redirect(url_for('admin_login'))
	
	conn = get_db_connection()
	# Opcional: Aqui você pode adicionar lógica para DELETAR a foto do servidor também.
	conn.execute('DELETE FROM noticias WHERE id = ?', (post_id,))
	conn.commit()
	conn.close()
	return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
	# Roda o aplicativo Flask no modo debug (desative em produção!)
	app.run(debug=True)