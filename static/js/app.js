// WebSocket connection
const socket = io();

// State
let allDeals = [];
let categories = {};
let currentCategory = null;
let filters = {
    minDiscount: 0,
    minRating: 0
};

// DOM elements
const refreshBtn = document.getElementById('refresh-btn');
const refreshIcon = document.getElementById('refresh-icon');
const refreshText = document.getElementById('refresh-text');
const lastUpdated = document.getElementById('last-updated');
const dealCount = document.getElementById('deal-count');
const progressBar = document.getElementById('progress-bar');
const dealsContainer = document.getElementById('deals-container');
const discountFilter = document.getElementById('discount-filter');
const ratingFilter = document.getElementById('rating-filter');
const discountValue = document.getElementById('discount-value');
const ratingValue = document.getElementById('rating-value');
const modal = document.getElementById('deal-modal');
const closeBtn = document.querySelector('.close-btn');

// Initialize
loadDeals();
setupEventListeners();

function setupEventListeners() {
    // Refresh button
    refreshBtn.addEventListener('click', startRefresh);

    // Filters
    discountFilter.addEventListener('input', (e) => {
        filters.minDiscount = parseInt(e.target.value);
        discountValue.textContent = filters.minDiscount + '%';
        renderDeals();
    });

    ratingFilter.addEventListener('input', (e) => {
        filters.minRating = parseFloat(e.target.value);
        ratingValue.textContent = filters.minRating === 0 ? 'Any' : filters.minRating + '★';
        renderDeals();
    });

    // Modal close
    closeBtn.addEventListener('click', () => {
        modal.classList.remove('show');
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('show');
        }
    });

    // WebSocket events
    socket.on('scraping_progress', (data) => {
        console.log('Progress:', data);
        refreshText.textContent = `${data.retailer}: ${data.deals_found} deals`;
    });

    socket.on('scraping_complete', (data) => {
        console.log('Complete:', data);
        refreshBtn.classList.remove('loading');
        refreshIcon.textContent = '✓';
        refreshText.textContent = 'Refresh Complete';
        progressBar.classList.add('hidden');

        setTimeout(() => {
            refreshIcon.textContent = '🔄';
            refreshText.textContent = 'Refresh Deals';
        }, 2000);

        loadDeals();
    });

    socket.on('scraping_error', (data) => {
        console.error('Error:', data);
        refreshBtn.classList.remove('loading');
        refreshText.textContent = 'Error - Try Again';
        progressBar.classList.add('hidden');
    });
}

async function loadDeals() {
    try {
        const response = await fetch('/api/deals');
        const data = await response.json();

        allDeals = data.deals || [];
        categories = data.categories || {};

        // Update last updated
        if (data.last_updated) {
            const date = new Date(data.last_updated);
            lastUpdated.textContent = `Updated ${formatTimeAgo(date)}`;
        }

        // Render category buttons
        renderCategoryButtons();

        // Set first category as default
        if (!currentCategory && Object.keys(categories).length > 0) {
            currentCategory = Object.keys(categories)[0];
        }

        renderDeals();
    } catch (error) {
        console.error('Failed to load deals:', error);
    }
}

function renderCategoryButtons() {
    const categoryList = document.getElementById('category-list');
    const sortedCategories = Object.keys(categories).sort();

    categoryList.innerHTML = sortedCategories.map(category => `
        <button class="collection-btn ${category === currentCategory ? 'active' : ''}"
                data-category="${category}"
                onclick="selectCategory('${category}')">
            <span class="collection-name">${category}</span>
            <span class="collection-count">${categories[category].length}</span>
        </button>
    `).join('');
}

function selectCategory(category) {
    currentCategory = category;
    document.querySelectorAll('.collection-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.category === category);
    });
    renderDeals();
}

function renderDeals() {
    // Get deals for current category
    const categoryDealIds = categories[currentCategory] || [];
    let deals = allDeals.filter(d => categoryDealIds.includes(d.id));

    // Apply filters
    deals = deals.filter(d => {
        if (filters.minDiscount > 0 && d.discount_pct < filters.minDiscount) return false;
        if (filters.minRating > 0 && d.rating < filters.minRating) return false;
        return true;
    });

    dealCount.textContent = `${deals.length} deals`;

    if (deals.length === 0) {
        dealsContainer.innerHTML = `
            <div class="empty-state">
                <h2>No deals found</h2>
                <p>Try adjusting your filters or refresh deals</p>
            </div>
        `;
        return;
    }

    dealsContainer.innerHTML = deals.map(deal => createDealCard(deal)).join('');

    // Add click handlers
    document.querySelectorAll('.deal-card').forEach(card => {
        card.addEventListener('click', () => {
            showDealModal(allDeals.find(d => d.id === card.dataset.id));
        });
    });
}

function createDealCard(deal) {
    const scoreClass = deal.scores.total >= 80 ? 'excellent' : deal.scores.total >= 60 ? 'good' : 'mediocre';

    return `
        <a href="${deal.url}" target="_blank" rel="noopener noreferrer" class="deal-card-link">
            <div class="deal-card" data-id="${deal.id}">
                <div class="score-badge ${scoreClass}">${deal.scores.total}</div>
                <img src="${deal.image || 'https://via.placeholder.com/300x200?text=No+Image'}"
                     alt="${deal.title}"
                     class="deal-image">
                <div class="deal-content">
                    <h3 class="deal-title">${deal.title}</h3>
                    <div class="deal-price">
                        <span class="price-current">$${deal.price.toFixed(2)}</span>
                        ${deal.original_price > deal.price ? `<span class="price-original">$${deal.original_price.toFixed(2)}</span>` : ''}
                        ${deal.discount_pct > 0 ? `<span class="discount-badge">${deal.discount_pct}% off</span>` : ''}
                    </div>
                    <div class="deal-rating">
                        ${'★'.repeat(Math.round(deal.rating))}${'☆'.repeat(5 - Math.round(deal.rating))}
                        <span>(${deal.review_count})</span>
                    </div>
                    <div class="deal-retailer">${deal.retailer}</div>
                </div>
            </div>
        </a>
    `;
}

function showDealModal(deal) {
    const modalBody = document.getElementById('modal-body');

    modalBody.innerHTML = `
        <img src="${deal.image || 'https://via.placeholder.com/600x400?text=No+Image'}"
             style="width: 100%; border-radius: 8px; margin-bottom: 1rem;">
        <h2>${deal.title}</h2>
        <div style="display: flex; gap: 1rem; margin: 1rem 0; align-items: center;">
            <span style="font-size: 2rem; font-weight: 600;">$${deal.price.toFixed(2)}</span>
            ${deal.original_price > deal.price ? `<span style="text-decoration: line-through; color: #86868b;">$${deal.original_price.toFixed(2)}</span>` : ''}
            ${deal.discount_pct > 0 ? `<span style="background: #ff3b30; color: white; padding: 0.3rem 0.8rem; border-radius: 4px;">${deal.discount_pct}% OFF</span>` : ''}
        </div>
        <div style="margin: 1rem 0;">
            <strong>Rating:</strong> ${deal.rating.toFixed(1)} ★ (${deal.review_count} reviews)
        </div>
        <div style="margin: 1rem 0;">
            <strong>Retailer:</strong> ${deal.retailer}
        </div>
        <div style="margin: 1rem 0;">
            <strong>Value Score:</strong> ${deal.scores.total} / 100
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-top: 0.5rem; font-size: 0.9rem;">
                <div>Discount: ${deal.scores.discount}</div>
                <div>Quality: ${deal.scores.quality}</div>
                <div>Credibility: ${deal.scores.credibility}</div>
                <div>Price Tier: ${deal.scores.price_tier}</div>
                <div>Legitimacy: ${deal.scores.legitimacy}</div>
            </div>
        </div>
        <a href="${deal.url}" target="_blank" style="display: block; background: #0071e3; color: white; padding: 1rem; text-align: center; border-radius: 8px; text-decoration: none; margin-top: 1.5rem;">
            View Deal →
        </a>
    `;

    modal.classList.add('show');
}

async function startRefresh() {
    if (refreshBtn.classList.contains('loading')) return;

    refreshBtn.classList.add('loading');
    refreshIcon.textContent = '⏳';
    refreshText.textContent = 'Triggering local scraper...';
    progressBar.classList.remove('hidden');

    try {
        // First check if local machine is online
        const statusResponse = await fetch('/api/check-local-status');
        const statusData = await statusResponse.json();

        if (statusData.status !== 'online') {
            refreshBtn.classList.remove('loading');
            refreshIcon.textContent = '❌';
            refreshText.textContent = 'Local machine offline';
            progressBar.classList.add('hidden');

            setTimeout(() => {
                refreshIcon.textContent = '🔄';
                refreshText.textContent = 'Refresh Deals';
            }, 3000);
            return;
        }

        // Trigger local scraping
        const triggerResponse = await fetch('/api/trigger-local-scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const triggerData = await triggerResponse.json();

        if (triggerResponse.status === 202) {
            refreshText.textContent = 'Local scraping started...';

            // Poll for updates (GitHub will update, Render will redeploy)
            pollForUpdates();
        } else {
            throw new Error(triggerData.message || 'Failed to trigger scraping');
        }

    } catch (error) {
        console.error('Error:', error);
        refreshBtn.classList.remove('loading');
        refreshIcon.textContent = '❌';
        refreshText.textContent = 'Error - Try Again';
        progressBar.classList.add('hidden');

        setTimeout(() => {
            refreshIcon.textContent = '🔄';
            refreshText.textContent = 'Refresh Deals';
        }, 3000);
    }
}

function pollForUpdates() {
    // Poll every 10 seconds for updated deals
    let pollCount = 0;
    const maxPolls = 36; // 6 minutes max

    const pollInterval = setInterval(async () => {
        pollCount++;

        try {
            const response = await fetch('/api/deals');
            const data = await response.json();

            const currentTime = new Date();
            const lastUpdateTime = new Date(data.last_updated);
            const timeDiff = (currentTime - lastUpdateTime) / 1000; // seconds

            // If data was updated in the last 2 minutes, scraping completed
            if (timeDiff < 120) {
                clearInterval(pollInterval);

                refreshBtn.classList.remove('loading');
                refreshIcon.textContent = '✓';
                refreshText.textContent = 'Refresh Complete';
                progressBar.classList.add('hidden');

                setTimeout(() => {
                    refreshIcon.textContent = '🔄';
                    refreshText.textContent = 'Refresh Deals';
                }, 2000);

                loadDeals();
            } else if (pollCount >= maxPolls) {
                // Timeout after 6 minutes
                clearInterval(pollInterval);

                refreshBtn.classList.remove('loading');
                refreshIcon.textContent = '⏱';
                refreshText.textContent = 'Still processing...';
                progressBar.classList.add('hidden');

                setTimeout(() => {
                    refreshIcon.textContent = '🔄';
                    refreshText.textContent = 'Refresh Deals';
                }, 3000);
            } else {
                // Update progress text
                refreshText.textContent = `Waiting for updates... (${pollCount * 10}s)`;
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 10000); // Poll every 10 seconds
}

function formatTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
    return `${Math.floor(seconds / 86400)} days ago`;
}
