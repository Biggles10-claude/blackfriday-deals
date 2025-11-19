from typing import List, Dict

class CategoryOrganizer:
    """Organizes deals by shopping categories"""

    def organize_by_category(self, deals: List[Dict]) -> Dict[str, List[str]]:
        """Group deals by their category field"""
        categories = {}

        for deal in deals:
            category = deal.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append(deal['id'])

        return categories

    def get_category_stats(self, deals: List[Dict]) -> Dict[str, Dict]:
        """Get statistics for each category"""
        stats = {}

        for deal in deals:
            category = deal.get('category', 'Other')
            if category not in stats:
                stats[category] = {
                    'count': 0,
                    'avg_discount': 0,
                    'avg_price': 0,
                    'max_discount': 0
                }

            stats[category]['count'] += 1
            stats[category]['avg_discount'] += deal.get('discount_pct', 0)
            stats[category]['avg_price'] += deal.get('price', 0)
            stats[category]['max_discount'] = max(
                stats[category]['max_discount'],
                deal.get('discount_pct', 0)
            )

        # Calculate averages
        for category in stats:
            count = stats[category]['count']
            if count > 0:
                stats[category]['avg_discount'] /= count
                stats[category]['avg_price'] /= count

        return stats
