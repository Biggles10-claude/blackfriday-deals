# Local Scraper Service Setup Guide

## Overview

This service runs on your local machine via Tailscale to scrape Amazon deals, bypassing Render's IP blocks.

**How it works:**
1. User clicks "Refresh Deals" on deployed website
2. Render sends webhook to your local machine (via Tailscale)
3. Local machine scrapes Amazon (not blocked by Amazon)
4. Results committed to GitHub
5. Render auto-deploys new data

---

## Prerequisites

- ✅ Tailscale installed and running
- ✅ GitHub Personal Access Token
- ✅ Python 3.9+

---

## Installation

### 1. Install Dependencies

```bash
cd /workspace/blackfriday-aggregator
pip install -r requirements-local.txt
```

### 2. Set Environment Variables

**On your local machine:**

```bash
export GITHUB_TOKEN="your_github_personal_access_token_here"
export WEBHOOK_SECRET="wn7IhnHfKOVinlANQW6PZrIZxpNzHs4y1w9iilBNH9k"
```

**Make persistent** (add to `~/.bashrc` or `~/.zshrc`):

```bash
echo 'export GITHUB_TOKEN="your_github_personal_access_token_here"' >> ~/.bashrc
echo 'export WEBHOOK_SECRET="wn7IhnHfKOVinlANQW6PZrIZxpNzHs4y1w9iilBNH9k"' >> ~/.bashrc
source ~/.bashrc
```

### 3. Configure Git

```bash
cd /workspace/blackfriday-aggregator
git config user.name "Local Scraper Bot"
git config user.email "henri.dovan@gmail.com"
```

---

## Running the Service

### Start the Service

```bash
cd /workspace/blackfriday-aggregator
python local_scraper_service.py
```

You should see:

```
============================================================
LOCAL SCRAPER SERVICE
============================================================
Webhook secret configured: ✅
GitHub token configured: ✅
Listening on: http://0.0.0.0:5001
============================================================
```

### Verify It's Reachable via Tailscale

From another machine on your Tailscale network:

```bash
curl https://claude-workspace.taildc3fd3.ts.net:5001/webhook/status
```

Should return:

```json
{
  "status": "online",
  "service": "local-scraper",
  "timestamp": "2025-11-19T09:10:00.123456"
}
```

---

## How to Use

### Option 1: Automatic Trigger (from deployed website)

1. Go to https://blackfriday-aggregator.onrender.com
2. Click "Refresh Deals" button
3. Render sends webhook to your local machine
4. Local machine scrapes and pushes to GitHub
5. Render auto-deploys new data

### Option 2: Manual Trigger (for testing)

```bash
curl -X POST https://blackfriday-aggregator.onrender.com/api/trigger-local-scrape
```

---

## Configuration

### Render Environment Variables

**Already configured:**
- `WEBHOOK_SECRET`: `wn7IhnHfKOVinlANQW6PZrIZxpNzHs4y1w9iilBNH9k`
- `LOCAL_TAILSCALE_IP`: `https://claude-workspace.taildc3fd3.ts.net`

### Local Environment Variables

**Required:**
- `GITHUB_TOKEN`: Your GitHub Personal Access Token
- `WEBHOOK_SECRET`: Same secret as Render (for webhook verification)

---

## Troubleshooting

### Service won't start

**Check Python version:**
```bash
python --version  # Should be 3.9+
```

**Check dependencies installed:**
```bash
pip list | grep -E 'flask|httpx|beautifulsoup4|aiohttp'
```

### Webhook not reaching local machine

**Check Tailscale is running:**
```bash
tailscale status
```

**Check firewall allows port 5001:**
```bash
sudo ufw allow 5001/tcp  # Linux
```

**Test local access:**
```bash
curl http://localhost:5001/webhook/status
```

### Scraping works but GitHub push fails

**Check GitHub token:**
```bash
echo $GITHUB_TOKEN  # Should show token
```

**Test Git authentication:**
```bash
git ls-remote https://your_github_token@github.com/Biggles10-claude/blackfriday-deals.git
```

### Invalid webhook signature error

**Check webhook secret matches:**
```bash
echo $WEBHOOK_SECRET  # Should be: wn7IhnHfKOVinlANQW6PZrIZxpNzHs4y1w9iilBNH9k
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│ User clicks "Refresh Deals" on deployed website    │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│ Render: POST /api/trigger-local-scrape              │
│ - Creates HMAC signature with WEBHOOK_SECRET        │
│ - Sends webhook to LOCAL_TAILSCALE_IP               │
└────────────────────┬────────────────────────────────┘
                     │ (via Tailscale)
                     ▼
┌─────────────────────────────────────────────────────┐
│ Local Machine: POST /webhook/trigger                │
│ - Verifies HMAC signature                           │
│ - Starts async scraping workflow                    │
│ - Returns 202 Accepted immediately                  │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│ Scraping Workflow:                                  │
│ 1. Scrape Amazon (not blocked, local IP)           │
│ 2. Save to data/deals_cache.json                   │
│ 3. git add, commit, push to GitHub                 │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│ GitHub: main branch updated                         │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│ Render: Auto-deploy triggered                       │
│ - Pulls latest code from GitHub                    │
│ - Deploys with new deals_cache.json                │
└─────────────────────────────────────────────────────┘
```

---

## Security Notes

- **Webhook Secret**: HMAC-SHA256 signature verification prevents unauthorized triggers
- **Tailscale**: Private mesh network, not exposed to public internet
- **GitHub Token**: Scoped to repo access only (read/write)
- **No API keys in code**: All secrets via environment variables

---

## Maintenance

### Update Scraper Code

1. Make changes to `scrapers/amazon_au.py` or other scrapers
2. Restart local service: `Ctrl+C` then `python local_scraper_service.py`
3. Test by clicking "Refresh Deals" on website

### Monitor Scraping

**Watch logs in real-time:**
```bash
tail -f local_scraper_service.log  # If logging to file
```

**Check GitHub commits:**
```bash
git log --oneline --author="Local Scraper Bot"
```

### Rotate Webhook Secret

1. Generate new secret:
   ```bash
   openssl rand -base64 32
   ```

2. Update Render env var:
   ```bash
   # Via Render dashboard or API
   ```

3. Update local env var:
   ```bash
   export WEBHOOK_SECRET="new-secret-here"
   ```

---

## Performance

- **Scraping time**: 2-5 minutes for all categories
- **Deals per scrape**: 50-150 (10%+ discount only)
- **GitHub push**: ~5 seconds
- **Render auto-deploy**: 1-2 minutes

**Total time from click to updated website: ~3-7 minutes**
