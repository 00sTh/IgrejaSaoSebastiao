"""
Sistema de Autenticação e RBAC - Igreja São Sebastião
Implementa: Sessions seguras, CSRF, Rate Limiting, Roles
"""

import sqlite3
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import session, request, redirect, url_for, flash, g, abort, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from middleware.logger import AppLogger, log_request, log_error


# ==================== RATE LIMITER ====================

class RateLimiter:
    """
    Rate limiter em memória para proteção contra brute force.
    Em produção, considere usar Redis.
    """

    _attempts = {}  # {ip: [(timestamp, count)]}
    MAX_ATTEMPTS = 5
    WINDOW_SECONDS = 300  # 5 minutos
    BLOCK_SECONDS = 900   # 15 minutos de bloqueio

    @classmethod
    def is_blocked(cls, ip):
        """Verifica se IP está bloqueado"""
        cls._cleanup()
        if ip in cls._attempts:
            attempts = cls._attempts[ip]
            if len(attempts) >= cls.MAX_ATTEMPTS:
                last_attempt = attempts[-1][0]
                if time.time() - last_attempt < cls.BLOCK_SECONDS:
                    return True
        return False

    @classmethod
    def record_attempt(cls, ip, success=False):
        """Registra tentativa de login"""
        cls._cleanup()
        now = time.time()

        if success:
            # Login bem-sucedido limpa tentativas
            cls._attempts.pop(ip, None)
            return

        if ip not in cls._attempts:
            cls._attempts[ip] = []

        cls._attempts[ip].append((now, 1))
        log_request(f"Tentativa de login falha", level='warning', ip=ip,
                   attempts=len(cls._attempts[ip]))

    @classmethod
    def _cleanup(cls):
        """Remove entradas antigas"""
        now = time.time()
        for ip in list(cls._attempts.keys()):
            cls._attempts[ip] = [
                (ts, count) for ts, count in cls._attempts[ip]
                if now - ts < cls.WINDOW_SECONDS
            ]
            if not cls._attempts[ip]:
                del cls._attempts[ip]

    @classmethod
    def get_remaining_attempts(cls, ip):
        """Retorna tentativas restantes"""
        cls._cleanup()
        used = len(cls._attempts.get(ip, []))
        return max(0, cls.MAX_ATTEMPTS - used)


# ==================== ROLES E PERMISSÕES ====================

class Permissions:
    """Definição de permissões do sistema"""

    # Permissões disponíveis
    NOTICIAS_CREATE = 'noticias:create'
    NOTICIAS_READ = 'noticias:read'
    NOTICIAS_UPDATE = 'noticias:update'
    NOTICIAS_DELETE = 'noticias:delete'

    GALERIA_CREATE = 'galeria:create'
    GALERIA_READ = 'galeria:read'
    GALERIA_UPDATE = 'galeria:update'
    GALERIA_DELETE = 'galeria:delete'

    HORARIOS_CREATE = 'horarios:create'
    HORARIOS_READ = 'horarios:read'
    HORARIOS_UPDATE = 'horarios:update'
    HORARIOS_DELETE = 'horarios:delete'

    CONFIG_READ = 'config:read'
    CONFIG_UPDATE = 'config:update'

    USERS_CREATE = 'users:create'
    USERS_READ = 'users:read'
    USERS_UPDATE = 'users:update'
    USERS_DELETE = 'users:delete'

    BACKUP_CREATE = 'backup:create'


# Mapeamento de roles para permissões
ROLE_PERMISSIONS = {
    'super_admin': [
        # Todas as permissões
        Permissions.NOTICIAS_CREATE, Permissions.NOTICIAS_READ,
        Permissions.NOTICIAS_UPDATE, Permissions.NOTICIAS_DELETE,
        Permissions.GALERIA_CREATE, Permissions.GALERIA_READ,
        Permissions.GALERIA_UPDATE, Permissions.GALERIA_DELETE,
        Permissions.HORARIOS_CREATE, Permissions.HORARIOS_READ,
        Permissions.HORARIOS_UPDATE, Permissions.HORARIOS_DELETE,
        Permissions.CONFIG_READ, Permissions.CONFIG_UPDATE,
        Permissions.USERS_CREATE, Permissions.USERS_READ,
        Permissions.USERS_UPDATE, Permissions.USERS_DELETE,
        Permissions.BACKUP_CREATE,
    ],
    'admin': [
        # Tudo exceto gestão de usuários
        Permissions.NOTICIAS_CREATE, Permissions.NOTICIAS_READ,
        Permissions.NOTICIAS_UPDATE, Permissions.NOTICIAS_DELETE,
        Permissions.GALERIA_CREATE, Permissions.GALERIA_READ,
        Permissions.GALERIA_UPDATE, Permissions.GALERIA_DELETE,
        Permissions.HORARIOS_CREATE, Permissions.HORARIOS_READ,
        Permissions.HORARIOS_UPDATE, Permissions.HORARIOS_DELETE,
        Permissions.CONFIG_READ, Permissions.CONFIG_UPDATE,
        Permissions.BACKUP_CREATE,
    ],
    'editor': [
        # Criar e editar conteúdo, sem deletar
        Permissions.NOTICIAS_CREATE, Permissions.NOTICIAS_READ,
        Permissions.NOTICIAS_UPDATE,
        Permissions.GALERIA_CREATE, Permissions.GALERIA_READ,
        Permissions.GALERIA_UPDATE,
        Permissions.HORARIOS_READ,
        Permissions.CONFIG_READ,
    ],
    'viewer': [
        # Apenas visualizar
        Permissions.NOTICIAS_READ,
        Permissions.GALERIA_READ,
        Permissions.HORARIOS_READ,
        Permissions.CONFIG_READ,
    ]
}


# ==================== AUTH MANAGER ====================

class AuthManager:
    """Gerenciador central de autenticação"""

    SESSION_LIFETIME = timedelta(hours=8)

    @classmethod
    def setup(cls, app):
        """Configura autenticação na aplicação Flask"""

        # Configurações de sessão segura
        app.config['SESSION_COOKIE_SECURE'] = not app.debug  # HTTPS em produção
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        app.config['PERMANENT_SESSION_LIFETIME'] = cls.SESSION_LIFETIME

        # Inicializar tabela de usuários
        cls.init_users_table(app.config.get('DATABASE_PATH', 'database.db'))

        # Middleware para verificar sessão em cada request
        @app.before_request
        def check_session():
            # Verificar expiração de sessão
            if session.get('logged_in'):
                last_activity = session.get('last_activity')
                if last_activity:
                    last_dt = datetime.fromisoformat(last_activity)
                    if datetime.utcnow() - last_dt > cls.SESSION_LIFETIME:
                        session.clear()
                        flash('Sua sessão expirou. Faça login novamente.', 'warning')
                        return redirect(url_for('admin_login'))
                session['last_activity'] = datetime.utcnow().isoformat()

            # Carregar usuário atual no contexto g
            if session.get('user_id'):
                g.current_user = cls.get_user_by_id(session['user_id'])
            else:
                g.current_user = None

        # CSRF Token
        @app.before_request
        def csrf_protect():
            if request.method in ['POST', 'PUT', 'DELETE']:
                # Ignorar API com autenticação diferente (futuro)
                if request.path.startswith('/api/') and request.is_json:
                    # Para API, verificar header X-CSRF-Token
                    token = request.headers.get('X-CSRF-Token')
                else:
                    token = request.form.get('csrf_token')

                if session.get('logged_in') and token != session.get('csrf_token'):
                    log_request("CSRF token inválido", level='warning')
                    abort(403)

        # Gerar CSRF token para templates
        @app.context_processor
        def inject_csrf_token():
            if 'csrf_token' not in session:
                session['csrf_token'] = secrets.token_hex(32)
            return {'csrf_token': session['csrf_token']}

        # Injetar current_user nos templates
        @app.context_processor
        def inject_user():
            return {
                'current_user': getattr(g, 'current_user', None),
                'has_permission': cls.has_permission
            }

        logger = AppLogger.get_logger()
        logger.info("Sistema de autenticação inicializado")

    @classmethod
    def init_users_table(cls, db_path):
        """Cria tabela de usuários se não existir"""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Criar tabela de usuários
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                email TEXT,
                role TEXT NOT NULL DEFAULT 'viewer',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                failed_attempts INTEGER DEFAULT 0
            )
        ''')

        # Criar tabela de sessões (para invalidação)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Criar tabela de log de auditoria
        conn.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                entity_type TEXT,
                entity_id INTEGER,
                old_value TEXT,
                new_value TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Verificar se existe admin padrão
        existing = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()
        if existing['count'] == 0:
            # Criar super admin padrão (DEVE SER ALTERADO!)
            from config import Config
            default_password = Config.ADMIN_PASSWORD
            password_hash = generate_password_hash(default_password, method='pbkdf2:sha256')

            conn.execute('''
                INSERT INTO users (username, password_hash, email, role)
                VALUES (?, ?, ?, ?)
            ''', (Config.ADMIN_USERNAME, password_hash, 'admin@igreja.local', 'super_admin'))

            print("! Usuário admin padrão criado. ALTERE A SENHA!")

        conn.commit()
        conn.close()

    @classmethod
    def authenticate(cls, username, password, ip_address=None):
        """
        Autentica usuário.
        Retorna: (success: bool, user: dict|None, error: str|None)
        """
        # Verificar rate limiting
        if ip_address and RateLimiter.is_blocked(ip_address):
            remaining = RateLimiter.BLOCK_SECONDS // 60
            log_request("Login bloqueado por rate limit", level='warning', ip=ip_address)
            return False, None, f'Muitas tentativas. Aguarde {remaining} minutos.'

        from config import Config
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row

        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND is_active = 1',
            (username,)
        ).fetchone()

        if not user:
            if ip_address:
                RateLimiter.record_attempt(ip_address, success=False)
            conn.close()
            log_request("Login falhou - usuário não encontrado", level='warning', username=username)
            return False, None, 'Usuário ou senha incorretos.'

        if not check_password_hash(user['password_hash'], password):
            if ip_address:
                RateLimiter.record_attempt(ip_address, success=False)

            # Incrementar tentativas falhas
            conn.execute(
                'UPDATE users SET failed_attempts = failed_attempts + 1 WHERE id = ?',
                (user['id'],)
            )
            conn.commit()
            conn.close()

            log_request("Login falhou - senha incorreta", level='warning', username=username)
            return False, None, 'Usuário ou senha incorretos.'

        # Login bem-sucedido
        if ip_address:
            RateLimiter.record_attempt(ip_address, success=True)

        # Atualizar last_login e resetar tentativas
        conn.execute('''
            UPDATE users SET last_login = ?, failed_attempts = 0 WHERE id = ?
        ''', (datetime.utcnow().isoformat(), user['id']))
        conn.commit()
        conn.close()

        log_request("Login bem-sucedido", level='info', username=username, user_id=user['id'])
        return True, dict(user), None

    @classmethod
    def create_session(cls, user):
        """Cria sessão para usuário autenticado"""
        session.clear()
        session['logged_in'] = True
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['last_activity'] = datetime.utcnow().isoformat()
        session['csrf_token'] = secrets.token_hex(32)
        session.permanent = True

    @classmethod
    def logout(cls):
        """Encerra sessão do usuário"""
        username = session.get('username', 'unknown')
        session.clear()
        log_request("Logout realizado", level='info', username=username)

    @classmethod
    def get_user_by_id(cls, user_id):
        """Busca usuário por ID"""
        from config import Config
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        return dict(user) if user else None

    @classmethod
    def has_permission(cls, permission):
        """Verifica se usuário atual tem permissão"""
        if not g.get('current_user'):
            return False
        role = g.current_user.get('role', 'viewer')
        return permission in ROLE_PERMISSIONS.get(role, [])

    @classmethod
    def change_password(cls, user_id, old_password, new_password):
        """Altera senha do usuário"""
        from config import Config
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row

        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            conn.close()
            return False, 'Usuário não encontrado.'

        if not check_password_hash(user['password_hash'], old_password):
            conn.close()
            return False, 'Senha atual incorreta.'

        new_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        conn.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_hash, user_id))
        conn.commit()
        conn.close()

        log_request("Senha alterada", level='info', user_id=user_id)
        return True, 'Senha alterada com sucesso.'

    @classmethod
    def create_user(cls, username, password, email=None, role='viewer'):
        """Cria novo usuário"""
        from config import Config
        conn = sqlite3.connect(Config.DATABASE_PATH)

        # Verificar se username já existe
        existing = conn.execute(
            'SELECT id FROM users WHERE username = ?', (username,)
        ).fetchone()
        if existing:
            conn.close()
            return False, None, 'Nome de usuário já existe.'

        password_hash = generate_password_hash(password, method='pbkdf2:sha256')

        try:
            cursor = conn.execute('''
                INSERT INTO users (username, password_hash, email, role)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, email, role))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()

            log_request("Usuário criado", level='info', new_user_id=user_id, username=username)
            return True, user_id, None
        except Exception as e:
            conn.close()
            log_error("Erro ao criar usuário", exception=e)
            return False, None, str(e)

    @classmethod
    def audit_log(cls, action, entity_type=None, entity_id=None, old_value=None, new_value=None):
        """Registra ação no log de auditoria"""
        from config import Config

        try:
            conn = sqlite3.connect(Config.DATABASE_PATH)

            # Obter user_id e ip_address apenas se estiver dentro de request context
            user_id = None
            ip_address = None

            if has_request_context():
                try:
                    user_id = session.get('user_id')
                    ip_address = request.remote_addr
                except RuntimeError:
                    pass

            conn.execute('''
                INSERT INTO audit_log (user_id, action, entity_type, entity_id, old_value, new_value, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, action, entity_type, entity_id,
                  str(old_value) if old_value else None,
                  str(new_value) if new_value else None,
                  ip_address))
            conn.commit()
            conn.close()
        except Exception as e:
            # Não deixar falha no audit_log quebrar a operação principal
            log_error("Erro ao registrar audit_log", exception=e)


# Importar has_request_context
from flask import has_request_context


# ==================== DECORATORS ====================

def login_required(f):
    """Decorator que exige autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Você precisa estar logado para acessar esta página.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """
    Decorator que exige role específica.

    Uso:
        @role_required('admin', 'super_admin')
        def admin_only_view():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                flash('Você precisa estar logado.', 'error')
                return redirect(url_for('admin_login'))

            user_role = session.get('role', 'viewer')
            if user_role not in roles:
                log_request("Acesso negado por role", level='warning',
                           required=roles, user_role=user_role)
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def permission_required(permission):
    """
    Decorator que exige permissão específica.

    Uso:
        @permission_required(Permissions.NOTICIAS_DELETE)
        def deletar_noticia():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                flash('Você precisa estar logado.', 'error')
                return redirect(url_for('admin_login'))

            if not AuthManager.has_permission(permission):
                log_request("Acesso negado por permissão", level='warning',
                           required=permission, user_role=session.get('role'))
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
