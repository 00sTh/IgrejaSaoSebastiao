"""
Rotas do CRUD Dinâmico - Igreja São Sebastião
Blueprint que registra rotas automaticamente para todas as entidades.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g, abort
from core.crud import CRUDEngine
from core.schema import SchemaRegistry, FieldType
from core.cache import CacheManager
from middleware.auth import login_required, permission_required, AuthManager
from middleware.logger import log_request
from config import Config

# Criar Blueprint
crud_bp = Blueprint('crud', __name__, url_prefix='/admin/crud')

# Engine global (inicializado no setup)
_engine: CRUDEngine = None


def init_crud_routes(app):
    """Inicializa o CRUD engine e registra o blueprint"""
    global _engine
    _engine = CRUDEngine(Config.DATABASE_PATH)

    # Registrar blueprint
    app.register_blueprint(crud_bp)

    # Injetar menu no contexto global
    @app.context_processor
    def inject_crud_menu():
        registry = SchemaRegistry()
        menu_items = []

        # Agrupar por categoria
        categories = {
            "Conteúdo": ["noticias", "galeria"],
            "Configurações": ["horarios_missas", "paroquia_info", "contatos", "configuracoes"],
            "Sistema": ["users"]
        }

        for category, entities in categories.items():
            items = []
            for entity_name in entities:
                schema = registry.get(entity_name)
                if schema:
                    # Verificar permissão de leitura
                    perm = schema.permissions.get('list', f'{entity_name}:read')
                    has_access = AuthManager.has_permission(perm) if g.get('current_user') else False

                    items.append({
                        "name": entity_name,
                        "display_name": schema.display_name_plural,
                        "icon": schema.icon,
                        "url": url_for('crud.crud_list', entity_name=entity_name),
                        "has_access": has_access
                    })

            if items:
                menu_items.append({
                    "category": category,
                    "items": items
                })

        return {"crud_menu": menu_items}

    log_request("CRUD Routes inicializadas", level="info")


def get_engine() -> CRUDEngine:
    """Obtém instância do engine"""
    if _engine is None:
        raise RuntimeError("CRUD Engine não inicializado. Chame init_crud_routes primeiro.")
    return _engine


# ==================== ROTAS ====================

@crud_bp.route('/<entity_name>')
@login_required
def crud_list(entity_name: str):
    """Lista registros de uma entidade"""
    engine = get_engine()
    registry = SchemaRegistry()

    schema = registry.get(entity_name)
    if not schema:
        abort(404)

    # Verificar permissão
    perm = schema.permissions.get('list', f'{entity_name}:read')
    if not AuthManager.has_permission(perm):
        abort(403)

    # Parâmetros de listagem
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    filters = {}

    # Coletar filtros
    for field_name in schema.filter_fields:
        filter_value = request.args.get(f'filter_{field_name}')
        if filter_value and filter_value != 'all':
            filters[field_name] = filter_value

    # Obter contexto
    context = engine.get_list_context(entity_name, page=page, search=search, filters=filters)

    # Verificar permissões de ações
    context['can_create'] = AuthManager.has_permission(
        schema.permissions.get('create', f'{entity_name}:create')
    )
    context['can_update'] = AuthManager.has_permission(
        schema.permissions.get('update', f'{entity_name}:update')
    )
    context['can_delete'] = AuthManager.has_permission(
        schema.permissions.get('delete', f'{entity_name}:delete')
    )
    context['entity_name'] = entity_name

    return render_template('crud/list.html', **context)


@crud_bp.route('/<entity_name>/new', methods=['GET', 'POST'])
@login_required
def crud_create(entity_name: str):
    """Cria novo registro"""
    engine = get_engine()
    registry = SchemaRegistry()

    schema = registry.get(entity_name)
    if not schema:
        abort(404)

    # Verificar permissão
    perm = schema.permissions.get('create', f'{entity_name}:create')
    if not AuthManager.has_permission(perm):
        abort(403)

    if request.method == 'POST':
        # Coletar dados do formulário
        data = {}
        for field_name, field_schema in schema.fields.items():
            if field_schema.show_in_form and field_schema.editable:
                if field_schema.field_type == FieldType.IMAGE:
                    # Processar upload
                    if field_name in request.files:
                        file = request.files[field_name]
                        if file and file.filename:
                            from app import save_uploaded_file
                            data[field_name] = save_uploaded_file(file)
                elif field_schema.field_type == FieldType.CHECKBOX:
                    data[field_name] = field_name in request.form
                else:
                    data[field_name] = request.form.get(field_name)

        success, result, error = engine.create(entity_name, data)

        if success:
            flash(f'{schema.display_name} criado com sucesso!', 'success')
            return redirect(url_for('crud.crud_list', entity_name=entity_name))
        else:
            flash(f'Erro: {error}', 'error')

    # GET ou erro no POST
    context = engine.get_form_context(entity_name)
    context['entity_name'] = entity_name
    context['action_url'] = url_for('crud.crud_create', entity_name=entity_name)
    context['FieldType'] = FieldType

    return render_template('crud/form.html', **context)


@crud_bp.route('/<entity_name>/<entity_id>/edit', methods=['GET', 'POST'])
@login_required
def crud_edit(entity_name: str, entity_id):
    """Edita registro existente"""
    engine = get_engine()
    registry = SchemaRegistry()

    schema = registry.get(entity_name)
    if not schema:
        abort(404)

    # Verificar permissão
    perm = schema.permissions.get('update', f'{entity_name}:update')
    if not AuthManager.has_permission(perm):
        abort(403)

    # Converter ID se necessário
    if schema.primary_key == 'id':
        try:
            entity_id = int(entity_id)
        except ValueError:
            abort(404)

    if request.method == 'POST':
        # Coletar dados do formulário
        data = {}
        for field_name, field_schema in schema.fields.items():
            if field_schema.show_in_form and field_schema.editable:
                if field_schema.field_type == FieldType.IMAGE:
                    # Processar upload
                    if field_name in request.files:
                        file = request.files[field_name]
                        if file and file.filename:
                            from app import save_uploaded_file
                            data[field_name] = save_uploaded_file(file)
                elif field_schema.field_type == FieldType.CHECKBOX:
                    data[field_name] = field_name in request.form
                elif field_schema.field_type == FieldType.PASSWORD:
                    # Só atualiza senha se foi preenchida
                    value = request.form.get(field_name)
                    if value and value.strip():
                        data[field_name] = value
                else:
                    data[field_name] = request.form.get(field_name)

        success, error = engine.update(entity_name, entity_id, data)

        if success:
            flash(f'{schema.display_name} atualizado com sucesso!', 'success')
            return redirect(url_for('crud.crud_list', entity_name=entity_name))
        else:
            flash(f'Erro: {error}', 'error')

    # GET ou erro no POST
    context = engine.get_form_context(entity_name, entity_id)
    if not context['record']:
        abort(404)

    context['entity_name'] = entity_name
    context['action_url'] = url_for('crud.crud_edit', entity_name=entity_name, entity_id=entity_id)
    context['FieldType'] = FieldType

    return render_template('crud/form.html', **context)


@crud_bp.route('/<entity_name>/<entity_id>/delete', methods=['POST'])
@login_required
def crud_delete(entity_name: str, entity_id):
    """Deleta registro"""
    engine = get_engine()
    registry = SchemaRegistry()

    schema = registry.get(entity_name)
    if not schema:
        abort(404)

    # Verificar permissão
    perm = schema.permissions.get('delete', f'{entity_name}:delete')
    if not AuthManager.has_permission(perm):
        abort(403)

    # Converter ID se necessário
    if schema.primary_key == 'id':
        try:
            entity_id = int(entity_id)
        except ValueError:
            abort(404)

    success, error = engine.delete(entity_name, entity_id)

    if success:
        flash(f'{schema.display_name} deletado com sucesso!', 'success')
    else:
        flash(f'Erro ao deletar: {error}', 'error')

    return redirect(url_for('crud.crud_list', entity_name=entity_name))


# ==================== API JSON ====================

@crud_bp.route('/api/<entity_name>')
@login_required
def api_list(entity_name: str):
    """API: Lista registros em JSON"""
    engine = get_engine()
    registry = SchemaRegistry()

    schema = registry.get(entity_name)
    if not schema:
        return jsonify({"error": "Entidade não encontrada"}), 404

    perm = schema.permissions.get('list', f'{entity_name}:read')
    if not AuthManager.has_permission(perm):
        return jsonify({"error": "Acesso negado"}), 403

    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    per_page = request.args.get('per_page', schema.per_page, type=int)

    result = engine.list(entity_name, page=page, search=search, per_page=per_page)
    return jsonify(result)


@crud_bp.route('/api/<entity_name>/<entity_id>')
@login_required
def api_read(entity_name: str, entity_id):
    """API: Lê registro em JSON"""
    engine = get_engine()
    registry = SchemaRegistry()

    schema = registry.get(entity_name)
    if not schema:
        return jsonify({"error": "Entidade não encontrada"}), 404

    perm = schema.permissions.get('read', f'{entity_name}:read')
    if not AuthManager.has_permission(perm):
        return jsonify({"error": "Acesso negado"}), 403

    record = engine.read(entity_name, entity_id)
    if not record:
        return jsonify({"error": "Registro não encontrado"}), 404

    return jsonify(record)


@crud_bp.route('/api/cache/stats')
@login_required
def api_cache_stats():
    """API: Estatísticas do cache"""
    if not AuthManager.has_permission('config:read'):
        return jsonify({"error": "Acesso negado"}), 403

    return jsonify(CacheManager.get_stats())


@crud_bp.route('/api/cache/clear', methods=['POST'])
@login_required
def api_cache_clear():
    """API: Limpa cache"""
    if not AuthManager.has_permission('config:update'):
        return jsonify({"error": "Acesso negado"}), 403

    count = CacheManager.invalidate_all()
    return jsonify({"success": True, "items_cleared": count})


# ==================== MEDIA API ====================

@crud_bp.route('/api/media/upload', methods=['POST'])
@login_required
def api_media_upload():
    """
    API: Upload de imagem com processamento automático.

    Retorna URLs de todas as variantes processadas.
    """
    from core.media import get_media_pipeline, MediaValidationError

    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files['file']
    convert_to_webp = request.form.get('webp', 'true').lower() == 'true'

    try:
        pipeline = get_media_pipeline()
        result = pipeline.process(file, convert_to_webp=convert_to_webp)

        return jsonify({
            "success": True,
            "data": {
                "original_name": result.original_name,
                "stored_name": result.stored_name,
                "primary_url": result.primary_url,
                "thumb_url": result.thumb_url,
                "variants": {
                    k: {"url": v.url, "width": v.width, "height": v.height, "size": v.file_size}
                    for k, v in result.variants.items()
                }
            }
        })

    except MediaValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        log_request("Erro no upload", level="error", error=str(e))
        return jsonify({"error": "Erro ao processar imagem"}), 500


@crud_bp.route('/api/media/delete', methods=['POST'])
@login_required
def api_media_delete():
    """API: Deleta imagem e todas as variantes"""
    from core.media import get_media_pipeline

    if not AuthManager.has_permission('galeria:delete'):
        return jsonify({"error": "Acesso negado"}), 403

    data = request.get_json()
    stored_name = data.get('stored_name')

    if not stored_name:
        return jsonify({"error": "stored_name é obrigatório"}), 400

    pipeline = get_media_pipeline()
    deleted = pipeline.delete_image(stored_name)

    return jsonify({
        "success": True,
        "files_deleted": deleted
    })


@crud_bp.route('/api/media/stats')
@login_required
def api_media_stats():
    """API: Estatísticas de uso de armazenamento"""
    from core.media import get_media_pipeline

    if not AuthManager.has_permission('config:read'):
        return jsonify({"error": "Acesso negado"}), 403

    pipeline = get_media_pipeline()
    stats = pipeline.get_stats()

    return jsonify(stats)
