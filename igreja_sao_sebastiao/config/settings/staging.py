"""
Staging settings - PostgreSQL, DEBUG=False.
"""

from .prod import *  # noqa: F401, F403

SECURE_SSL_REDIRECT = False
