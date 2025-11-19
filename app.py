from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import json
import os
from datetime import datetime
import asyncio
import httpx
from scrapers.orchestrator import ScrapingOrchestrator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'blackfriday-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

CACHE_FILE = 'data/deals_cache.json'
GITHUB_RAW_URL = 'https://raw.githubusercontent.com/Biggles10-claude/blackfriday-deals/main/data/deals_cache.json'

def progress_callback(data):
    """Emit scraping progress via WebSocket"""
    socketio.emit('scraping_progress', data)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/deals')
def get_deals():
    # Try to load from local cache first
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return jsonify(json.load(f))
        except:
            pass

    # Fallback to GitHub raw URL
    try:
        response = httpx.get(GITHUB_RAW_URL, timeout=10.0)
        if response.status_code == 200:
            return jsonify(response.json())
    except:
        pass

    return jsonify({'deals': [], 'categories': {}, 'category_stats': {}, 'last_updated': None})

@socketio.on('start_refresh')
def handle_refresh():
    """Handle refresh request from client"""
    emit('scraping_started', {'message': 'Starting scrape...'})

    # Run async scraping in event loop
    orchestrator = ScrapingOrchestrator(progress_callback=progress_callback)

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(orchestrator.scrape_all())
        loop.close()

        # Save to cache
        os.makedirs('data', exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump(result, f, indent=2)

        emit('scraping_complete', {
            'deals_count': len(result['deals']),
            'last_updated': result['last_updated']
        })

    except Exception as e:
        emit('scraping_error', {'error': str(e)})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
