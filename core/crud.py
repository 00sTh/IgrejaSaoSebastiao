"""
CRUD Engine - Igreja São Sebastião
Motor de CRUD dinâmico baseado em Schema.
Gera operações automaticamente a partir do schema registry.
"""

import sqlite3
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from flask import request, flash, g
from werkzeug.security import generate_password_hash

from flask import has_request_context

from core.schema import SchemaRegistry, EntitySchema, FieldSchema, FieldType
from core.cache import CacheManager, invalidate_on_change, QueryCache
from middleware.logger import log_request, log_error
from middleware.auth import AuthManager, Permissions


class ValidationError(Exception):
    """Erro de validação de dados"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class CRUDEngine:
    """
    Motor de CRUD dinâmico.
    Usa SchemaRegistry para determinar operações válidas.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.registry = SchemaRegistry()

    def _get_connection(self) -> sqlite3.Connection:
        """Cria conexão com o banco"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_schema(self, entity_name: str) -> EntitySchema:
        """Obtém schema de uma entidade"""
        schema = self.registry.get(entity_name)
        if not schema:
            raise ValueError(f"Entidade '{entity_name}' não encontrada no schema")
        return schema

    # ==================== LIST ====================

    def list(
        self,
        entity_name: str,
        page: int = 1,
        per_page: Optional[int] = None,
        search: Optional[str] = None,
        filters: Optional[Dict] = None,
        order_by: Optional[str] = None
    ) -> Dict:
        """
        Lista registros de uma entidade com paginação, busca e filtros.

        Returns:
            {
                "items": [...],
                "total": int,
                "page": int,
                "per_page": int,
                "pages": int,
                "has_next": bool,
                "has_prev": bool
            }
        """
        schema = self._get_schema(entity_name)
        per_page = per_page or schema.per_page
        order_by = order_by or schema.order_by

        # Construir query
        conditions = []
        params = []

        # Filtro de busca
        if search and schema.search_fields:
            search_conditions = []
            for field in schema.search_fields:
                search_conditions.append(f"{field} LIKE ?")
                params.append(f"%{search}%")
            conditions.append(f"({' OR '.join(search_conditions)})")

        # Filtros específicos
        if filters:
            for field, value in filters.items():
                if field in schema.fields and value not in (None, '', 'all'):
                    conditions.append(f"{field} = ?")
                    params.append(value)

        # Montar WHERE
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Query de contagem
        count_sql = f"SELECT COUNT(*) as total FROM {schema.table} {where_clause}"

        # Query de dados
        offset = (page - 1) * per_page
        data_sql = f"""
            SELECT * FROM {schema.table}
            {where_clause}
            ORDER BY {order_by}
            LIMIT ? OFFSET ?
        """

        # Executar com cache
        query_hash = QueryCache.hash_query(f"{count_sql}|{data_sql}", tuple(params))

        def execute():
            conn = self._get_connection()
            try:
                total = conn.execute(count_sql, params).fetchone()['total']
                items = conn.execute(data_sql, params + [per_page, offset]).fetchall()
                return {
                    "total": total,
                    "items": [dict(row) for row in items]
                }
            finally:
                conn.close()

        # Cache apenas para listagens públicas (não admin)
        # Verificar contexto de request antes de acessar g
        is_admin_request = False
        if has_request_context():
            is_admin_request = g.get('current_user') is not None

        if not is_admin_request:
            result = QueryCache.get_or_execute(entity_name, query_hash, execute, ttl=60)
        else:
            result = execute()

        pages = (result["total"] + per_page - 1) // per_page if result["total"] > 0 else 1

        return {
            "items": result["items"],
            "total": result["total"],
            "page": page,
            "per_page": per_page,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1
        }

    # ==================== READ ====================

    def read(self, entity_name: str, entity_id: Any) -> Optional[Dict]:
        """Obtém um registro específico"""
        schema = self._get_schema(entity_name)
        pk = schema.primary_key

        conn = self._get_connection()
        try:
            row = conn.execute(
                f"SELECT * FROM {schema.table} WHERE {pk} = ?",
                (entity_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # ==================== CREATE ====================

    def create(self, entity_name: str, data: Dict) -> Tuple[bool, Any, Optional[str]]:
        """
        Cria um novo registro.

        Returns:
            (success: bool, id_or_error: Any, message: Optional[str])
        """
        schema = self._get_schema(entity_name)

        try:
            # Validar e processar dados
            processed_data = self._validate_and_process(schema, data, is_create=True)

            # Construir INSERT
            fields = list(processed_data.keys())
            placeholders = ["?" for _ in fields]
            values = [processed_data[f] for f in fields]

            sql = f"""
                INSERT INTO {schema.table} ({', '.join(fields)})
                VALUES ({', '.join(placeholders)})
            """

            conn = self._get_connection()
            try:
                cursor = conn.execute(sql, values)
                conn.commit()
                new_id = cursor.lastrowid

                # Invalidar cache
                CacheManager.invalidate_entity(entity_name)

                # Auditoria
                AuthManager.audit_log(
                    action='create',
                    entity_type=entity_name,
                    entity_id=new_id,
                    new_value=processed_data
                )

                log_request(f"Registro criado: {entity_name}", entity_id=new_id)
                return True, new_id, None

            finally:
                conn.close()

        except ValidationError as e:
            return False, None, e.message
        except Exception as e:
            log_error(f"Erro ao criar {entity_name}", exception=e)
            return False, None, "Erro interno ao criar registro"

    # ==================== UPDATE ====================

    def update(self, entity_name: str, entity_id: Any, data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Atualiza um registro existente.

        Returns:
            (success: bool, error_message: Optional[str])
        """
        schema = self._get_schema(entity_name)
        pk = schema.primary_key

        try:
            # Buscar registro atual para auditoria
            old_record = self.read(entity_name, entity_id)
            if not old_record:
                return False, "Registro não encontrado"

            # Validar e processar dados
            processed_data = self._validate_and_process(schema, data, is_create=False)

            # Remover campos readonly
            for field_name in schema.readonly_fields:
                processed_data.pop(field_name, None)

            # Remover PK do update
            processed_data.pop(pk, None)

            if not processed_data:
                return False, "Nenhum campo para atualizar"

            # Construir UPDATE
            set_clauses = [f"{field} = ?" for field in processed_data.keys()]
            values = list(processed_data.values()) + [entity_id]

            sql = f"""
                UPDATE {schema.table}
                SET {', '.join(set_clauses)}
                WHERE {pk} = ?
            """

            conn = self._get_connection()
            try:
                conn.execute(sql, values)
                conn.commit()

                # Invalidar cache
                CacheManager.invalidate_entity(entity_name, entity_id)

                # Auditoria
                AuthManager.audit_log(
                    action='update',
                    entity_type=entity_name,
                    entity_id=entity_id,
                    old_value=old_record,
                    new_value=processed_data
                )

                log_request(f"Registro atualizado: {entity_name}", entity_id=entity_id)
                return True, None

            finally:
                conn.close()

        except ValidationError as e:
            return False, e.message
        except Exception as e:
            log_error(f"Erro ao atualizar {entity_name}", exception=e, entity_id=entity_id)
            return False, "Erro interno ao atualizar registro"

    # ==================== DELETE ====================

    def delete(self, entity_name: str, entity_id: Any) -> Tuple[bool, Optional[str]]:
        """
        Deleta um registro.
        Se soft_delete estiver ativo, marca como inativo.

        Returns:
            (success: bool, error_message: Optional[str])
        """
        schema = self._get_schema(entity_name)
        pk = schema.primary_key

        try:
            # Buscar registro para auditoria
            old_record = self.read(entity_name, entity_id)
            if not old_record:
                return False, "Registro não encontrado"

            conn = self._get_connection()
            try:
                if schema.soft_delete and 'ativo' in schema.fields:
                    # Soft delete
                    conn.execute(
                        f"UPDATE {schema.table} SET ativo = 0 WHERE {pk} = ?",
                        (entity_id,)
                    )
                else:
                    # Hard delete
                    conn.execute(
                        f"DELETE FROM {schema.table} WHERE {pk} = ?",
                        (entity_id,)
                    )

                conn.commit()

                # Invalidar cache
                CacheManager.invalidate_entity(entity_name, entity_id)

                # Auditoria
                AuthManager.audit_log(
                    action='delete',
                    entity_type=entity_name,
                    entity_id=entity_id,
                    old_value=old_record
                )

                log_request(f"Registro deletado: {entity_name}", entity_id=entity_id)
                return True, None

            finally:
                conn.close()

        except Exception as e:
            log_error(f"Erro ao deletar {entity_name}", exception=e, entity_id=entity_id)
            return False, "Erro interno ao deletar registro"

    # ==================== VALIDAÇÃO ====================

    def _validate_and_process(
        self,
        schema: EntitySchema,
        data: Dict,
        is_create: bool = True
    ) -> Dict:
        """
        Valida e processa dados de acordo com o schema.

        Args:
            schema: Schema da entidade
            data: Dados a validar
            is_create: Se é criação (valida required) ou update

        Returns:
            Dict com dados processados

        Raises:
            ValidationError se validação falhar
        """
        processed = {}

        for field_name, field_schema in schema.fields.items():
            value = data.get(field_name)

            # Pular campos não editáveis
            if not field_schema.editable and field_name != schema.primary_key:
                continue

            # Pular campos hidden no form
            if field_schema.field_type == FieldType.HIDDEN and not is_create:
                continue

            # Verificar required
            if field_schema.required and is_create:
                if value is None or (isinstance(value, str) and not value.strip()):
                    # Usar default se disponível
                    if field_schema.default is not None:
                        value = field_schema.default
                    else:
                        raise ValidationError(field_name, f"Campo '{field_schema.label}' é obrigatório")

            # Pular se não tem valor e não é required
            if value is None or value == '':
                if field_schema.default is not None and is_create:
                    processed[field_name] = field_schema.default
                continue

            # Processar por tipo
            processed_value = self._process_field(field_schema, value)
            processed[field_name] = processed_value

        return processed

    def _process_field(self, field: FieldSchema, value: Any) -> Any:
        """Processa e valida um campo individual"""

        # Processar por tipo
        if field.field_type == FieldType.TEXT:
            value = str(value).strip()
            if field.max_length and len(value) > field.max_length:
                raise ValidationError(field.name, f"Máximo {field.max_length} caracteres")
            if field.min_length and len(value) < field.min_length:
                raise ValidationError(field.name, f"Mínimo {field.min_length} caracteres")

        elif field.field_type == FieldType.TEXTAREA:
            value = str(value).strip()

        elif field.field_type == FieldType.RICHTEXT:
            value = str(value)  # Não strip para manter formatação

        elif field.field_type == FieldType.NUMBER:
            try:
                value = float(value)
                if field.min_value is not None and value < field.min_value:
                    raise ValidationError(field.name, f"Valor mínimo: {field.min_value}")
                if field.max_value is not None and value > field.max_value:
                    raise ValidationError(field.name, f"Valor máximo: {field.max_value}")
            except (ValueError, TypeError):
                raise ValidationError(field.name, "Deve ser um número válido")

        elif field.field_type == FieldType.EMAIL:
            value = str(value).strip().lower()
            if value and '@' not in value:
                raise ValidationError(field.name, "E-mail inválido")

        elif field.field_type == FieldType.PASSWORD:
            value = str(value)
            if field.min_length and len(value) < field.min_length:
                raise ValidationError(field.name, f"Senha deve ter no mínimo {field.min_length} caracteres")
            # Hash da senha
            value = generate_password_hash(value, method='pbkdf2:sha256')

        elif field.field_type == FieldType.SELECT:
            valid_values = [opt['value'] for opt in field.options]
            if value not in valid_values:
                raise ValidationError(field.name, "Opção inválida")

        elif field.field_type == FieldType.CHECKBOX:
            # Converter para 0/1 para SQLite
            if isinstance(value, str):
                value = 1 if value.lower() in ('true', '1', 'on', 'yes') else 0
            else:
                value = 1 if value else 0

        elif field.field_type == FieldType.TIME:
            # Validar formato HH:MM
            value = str(value).strip()
            if value:
                parts = value.split(':')
                if len(parts) < 2:
                    raise ValidationError(field.name, "Formato inválido. Use HH:MM")

        elif field.field_type == FieldType.DATE:
            value = str(value).strip()

        elif field.field_type == FieldType.DATETIME:
            value = str(value).strip()

        # Executar validadores customizados
        for validator in field.validators:
            try:
                result = validator(value)
                if result is not None:
                    value = result
            except Exception as e:
                raise ValidationError(field.name, str(e))

        return value

    # ==================== HELPERS ====================

    def get_form_context(self, entity_name: str, entity_id: Optional[Any] = None) -> Dict:
        """
        Retorna contexto para renderizar formulário.

        Returns:
            {
                "schema": EntitySchema,
                "record": dict or None,
                "is_edit": bool,
                "fields": [FieldSchema...]
            }
        """
        schema = self._get_schema(entity_name)
        record = self.read(entity_name, entity_id) if entity_id else None

        # Filtrar campos que aparecem no form
        form_fields = [
            f for f in schema.fields.values()
            if f.show_in_form
        ]

        return {
            "schema": schema,
            "record": record,
            "is_edit": record is not None,
            "fields": form_fields
        }

    def get_list_context(
        self,
        entity_name: str,
        page: int = 1,
        search: Optional[str] = None,
        filters: Optional[Dict] = None
    ) -> Dict:
        """
        Retorna contexto para renderizar listagem.

        Returns:
            {
                "schema": EntitySchema,
                "pagination": {...},
                "columns": [FieldSchema...],
                "filters": {...}
            }
        """
        schema = self._get_schema(entity_name)
        pagination = self.list(entity_name, page=page, search=search, filters=filters)

        # Campos da listagem
        list_fields = []
        for field_name in schema.list_display:
            if field_name in schema.fields:
                list_fields.append(schema.fields[field_name])

        # Campos filtráveis
        filter_fields = [
            schema.fields[f] for f in schema.filter_fields
            if f in schema.fields
        ]

        return {
            "schema": schema,
            "pagination": pagination,
            "columns": list_fields,
            "filter_fields": filter_fields,
            "current_filters": filters or {},
            "search": search or ""
        }

    def get_dashboard_stats(self) -> Dict:
        """Retorna estatísticas para o dashboard"""
        stats = {}
        conn = self._get_connection()

        try:
            for name, schema in self.registry.get_all().items():
                # Pular entidades internas
                if name in ('users', 'user_sessions', 'audit_log'):
                    continue

                count = conn.execute(
                    f"SELECT COUNT(*) as count FROM {schema.table}"
                ).fetchone()['count']

                stats[name] = {
                    "display_name": schema.display_name_plural,
                    "icon": schema.icon,
                    "count": count,
                    "url": f"/admin/crud/{name}"
                }
        finally:
            conn.close()

        return stats
