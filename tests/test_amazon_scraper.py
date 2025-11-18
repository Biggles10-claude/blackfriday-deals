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

    # Mock HTML for a product card
    html = '''
    <div data-asin="B08N5WRWNW">
        <h2><a href="/dp/B08N5WRWNW">Samsung Galaxy Tab</a></h2>
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

    assert deal is not None
    assert deal['title'] == 'Samsung Galaxy Tab'
    assert deal['price'] == 599.00
    assert deal['original_price'] == 1199.00
