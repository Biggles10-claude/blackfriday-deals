# Black Friday Deal Finder

A web dashboard that scrapes Black Friday deals from Australian retailers, validates pricing, scores deals by genuine value, and presents them through smart collections.

## Features

- **Multi-source scraping**: Amazon AU, JB Hi-Fi, Harvey Norman, The Good Guys
- **Smart scoring**: 5-factor algorithm (discount, quality, credibility, price tier, legitimacy)
- **Smart collections**: Best Overall, Biggest Discounts, Hidden Gems, Verified Drops, Premium Picks
- **Real-time updates**: WebSocket progress during scraping
- **Advanced filtering**: By discount %, rating, price range, retailer

## Installation

```bash
cd blackfriday-aggregator
pip install -r requirements.txt
```

## Usage

```bash
python app.py
```

Open browser to http://localhost:5000

## First Time Use

1. Click "Refresh Deals" button
2. Wait 30-90 seconds for scraping to complete
3. Browse collections in sidebar
4. Apply filters as needed
5. Click deals for detailed view

## Architecture

- **Backend**: Flask + Flask-SocketIO
- **Scrapers**: Async BeautifulSoup4 + httpx
- **Frontend**: Vanilla JavaScript
- **Storage**: JSON file cache

## Scoring Algorithm

Each deal scored 0-100 across 5 dimensions:

- **Discount** (30%): Percentage off original price
- **Quality** (25%): Star rating
- **Credibility** (15%): Review count (log scale)
- **Price Tier** (15%): Higher scores for bigger purchases
- **Legitimacy** (15%): Validates "original price" vs market data

## Collections

- **Best Overall**: Top scores (80+), all categories
- **Biggest Discounts**: 50%+ off, 3.5+ stars
- **Hidden Gems**: High scores (70+), <100 reviews
- **Verified Drops**: Legitimacy score 80+
- **Premium Picks**: $500+, 4.5+ stars

## License

MIT
