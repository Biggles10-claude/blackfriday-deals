import math
from typing import Dict

class DealScorer:
    """Calculates value scores for deals based on multiple dimensions"""

    # Scoring weights
    WEIGHTS = {
        'discount': 0.30,
        'quality': 0.25,
        'credibility': 0.15,
        'price_tier': 0.15,
        'legitimacy': 0.15
    }

    def calculate_discount_score(self, discount_pct: float) -> float:
        """Score based on discount percentage (0-100)"""
        # Linear scale, capped at 90 to prevent scam detection
        return min(discount_pct, 90)

    def calculate_quality_score(self, rating: float) -> float:
        """Score based on star rating (0-100)"""
        if rating == 0:
            return 0

        # 5 stars = 100, 4 stars = 80, 3 stars = 50
        # Below 3.5 penalized heavily
        if rating >= 4.5:
            return 100
        elif rating >= 4.0:
            return 80
        elif rating >= 3.5:
            return 65
        elif rating >= 3.0:
            return 50
        else:
            return max(40, rating * 10)  # Below 3.5 gets max 40

    def calculate_credibility_score(self, review_count: int) -> float:
        """Score based on review count (0-100) using log scale"""
        if review_count == 0:
            return 0

        # Log scale: 10 reviews = ~30, 100 = ~60, 1000+ = ~90
        # Formula: 30 * log10(review_count)
        score = 30 * math.log10(review_count)
        return min(score, 100)

    def calculate_price_tier_score(self, price: float) -> float:
        """Score based on price tier (0-100)"""
        if price < 50:
            return 40
        elif price < 200:
            return 70
        elif price < 1000:
            return 90
        else:
            return 100

    def calculate_legitimacy_score(self, price: float, original_price: float,
                                   market_range: Dict = None) -> float:
        """Score based on price legitimacy (0-100)"""
        # Default to neutral if no market data
        if not market_range:
            return 60

        market_min = market_range.get('min', original_price)
        market_max = market_range.get('max', original_price)
        market_avg = (market_min + market_max) / 2

        # Calculate how much above market average the "original price" is
        if market_avg > 0:
            markup_pct = ((original_price - market_avg) / market_avg) * 100

            if markup_pct <= 10:
                return 100  # Within 10% = verified legitimate
            elif markup_pct <= 20:
                return 70   # 10-20% above = slightly suspicious
            else:
                return 30   # 20%+ above = likely inflated RRP

        return 60

    def score_deal(self, deal: Dict, market_range: Dict = None) -> Dict[str, float]:
        """Calculate all scores for a deal"""
        scores = {
            'discount': self.calculate_discount_score(deal.get('discount_pct', 0)),
            'quality': self.calculate_quality_score(deal.get('rating', 0)),
            'credibility': self.calculate_credibility_score(deal.get('review_count', 0)),
            'price_tier': self.calculate_price_tier_score(deal.get('price', 0)),
            'legitimacy': self.calculate_legitimacy_score(
                deal.get('price', 0),
                deal.get('original_price', 0),
                market_range
            )
        }

        # Calculate weighted total
        total = sum(scores[key] * self.WEIGHTS[key] for key in scores.keys())
        scores['total'] = round(total, 1)

        return scores
