"""
Schema Registry - Igreja São Sebastião
Define metadados de cada entidade do sistema.
O schema dita como o painel administrativo funciona.
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field


class FieldType(Enum):
    """Tipos de campos suportados"""
    TEXT = "text"              # Input text simples
    TEXTAREA = "textarea"      # Textarea multilinha
    RICHTEXT = "richtext"      # Editor WYSIWYG
    NUMBER = "number"          # Input numérico
    EMAIL = "email"            # Input email
    PASSWORD = "password"      # Input senha
    DATE = "date"              # Date picker
    DATETIME = "datetime"      # DateTime picker
    TIME = "time"              # Time picker
    SELECT = "select"          # Dropdown
    MULTISELECT = "multiselect"  # Multi-select
    CHECKBOX = "checkbox"      # Checkbox boolean
    IMAGE = "image"            # Upload de imagem
    FILE = "file"              # Upload de arquivo
    HIDDEN = "hidden"          # Campo oculto
    READONLY = "readonly"      # Apenas leitura


@dataclass
class FieldSchema:
    """Definição de um campo"""
    name: str
    field_type: FieldType
    label: str
    required: bool = False
    default: Any = None
    placeholder: str = ""
    help_text: str = ""
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    options: List[Dict[str, str]] = field(default_factory=list)  # Para SELECT
    validators: List[Callable] = field(default_factory=list)
    searchable: bool = False
    sortable: bool = True
    filterable: bool = False
    show_in_list: bool = True
    show_in_form: bool = True
    editable: bool = True
    column_width: str = "auto"  # CSS width


@dataclass
class EntitySchema:
    """Definição completa de uma entidade"""
    name: str                    # Nome interno (ex: "noticias")
    table: str                   # Nome da tabela no banco
    display_name: str            # Nome para exibição (ex: "Notícias")
    display_name_plural: str     # Plural (ex: "Notícias")
    icon: str                    # Ícone FontAwesome
    fields: Dict[str, FieldSchema]
    primary_key: str = "id"
    order_by: str = "id DESC"
    list_display: List[str] = field(default_factory=list)  # Campos na listagem
    search_fields: List[str] = field(default_factory=list)  # Campos pesquisáveis
    filter_fields: List[str] = field(default_factory=list)  # Campos filtráveis
    readonly_fields: List[str] = field(default_factory=list)
    permissions: Dict[str, str] = field(default_factory=dict)  # action: permission
    soft_delete: bool = False    # Usar campo 'ativo' ao invés de DELETE
    timestamps: bool = True      # Tem created_at/updated_at
    per_page: int = 20           # Itens por página
    export_fields: List[str] = field(default_factory=list)


class SchemaRegistry:
    """
    Registro central de schemas de entidades.
    Singleton que mantém todos os schemas do sistema.
    """

    _instance = None
    _schemas: Dict[str, EntitySchema] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_default_schemas()
        return cls._instance

    def _init_default_schemas(self):
        """Inicializa schemas padrão do sistema"""

        # ==================== NOTÍCIAS ====================
        self.register(EntitySchema(
            name="noticias",
            table="noticias",
            display_name="Notícia",
            display_name_plural="Notícias",
            icon="fas fa-newspaper",
            primary_key="id",
            order_by="data_criacao DESC",
            list_display=["titulo", "tipo", "data_criacao"],
            search_fields=["titulo", "conteudo", "subtitulo"],
            filter_fields=["tipo"],
            permissions={
                "list": "noticias:read",
                "create": "noticias:create",
                "read": "noticias:read",
                "update": "noticias:update",
                "delete": "noticias:delete"
            },
            fields={
                "id": FieldSchema(
                    name="id",
                    field_type=FieldType.HIDDEN,
                    label="ID",
                    show_in_list=True,
                    show_in_form=False,
                    editable=False,
                    column_width="60px"
                ),
                "titulo": FieldSchema(
                    name="titulo",
                    field_type=FieldType.TEXT,
                    label="Título",
                    required=True,
                    max_length=200,
                    placeholder="Digite o título da notícia",
                    searchable=True,
                    column_width="300px"
                ),
                "subtitulo": FieldSchema(
                    name="subtitulo",
                    field_type=FieldType.TEXT,
                    label="Subtítulo",
                    required=False,
                    max_length=300,
                    placeholder="Subtítulo opcional",
                    show_in_list=False
                ),
                "conteudo": FieldSchema(
                    name="conteudo",
                    field_type=FieldType.RICHTEXT,
                    label="Conteúdo",
                    required=True,
                    placeholder="Digite o conteúdo completo",
                    searchable=True,
                    show_in_list=False
                ),
                "imagem_url": FieldSchema(
                    name="imagem_url",
                    field_type=FieldType.IMAGE,
                    label="Imagem",
                    required=False,
                    help_text="Formatos: JPG, PNG, WebP. Máx: 5MB",
                    show_in_list=False
                ),
                "tipo": FieldSchema(
                    name="tipo",
                    field_type=FieldType.SELECT,
                    label="Tipo",
                    required=True,
                    default="Notícia",
                    options=[
                        {"value": "Notícia", "label": "Notícia"},
                        {"value": "Evento", "label": "Evento"},
                        {"value": "Aviso", "label": "Aviso"},
                        {"value": "Comunicado", "label": "Comunicado"}
                    ],
                    filterable=True,
                    column_width="120px"
                ),
                "data_criacao": FieldSchema(
                    name="data_criacao",
                    field_type=FieldType.DATETIME,
                    label="Data de Criação",
                    editable=False,
                    show_in_form=False,
                    column_width="150px"
                )
            }
        ))

        # ==================== HORÁRIOS DE MISSAS ====================
        self.register(EntitySchema(
            name="horarios_missas",
            table="horarios_missas",
            display_name="Horário de Missa",
            display_name_plural="Horários de Missas",
            icon="fas fa-clock",
            primary_key="id",
            order_by="id ASC",
            list_display=["dia_semana", "horario", "tipo", "ativo"],
            search_fields=["dia_semana", "tipo"],
            filter_fields=["dia_semana", "ativo"],
            soft_delete=False,
            permissions={
                "list": "horarios:read",
                "create": "horarios:create",
                "read": "horarios:read",
                "update": "horarios:update",
                "delete": "horarios:delete"
            },
            fields={
                "id": FieldSchema(
                    name="id",
                    field_type=FieldType.HIDDEN,
                    label="ID",
                    show_in_list=True,
                    show_in_form=False,
                    editable=False,
                    column_width="60px"
                ),
                "dia_semana": FieldSchema(
                    name="dia_semana",
                    field_type=FieldType.SELECT,
                    label="Dia da Semana",
                    required=True,
                    options=[
                        {"value": "Segunda-feira", "label": "Segunda-feira"},
                        {"value": "Terça-feira", "label": "Terça-feira"},
                        {"value": "Quarta-feira", "label": "Quarta-feira"},
                        {"value": "Quinta-feira", "label": "Quinta-feira"},
                        {"value": "Sexta-feira", "label": "Sexta-feira"},
                        {"value": "Sábado", "label": "Sábado"},
                        {"value": "Domingo", "label": "Domingo"}
                    ],
                    filterable=True,
                    column_width="150px"
                ),
                "horario": FieldSchema(
                    name="horario",
                    field_type=FieldType.TIME,
                    label="Horário",
                    required=True,
                    placeholder="HH:MM",
                    column_width="100px"
                ),
                "tipo": FieldSchema(
                    name="tipo",
                    field_type=FieldType.SELECT,
                    label="Tipo",
                    required=False,
                    default="Missa",
                    options=[
                        {"value": "Missa", "label": "Missa"},
                        {"value": "Missa Solene", "label": "Missa Solene"},
                        {"value": "Adoração", "label": "Adoração"},
                        {"value": "Confissão", "label": "Confissão"},
                        {"value": "Terço", "label": "Terço"}
                    ],
                    column_width="120px"
                ),
                "ativo": FieldSchema(
                    name="ativo",
                    field_type=FieldType.CHECKBOX,
                    label="Ativo",
                    default=True,
                    help_text="Desmarque para ocultar este horário do site",
                    filterable=True,
                    column_width="80px"
                )
            }
        ))

        # ==================== GALERIA ====================
        self.register(EntitySchema(
            name="galeria",
            table="galeria",
            display_name="Foto",
            display_name_plural="Galeria de Fotos",
            icon="fas fa-images",
            primary_key="id",
            order_by="data_upload DESC",
            list_display=["titulo", "categoria", "imagem_url", "data_upload", "ativo"],
            search_fields=["titulo", "descricao", "categoria"],
            filter_fields=["ativo", "categoria"],
            soft_delete=True,
            permissions={
                "list": "galeria:read",
                "create": "galeria:create",
                "read": "galeria:read",
                "update": "galeria:update",
                "delete": "galeria:delete"
            },
            fields={
                "id": FieldSchema(
                    name="id",
                    field_type=FieldType.HIDDEN,
                    label="ID",
                    show_in_list=True,
                    show_in_form=False,
                    editable=False,
                    column_width="60px"
                ),
                "titulo": FieldSchema(
                    name="titulo",
                    field_type=FieldType.TEXT,
                    label="Título",
                    required=True,
                    max_length=150,
                    placeholder="Título da foto",
                    searchable=True,
                    column_width="250px"
                ),
                "descricao": FieldSchema(
                    name="descricao",
                    field_type=FieldType.TEXTAREA,
                    label="Descrição",
                    required=False,
                    placeholder="Descrição opcional",
                    show_in_list=False
                ),
                "categoria": FieldSchema(
                    name="categoria",
                    field_type=FieldType.SELECT,
                    label="Categoria",
                    required=False,
                    options=[
                        {"value": "", "label": "Sem categoria"},
                        {"value": "Igreja", "label": "Igreja"},
                        {"value": "Eventos", "label": "Eventos"},
                        {"value": "Comunidade", "label": "Comunidade"},
                        {"value": "Celebrações", "label": "Celebrações"},
                        {"value": "Outros", "label": "Outros"}
                    ],
                    filterable=True,
                    column_width="120px"
                ),
                "imagem_url": FieldSchema(
                    name="imagem_url",
                    field_type=FieldType.IMAGE,
                    label="Imagem",
                    required=True,
                    help_text="Formatos: JPG, PNG, WebP. Máx: 5MB",
                    column_width="100px"
                ),
                "data_upload": FieldSchema(
                    name="data_upload",
                    field_type=FieldType.DATETIME,
                    label="Data Upload",
                    editable=False,
                    show_in_form=False,
                    column_width="150px"
                ),
                "ativo": FieldSchema(
                    name="ativo",
                    field_type=FieldType.CHECKBOX,
                    label="Ativo",
                    default=True,
                    filterable=True,
                    column_width="80px"
                )
            }
        ))

        # ==================== CONTATOS ====================
        self.register(EntitySchema(
            name="contatos",
            table="contatos",
            display_name="Contato",
            display_name_plural="Contatos",
            icon="fas fa-address-book",
            primary_key="id",
            order_by="ordem ASC",
            list_display=["tipo", "valor", "icone", "ordem"],
            search_fields=["tipo", "valor"],
            permissions={
                "list": "config:read",
                "create": "config:update",
                "read": "config:read",
                "update": "config:update",
                "delete": "config:update"
            },
            fields={
                "id": FieldSchema(
                    name="id",
                    field_type=FieldType.HIDDEN,
                    label="ID",
                    show_in_list=False,
                    show_in_form=False,
                    editable=False
                ),
                "tipo": FieldSchema(
                    name="tipo",
                    field_type=FieldType.SELECT,
                    label="Tipo",
                    required=True,
                    options=[
                        {"value": "telefone", "label": "Telefone"},
                        {"value": "email", "label": "E-mail"},
                        {"value": "endereco", "label": "Endereço"},
                        {"value": "whatsapp", "label": "WhatsApp"},
                        {"value": "instagram", "label": "Instagram"},
                        {"value": "facebook", "label": "Facebook"}
                    ],
                    column_width="120px"
                ),
                "valor": FieldSchema(
                    name="valor",
                    field_type=FieldType.TEXT,
                    label="Valor",
                    required=True,
                    max_length=200,
                    placeholder="Ex: (31) 99999-9999",
                    column_width="250px"
                ),
                "icone": FieldSchema(
                    name="icone",
                    field_type=FieldType.TEXT,
                    label="Ícone",
                    required=False,
                    placeholder="fas fa-phone",
                    help_text="Classe do FontAwesome",
                    column_width="150px"
                ),
                "ordem": FieldSchema(
                    name="ordem",
                    field_type=FieldType.NUMBER,
                    label="Ordem",
                    default=0,
                    min_value=0,
                    column_width="80px"
                )
            }
        ))

        # ==================== CONFIGURAÇÕES ====================
        self.register(EntitySchema(
            name="configuracoes",
            table="configuracoes",
            display_name="Configuração",
            display_name_plural="Configurações",
            icon="fas fa-cog",
            primary_key="chave",
            order_by="chave ASC",
            list_display=["chave", "valor", "descricao"],
            search_fields=["chave", "valor", "descricao"],
            readonly_fields=["chave"],
            permissions={
                "list": "config:read",
                "read": "config:read",
                "update": "config:update"
            },
            fields={
                "chave": FieldSchema(
                    name="chave",
                    field_type=FieldType.READONLY,
                    label="Chave",
                    editable=False,
                    column_width="200px"
                ),
                "valor": FieldSchema(
                    name="valor",
                    field_type=FieldType.TEXT,
                    label="Valor",
                    required=True,
                    column_width="300px"
                ),
                "descricao": FieldSchema(
                    name="descricao",
                    field_type=FieldType.TEXT,
                    label="Descrição",
                    editable=False,
                    column_width="250px"
                )
            }
        ))

        # ==================== PAROQUIA INFO ====================
        self.register(EntitySchema(
            name="paroquia_info",
            table="paroquia_info",
            display_name="Informação da Paróquia",
            display_name_plural="Informações da Paróquia",
            icon="fas fa-church",
            primary_key="id",
            order_by="ordem ASC",
            list_display=["secao", "titulo", "ordem"],
            search_fields=["secao", "titulo", "conteudo"],
            readonly_fields=["secao"],
            permissions={
                "list": "config:read",
                "read": "config:read",
                "update": "config:update"
            },
            fields={
                "id": FieldSchema(
                    name="id",
                    field_type=FieldType.HIDDEN,
                    label="ID",
                    show_in_list=False,
                    show_in_form=False,
                    editable=False
                ),
                "secao": FieldSchema(
                    name="secao",
                    field_type=FieldType.READONLY,
                    label="Seção",
                    editable=False,
                    column_width="200px"
                ),
                "titulo": FieldSchema(
                    name="titulo",
                    field_type=FieldType.TEXT,
                    label="Valor",
                    required=True,
                    column_width="300px"
                ),
                "conteudo": FieldSchema(
                    name="conteudo",
                    field_type=FieldType.TEXTAREA,
                    label="Descrição",
                    required=False,
                    show_in_list=False
                ),
                "ordem": FieldSchema(
                    name="ordem",
                    field_type=FieldType.NUMBER,
                    label="Ordem",
                    default=0,
                    column_width="80px"
                )
            }
        ))

        # ==================== USUÁRIOS ====================
        self.register(EntitySchema(
            name="users",
            table="users",
            display_name="Usuário",
            display_name_plural="Usuários",
            icon="fas fa-users",
            primary_key="id",
            order_by="username ASC",
            list_display=["username", "email", "role", "is_active", "last_login"],
            search_fields=["username", "email"],
            filter_fields=["role", "is_active"],
            permissions={
                "list": "users:read",
                "create": "users:create",
                "read": "users:read",
                "update": "users:update",
                "delete": "users:delete"
            },
            fields={
                "id": FieldSchema(
                    name="id",
                    field_type=FieldType.HIDDEN,
                    label="ID",
                    show_in_list=True,
                    show_in_form=False,
                    editable=False,
                    column_width="60px"
                ),
                "username": FieldSchema(
                    name="username",
                    field_type=FieldType.TEXT,
                    label="Usuário",
                    required=True,
                    max_length=50,
                    placeholder="Nome de usuário",
                    column_width="150px"
                ),
                "email": FieldSchema(
                    name="email",
                    field_type=FieldType.EMAIL,
                    label="E-mail",
                    required=False,
                    max_length=100,
                    column_width="200px"
                ),
                "password": FieldSchema(
                    name="password",
                    field_type=FieldType.PASSWORD,
                    label="Senha",
                    required=True,
                    min_length=8,
                    help_text="Mínimo 8 caracteres",
                    show_in_list=False
                ),
                "role": FieldSchema(
                    name="role",
                    field_type=FieldType.SELECT,
                    label="Perfil",
                    required=True,
                    default="viewer",
                    options=[
                        {"value": "super_admin", "label": "Super Admin"},
                        {"value": "admin", "label": "Administrador"},
                        {"value": "editor", "label": "Editor"},
                        {"value": "viewer", "label": "Visualizador"}
                    ],
                    filterable=True,
                    column_width="130px"
                ),
                "is_active": FieldSchema(
                    name="is_active",
                    field_type=FieldType.CHECKBOX,
                    label="Ativo",
                    default=True,
                    filterable=True,
                    column_width="80px"
                ),
                "last_login": FieldSchema(
                    name="last_login",
                    field_type=FieldType.DATETIME,
                    label="Último Login",
                    editable=False,
                    show_in_form=False,
                    column_width="150px"
                ),
                "created_at": FieldSchema(
                    name="created_at",
                    field_type=FieldType.DATETIME,
                    label="Criado em",
                    editable=False,
                    show_in_form=False,
                    show_in_list=False
                )
            }
        ))

    def register(self, schema: EntitySchema):
        """Registra um schema de entidade"""
        self._schemas[schema.name] = schema

    def get(self, name: str) -> Optional[EntitySchema]:
        """Obtém schema por nome"""
        return self._schemas.get(name)

    def get_all(self) -> Dict[str, EntitySchema]:
        """Retorna todos os schemas"""
        return self._schemas.copy()

    def get_menu_items(self) -> List[Dict]:
        """Retorna itens para menu do admin"""
        items = []
        for name, schema in self._schemas.items():
            items.append({
                "name": name,
                "display_name": schema.display_name_plural,
                "icon": schema.icon,
                "url": f"/admin/crud/{name}"
            })
        return items
