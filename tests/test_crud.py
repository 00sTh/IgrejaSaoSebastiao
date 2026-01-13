"""
Testes do Motor CRUD Dinâmico - Igreja São Sebastião

Testa:
- Schema Registry
- Cache Manager
- CRUD Engine operations
- Validações
"""

import pytest
import sys
import os
import sqlite3
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSchemaRegistry:
    """Testes do Schema Registry"""

    def test_registry_is_singleton(self):
        """Prova que SchemaRegistry é singleton"""
        from core.schema import SchemaRegistry

        registry1 = SchemaRegistry()
        registry2 = SchemaRegistry()

        assert registry1 is registry2

    def test_default_schemas_loaded(self):
        """Prova que schemas padrão são carregados"""
        from core.schema import SchemaRegistry

        registry = SchemaRegistry()
        schemas = registry.get_all()

        expected_entities = ['noticias', 'horarios_missas', 'galeria',
                           'paroquia_info', 'contatos', 'configuracoes', 'users']

        for entity in expected_entities:
            assert entity in schemas, f"Schema {entity} não encontrado"

    def test_schema_has_required_fields(self):
        """Prova que schemas têm campos obrigatórios"""
        from core.schema import SchemaRegistry

        registry = SchemaRegistry()
        schema = registry.get('noticias')

        assert schema is not None
        assert schema.table == 'noticias'
        assert schema.primary_key == 'id'
        assert 'titulo' in schema.fields
        assert 'conteudo' in schema.fields

    def test_field_schema_properties(self):
        """Prova que FieldSchema tem propriedades corretas"""
        from core.schema import SchemaRegistry, FieldType

        registry = SchemaRegistry()
        schema = registry.get('noticias')
        titulo_field = schema.fields['titulo']

        assert titulo_field.field_type == FieldType.TEXT
        assert titulo_field.required is True
        assert titulo_field.label == "Título"


class TestCacheManager:
    """Testes do Cache Manager"""

    def test_cache_set_and_get(self):
        """Prova que cache armazena e recupera valores"""
        from core.cache import CacheManager

        CacheManager.invalidate_all()

        CacheManager.set("test_key", {"data": "value"}, ttl=60)
        result = CacheManager.get("test_key")

        assert result is not None
        assert result["data"] == "value"

    def test_cache_expiration(self):
        """Prova que cache expira corretamente"""
        from core.cache import CacheManager
        import time

        CacheManager.set("expire_test", "value", ttl=1)

        # Valor deve existir imediatamente
        assert CacheManager.get("expire_test") == "value"

        # Após 1.5 segundos deve expirar
        time.sleep(1.5)
        assert CacheManager.get("expire_test") is None

    def test_cache_invalidate_entity(self):
        """Prova que invalidação de entidade funciona"""
        from core.cache import CacheManager

        CacheManager.invalidate_all()

        # Criar várias entradas para uma entidade
        CacheManager.set("entity:noticias:1", "data1")
        CacheManager.set("entity:noticias:2", "data2")
        CacheManager.set("entity:galeria:1", "other")

        # Invalidar apenas noticias
        count = CacheManager.invalidate_entity("noticias")

        assert count == 2
        assert CacheManager.get("entity:noticias:1") is None
        assert CacheManager.get("entity:noticias:2") is None
        assert CacheManager.get("entity:galeria:1") == "other"

    def test_cache_stats(self):
        """Prova que estatísticas funcionam"""
        from core.cache import CacheManager

        CacheManager.invalidate_all()
        CacheManager.set("stats_test_1", "value1")
        CacheManager.set("stats_test_2", "value2")

        stats = CacheManager.get_stats()

        assert stats["total_entries"] >= 2
        assert "valid_entries" in stats
        assert "by_type" in stats


class TestCRUDEngine:
    """Testes do CRUD Engine"""

    @pytest.fixture
    def temp_db(self):
        """Cria banco de dados temporário"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        conn = sqlite3.connect(path)
        conn.execute('''
            CREATE TABLE noticias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                subtitulo TEXT,
                conteudo TEXT NOT NULL,
                imagem_url TEXT,
                tipo TEXT NOT NULL DEFAULT 'Notícia',
                data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

        yield path

        os.unlink(path)

    def test_crud_create(self, temp_db):
        """Prova que criação funciona"""
        from core.crud import CRUDEngine

        engine = CRUDEngine(temp_db)

        success, new_id, error = engine.create('noticias', {
            'titulo': 'Teste de Notícia',
            'conteudo': 'Conteúdo de teste',
            'tipo': 'Notícia'
        })

        assert success is True
        assert new_id is not None
        assert error is None

        # Verificar que foi criado
        record = engine.read('noticias', new_id)
        assert record is not None
        assert record['titulo'] == 'Teste de Notícia'

    def test_crud_read(self, temp_db):
        """Prova que leitura funciona"""
        from core.crud import CRUDEngine

        engine = CRUDEngine(temp_db)

        # Criar registro
        engine.create('noticias', {
            'titulo': 'Leitura Teste',
            'conteudo': 'Conteúdo',
            'tipo': 'Notícia'
        })

        # Ler registro
        record = engine.read('noticias', 1)

        assert record is not None
        assert record['titulo'] == 'Leitura Teste'

    def test_crud_update(self, temp_db):
        """Prova que atualização funciona"""
        from core.crud import CRUDEngine

        engine = CRUDEngine(temp_db)

        # Criar registro
        success, new_id, _ = engine.create('noticias', {
            'titulo': 'Original',
            'conteudo': 'Conteúdo Original',
            'tipo': 'Notícia'
        })

        # Atualizar
        success, error = engine.update('noticias', new_id, {
            'titulo': 'Atualizado'
        })

        assert success is True
        assert error is None

        # Verificar atualização
        record = engine.read('noticias', new_id)
        assert record['titulo'] == 'Atualizado'

    def test_crud_delete(self, temp_db):
        """Prova que deleção funciona"""
        from core.crud import CRUDEngine

        engine = CRUDEngine(temp_db)

        # Criar registro
        success, new_id, _ = engine.create('noticias', {
            'titulo': 'Para Deletar',
            'conteudo': 'Será deletado',
            'tipo': 'Notícia'
        })

        # Deletar
        success, error = engine.delete('noticias', new_id)

        assert success is True

        # Verificar que foi deletado
        record = engine.read('noticias', new_id)
        assert record is None

    def test_crud_list_pagination(self, temp_db):
        """Prova que listagem com paginação funciona"""
        from core.crud import CRUDEngine

        engine = CRUDEngine(temp_db)

        # Criar 25 registros
        for i in range(25):
            engine.create('noticias', {
                'titulo': f'Notícia {i}',
                'conteudo': f'Conteúdo {i}',
                'tipo': 'Notícia'
            })

        # Listar primeira página
        result = engine.list('noticias', page=1, per_page=10)

        assert result['total'] == 25
        assert len(result['items']) == 10
        assert result['pages'] == 3
        assert result['has_next'] is True
        assert result['has_prev'] is False

    def test_crud_list_search(self, temp_db):
        """Prova que busca funciona"""
        from core.crud import CRUDEngine

        engine = CRUDEngine(temp_db)

        engine.create('noticias', {
            'titulo': 'Festa Junina',
            'conteudo': 'Evento especial',
            'tipo': 'Evento'
        })
        engine.create('noticias', {
            'titulo': 'Missa Especial',
            'conteudo': 'Celebração',
            'tipo': 'Notícia'
        })

        # Buscar por "Festa"
        result = engine.list('noticias', search='Festa')

        assert result['total'] == 1
        assert result['items'][0]['titulo'] == 'Festa Junina'


class TestValidation:
    """Testes de validação"""

    def test_required_field_validation(self):
        """Prova que campos obrigatórios são validados"""
        from core.crud import CRUDEngine, ValidationError
        import tempfile

        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        conn = sqlite3.connect(path)
        conn.execute('''
            CREATE TABLE noticias (
                id INTEGER PRIMARY KEY,
                titulo TEXT NOT NULL,
                conteudo TEXT NOT NULL,
                tipo TEXT DEFAULT 'Notícia'
            )
        ''')
        conn.close()

        engine = CRUDEngine(path)

        # Tentar criar sem título
        success, _, error = engine.create('noticias', {
            'conteudo': 'Apenas conteúdo'
        })

        assert success is False
        assert 'obrigatório' in error.lower() or 'Título' in error

        os.unlink(path)

    def test_select_field_validation(self):
        """Prova que campos SELECT validam opções"""
        from core.schema import SchemaRegistry

        registry = SchemaRegistry()
        schema = registry.get('noticias')
        tipo_field = schema.fields['tipo']

        valid_values = [opt['value'] for opt in tipo_field.options]

        assert 'Notícia' in valid_values
        assert 'Evento' in valid_values
        assert 'InvalidOption' not in valid_values


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
