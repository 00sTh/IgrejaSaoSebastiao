"""
Middleware Package - Igreja São Sebastião
Contém: Logger, Auth, ErrorHandler
"""

from middleware.logger import AppLogger, log_request, log_error
from middleware.auth import AuthManager, login_required, role_required

__all__ = [
    'AppLogger',
    'log_request',
    'log_error',
    'AuthManager',
    'login_required',
    'role_required'
]
