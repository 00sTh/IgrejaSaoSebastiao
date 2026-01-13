"""
Cache Manager - Igreja São Sebastião
Sistema de cache em memória com invalidação automática.
Em produção, considere usar Redis.
"""

import time
import hashlib
import json
from typing import Any, Optional, Dict, List, Callable
from functools import wraps
from threading import Lock
from middleware.logger import AppLogger, log_request


class CacheManager:
    """
    Gerenciador de cache em memória com TTL e invalidação.

    Estratégias:
    1. Cache por entidade com TTL configurável
    2. Invalidação automática no UPDATE/DELETE
    3. Cache de queries com hash da query como chave
    4. Sem cache para dados do admin (sempre fresh)
    """

    _instance = None
    _cache: Dict[str, Dict] = {}  # {key: {"value": ..., "expires": timestamp}}
    _lock = Lock()

    DEFAULT_TTL = 300  # 5 minutos

    # TTLs específicos por tipo
    TTL_CONFIG = {
        "entity": 300,        # 5 min para entidades
        "query": 60,          # 1 min para queries
        "config": 600,        # 10 min para configs (mudam pouco)
        "static": 3600,       # 1 hora para dados estáticos
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def _generate_key(cls, prefix: str, *args, **kwargs) -> str:
        """Gera chave única para cache"""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()

    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """Obtém valor do cache"""
        with cls._lock:
            if key in cls._cache:
                entry = cls._cache[key]
                if entry["expires"] > time.time():
                    return entry["value"]
                else:
                    # Expirado, remover
                    del cls._cache[key]
            return None

    @classmethod
    def set(cls, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Define valor no cache"""
        if ttl is None:
            ttl = cls.DEFAULT_TTL

        with cls._lock:
            cls._cache[key] = {
                "value": value,
                "expires": time.time() + ttl
            }

    @classmethod
    def delete(cls, key: str) -> bool:
        """Remove item do cache"""
        with cls._lock:
            if key in cls._cache:
                del cls._cache[key]
                return True
            return False

    @classmethod
    def invalidate_entity(cls, entity_name: str, entity_id: Optional[int] = None) -> int:
        """
        Invalida cache de uma entidade.
        Se entity_id for None, invalida todos os registros da entidade.
        """
        count = 0
        prefix = f"entity:{entity_name}"

        with cls._lock:
            keys_to_delete = []
            for key in cls._cache.keys():
                if key.startswith(prefix):
                    if entity_id is None or f":{entity_id}" in key:
                        keys_to_delete.append(key)

            for key in keys_to_delete:
                del cls._cache[key]
                count += 1

        # Também invalidar queries relacionadas
        cls.invalidate_queries(entity_name)

        if count > 0:
            log_request(f"Cache invalidado: {entity_name}", level="debug",
                       entity_id=entity_id, items_removed=count)

        return count

    @classmethod
    def invalidate_queries(cls, entity_name: str) -> int:
        """Invalida todas as queries cacheadas de uma entidade"""
        count = 0
        prefix = f"query:{entity_name}"

        with cls._lock:
            keys_to_delete = [k for k in cls._cache.keys() if k.startswith(prefix)]
            for key in keys_to_delete:
                del cls._cache[key]
                count += 1

        return count

    @classmethod
    def invalidate_all(cls) -> int:
        """Limpa todo o cache"""
        with cls._lock:
            count = len(cls._cache)
            cls._cache.clear()

        log_request("Cache completamente limpo", level="info", items_removed=count)
        return count

    @classmethod
    def get_stats(cls) -> Dict:
        """Retorna estatísticas do cache"""
        with cls._lock:
            now = time.time()
            total = len(cls._cache)
            expired = sum(1 for v in cls._cache.values() if v["expires"] <= now)
            valid = total - expired

            # Agrupar por prefixo
            by_type = {}
            for key in cls._cache.keys():
                prefix = key.split(":")[0] if ":" in key else "other"
                by_type[prefix] = by_type.get(prefix, 0) + 1

            return {
                "total_entries": total,
                "valid_entries": valid,
                "expired_entries": expired,
                "by_type": by_type
            }

    @classmethod
    def cleanup_expired(cls) -> int:
        """Remove entradas expiradas"""
        count = 0
        now = time.time()

        with cls._lock:
            keys_to_delete = [
                k for k, v in cls._cache.items()
                if v["expires"] <= now
            ]
            for key in keys_to_delete:
                del cls._cache[key]
                count += 1

        return count


def cached(prefix: str, ttl: Optional[int] = None):
    """
    Decorator para cachear resultado de função.

    Uso:
        @cached("entity:noticias", ttl=300)
        def get_noticias():
            return db.query(...)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gerar chave baseada nos argumentos
            cache_key = f"{prefix}:{CacheManager._generate_key(func.__name__, *args, **kwargs)}"

            # Tentar obter do cache
            cached_value = CacheManager.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Executar função e cachear resultado
            result = func(*args, **kwargs)
            CacheManager.set(cache_key, result, ttl or CacheManager.TTL_CONFIG.get(prefix.split(":")[0], CacheManager.DEFAULT_TTL))

            return result
        return wrapper
    return decorator


def invalidate_on_change(entity_name: str):
    """
    Decorator que invalida cache após execução da função.
    Usar em funções de CREATE/UPDATE/DELETE.

    Uso:
        @invalidate_on_change("noticias")
        def create_noticia(data):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Extrair entity_id se possível
            entity_id = kwargs.get('id') or kwargs.get('entity_id')
            if not entity_id and args:
                # Tentar pegar do primeiro argumento se for int
                if isinstance(args[0], int):
                    entity_id = args[0]

            CacheManager.invalidate_entity(entity_name, entity_id)
            return result
        return wrapper
    return decorator


class QueryCache:
    """
    Helper para cachear queries do banco de dados.
    """

    @staticmethod
    def get_or_execute(entity_name: str, query_hash: str, executor: Callable, ttl: int = 60) -> Any:
        """
        Obtém resultado do cache ou executa query.

        Args:
            entity_name: Nome da entidade
            query_hash: Hash único da query
            executor: Função que executa a query
            ttl: Tempo de vida em segundos
        """
        cache_key = f"query:{entity_name}:{query_hash}"

        cached = CacheManager.get(cache_key)
        if cached is not None:
            return cached

        result = executor()
        CacheManager.set(cache_key, result, ttl)
        return result

    @staticmethod
    def hash_query(sql: str, params: tuple = ()) -> str:
        """Gera hash de uma query SQL com parâmetros"""
        data = f"{sql}:{params}"
        return hashlib.md5(data.encode()).hexdigest()[:16]
