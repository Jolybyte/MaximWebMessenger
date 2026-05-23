# app.py - исправленная версия с REST API
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

class MessengerApp:
    @staticmethod
    def hash_password(password):
        """Хеширует пароль"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def create_user(username, password, avatar_base64=None):
        """Создает нового пользователя"""
        try:
            # Проверяем существование пользователя
            existing_user = FirebaseRESTAPI.get_user_by_username(username)
            if existing_user:
                return None, "Пользователь уже существует"
            
            user_id = str(uuid.uuid4())
            password_hash = MessengerApp.hash_password(password)
            
            user_data = {
                'username': username,
                'password_hash': password_hash,
                'avatar_base64': avatar_base64 or '',
                'online': False,
                'last_seen': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            if FirebaseRESTAPI.create_user(user_id, user_data):
                user_data['id'] = user_id
                return user_data, None
            else:
                return None, "Ошибка при создании пользователя"
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def authenticate_user(username, password):
        """Аутентификация пользователя"""
        try:
            user = FirebaseRESTAPI.get_user_by_username(username)
            if not user:
                return None, "Пользователь не найден"
            
            password_hash = MessengerApp.hash_password(password)
            if user.get('password_hash') != password_hash:
                return None, "Неверный пароль"
            
            return user, None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def update_user_status(user_id, online):
        """Обновляет статус пользователя"""
        try:
            return FirebaseRESTAPI.update_user(user_id, {
                'online': online,
                'last_seen': datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Error updating user status: {e}")
            return False
    
    @staticmethod
    def save_message(user_id, username, avatar_base64, text=None, image_base64=None):
        """Сохраняет сообщение"""
        try:
            message_id = str(uuid.uuid4())
            message_data = {
                'id': message_id,
                'user_id': user_id,
                'username': username,
                'avatar_base64': avatar_base64,
                'timestamp': datetime.now().isoformat()
            }
            
            if text:
                message_data['text'] = text
            if image_base64:
                message_data['image_base64'] = image_base64
            
            if FirebaseRESTAPI.save_message(message_id, message_data):
                return message_data
            return None
        except Exception as e:
            print(f"Error saving message: {e}")
            return None
    
    @staticmethod
    def get_messages(limit=100):
        """Получает последние сообщения"""
        return FirebaseRESTAPI.get_messages(limit)
    
    @staticmethod
    def get_users():
        """Получает список пользователей"""
        return FirebaseRESTAPI.get_users()
    
    @staticmethod
    def update_avatar(user_id, avatar_base64):
        """Обновляет аватар пользователя"""
        try:
            return FirebaseRESTAPI.update_user(user_id, {'avatar_base64': avatar_base64})
        except Exception as e:
            print(f"Error updating avatar: {e}")
            return False
    
    @staticmethod
    def delete_user(user_id):
        """Удаляет пользователя"""
        try:
            return FirebaseRESTAPI.delete_user(user_id)
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

# Маршруты
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('chat'))
    return render_template('index.html')

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('chat.html', user=session.get('user'))

@app.route('/api/check_session', methods=['GET'])
def check_session():
    """Проверяет, авторизован ли пользователь"""
    if 'user_id' in session and session.get('user'):
        return jsonify({
            'authenticated': True,
            'user': session.get('user')
        })
    return jsonify({'authenticated': False}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    avatar_base64 = data.get('avatar_base64', '')
    
    if not username or not password:
        return jsonify({'error': 'Заполните все поля'}), 400
    
    if len(username) < 3:
        return jsonify({'error': 'Имя пользователя должно содержать минимум 3 символа'}), 400
    
    if len(password) < 4:
        return jsonify({'error': 'Пароль должен содержать минимум 4 символа'}), 400
    
    user, error = MessengerApp.create_user(username, password, avatar_base64)
    
    if error:
        return jsonify({'error': error}), 400
    
    session['user_id'] = user['id']
    session['user'] = user
    
    # Обновляем статус онлайн
    MessengerApp.update_user_status(user['id'], True)
    
    return jsonify({'success': True, 'user': user})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Заполните все поля'}), 400
    
    user, error = MessengerApp.authenticate_user(username, password)
    
    if error:
        return jsonify({'error': error}), 401
    
    session['user_id'] = user['id']
    session['user'] = user
    
    # Обновляем статус онлайн
    MessengerApp.update_user_status(user['id'], True)
    
    return jsonify({'success': True, 'user': user})

@app.route('/api/logout', methods=['POST'])
def logout():
    user_id = session.get('user_id')
    if user_id:
        MessengerApp.update_user_status(user_id, False)
    
    session.clear()
    return jsonify({'success': True})

@app.route('/api/messages', methods=['GET'])
def get_messages():
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    limit = request.args.get('limit', 100, type=int)
    messages = MessengerApp.get_messages(limit)
    return jsonify({'messages': messages})

@app.route('/api/users', methods=['GET'])
def get_users():
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    users = MessengerApp.get_users()
    return jsonify({'users': users})

@app.route('/api/update_avatar', methods=['POST'])
def update_avatar():
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.json
    avatar_base64 = data.get('avatar_base64', '')
    
    if MessengerApp.update_avatar(session['user_id'], avatar_base64):
        session['user']['avatar_base64'] = avatar_base64
        socketio.emit('user_updated', {
            'user_id': session['user_id'],
            'user': session['user']
        })
        return jsonify({'success': True})
    
    return jsonify({'error': 'Не удалось обновить аватар'}), 400

@app.route('/api/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    if MessengerApp.delete_user(session['user_id']):
        socketio.emit('user_left', {'user_id': session['user_id']})
        session.clear()
        return jsonify({'success': True})
    
    return jsonify({'error': 'Не удалось удалить аккаунт'}), 400

# SocketIO события
active_users = {}

@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        user_id = session['user_id']
        active_users[request.sid] = user_id
        MessengerApp.update_user_status(user_id, True)
        emit('user_joined', {
            'user_id': user_id,
            'user': session.get('user')
        }, broadcast=True, include_self=False)

@socketio.on('disconnect')
def handle_disconnect():
    user_id = active_users.pop(request.sid, None)
    if user_id:
        MessengerApp.update_user_status(user_id, False)
        emit('user_left', {'user_id': user_id}, broadcast=True)

@socketio.on('send_message')
def handle_send_message(data):
    if 'user_id' not in session:
        return
    
    text = data.get('text', '').strip()
    image_base64 = data.get('image_base64', '')
    
    if not text and not image_base64:
        return
    
    user = session.get('user')
    
    message = MessengerApp.save_message(
        user_id=session['user_id'],
        username=user['username'],
        avatar_base64=user.get('avatar_base64', ''),
        text=text,
        image_base64=image_base64
    )
    
    if message:
        emit('new_message', message, broadcast=True)

@socketio.on('typing')
def handle_typing(data):
    if 'user_id' not in session:
        return
    
    emit('user_typing', {
        'user_id': session['user_id'],
        'username': session['user']['username'],
        'is_typing': data.get('is_typing', False)
    }, broadcast=True, include_self=False)

if __name__ == '__main__':
    # Проверяем соединение с Firebase
    print("Checking Firebase connection...")
    test = FirebaseRESTAPI.get_users()
    if test is not None:
        print("✅ Firebase connection successful!")
    else:
        print("⚠️ Warning: Firebase connection failed. Check your DATABASE_URL.")
        print(f"   Current URL: {FIREBASE_DB_URL}")
    
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
