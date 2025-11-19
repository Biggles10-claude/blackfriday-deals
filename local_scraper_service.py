"""
Local Scraper Service - Runs on your local machine via Tailscale

This service:
1. Receives webhook triggers from Render deployment
2. Runs scraping locally (avoiding Amazon's Render IP blocks)
3. Commits results to GitHub
4. Render auto-deploys the new data

Setup:
1. Install Tailscale and get your Tailscale IP
2. Set environment variables:
   - GITHUB_TOKEN=your_github_personal_access_token
   - WEBHOOK_SECRET=same_secret_as_in_render
3. Run: python local_scraper_service.py
"""

from flask import Flask, request, jsonify
import asyncio
import json
import os
import hmac
import hashlib
from datetime import datetime
import subprocess
import threading
from scrapers.orchestrator import ScrapingOrchestrator

app = Flask(__name__)

# Configuration
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'dev-secret-key-change-me')
GITHUB_REPO = 'Biggles10-claude/blackfriday-deals'
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
DATA_FILE = 'data/deals_cache.json'

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify the webhook request is authentic"""
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)

@app.route('/webhook/status', methods=['GET'])
def status():
    """Health check endpoint"""
    return jsonify({
        'status': 'online',
        'service': 'local-scraper',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/webhook/trigger', methods=['POST'])
def trigger_scrape():
    """Receive webhook trigger from Render and start scraping"""

    # Verify webhook signature
    signature = request.headers.get('X-Webhook-Signature', '')
    payload = request.get_data()

    if not verify_webhook_signature(payload, signature):
        return jsonify({
            'status': 'error',
            'message': 'Invalid webhook signature'
        }), 403

    print(f"\n{'='*60}")
    print(f"[LOCAL SCRAPER] Webhook received at {datetime.now()}")
    print(f"{'='*60}\n")

    # Start scraping in background (don't block webhook response)
    thread = threading.Thread(target=lambda: asyncio.run(run_scraping_workflow()))
    thread.daemon = True
    thread.start()

    return jsonify({
        'status': 'accepted',
        'message': 'Scraping started on local machine'
    }), 202

async def run_scraping_workflow():
    """Run the complete scraping workflow and push to GitHub"""
    try:
        print("[LOCAL SCRAPER] Starting scraping workflow...")

        # 1. Run scraping
        orchestrator = ScrapingOrchestrator()
        result = await orchestrator.scrape_all()

        print(f"[LOCAL SCRAPER] ✅ Scraped {len(result['deals'])} deals")

        # 2. Save to file
        os.makedirs('data', exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"[LOCAL SCRAPER] ✅ Saved to {DATA_FILE}")

        # 3. Commit and push to GitHub
        if GITHUB_TOKEN:
            commit_message = f"Update deals: {len(result['deals'])} deals at {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            # Configure git
            subprocess.run(['git', 'config', 'user.name', 'Local Scraper Bot'], check=True)
            subprocess.run(['git', 'config', 'user.email', 'henri.dovan@gmail.com'], check=True)

            # Add, commit, push
            subprocess.run(['git', 'add', DATA_FILE], check=True)
            subprocess.run(['git', 'commit', '-m', commit_message], check=True)

            # Push with token authentication
            remote_url = f'https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git'
            subprocess.run(['git', 'remote', 'set-url', 'origin', remote_url], check=True)
            subprocess.run(['git', 'push', 'origin', 'main'], check=True)

            print(f"[LOCAL SCRAPER] ✅ Pushed to GitHub")
            print(f"[LOCAL SCRAPER] 🎉 Render will auto-deploy new data")
        else:
            print(f"[LOCAL SCRAPER] ⚠️ No GITHUB_TOKEN - skipping git push")

        print(f"\n{'='*60}")
        print(f"[LOCAL SCRAPER] Workflow complete!")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"[LOCAL SCRAPER] ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    PORT = int(os.getenv('PORT', '5002'))
    print("\n" + "="*60)
    print("LOCAL SCRAPER SERVICE")
    print("="*60)
    print(f"Webhook secret configured: {'✅' if WEBHOOK_SECRET != 'dev-secret-key-change-me' else '⚠️ Using default'}")
    print(f"GitHub token configured: {'✅' if GITHUB_TOKEN else '❌ Not configured'}")
    print(f"Listening on: http://0.0.0.0:{PORT}")
    print("="*60 + "\n")

    # Run Flask (asyncio tasks work fine with Flask)
    app.run(host='0.0.0.0', port=PORT, debug=False)
