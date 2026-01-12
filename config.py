"""
Arquivo de Configuração - Igreja São Sebastião
Gerencia variáveis de ambiente e configurações da aplicação
"""
import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

class Config:
    """Configurações da aplicação"""

    # Chave secreta
    SECRET_KEY = os.getenv('SECRET_KEY', 'chave_padrao_insegura')

    # Banco de dados
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'database.db')

    # Upload de arquivos
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/uploads')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 5242880))  # 5MB padrão
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Credenciais admin
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

    # Flask
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
