from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
import random
import threading
import time
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Данные системы (как в вашем боте)
system_data = {
    'temperature': 24.5,
    'radiation': 12500,
    'humidity': 45.0,
    'pressure': 1013.2,
    'voltage': 12.4,
    'signal_level': 95,
    'system_status': 'НОРМА',
    'fan_status': 'ВЫКЛ',
    'historical_data': []
}

# Фоновая задача для обновления данных
def background_task():
    while True:
        # Обновляем данные (как в вашем боте)
        system_data['temperature'] = round(24.5 + random.uniform(-2, 2), 1)
        system_data['radiation'] = int(12500 + random.uniform(-1000, 1000))
        system_data['humidity'] = round(45.0 + random.uniform(-5, 5), 1)
        
        # Добавляем в историю для графиков
        system_data['historical_data'].append({
            'timestamp': datetime.now().isoformat(),
            'temperature': system_data['temperature'],
            'radiation': system_data['radiation'],
            'humidity': system_data['humidity']
        })
        
        # Ограничиваем историю
        if len(system_data['historical_data']) > 50:
            system_data['historical_data'].pop(0)
        
        # Отправляем обновления всем подключенным клиентам
        socketio.emit('data_update', system_data)
        time.sleep(2)  # Обновление каждые 2 секунды

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    return jsonify(system_data)

@app.route('/api/fan/<action>')
def control_fan(action):
    if action == 'on':
        system_data['fan_status'] = 'ВКЛ'
    elif action == 'off':
        system_data['fan_status'] = 'ВЫКЛ'
    
    socketio.emit('fan_status', {'status': system_data['fan_status']})
    return jsonify({'status': 'success', 'fan_status': system_data['fan_status']})

@app.route('/api/emergency_stop')
def emergency_stop():
    system_data.update({
        'system_status': 'АВАРИЯ',
        'fan_status': 'ВЫКЛ'
    })
    socketio.emit('emergency_stop', system_data)
    return jsonify({'status': 'emergency_stop_activated'})

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    socketio.emit('data_update', system_data)

if __name__ == '__main__':
    # Запускаем фоновую задачу
    thread = threading.Thread(target=background_task, daemon=True)
    thread.start()
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)