# firebase_config.py
import firebase_admin
from firebase_admin import credentials
import json
from pathlib import Path
from config import Config

def initialize_firebase():
    """Инициализирует Firebase"""
    try:
        # Проверяем, уже инициализирован ли Firebase
        if firebase_admin._DEFAULT_APP_NAME in firebase_admin._apps:
            return True
        
        # Вариант 1: Используем переменные окружения (для продакшена)
        if Config.is_firebase_configured():
            print("Initializing Firebase with environment variables...")
            firebase_creds = Config.get_firebase_credentials()
            cred = credentials.Certificate(firebase_creds)
            database_url = Config.FIREBASE_DATABASE_URL
            
        # Вариант 2: Локальный файл (для разработки)
        else:
            service_account_path = Path(__file__).parent / 'serviceAccountKey.json'
            
            if not service_account_path.exists():
                print("❌ Error: Neither environment variables nor serviceAccountKey.json found")
                print("   Please configure Firebase credentials in .env file or add serviceAccountKey.json")
                return False
            
            print("Initializing Firebase with local serviceAccountKey.json...")
            
            # Читаем URL из файла
            with open(service_account_path, 'r') as f:
                service_account_data = json.load(f)
            
            cred = credentials.Certificate(str(service_account_path))
            database_url = f"https://{service_account_data['project_id']}-default-rtdb.europe-west1.firebasedatabase.app"
        
        # Инициализируем Firebase
        firebase_admin.initialize_app(cred, {
            'databaseURL': database_url
        })
        
        print("✅ Firebase initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing Firebase: {e}")
        return False