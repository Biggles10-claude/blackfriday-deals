import pytest
from scrapers.amazon_au import AmazonAUScraper

@pytest.mark.asyncio
async def test_amazon_scraper_initialization():
    scraper = AmazonAUScraper()
    assert scraper.retailer_name == 'Amazon AU'
    assert scraper.base_url == 'https://www.amazon.com.au'

@pytest.mark.asyncio
async def test_parse_product_card():
    scraper = AmazonAUScraper()

    # Mock HTML for a product card with ALL fields
    html = '''
    <div data-asin="B08N5WRWNW">
        <h2><a href="/dp/B08N5WRWNW">Samsung Galaxy Tab</a></h2>
        <img class="s-image" src="https://m.media-amazon.com/images/I/61abc123.jpg" />
        <span class="a-price-whole">599</span>
        <span class="a-price-decimal">.</span>
        <span class="a-price-fraction">00</span>
        <span class="a-text-price"><span>$1,199.00</span></span>
        <i class="a-icon-star"><span>4.6 out of 5 stars</span></i>
        <span class="a-size-base">1,247</span>
    </div>
    '''

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    card = soup.find('div')

    deal = scraper.parse_product_card(card)

    # Assert ALL fields extracted by parse_product_card
    assert deal is not None
    assert deal['title'] == 'Samsung Galaxy Tab'
    assert deal['price'] == 599.00
    assert deal['original_price'] == 1199.00
    assert deal['url'] == 'https://www.amazon.com.au/dp/B08N5WRWNW'
    assert deal['image'] == 'https://m.media-amazon.com/images/I/61abc123.jpg'
    assert deal['rating'] == 4.6
    assert deal['review_count'] == 1247
    assert deal['category'] == 'Electronics'
