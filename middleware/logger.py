"""
Sistema de Logging Estruturado - Igreja São Sebastião
Logs em formato JSON para fácil parsing e debugging
"""

import logging
import json
import traceback
import uuid
from datetime import datetime
from functools import wraps
from flask import request, g, has_request_context
from logging.handlers import RotatingFileHandler
import os


class JSONFormatter(logging.Formatter):
    """Formatter que gera logs em JSON estruturado"""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Adiciona request_id se disponível
        if has_request_context():
            log_data["request_id"] = getattr(g, 'request_id', 'no-request')
            log_data["method"] = request.method
            log_data["path"] = request.path
            log_data["ip"] = request.remote_addr
            log_data["user_agent"] = request.user_agent.string[:100] if request.user_agent else None

        # Adiciona user se disponível
        if has_request_context():
            from flask import session
            log_data["user"] = session.get('username', 'anonymous')

        # Adiciona dados extras do record
        if hasattr(record, 'extra_data'):
            log_data["context"] = record.extra_data

        # Adiciona exception info se houver
        if record.exc_info:
            log_data["error_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
            log_data["stack_trace"] = traceback.format_exception(*record.exc_info)

        return json.dumps(log_data, ensure_ascii=False, default=str)


class AppLogger:
    """
    Logger centralizado da aplicação.

    Uso:
        logger = AppLogger.get_logger()
        logger.info("Mensagem", extra={'extra_data': {'key': 'value'}})
    """

    _instance = None
    _logger = None

    @classmethod
    def setup(cls, app):
        """Configura o logger para a aplicação Flask"""

        # Criar diretório de logs se não existir
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)

        # Configurar logger principal
        cls._logger = logging.getLogger('igreja')
        cls._logger.setLevel(logging.DEBUG)

        # Limpar handlers existentes
        cls._logger.handlers = []

        # Handler para arquivo (JSON) - com rotação
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'app.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        cls._logger.addHandler(file_handler)

        # Handler para erros separado
        error_handler = RotatingFileHandler(
            os.path.join(log_dir, 'error.log'),
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        cls._logger.addHandler(error_handler)

        # Handler para console (desenvolvimento)
        if app.debug:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_format = logging.Formatter(
                '[%(asctime)s] %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_format)
            cls._logger.addHandler(console_handler)

        # Registrar middleware de request
        @app.before_request
        def before_request():
            g.request_id = str(uuid.uuid4())[:8]
            g.request_start = datetime.utcnow()
            cls._logger.debug(f"Request iniciado: {request.method} {request.path}")

        @app.after_request
        def after_request(response):
            if hasattr(g, 'request_start'):
                duration = (datetime.utcnow() - g.request_start).total_seconds() * 1000
                cls._logger.info(
                    f"Request finalizado: {response.status_code}",
                    extra={'extra_data': {
                        'status_code': response.status_code,
                        'duration_ms': round(duration, 2)
                    }}
                )
            return response

        # Error handlers globais
        @app.errorhandler(Exception)
        def handle_exception(e):
            cls._logger.exception(
                f"Erro não tratado: {str(e)}",
                extra={'extra_data': {
                    'error_class': e.__class__.__name__,
                    'path': request.path,
                    'method': request.method,
                    'form_data': dict(request.form) if request.form else None
                }}
            )
            # Retorna erro genérico para o usuário (sem expor detalhes)
            from flask import render_template, jsonify
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'status': 'error',
                    'message': 'Erro interno do servidor',
                    'request_id': getattr(g, 'request_id', 'unknown')
                }), 500
            return render_template('error.html',
                                   error_code=500,
                                   message='Erro interno do servidor',
                                   request_id=getattr(g, 'request_id', 'unknown')), 500

        @app.errorhandler(404)
        def handle_404(e):
            cls._logger.warning(f"404 - Página não encontrada: {request.path}")
            from flask import render_template, jsonify
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'status': 'error', 'message': 'Recurso não encontrado'}), 404
            return render_template('error.html',
                                   error_code=404,
                                   message='Página não encontrada'), 404

        @app.errorhandler(403)
        def handle_403(e):
            cls._logger.warning(f"403 - Acesso negado: {request.path}")
            from flask import render_template, jsonify
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'status': 'error', 'message': 'Acesso negado'}), 403
            return render_template('error.html',
                                   error_code=403,
                                   message='Acesso negado'), 403

        cls._logger.info("Sistema de logging inicializado")
        return cls._logger

    @classmethod
    def get_logger(cls):
        """Retorna a instância do logger"""
        if cls._logger is None:
            # Logger básico se não foi configurado com app
            cls._logger = logging.getLogger('igreja')
            cls._logger.setLevel(logging.DEBUG)
            if not cls._logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
                cls._logger.addHandler(handler)
        return cls._logger


def log_request(message, level='info', **extra):
    """
    Helper para logar com contexto de request.

    Uso:
        log_request("Usuário criou notícia", level='info', noticia_id=123)
    """
    logger = AppLogger.get_logger()
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message, extra={'extra_data': extra})


def log_error(message, exception=None, **extra):
    """
    Helper para logar erros com contexto.

    Uso:
        try:
            ...
        except Exception as e:
            log_error("Erro ao salvar", exception=e, dados={'id': 123})
    """
    logger = AppLogger.get_logger()
    extra_data = {
        'error_class': exception.__class__.__name__ if exception else None,
        'error_message': str(exception) if exception else None,
        **extra
    }
    if exception:
        logger.exception(message, extra={'extra_data': extra_data})
    else:
        logger.error(message, extra={'extra_data': extra_data})


def log_action(action_name):
    """
    Decorator para logar ações automaticamente.

    Uso:
        @log_action("criar_noticia")
        def criar_noticia():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            logger = AppLogger.get_logger()
            logger.info(f"Ação iniciada: {action_name}")
            try:
                result = f(*args, **kwargs)
                logger.info(f"Ação concluída: {action_name}")
                return result
            except Exception as e:
                logger.exception(f"Ação falhou: {action_name}")
                raise
        return decorated_function
    return decorator
