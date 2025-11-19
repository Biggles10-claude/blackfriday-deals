from typing import List, Dict

class CollectionBuilder:
    """Builds smart collections from scored deals"""

    def build_best_overall(self, deals: List[Dict], limit: int = 50) -> List[str]:
        """Top deals by total score - if no high-scoring deals, show all deals"""
        # Try to get deals with score >= 80 and rating >= 3.5
        filtered = [
            d for d in deals
            if d['scores']['total'] >= 80
            and d.get('rating', 0) >= 3.5
        ]

        # If no deals meet strict criteria, show all deals sorted by score
        if not filtered:
            filtered = deals

        sorted_deals = sorted(filtered, key=lambda x: x['scores']['total'], reverse=True)
        return [d['id'] for d in sorted_deals[:limit]]

    def build_biggest_discounts(self, deals: List[Dict], limit: int = 50) -> List[str]:
        """Highest discount %, minimum 50% off and 3.5+ stars"""
        filtered = [
            d for d in deals
            if d.get('discount_pct', 0) >= 50
            and d.get('rating', 0) >= 3.5
        ]

        sorted_deals = sorted(filtered, key=lambda x: x['discount_pct'], reverse=True)
        return [d['id'] for d in sorted_deals[:limit]]

    def build_hidden_gems(self, deals: List[Dict], limit: int = 50) -> List[str]:
        """High scores (70+) but <100 reviews"""
        filtered = [
            d for d in deals
            if d['scores']['total'] >= 70
            and d.get('review_count', 0) < 100
            and d.get('rating', 0) >= 4.0
        ]

        sorted_deals = sorted(filtered, key=lambda x: x['scores']['total'], reverse=True)
        return [d['id'] for d in sorted_deals[:limit]]

    def build_verified_drops(self, deals: List[Dict], limit: int = 50) -> List[str]:
        """Deals with legitimacy score 80+ (verified price drops)"""
        filtered = [
            d for d in deals
            if d['scores'].get('legitimacy', 0) >= 80
            and d['scores']['total'] >= 60
        ]

        sorted_deals = sorted(filtered, key=lambda x: x['scores']['total'], reverse=True)
        return [d['id'] for d in sorted_deals[:limit]]

    def build_premium_picks(self, deals: List[Dict], limit: int = 50) -> List[str]:
        """High-value items (>$500) with 4.5+ stars and verified pricing"""
        filtered = [
            d for d in deals
            if d.get('price', 0) > 500
            and d.get('rating', 0) >= 4.5
            and d['scores'].get('legitimacy', 0) >= 70
        ]

        sorted_deals = sorted(filtered, key=lambda x: x['scores']['total'], reverse=True)
        return [d['id'] for d in sorted_deals[:limit]]

    def build_all_collections(self, deals: List[Dict]) -> Dict[str, List[str]]:
        """Build all smart collections"""
        return {
            'best_overall': self.build_best_overall(deals),
            'biggest_discounts': self.build_biggest_discounts(deals),
            'hidden_gems': self.build_hidden_gems(deals),
            'verified_drops': self.build_verified_drops(deals),
            'premium_picks': self.build_premium_picks(deals)
        }
