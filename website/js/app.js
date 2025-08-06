// ETF Analytics Dashboard JavaScript
class ETFDashboard {
    constructor() {
        this.chart = null;
        this.currentData = null;
        this.symbols = [];
        this.init();
    }

    async init() {
        try {
            await this.loadSymbols();
            this.setupEventListeners();
            this.hideLoading();
            
            // Load first ETF by default if available
            if (this.symbols.length > 0) {
                const firstSymbol = this.symbols[0];
                document.getElementById('etf-selector').value = firstSymbol.ticker;
                await this.loadETFData(firstSymbol.ticker);
            }
        } catch (error) {
            console.error('Error initializing dashboard:', error);
            this.showError('Failed to initialize dashboard');
        }
    }

    async loadSymbols() {
        try {
            const response = await fetch('data/symbols.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.symbols = await response.json();
            this.populateSelector();
        } catch (error) {
            console.error('Error loading symbols:', error);
            throw error;
        }
    }

    populateSelector() {
        const selector = document.getElementById('etf-selector');
        selector.innerHTML = '<option value="">Select an ETF...</option>';
        
        this.symbols.forEach(symbol => {
            const option = document.createElement('option');
            option.value = symbol.ticker;
            option.textContent = `${symbol.name} (${symbol.ticker})`;
            selector.appendChild(option);
        });
    }

    setupEventListeners() {
        const selector = document.getElementById('etf-selector');
        selector.addEventListener('change', async (e) => {
            const ticker = e.target.value;
            if (ticker) {
                this.showLoading();
                try {
                    await this.loadETFData(ticker);
                } catch (error) {
                    console.error('Error loading ETF data:', error);
                    this.showError('Failed to load ETF data');
                }
                this.hideLoading();
            } else {
                this.clearData();
            }
        });
    }

    async loadETFData(ticker) {
        try {
            const filename = `${ticker.toLowerCase()}.json`;
            const response = await fetch(`data/${filename}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            this.currentData = await response.json();
            this.updateUI();
            this.createChart();
        } catch (error) {
            console.error('Error loading ETF data:', error);
            throw error;
        }
    }

    updateUI() {
        if (!this.currentData) return;

        const { symbol, metrics, thresholds, lastUpdated } = this.currentData;
        
        // Update ETF info
        document.getElementById('etf-name').textContent = symbol.name;
        document.getElementById('etf-ticker').textContent = symbol.ticker;
        document.getElementById('etf-isin').textContent = symbol.isin;
        
        // Update 52-week metrics
        if (metrics.high52week !== undefined) {
            document.getElementById('high-52week').textContent = 
                metrics.high52week ? `$${metrics.high52week.toFixed(2)}` : 'N/A';
            document.getElementById('high-date').textContent = 
                metrics.highDate ? this.formatDate(metrics.highDate) : 'N/A';
        }
        
        if (metrics.low52week !== undefined) {
            document.getElementById('low-52week').textContent = 
                metrics.low52week ? `$${metrics.low52week.toFixed(2)}` : 'N/A';
            document.getElementById('low-date').textContent = 
                metrics.lowDate ? this.formatDate(metrics.lowDate) : 'N/A';
        }
        
        // Update thresholds
        this.updateThresholds(thresholds);
        
        // Update last updated time
        document.getElementById('last-updated').textContent = 
            this.formatDateTime(lastUpdated);
    }

    updateThresholds(thresholds) {
        const grid = document.getElementById('thresholds-grid');
        grid.innerHTML = '';
        
        if (!thresholds || thresholds.length === 0) {
            grid.innerHTML = '<p class="no-data">No threshold data available</p>';
            return;
        }
        
        // Get current price for comparison
        const currentPrice = this.getCurrentPrice();
        
        thresholds.forEach(threshold => {
            const card = document.createElement('div');
            card.className = 'threshold-card';
            
            // Check if threshold has been reached
            if (currentPrice && threshold.thresholdPrice && currentPrice <= threshold.thresholdPrice) {
                card.classList.add('reached');
            }
            
            card.innerHTML = `
                <div class="threshold-percentage">${threshold.percentage}% Drop</div>
                <div class="threshold-price">
                    ${threshold.thresholdPrice ? `$${threshold.thresholdPrice.toFixed(2)}` : 'N/A'}
                </div>
            `;
            
            grid.appendChild(card);
        });
    }

    getCurrentPrice() {
        if (!this.currentData || !this.currentData.priceData || this.currentData.priceData.length === 0) {
            return null;
        }
        
        // Get the most recent price
        const latestData = this.currentData.priceData[this.currentData.priceData.length - 1];
        return latestData.close;
    }

    createChart() {
        if (!this.currentData || !this.currentData.priceData) return;

        const ctx = document.getElementById('priceChart').getContext('2d');
        
        // Destroy existing chart if it exists
        if (this.chart) {
            this.chart.destroy();
        }

        // Prepare data for Chart.js
        const priceData = this.currentData.priceData;
        const labels = priceData.map(item => item.date);
        const prices = priceData.map(item => item.close);
        
        // Create datasets
        const datasets = [{
            label: 'Close Price',
            data: prices,
            borderColor: '#667eea',
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.1
        }];

        // Add 52-week high/low lines
        const { metrics, thresholds } = this.currentData;
        
        if (metrics.high52week) {
            datasets.push({
                label: '52-Week High',
                data: new Array(labels.length).fill(metrics.high52week),
                borderColor: '#10b981',
                borderWidth: 2,
                borderDash: [5, 5],
                fill: false,
                pointRadius: 0
            });
        }
        
        if (metrics.low52week) {
            datasets.push({
                label: '52-Week Low',
                data: new Array(labels.length).fill(metrics.low52week),
                borderColor: '#ef4444',
                borderWidth: 2,
                borderDash: [5, 5],
                fill: false,
                pointRadius: 0
            });
        }

        // Add threshold lines
        const colors = ['#f59e0b', '#f97316', '#dc2626', '#b91c1c', '#7f1d1d'];
        thresholds.forEach((threshold, index) => {
            if (threshold.thresholdPrice) {
                datasets.push({
                    label: `${threshold.percentage}% Drop`,
                    data: new Array(labels.length).fill(threshold.thresholdPrice),
                    borderColor: colors[index % colors.length],
                    borderWidth: 1,
                    borderDash: [3, 3],
                    fill: false,
                    pointRadius: 0
                });
            }
        });

        // Create chart
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    title: {
                        display: true,
                        text: `${this.currentData.symbol.name} - 3 Month Price History`,
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: $${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        },
                        type: 'time',
                        time: {
                            parser: 'YYYY-MM-DD',
                            tooltipFormat: 'MMM DD, YYYY',
                            displayFormats: {
                                day: 'MMM DD',
                                week: 'MMM DD',
                                month: 'MMM YYYY'
                            }
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Price ($)'
                        },
                        beginAtZero: false
                    }
                }
            }
        });
    }

    clearData() {
        document.getElementById('etf-name').textContent = '-';
        document.getElementById('etf-ticker').textContent = '-';
        document.getElementById('etf-isin').textContent = '-';
        document.getElementById('high-52week').textContent = '-';
        document.getElementById('high-date').textContent = '-';
        document.getElementById('low-52week').textContent = '-';
        document.getElementById('low-date').textContent = '-';
        document.getElementById('last-updated').textContent = '-';
        document.getElementById('thresholds-grid').innerHTML = '';
        
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }

    showLoading() {
        document.getElementById('loading').style.display = 'flex';
        document.getElementById('error-message').style.display = 'none';
    }

    hideLoading() {
        document.getElementById('loading').style.display = 'none';
    }

    showError(message) {
        document.getElementById('error-message').style.display = 'block';
        document.getElementById('error-message').querySelector('p').textContent = message;
        this.hideLoading();
    }

    formatDate(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } catch (error) {
            return dateString;
        }
    }

    formatDateTime(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return dateString;
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ETFDashboard();
});