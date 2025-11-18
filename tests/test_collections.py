import pytest
from analyzer.collections import CollectionBuilder

def create_mock_deal(deal_id, total_score, discount_pct, rating, review_count, price):
    return {
        'id': deal_id,
        'title': f'Product {deal_id}',
        'price': price,
        'original_price': price * 2,
        'discount_pct': discount_pct,
        'rating': rating,
        'review_count': review_count,
        'scores': {
            'total': total_score,
            'discount': discount_pct,
            'quality': rating * 20,
            'legitimacy': 80
        }
    }

def test_best_overall_collection():
    builder = CollectionBuilder()

    deals = [
        create_mock_deal('deal1', 85, 50, 4.5, 200, 500),
        create_mock_deal('deal2', 75, 40, 4.0, 150, 300),  # Below 80 threshold
        create_mock_deal('deal3', 90, 60, 5.0, 500, 800),
        create_mock_deal('deal4', 55, 30, 3.0, 50, 100),  # Below threshold
    ]

    collection = builder.build_best_overall(deals)

    assert len(collection) == 2  # Only deals with 80+ score and 3.5+ rating
    assert collection[0] == 'deal3'  # Highest score first
    assert collection[1] == 'deal1'

def test_biggest_discounts_collection():
    builder = CollectionBuilder()

    deals = [
        create_mock_deal('deal1', 70, 50, 4.5, 200, 500),
        create_mock_deal('deal2', 80, 70, 4.0, 150, 300),
        create_mock_deal('deal3', 65, 45, 3.0, 100, 200),  # Below 50% and 3.5 rating
        create_mock_deal('deal4', 75, 60, 4.2, 300, 600),
    ]

    collection = builder.build_biggest_discounts(deals)

    assert len(collection) == 3  # Only 50%+ discount and 3.5+ rating
    assert collection[0] == 'deal2'  # 70% discount
    assert collection[1] == 'deal4'  # 60% discount
    assert collection[2] == 'deal1'  # 50% discount

def test_all_collections():
    builder = CollectionBuilder()

    deals = [
        create_mock_deal('deal1', 85, 55, 4.8, 80, 700),    # Hidden gem
        create_mock_deal('deal2', 90, 60, 4.5, 500, 900),   # Best overall
        create_mock_deal('deal3', 82, 50, 4.9, 1200, 600),  # Premium pick
    ]

    collections = builder.build_all_collections(deals)

    assert 'best_overall' in collections
    assert 'biggest_discounts' in collections
    assert 'hidden_gems' in collections
    assert 'verified_drops' in collections
    assert 'premium_picks' in collections
