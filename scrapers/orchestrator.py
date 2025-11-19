import asyncio
from typing import List, Dict, Callable
from scrapers.amazon_au import AmazonAUScraper
from analyzer.scorer import DealScorer
from analyzer.categories import CategoryOrganizer
import json
from datetime import datetime, timezone

class ScrapingOrchestrator:
    """Orchestrates parallel scraping from all retailers"""

    def __init__(self, progress_callback: Callable = None):
        self.scrapers = [
            AmazonAUScraper(),
            # Add more scrapers here: JBHiFiScraper(), etc.
        ]
        self.scorer = DealScorer()
        self.category_organizer = CategoryOrganizer()
        self.progress_callback = progress_callback

    async def scrape_retailer(self, scraper) -> List[Dict]:
        """Scrape a single retailer and emit progress"""
        try:
            deals = await scraper.scrape()

            if self.progress_callback:
                self.progress_callback({
                    'retailer': scraper.retailer_name,
                    'deals_found': len(deals),
                    'status': 'complete'
                })

            return deals
        except Exception as e:
            print(f"Error scraping {scraper.retailer_name}: {str(e)}")

            if self.progress_callback:
                self.progress_callback({
                    'retailer': scraper.retailer_name,
                    'deals_found': 0,
                    'status': 'failed',
                    'error': str(e)
                })

            return []

    async def scrape_all(self) -> Dict:
        """Scrape all retailers in parallel"""
        print("Starting parallel scraping...")

        # Scrape all retailers concurrently
        tasks = [self.scrape_retailer(scraper) for scraper in self.scrapers]
        results = await asyncio.gather(*tasks)

        # Flatten all deals
        all_deals = []
        for deals in results:
            all_deals.extend(deals)

        print(f"Total deals scraped: {len(all_deals)}")

        # Score all deals
        for deal in all_deals:
            deal['scores'] = self.scorer.score_deal(deal)

        # Organize by categories
        categories = self.category_organizer.organize_by_category(all_deals)
        category_stats = self.category_organizer.get_category_stats(all_deals)

        return {
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'deals': all_deals,
            'categories': categories,
            'category_stats': category_stats
        }
