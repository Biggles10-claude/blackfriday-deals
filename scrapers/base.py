from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Optional
import hashlib
import httpx
from bs4 import BeautifulSoup
import asyncio
import time

class BaseScraper(ABC):
    """Base class for all retailer scrapers"""

    def __init__(self, retailer_name: str):
        self.retailer_name = retailer_name
        self.deals: List[Dict] = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.retry_delays = [10, 30, 60]  # Exponential backoff

    def standardize_deal(self, raw_deal: Dict) -> Dict:
        """Convert raw deal data to standardized format"""
        # Calculate discount percentage
        discount_pct = 0
        if raw_deal.get('original_price') and raw_deal.get('price'):
            discount_pct = round(
                ((raw_deal['original_price'] - raw_deal['price']) / raw_deal['original_price']) * 100,
                1
            )

        # Generate unique ID
        product_id = hashlib.md5(
            f"{self.retailer_name.lower()}-{raw_deal.get('url', '')}".encode()
        ).hexdigest()[:12]

        return {
            'id': f"{self.retailer_name.lower().replace(' ', '')}-{product_id}",
            'title': raw_deal.get('title', 'Unknown Product'),
            'price': raw_deal.get('price', 0),
            'original_price': raw_deal.get('original_price', raw_deal.get('price', 0)),
            'discount_pct': discount_pct,
            'url': raw_deal.get('url', ''),
            'image': raw_deal.get('image', ''),
            'rating': raw_deal.get('rating', 0),
            'review_count': raw_deal.get('review_count', 0),
            'category': raw_deal.get('category', 'Uncategorized'),
            'retailer': self.retailer_name,
            'scraped_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }

    async def fetch_page(self, url: str, retry_count: int = 0) -> Optional[str]:
        """Fetch page with retry logic and error handling"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.text
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            if retry_count < len(self.retry_delays):
                delay = self.retry_delays[retry_count]
                print(f"[{self.retailer_name}] Retry in {delay}s due to: {str(e)}")
                await asyncio.sleep(delay)
                return await self.fetch_page(url, retry_count + 1)
            print(f"[{self.retailer_name}] Failed after {retry_count} retries: {str(e)}")
            return None

    @abstractmethod
    async def scrape(self) -> List[Dict]:
        """Scrape deals from retailer - must be implemented by subclasses"""
        pass
