from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import json
import os
from datetime import datetime
import asyncio
import httpx
import hmac
import hashlib
from scrapers.orchestrator import ScrapingOrchestrator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'blackfriday-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

CACHE_FILE = 'data/deals_cache.json'
GITHUB_RAW_URL = 'https://raw.githubusercontent.com/Biggles10-claude/blackfriday-deals/main/data/deals_cache.json'
LOCAL_TAILSCALE_IP = os.getenv('LOCAL_TAILSCALE_IP', '100.83.37.54')
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'dev-secret-key-change-me')

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

@app.route('/api/trigger-local-scrape', methods=['POST'])
def trigger_local_scrape():
    """Trigger scraping on local machine via Tailscale webhook"""
    try:
        # Create signature for webhook authentication
        payload = json.dumps({'timestamp': datetime.now().isoformat()}).encode()
        signature = hmac.new(
            WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Send webhook to local machine
        local_url = f'http://{LOCAL_TAILSCALE_IP}:5001/webhook/trigger'
        response = httpx.post(
            local_url,
            json={'timestamp': datetime.now().isoformat()},
            headers={'X-Webhook-Signature': signature},
            timeout=5.0
        )

        if response.status_code == 202:
            return jsonify({
                'status': 'success',
                'message': 'Local scraper triggered',
                'local_response': response.json()
            }), 202
        else:
            return jsonify({
                'status': 'error',
                'message': f'Local machine returned {response.status_code}'
            }), 500

    except httpx.TimeoutException:
        return jsonify({
            'status': 'error',
            'message': 'Local machine unreachable (timeout)'
        }), 504
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/check-local-status', methods=['GET'])
def check_local_status():
    """Check if local machine is online and reachable"""
    try:
        local_url = f'http://{LOCAL_TAILSCALE_IP}:5001/webhook/status'
        response = httpx.get(local_url, timeout=3.0)

        if response.status_code == 200:
            return jsonify({
                'status': 'online',
                'local_data': response.json()
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': f'Local machine returned {response.status_code}'
            }), 500

    except httpx.TimeoutException:
        return jsonify({
            'status': 'offline',
            'message': 'Local machine unreachable (timeout)'
        }), 503
    except Exception as e:
        return jsonify({
            'status': 'offline',
            'message': str(e)
        }), 503

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
