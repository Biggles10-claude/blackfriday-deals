import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import os

DB_PATH = 'data/price_history.db'

def init_database():
    """Initialize the price history database"""
    os.makedirs('data', exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create price_history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asin TEXT NOT NULL,
            retailer TEXT NOT NULL,
            price REAL NOT NULL,
            original_price REAL NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(asin, retailer, timestamp)
        )
    ''')

    # Create index for faster lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_asin_retailer
        ON price_history(asin, retailer)
    ''')

    conn.commit()
    conn.close()

def save_price_snapshot(deal: Dict):
    """Save a price snapshot for a deal"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Extract ASIN from URL if available
        asin = extract_asin(deal.get('url', ''))
        if not asin:
            return  # Skip if no ASIN

        cursor.execute('''
            INSERT OR IGNORE INTO price_history
            (asin, retailer, price, original_price, title, url, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            asin,
            deal.get('retailer', 'Unknown'),
            deal.get('price', 0),
            deal.get('original_price', 0),
            deal.get('title', ''),
            deal.get('url', ''),
            datetime.now().isoformat()
        ))

        conn.commit()
    except Exception as e:
        print(f"[Database] Error saving price snapshot: {e}")
    finally:
        conn.close()

def get_price_history(asin: str, retailer: str, days: int = 30) -> List[Dict]:
    """Get price history for a product over the last N days"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT price, original_price, timestamp
        FROM price_history
        WHERE asin = ? AND retailer = ?
        AND timestamp >= datetime('now', '-' || ? || ' days')
        ORDER BY timestamp DESC
    ''', (asin, retailer, days))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            'price': row[0],
            'original_price': row[1],
            'timestamp': row[2]
        }
        for row in rows
    ]

def analyze_deal_legitimacy(deal: Dict) -> Dict:
    """
    Analyze if a deal is legitimate based on price history
    Returns dict with legitimacy score and reasoning
    """
    asin = extract_asin(deal.get('url', ''))
    if not asin:
        return {'legitimate': True, 'confidence': 'unknown', 'reason': 'No price history available'}

    history = get_price_history(asin, deal.get('retailer', 'Unknown'), days=30)

    if len(history) < 2:
        return {'legitimate': True, 'confidence': 'unknown', 'reason': 'Insufficient price history'}

    current_price = deal.get('price', 0)
    original_price = deal.get('original_price', 0)

    # Get historical prices (excluding today)
    historical_prices = [h['price'] for h in history[1:]]

    if not historical_prices:
        return {'legitimate': True, 'confidence': 'low', 'reason': 'First time seeing this price'}

    avg_historical_price = sum(historical_prices) / len(historical_prices)
    min_historical_price = min(historical_prices)
    max_historical_price = max(historical_prices)

    # Check if "original price" was ever the actual price
    original_was_real = any(h['price'] >= original_price * 0.95 for h in history)

    # Check if current price is actually lower than historical average
    is_real_discount = current_price < avg_historical_price * 0.90

    # Determine legitimacy
    if original_was_real and is_real_discount:
        return {
            'legitimate': True,
            'confidence': 'high',
            'reason': f'Price dropped from ${avg_historical_price:.2f} avg to ${current_price:.2f}',
            'avg_price': avg_historical_price,
            'min_price': min_historical_price,
            'max_price': max_historical_price
        }
    elif not original_was_real and current_price <= min_historical_price:
        return {
            'legitimate': True,
            'confidence': 'medium',
            'reason': 'Lowest price seen in 30 days',
            'avg_price': avg_historical_price,
            'min_price': min_historical_price
        }
    elif not original_was_real:
        return {
            'legitimate': False,
            'confidence': 'high',
            'reason': f'Fake discount - never sold at ${original_price:.2f}',
            'avg_price': avg_historical_price,
            'real_discount': round((1 - current_price / avg_historical_price) * 100, 1)
        }
    else:
        return {
            'legitimate': True,
            'confidence': 'medium',
            'reason': 'Price within normal range',
            'avg_price': avg_historical_price
        }

def extract_asin(url: str) -> Optional[str]:
    """Extract ASIN from Amazon URL"""
    import re

    # Amazon ASIN pattern: /dp/ASIN or /product/ASIN or data-asin
    patterns = [
        r'/dp/([A-Z0-9]{10})',
        r'/product/([A-Z0-9]{10})',
        r'data-asin="([A-Z0-9]{10})"',
        r'/([A-Z0-9]{10})/'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None

def get_database_stats() -> Dict:
    """Get statistics about the price history database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM price_history')
    total_records = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT asin) FROM price_history')
    unique_products = cursor.fetchone()[0]

    cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM price_history')
    date_range = cursor.fetchone()

    conn.close()

    return {
        'total_records': total_records,
        'unique_products': unique_products,
        'oldest_record': date_range[0],
        'newest_record': date_range[1]
    }

# Initialize database on module load
init_database()
