from flask import Flask, request, jsonify
import json
import os
from datetime import datetime
import subprocess
import hmac
import hashlib
import asyncio
import threading
from scrapers.orchestrator import ScrapingOrchestrator

app = Flask(__name__)

WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'dev-secret-key-change-me')
CACHE_FILE = 'data/deals_cache.json'

def verify_webhook_signature(signature, payload):
    """Verify webhook signature using HMAC"""
    if not signature:
        return False
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)

def run_scraper():
    """Run scraper in background thread"""
    print(f"\n[{datetime.now()}] 🚀 Starting local scraper...")

    try:
        # Run async scraper
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        orchestrator = ScrapingOrchestrator()
        result = loop.run_until_complete(orchestrator.scrape_all())
        loop.close()

        # Save to cache
        os.makedirs('data', exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"[{datetime.now()}] ✅ Scraped {len(result['deals'])} deals")

        # Commit and push to GitHub
        print(f"[{datetime.now()}] 📤 Pushing to GitHub...")

        subprocess.run(['git', 'add', 'data/deals_cache.json'], check=True)

        commit_msg = f"Update deals cache: {len(result['deals'])} deals - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)

        subprocess.run(['git', 'push', 'origin', 'main'], check=True)

        print(f"[{datetime.now()}] ✅ Pushed to GitHub. Render will auto-deploy.")

    except Exception as e:
        print(f"[{datetime.now()}] ❌ Scraping failed: {e}")
        import traceback
        traceback.print_exc()

@app.route('/webhook/trigger', methods=['POST'])
def webhook_trigger():
    """Webhook endpoint for Render to trigger local scraping"""

    # Verify signature
    signature = request.headers.get('X-Webhook-Signature')
    if not verify_webhook_signature(signature, request.data):
        print(f"[{datetime.now()}] ⚠️  Invalid webhook signature")
        return jsonify({'error': 'Invalid signature'}), 401

    print(f"[{datetime.now()}] ✅ Webhook received from Render")

    # Start scraper in background thread
    thread = threading.Thread(target=run_scraper, daemon=True)
    thread.start()

    return jsonify({
        'status': 'scraping_started',
        'message': 'Local scraper triggered',
        'timestamp': datetime.now().isoformat()
    }), 202

@app.route('/webhook/status', methods=['GET'])
def webhook_status():
    """Check if local app is reachable"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'tailscale_ip': '100.83.37.54'
    }), 200

@app.route('/', methods=['GET'])
def index():
    """Simple status page"""
    return jsonify({
        'service': 'Black Friday Scraper - Local Webhook Server',
        'status': 'running',
        'endpoints': {
            '/webhook/trigger': 'POST - Trigger scraping',
            '/webhook/status': 'GET - Check status'
        }
    }), 200

if __name__ == '__main__':
    print("="*60)
    print("🚀 Black Friday Local Webhook Server")
    print("="*60)
    print(f"Tailscale IP: 100.83.37.54")
    print(f"Listening on: http://0.0.0.0:5001")
    print(f"Webhook URL: http://100.83.37.54:5001/webhook/trigger")
    print(f"Status URL: http://100.83.37.54:5001/webhook/status")
    print("="*60)
    print(f"Webhook Secret: {WEBHOOK_SECRET[:10]}...")
    print("="*60)

    app.run(host='0.0.0.0', port=5001, debug=False)
