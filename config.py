# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env файл (только для локальной разработки)
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

class Config:
    """Централизованная конфигурация приложения"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    DEBUG = FLASK_ENV == 'development'
    
    # Firebase
    FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID')
    FIREBASE_PRIVATE_KEY_ID = os.environ.get('FIREBASE_PRIVATE_KEY_ID')
    FIREBASE_PRIVATE_KEY = os.environ.get('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n')
    FIREBASE_CLIENT_EMAIL = os.environ.get('FIREBASE_CLIENT_EMAIL')
    FIREBASE_CLIENT_ID = os.environ.get('FIREBASE_CLIENT_ID')
    FIREBASE_CLIENT_CERT_URL = os.environ.get('FIREBASE_CLIENT_CERT_URL')
    FIREBASE_DATABASE_URL = os.environ.get('FIREBASE_DATABASE_URL')
    
    @classmethod
    def get_firebase_credentials(cls):
        """Возвращает credentials для Firebase"""
        return {
            "type": "service_account",
            "project_id": cls.FIREBASE_PROJECT_ID,
            "private_key_id": cls.FIREBASE_PRIVATE_KEY_ID,
            "private_key": cls.FIREBASE_PRIVATE_KEY,
            "client_email": cls.FIREBASE_CLIENT_EMAIL,
            "client_id": cls.FIREBASE_CLIENT_ID,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": cls.FIREBASE_CLIENT_CERT_URL,
            "universe_domain": "googleapis.com"
        }
    
    @classmethod
    def is_firebase_configured(cls):
        """Проверяет, настроена ли Firebase"""
        return all([
            cls.FIREBASE_PROJECT_ID,
            cls.FIREBASE_PRIVATE_KEY,
            cls.FIREBASE_CLIENT_EMAIL,
            cls.FIREBASE_DATABASE_URL
        ])