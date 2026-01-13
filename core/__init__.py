"""
Core Package - Igreja São Sebastião
Motor de CRUD Dinâmico baseado em Schema
Pipeline de Mídia para processamento de imagens
"""

from core.schema import SchemaRegistry, FieldType
from core.cache import CacheManager
from core.crud import CRUDEngine
from core.media import MediaPipeline, get_media_pipeline, process_upload, ImageSize

__all__ = [
    'SchemaRegistry',
    'FieldType',
    'CacheManager',
    'CRUDEngine',
    'MediaPipeline',
    'get_media_pipeline',
    'process_upload',
    'ImageSize'
]
