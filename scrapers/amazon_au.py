from scrapers.base import BaseScraper
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re

class AmazonAUScraper(BaseScraper):
    """Scraper for Amazon Australia Black Friday deals"""

    def __init__(self):
        super().__init__('Amazon AU')
        self.base_url = 'https://www.amazon.com.au'
        self.deals_url = f'{self.base_url}/s?k=black+friday+deals'

    def parse_product_card(self, card) -> Optional[Dict]:
        """Parse a single product card from Amazon"""
        try:
            # Extract title
            title_elem = card.select_one('h2 a')
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True)

            # Extract URL
            url = self.base_url + title_elem['href']

            # Extract current price
            price_whole = card.select_one('.a-price-whole')
            price_fraction = card.select_one('.a-price-fraction')
            if not price_whole:
                return None

            # Combine whole and fractional parts with decimal point
            whole_part = price_whole.get_text(strip=True).replace(',', '')
            fraction_part = price_fraction.get_text(strip=True) if price_fraction else '00'
            price = float(f"{whole_part}.{fraction_part}")

            # Extract original price
            original_price_elem = card.select_one('.a-text-price span')
            original_price = price
            if original_price_elem:
                original_text = original_price_elem.get_text(strip=True)
                original_text = re.sub(r'[^\d.]', '', original_text)
                if original_text:
                    original_price = float(original_text)

            # Extract rating
            rating = 0
            rating_elem = card.select_one('i.a-icon-star span')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                match = re.search(r'(\d+\.?\d*)', rating_text)
                if match:
                    rating = float(match.group(1))

            # Extract review count
            review_count = 0
            review_elem = card.select_one('span.a-size-base')
            if review_elem:
                review_text = review_elem.get_text(strip=True).replace(',', '')
                if review_text.isdigit():
                    review_count = int(review_text)

            # Extract image
            image = ''
            img_elem = card.select_one('img.s-image')
            if img_elem:
                image = img_elem.get('src', '')

            return {
                'title': title,
                'price': price,
                'original_price': original_price,
                'url': url,
                'image': image,
                'rating': rating,
                'review_count': review_count,
                'category': 'Electronics'  # Default category
            }

        except Exception as e:
            print(f"[Amazon AU] Error parsing product card: {str(e)}")
            return None

    async def scrape(self) -> List[Dict]:
        """Scrape Amazon AU Black Friday deals"""
        print(f"[{self.retailer_name}] Starting scrape...")

        html = await self.fetch_page(self.deals_url)
        if not html:
            print(f"[{self.retailer_name}] Failed to fetch deals page")
            return []

        soup = BeautifulSoup(html, 'html.parser')
        product_cards = soup.select('[data-asin]:not([data-asin=""])')

        print(f"[{self.retailer_name}] Found {len(product_cards)} product cards")

        deals = []
        for card in product_cards:
            raw_deal = self.parse_product_card(card)
            if raw_deal and raw_deal['price'] > 0:
                deal = self.standardize_deal(raw_deal)
                deals.append(deal)

        self.deals = deals
        print(f"[{self.retailer_name}] Scraped {len(deals)} deals")
        return deals
