// app.js - Simple API calls
async function loadPortfolio() {
    try {
        const response = await fetch('/api/portfolio');
        const data = await response.json();
        
        if (!response.ok) {
            showError(data.error || 'Failed to load portfolio');
            return;
        }
        
        displayPortfolio(data);
    } catch (error) {
        showError(error.message);
    }
}

function displayPortfolio(data) {
    const html = `
        <div class="stats">
            <div class="stat">
                <div class="stat-label">Total Value</div>
                <div class="stat-value">₹${data.total_value?.toLocaleString() || 0}</div>
                <div class="stat-subtext">Mode: ${data.mode === 'live' ? '🟢 Live' : '📄 Paper'}</div>
            </div>
            <div class="stat">
                <div class="stat-label">Cash Available</div>
                <div class="stat-value">₹${data.cash_available?.toLocaleString() || 0}</div>
            </div>
            <div class="stat">
                <div class="stat-label">Invested</div>
                <div class="stat-value">₹${data.invested_value?.toLocaleString() || 0}</div>
            </div>
            <div class="stat">
                <div class="stat-label">P&L</div>
                <div class="stat-value" style="color: ${data.unrealized_pnl >= 0 ? 'green' : 'red'}">
                    ${data.unrealized_pnl >= 0 ? '+' : ''}₹${data.unrealized_pnl?.toLocaleString() || 0}
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('portfolio-data').innerHTML = html;
}

function showError(message) {
    document.getElementById('error-container').innerHTML = `<div class="error">❌ ${message}</div>`;
    document.getElementById('portfolio-data').innerHTML = '<div class="loading">Failed to load</div>';
}
