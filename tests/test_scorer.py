import pytest
from analyzer.scorer import DealScorer

def test_discount_score():
    scorer = DealScorer()

    assert scorer.calculate_discount_score(10) == 10
    assert scorer.calculate_discount_score(50) == 50
    assert scorer.calculate_discount_score(90) == 90
    assert scorer.calculate_discount_score(95) == 90  # Capped at 90

def test_quality_score():
    scorer = DealScorer()

    assert scorer.calculate_quality_score(5.0) == 100
    assert scorer.calculate_quality_score(4.0) == 80
    assert scorer.calculate_quality_score(3.0) == 50
    assert scorer.calculate_quality_score(2.5) == 40  # Below 3.5 penalized

def test_credibility_score():
    scorer = DealScorer()

    assert scorer.calculate_credibility_score(10) == pytest.approx(30, abs=5)
    assert scorer.calculate_credibility_score(100) == pytest.approx(60, abs=5)
    assert scorer.calculate_credibility_score(1000) == pytest.approx(90, abs=5)

def test_price_tier_score():
    scorer = DealScorer()

    assert scorer.calculate_price_tier_score(30) == 40
    assert scorer.calculate_price_tier_score(150) == 70
    assert scorer.calculate_price_tier_score(500) == 90
    assert scorer.calculate_price_tier_score(1500) == 100

def test_legitimacy_score():
    scorer = DealScorer()

    # Test with no market range (neutral)
    assert scorer.calculate_legitimacy_score(100, 200) == 60

    # Test with market range within 10%
    market_range = {'min': 180, 'max': 220}
    assert scorer.calculate_legitimacy_score(100, 200, market_range) == 100

    # Test with market range 10-20% above
    market_range = {'min': 150, 'max': 190}
    assert scorer.calculate_legitimacy_score(100, 200, market_range) == 70

    # Test with market range 20%+ above
    market_range = {'min': 120, 'max': 160}
    assert scorer.calculate_legitimacy_score(100, 200, market_range) == 30

def test_total_score():
    scorer = DealScorer()

    deal = {
        'discount_pct': 50,
        'rating': 4.5,
        'review_count': 500,
        'price': 600,
        'original_price': 1200
    }

    scores = scorer.score_deal(deal)

    assert 'total' in scores
    assert 'discount' in scores
    assert 'quality' in scores
    assert 'credibility' in scores
    assert 'price_tier' in scores
    assert 'legitimacy' in scores
    assert 0 <= scores['total'] <= 100
