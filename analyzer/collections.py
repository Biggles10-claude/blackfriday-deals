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
        """Highest discount %, minimum 20% off"""
        filtered = [
            d for d in deals
            if d.get('discount_pct', 0) >= 20
        ]

        sorted_deals = sorted(filtered, key=lambda x: x['discount_pct'], reverse=True)
        return [d['id'] for d in sorted_deals[:limit]]

    def build_hidden_gems(self, deals: List[Dict], limit: int = 50) -> List[str]:
        """Good discounts (25%+) with lower review counts"""
        filtered = [
            d for d in deals
            if d.get('discount_pct', 0) >= 25
            and d.get('review_count', 0) < 500
        ]

        sorted_deals = sorted(filtered, key=lambda x: x['scores']['total'], reverse=True)
        return [d['id'] for d in sorted_deals[:limit]]

    def build_verified_drops(self, deals: List[Dict], limit: int = 50) -> List[str]:
        """Deals with decent legitimacy (60+) and discounts"""
        filtered = [
            d for d in deals
            if d['scores'].get('legitimacy', 0) >= 60
            and d.get('discount_pct', 0) >= 15
        ]

        sorted_deals = sorted(filtered, key=lambda x: x['scores']['total'], reverse=True)
        return [d['id'] for d in sorted_deals[:limit]]

    def build_premium_picks(self, deals: List[Dict], limit: int = 50) -> List[str]:
        """Higher-value items ($100+) with good discounts"""
        filtered = [
            d for d in deals
            if d.get('price', 0) >= 100
            and d.get('discount_pct', 0) >= 20
        ]

        sorted_deals = sorted(filtered, key=lambda x: x['price'], reverse=True)
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
