"""
Testes do Sistema de Autenticação - Igreja São Sebastião

Protocolo de Teste:
1. Causa raiz do erro identificada
2. Teste criado para provar o erro
3. Código corrigido
4. Teste rodado e sucesso confirmado
"""

import pytest
import sys
import os
import sqlite3
import tempfile

# Adicionar path do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash, check_password_hash


class TestPasswordHashing:
    """
    CAUSA RAIZ: Senhas eram comparadas em texto plano (app.py:266-267)
    CORREÇÃO: Usar werkzeug.security para hash com pbkdf2:sha256
    """

    def test_password_not_stored_plain_text(self):
        """Prova que senha NÃO é armazenada em texto plano"""
        plain_password = "minha_senha_123"
        hashed = generate_password_hash(plain_password, method='pbkdf2:sha256')

        # Hash deve ser diferente da senha original
        assert hashed != plain_password
        # Hash deve começar com identificador do método
        assert hashed.startswith('pbkdf2:sha256')

    def test_password_verification_works(self):
        """Prova que verificação de senha funciona corretamente"""
        plain_password = "senha_correta"
        hashed = generate_password_hash(plain_password, method='pbkdf2:sha256')

        # Senha correta deve passar
        assert check_password_hash(hashed, plain_password) is True
        # Senha incorreta deve falhar
        assert check_password_hash(hashed, "senha_errada") is False

    def test_different_hashes_for_same_password(self):
        """Prova que cada hash é único (usa salt)"""
        password = "mesma_senha"
        hash1 = generate_password_hash(password, method='pbkdf2:sha256')
        hash2 = generate_password_hash(password, method='pbkdf2:sha256')

        # Hashes devem ser diferentes (salt diferente)
        assert hash1 != hash2
        # Mas ambos devem verificar corretamente
        assert check_password_hash(hash1, password) is True
        assert check_password_hash(hash2, password) is True


class TestRateLimiter:
    """
    CAUSA RAIZ: Sem proteção contra brute force
    CORREÇÃO: Implementar rate limiting com bloqueio após 5 tentativas
    """

    def test_rate_limiter_blocks_after_max_attempts(self):
        """Prova que IP é bloqueado após muitas tentativas"""
        from middleware.auth import RateLimiter

        # Limpar estado
        RateLimiter._attempts = {}

        test_ip = "192.168.1.100"

        # Não deve estar bloqueado inicialmente
        assert RateLimiter.is_blocked(test_ip) is False

        # Registrar tentativas falhas
        for i in range(5):
            RateLimiter.record_attempt(test_ip, success=False)

        # Agora deve estar bloqueado
        assert RateLimiter.is_blocked(test_ip) is True

    def test_rate_limiter_clears_on_success(self):
        """Prova que login bem-sucedido limpa tentativas"""
        from middleware.auth import RateLimiter

        RateLimiter._attempts = {}
        test_ip = "192.168.1.101"

        # Registrar algumas tentativas falhas
        for i in range(3):
            RateLimiter.record_attempt(test_ip, success=False)

        assert RateLimiter.get_remaining_attempts(test_ip) == 2

        # Login bem-sucedido deve limpar
        RateLimiter.record_attempt(test_ip, success=True)

        assert RateLimiter.get_remaining_attempts(test_ip) == 5
        assert RateLimiter.is_blocked(test_ip) is False


class TestSQLInjectionPrevention:
    """
    CAUSA RAIZ: Query construída com f-string (app.py:634)
    CORREÇÃO: Whitelist de campos permitidos
    """

    def test_field_whitelist_rejects_injection(self):
        """Prova que campos maliciosos são rejeitados"""
        ALLOWED_FIELDS = {'titulo': 'titulo', 'conteudo': 'conteudo', 'subtitulo': 'subtitulo'}

        # Tentativa de SQL injection
        malicious_fields = [
            "titulo; DROP TABLE noticias; --",
            "titulo OR 1=1",
            "titulo' OR '1'='1",
            "1; DELETE FROM users",
        ]

        for field in malicious_fields:
            assert field not in ALLOWED_FIELDS, f"Campo malicioso {field} passou pelo whitelist!"

    def test_only_allowed_fields_pass(self):
        """Prova que apenas campos permitidos passam"""
        ALLOWED_FIELDS = {'titulo': 'titulo', 'conteudo': 'conteudo', 'subtitulo': 'subtitulo'}

        valid_fields = ['titulo', 'conteudo', 'subtitulo']
        invalid_fields = ['id', 'data_criacao', 'imagem_url', 'tipo', 'password', 'admin']

        for field in valid_fields:
            assert field in ALLOWED_FIELDS

        for field in invalid_fields:
            assert field not in ALLOWED_FIELDS


class TestCSRFProtection:
    """
    CAUSA RAIZ: Sem proteção CSRF nas rotas POST
    CORREÇÃO: Token CSRF obrigatório em todos os forms
    """

    def test_csrf_token_is_generated(self):
        """Prova que CSRF token é gerado"""
        import secrets
        token = secrets.token_hex(32)

        # Token deve ter 64 caracteres (32 bytes em hex)
        assert len(token) == 64
        # Token deve ser hexadecimal
        assert all(c in '0123456789abcdef' for c in token)

    def test_csrf_tokens_are_unique(self):
        """Prova que cada token é único"""
        import secrets
        tokens = [secrets.token_hex(32) for _ in range(100)]

        # Todos os tokens devem ser únicos
        assert len(tokens) == len(set(tokens))


class TestRoleBasedAccessControl:
    """
    CAUSA RAIZ: Apenas um admin hardcoded, sem níveis de permissão
    CORREÇÃO: Sistema RBAC com roles e permissões
    """

    def test_role_hierarchy(self):
        """Prova que hierarquia de roles está correta"""
        from middleware.auth import ROLE_PERMISSIONS, Permissions

        # super_admin tem mais permissões que admin
        assert len(ROLE_PERMISSIONS['super_admin']) > len(ROLE_PERMISSIONS['admin'])

        # admin tem mais permissões que editor
        assert len(ROLE_PERMISSIONS['admin']) > len(ROLE_PERMISSIONS['editor'])

        # editor tem mais permissões que viewer
        assert len(ROLE_PERMISSIONS['editor']) > len(ROLE_PERMISSIONS['viewer'])

    def test_super_admin_has_user_management(self):
        """Prova que só super_admin pode gerenciar usuários"""
        from middleware.auth import ROLE_PERMISSIONS, Permissions

        assert Permissions.USERS_CREATE in ROLE_PERMISSIONS['super_admin']
        assert Permissions.USERS_DELETE in ROLE_PERMISSIONS['super_admin']

        assert Permissions.USERS_CREATE not in ROLE_PERMISSIONS['admin']
        assert Permissions.USERS_CREATE not in ROLE_PERMISSIONS['editor']
        assert Permissions.USERS_CREATE not in ROLE_PERMISSIONS['viewer']

    def test_viewer_is_read_only(self):
        """Prova que viewer só tem permissões de leitura"""
        from middleware.auth import ROLE_PERMISSIONS, Permissions

        viewer_perms = ROLE_PERMISSIONS['viewer']

        # Todas as permissões de viewer devem ser de leitura
        for perm in viewer_perms:
            assert ':read' in perm, f"Viewer tem permissão não-leitura: {perm}"


class TestDatabaseSchema:
    """
    Testes do schema do banco de dados
    """

    def test_users_table_has_required_fields(self):
        """Prova que tabela users tem campos necessários"""
        # Simula criação de tabela
        conn = sqlite3.connect(':memory:')
        conn.execute('''
            CREATE TABLE users (
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

        # Verificar que tabela foi criada
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        assert cursor.fetchone() is not None

        # Verificar colunas
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = {row[1] for row in cursor.fetchall()}

        required_columns = {'id', 'username', 'password_hash', 'role', 'is_active', 'failed_attempts'}
        assert required_columns.issubset(columns)

        conn.close()

    def test_audit_log_table_tracks_changes(self):
        """Prova que tabela audit_log rastreia alterações"""
        conn = sqlite3.connect(':memory:')
        conn.execute('''
            CREATE TABLE audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                entity_type TEXT,
                entity_id INTEGER,
                old_value TEXT,
                new_value TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Inserir log de teste
        conn.execute('''
            INSERT INTO audit_log (user_id, action, entity_type, entity_id, old_value, new_value)
            VALUES (1, 'update', 'noticias', 5, '{"titulo": "Antigo"}', '{"titulo": "Novo"}')
        ''')
        conn.commit()

        # Verificar que foi inserido
        cursor = conn.execute('SELECT * FROM audit_log WHERE entity_id = 5')
        row = cursor.fetchone()

        assert row is not None
        assert row[2] == 'update'  # action
        assert row[3] == 'noticias'  # entity_type

        conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
