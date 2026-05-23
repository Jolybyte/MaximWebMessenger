from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
import requests
import uuid
import hashlib
import sys
from datetime import datetime
from config import Config

# Увеличиваем лимит рекурсии
sys.setrecursionlimit(10000)

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY 
socketio = SocketIO(app, cors_allowed_origins="*")

# Конфигурация Firebase
FIREBASE_DB_URL = Config.FIREBASE_DATABASE_URL

class FirebaseRESTAPI:
    """Класс для работы с Firebase через REST API"""
    
    @staticmethod
    def _make_request(method, path, data=None):
        """Выполняет запрос к Firebase REST API"""
        try:
            path = path.strip('/')
            url = f"{FIREBASE_DB_URL}/{path}.json?print=silent"
            
            timeout = 30
            
            if method == 'GET':
                response = requests.get(url, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, timeout=timeout)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, timeout=timeout)
            else:
                return None
            
            if response.status_code in [200, 201]:
                result = response.json()
                return result if result is not None else ({} if method == 'GET' else True)
            elif response.status_code == 404:
                return {} if method == 'GET' else None
            else:
                print(f"Firebase REST error: {response.status_code}")
                return {} if method == 'GET' else None
                
        except requests.exceptions.Timeout:
            print(f"Firebase REST timeout: {method} {path}")
            return {} if method == 'GET' else None
        except Exception as e:
            print(f"Firebase REST request error: {e}")
            return {} if method == 'GET' else None
    
    @staticmethod
    def get_user_by_username(username):
        """Получает пользователя по имени"""
        try:
            users = FirebaseRESTAPI._make_request('GET', 'users')
            if users and isinstance(users, dict):
                for user_id, user_data in users.items():
                    if isinstance(user_data, dict) and user_data.get('username') == username:
                        user_data['id'] = user_id
                        return user_data
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    @staticmethod
    def create_user(user_id, user_data):
        """Создает нового пользователя"""
        try:
            result = FirebaseRESTAPI._make_request('PUT', f'users/{user_id}', user_data)
            return result is not None
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    @staticmethod
    def update_user(user_id, user_data):
        """Обновляет пользователя"""
        try:
            result = FirebaseRESTAPI._make_request('PATCH', f'users/{user_id}', user_data)
            return result is not None
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
    
    @staticmethod
    def delete_user(user_id):
        """Удаляет пользователя"""
        try:
            result = FirebaseRESTAPI._make_request('DELETE', f'users/{user_id}')
            return result is not None
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    @staticmethod
    def get_messages(limit=100):
        """Получает последние сообщения"""
        try:
            messages = FirebaseRESTAPI._make_request('GET', 'messages')
            if messages and isinstance(messages, dict):
                sorted_messages = sorted(messages.items(), 
                                       key=lambda x: x[1].get('timestamp', '') if isinstance(x[1], dict) else '')
                return [msg[1] for msg in sorted_messages[-limit:] if isinstance(msg[1], dict)]
            return []
        except Exception as e:
            print(f"Error getting messages: {e}")
            return []
    
    @staticmethod
    def save_message(message_id, message_data):
        """Сохраняет сообщение"""
        try:
            result = FirebaseRESTAPI._make_request('PUT', f'messages/{message_id}', message_data)
            return result is not None
        except Exception as e:
            print(f"Error saving message: {e}")
            return False
    
    @staticmethod
    def get_users():
        """Получает всех пользователей"""
        try:
            users = FirebaseRESTAPI._make_request('GET', 'users')
            return users if isinstance(users, dict) else {}
        except Exception as e:
            print(f"Error getting users: {e}")
            return {}
