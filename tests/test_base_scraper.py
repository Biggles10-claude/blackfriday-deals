import pytest
from scrapers.base import BaseScraper
from datetime import datetime
from typing import List, Dict

# Create a concrete test implementation
class ConcreteScraper(BaseScraper):
    async def scrape(self) -> List[Dict]:
        return []

def test_base_scraper_initialization():
    scraper = ConcreteScraper('TestRetailer')
    assert scraper.retailer_name == 'TestRetailer'
    assert scraper.deals == []

def test_standardize_deal():
    scraper = ConcreteScraper('TestRetailer')
    raw_deal = {
        'title': 'Test Product',
        'price': 99.99,
        'original_price': 199.99,
        'url': 'https://example.com/product',
        'image': 'https://example.com/image.jpg',
        'rating': 4.5,
        'review_count': 100,
        'category': 'Electronics'
    }

    deal = scraper.standardize_deal(raw_deal)

    assert deal['id'].startswith('testretailer-')
    assert deal['retailer'] == 'TestRetailer'
    assert deal['discount_pct'] == 50
    assert 'scraped_at' in deal
    assert deal['title'] == 'Test Product'
