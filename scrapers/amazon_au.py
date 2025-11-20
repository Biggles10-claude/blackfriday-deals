from scrapers.base import BaseScraper
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re

class AmazonAUScraper(BaseScraper):
    """Scraper for Amazon Australia Black Friday deals"""

    def __init__(self):
        super().__init__('Amazon AU')
        self.base_url = 'https://www.amazon.com.au'
        # Product categories for Black Friday deals
        self.deals_categories = [
            ('gaming', 'Gaming'),
            ('electronics', 'Electronics'),
            ('home & kitchen', 'Home & Kitchen'),
            ('sports & fitness', 'Sports & Fitness'),
            ('computers & accessories', 'Computers'),
            ('smart home', 'Smart Home'),
            ('beauty & personal care', 'Beauty & Personal Care'),
            ('tools & home improvement', 'Tools & DIY'),
            # New categories
            ('innovative gadgets', 'Cool Gadgets & Tools'),
            ('desk setup productivity', 'Office & Stationery'),
            ('health gadgets fitness', 'Health & Wellness'),
            ('car accessories', 'Automotive'),
            ('watches bags jewelry', 'Fashion & Accessories')
        ]

    def parse_product_card(self, card) -> Optional[Dict]:
        """Parse a single product card from Amazon"""
        try:
            # Extract title from image alt/aria-label text (Amazon AU structure)
            img_elem = card.select_one('img')
            if not img_elem:
                return None
            # Try aria-label first, fall back to alt
            title = img_elem.get('aria-label', '') or img_elem.get('alt', '')
            title = title.strip()
            if not title:
                return None

            # Extract URL from first link (may be tracking URL, but contains product info)
            link_elem = card.select_one('a[href]')
            if not link_elem:
                return None
            url = link_elem.get('href', '')
            if not url.startswith('http'):
                url = self.base_url + url

            # Extract current price
            price_whole = card.select_one('.a-price-whole')
            price_fraction = card.select_one('.a-price-fraction')
            if not price_whole:
                return None

            # Combine whole and fractional parts with decimal point
            whole_part = price_whole.get_text(strip=True).replace(',', '').rstrip('.')
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

            # Extract image (use the same img element we found for the title)
            image = img_elem.get('src', '') if img_elem else ''

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
            import traceback
            print(f"[Amazon AU] Error parsing product card: {str(e)}")
            traceback.print_exc()
            return None

    async def scrape(self, pages_per_category: int = 3) -> List[Dict]:
        """Scrape discounted deals from Amazon AU (filtering for 10%+ discounts)

        Args:
            pages_per_category: Number of pages per category (default 3 = ~100 deals per category)
        """
        print(f"[{self.retailer_name}] Scraping deals from {len(self.deals_categories)} categories...")

        all_deals = []
        seen_asins = set()

        for search_term, category_name in self.deals_categories:
            print(f"\n[{self.retailer_name}] === {category_name} ===")
            category_deals = 0

            for page_num in range(1, pages_per_category + 1):
                # Search with "deal" keyword to prioritize discounted items
                search_url = f'{self.base_url}/s?k={search_term}+deal&page={page_num}'

                html = await self.fetch_page(search_url)
                if not html:
                    print(f"[{self.retailer_name}] Failed to fetch {category_name} page {page_num}")
                    continue

                soup = BeautifulSoup(html, 'html.parser')
                product_cards = soup.select('[data-asin]:not([data-asin=""])')
                print(f"[{self.retailer_name}] Page {page_num}: {len(product_cards)} products found")

                page_deals = 0
                for card in product_cards:
                    asin = card.get('data-asin', '')
                    if asin in seen_asins:
                        continue

                    raw_deal = self.parse_product_card(card)
                    if raw_deal and raw_deal['price'] > 0:
                        deal = self.standardize_deal(raw_deal)
                        deal['category'] = category_name

                        # ONLY include if it has a discount of 10% or more
                        if deal['discount_pct'] >= 10:
                            all_deals.append(deal)
                            seen_asins.add(asin)
                            page_deals += 1
                            category_deals += 1

                print(f"[{self.retailer_name}] → {page_deals} deals with 10%+ discount")

            print(f"[{self.retailer_name}] {category_name}: {category_deals} total deals")

        self.deals = all_deals
        print(f"\n[{self.retailer_name}] ✅ TOTAL: {len(all_deals)} deals across all categories")
        return all_deals
