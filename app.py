from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
import json
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'blackfriday-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

CACHE_FILE = 'data/deals_cache.json'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/deals')
def get_deals():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return jsonify(json.load(f))
    return jsonify({'deals': [], 'collections': {}, 'last_updated': None})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
