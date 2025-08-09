// ETF Analytics Dashboard JavaScript
class ETFDashboard {
    constructor() {
        this.chart = null;
        this.currentData = null;
        this.symbols = [];
        this.currentCurrency = 'EUR'; // Default to EUR
        this.currentTimeRange = '1y'; // Default to 1 year
        this.chartMetrics = {
            show52WeekHigh: true,
            show52WeekLow: true,
            showThresholds: false
        };
        console.log('🚀 ETF Dashboard initialized with EUR as default currency');
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
        const currencySelector = document.getElementById('currency-selector');
        const timeSelector = document.getElementById('time-filter');
        
        // Initialize selectors with defaults
        if (currencySelector) {
            currencySelector.value = 'EUR';
            console.log('💱 Currency selector initialized with EUR as default');
        }
        if (timeSelector) {
            timeSelector.value = '1y';
            console.log('⏰ Time filter initialized with 1 year as default');
        }
        
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
        
        // Currency toggle event listener
        if (currencySelector) {
            currencySelector.addEventListener('change', (e) => {
                this.currentCurrency = e.target.value;
                console.log(`🔄 Currency changed to: ${this.currentCurrency}`);
                if (this.currentData) {
                    this.updateUI();
                    this.createChart();
                }
            });
        }
        
        // Time range toggle event listener
        if (timeSelector) {
            timeSelector.addEventListener('change', async (e) => {
                this.currentTimeRange = e.target.value;
                console.log(`🕒 Time range changed to: ${this.currentTimeRange}`);
                if (this.currentData) {
                    this.updateUI();
                    this.createChart();
                }
            });
        }
        
        // Chart metrics toggles
        const show52WeekHigh = document.getElementById('show-52week-high');
        const show52WeekLow = document.getElementById('show-52week-low');
        const showThresholds = document.getElementById('show-thresholds');
        
        if (show52WeekHigh) {
            show52WeekHigh.addEventListener('change', (e) => {
                this.chartMetrics.show52WeekHigh = e.target.checked;
                console.log(`📊 52-week high toggle: ${e.target.checked}`);
                if (this.currentData) {
                    this.createChart();
                }
            });
        }
        
        if (show52WeekLow) {
            show52WeekLow.addEventListener('change', (e) => {
                this.chartMetrics.show52WeekLow = e.target.checked;
                console.log(`📊 52-week low toggle: ${e.target.checked}`);
                if (this.currentData) {
                    this.createChart();
                }
            });
        }
        
        if (showThresholds) {
            showThresholds.addEventListener('change', (e) => {
                this.chartMetrics.showThresholds = e.target.checked;
                console.log(`📊 Thresholds toggle: ${e.target.checked}`);
                if (this.currentData) {
                    this.createChart();
                }
            });
        }
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
            this.createChart(); // Default to EUR
        } catch (error) {
            console.error('Error loading ETF data:', error);
            throw error;
        }
    }

    updateUI() {
        if (!this.currentData) return;

        const { symbol, metrics, thresholds, lastUpdated } = this.currentData;
        
        console.log(`🔄 Updating UI with currency: ${this.currentCurrency}`);
        
        // Update ETF info
        document.getElementById('etf-name').textContent = symbol.name;
        document.getElementById('etf-ticker').textContent = symbol.ticker;
        document.getElementById('etf-isin').textContent = symbol.isin;
        
        // Update 52-week metrics (use EUR if available)
        if (metrics.high52week !== undefined) {
            const highPrice = this.formatCurrency(metrics.high52week, this.currentCurrency);
            document.getElementById('high-52week').textContent = highPrice;
            document.getElementById('high-date').textContent = 
                metrics.highDate ? this.formatDate(metrics.highDate) : 'N/A';
            console.log(`📊 52-week high: ${highPrice} (${this.currentCurrency})`);
        }
        
        if (metrics.low52week !== undefined) {
            const lowPrice = this.formatCurrency(metrics.low52week, this.currentCurrency);
            document.getElementById('low-52week').textContent = lowPrice;
            document.getElementById('low-date').textContent = 
                metrics.lowDate ? this.formatDate(metrics.lowDate) : 'N/A';
            console.log(`📊 52-week low: ${lowPrice} (${this.currentCurrency})`);
        }
        
        // Update thresholds
        this.updateThresholds(thresholds);
        
        // Update profit targets
        this.updateProfitTargets(thresholds);
        
        // Note: last-updated element removed from HTML
    }

    updateThresholds(thresholds) {
        const grid = document.getElementById('thresholds-grid');
        grid.innerHTML = '';
        
        if (!thresholds || thresholds.length === 0) {
            grid.innerHTML = '<p class="no-data">No threshold data available</p>';
            return;
        }
        
        // Get current price for comparison
        const currentPrice = this.getCurrentPrice(this.currentCurrency);
        
        thresholds.forEach(threshold => {
            const card = document.createElement('div');
            card.className = 'threshold-card';
            
            // Convert threshold price to current currency
            const thresholdPrice = this.currentCurrency === 'EUR' ? 
                this.convertToEUR(threshold.thresholdPrice) : 
                threshold.thresholdPrice;
            
            // Check if threshold has been reached
            if (currentPrice && thresholdPrice && currentPrice <= thresholdPrice) {
                card.classList.add('reached');
            }
            
            const currencySymbol = this.currentCurrency === 'EUR' ? '€' : '$';
            card.innerHTML = `
                <div class="threshold-percentage">${threshold.percentage}% Drop</div>
                <div class="threshold-price">
                    ${thresholdPrice ? `${currencySymbol}${thresholdPrice.toFixed(2)}` : 'N/A'}
                </div>
            `;
            
            grid.appendChild(card);
        });
    }

    updateProfitTargets(thresholds) {
        const grid = document.getElementById('profit-targets-grid');
        const filterSelect = document.getElementById('threshold-filter');
        const clearButton = document.getElementById('clear-filter');
        
        if (!grid || !filterSelect || !clearButton) {
            console.error('Required elements not found for profit targets');
            return;
        }
        
        // Clear the grid initially
        grid.innerHTML = '';
        
        if (!thresholds || thresholds.length === 0) {
            grid.innerHTML = '<p class="no-data">No entry point data available</p>';
            return;
        }
        
        // Populate the filter dropdown
        this.populateThresholdFilter(thresholds);
        
        // Set up event listeners for filter
        this.setupProfitTargetsFilter(thresholds, grid);
        
        // Initially show empty grid until user selects a threshold
        grid.innerHTML = '';
    }

    populateThresholdFilter(thresholds) {
        const filterSelect = document.getElementById('threshold-filter');
        if (!filterSelect) return;
        
        // Clear existing options except the first one
        filterSelect.innerHTML = '<option value="">Choose an entry point...</option>';
        
        // Add options for each threshold
        thresholds.forEach((threshold) => {
            if (threshold.thresholdPrice) {
                const option = document.createElement('option');
                option.value = threshold.percentage;
                
                // Convert price to current currency
                const thresholdPrice = this.currentCurrency === 'EUR' ? 
                    this.convertToEUR(threshold.thresholdPrice) : 
                    threshold.thresholdPrice;
                
                const currencySymbol = this.currentCurrency === 'EUR' ? '€' : '$';
                option.textContent = `${threshold.percentage}% Drop (${currencySymbol}${thresholdPrice.toFixed(2)})`;
                filterSelect.appendChild(option);
            }
        });
    }

    setupProfitTargetsFilter(thresholds, grid) {
        const filterSelect = document.getElementById('threshold-filter');
        const clearButton = document.getElementById('clear-filter');
        
        if (!filterSelect || !clearButton) {
            console.error('Filter elements not found');
            return;
        }
        
        // Remove existing event listeners if they exist
        if (filterSelect._hasListeners) {
            filterSelect.removeEventListener('change', filterSelect._changeHandler);
            clearButton.removeEventListener('click', clearButton._clickHandler);
        }
        
        // Filter change event
        const changeHandler = (e) => {
            const selectedPercentage = parseInt(e.target.value);
            if (selectedPercentage) {
                this.showProfitTargetsForThreshold(thresholds, selectedPercentage, grid);
                clearButton.disabled = false;
            } else {
                grid.innerHTML = '';
                clearButton.disabled = true;
            }
        };
        
        // Clear button event
        const clickHandler = () => {
            filterSelect.value = '';
            grid.innerHTML = '';
            clearButton.disabled = true;
        };
        
        // Add event listeners
        filterSelect.addEventListener('change', changeHandler);
        clearButton.addEventListener('click', clickHandler);
        
        // Store references to handlers for later removal
        filterSelect._changeHandler = changeHandler;
        clearButton._clickHandler = clickHandler;
        filterSelect._hasListeners = true;
        clearButton._hasListeners = true;
        
        // Initially disable the clear button
        clearButton.disabled = true;
        
        // Ensure the filter is properly initialized
        filterSelect.value = '';
        grid.innerHTML = '';
    }

    showProfitTargetsForThreshold(thresholds, selectedPercentage, grid) {
        // Find the selected threshold
        const selectedThreshold = thresholds.find(t => t.percentage === selectedPercentage);
        if (!selectedThreshold || !selectedThreshold.thresholdPrice) {
            grid.innerHTML = '<p class="no-data">Selected entry point not found</p>';
            return;
        }
        
        // Clear the grid
        grid.innerHTML = '';
        
        // Get current price for comparison
        const currentPrice = this.getCurrentPrice(this.currentCurrency);
        
        // Define profit target percentages
        const profitTargets = [10, 20, 50, 100];
        
        // Convert threshold price to current currency
        const entryPrice = this.currentCurrency === 'EUR' ? 
            this.convertToEUR(selectedThreshold.thresholdPrice) : 
            selectedThreshold.thresholdPrice;
        
        // Create profit target cards for the selected threshold
        profitTargets.forEach(profitPercent => {
            const profitTargetPrice = entryPrice * (1 + profitPercent / 100);
            
            const card = document.createElement('div');
            card.className = 'profit-target-card';
            
            // Check if profit target has been reached
            if (currentPrice && currentPrice >= profitTargetPrice) {
                card.classList.add('reached');
            }
            
            const currencySymbol = this.currentCurrency === 'EUR' ? '€' : '$';
            
            // Create the card content
            card.innerHTML = `
                <div class="profit-target-header">
                    <div class="profit-target-percentage">${profitPercent}% Profit</div>
                    <div class="entry-point-info">from ${selectedThreshold.percentage}% Drop Entry</div>
                </div>
                <div class="profit-target-price">
                    ${currencySymbol}${profitTargetPrice.toFixed(2)}
                </div>
                <div class="entry-point-price">
                    Entry: ${currencySymbol}${entryPrice.toFixed(2)}
                </div>
            `;
            
            grid.appendChild(card);
        });
    }

    getCurrentPrice(currency = 'original') {
        if (!this.currentData || !this.currentData.priceData || this.currentData.priceData.length === 0) {
            return null;
        }
        
        // Get the most recent price
        const latestData = this.currentData.priceData[this.currentData.priceData.length - 1];
        
        // Return EUR price if available and requested, otherwise original price
        if (currency === 'EUR' && latestData.close_eur !== null && latestData.close_eur !== undefined) {
            return latestData.close_eur;
        }
        
        return latestData.close;
    }

    createChart() {
        if (!this.currentData || !this.currentData.priceData) return;

        const ctx = document.getElementById('priceChart').getContext('2d');
        
        // Destroy existing chart if it exists
        if (this.chart) {
            this.chart.destroy();
        }

        // Filter data based on time range
        const filteredData = this.filterDataByTimeRange(this.currentData.priceData);
        
        if (filteredData.length === 0) {
            console.log('No data available for selected time range');
            return;
        }

        // Prepare data for Chart.js
        const labels = filteredData.map(item => item.date);
        
        // Choose price field based on currency preference
        const priceField = this.currentCurrency === 'EUR' ? 'close_eur' : 'close';
        const prices = filteredData.map(item => item[priceField]).filter(price => price !== null && price !== undefined);
        
        // Create datasets
        const datasets = [{
            label: `Close Price (${this.currentCurrency === 'EUR' ? 'EUR' : 'USD'})`,
            data: prices,
            borderColor: '#667eea',
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.1
        }];

        // Add optional metrics based on user selection
        const { metrics, thresholds } = this.currentData;
        
        // Add 52-week high if enabled
        if (this.chartMetrics.show52WeekHigh && metrics.high52week) {
            let high52week = metrics.high52week;
            if (this.currentCurrency === 'EUR') {
                high52week = this.convertToEUR(metrics.high52week);
            }
            
            datasets.push({
                label: '52-Week High',
                data: new Array(labels.length).fill(high52week),
                borderColor: '#10b981',
                borderWidth: 2,
                borderDash: [5, 5],
                fill: false,
                pointRadius: 0
            });
        }
        
        // Add 52-week low if enabled
        if (this.chartMetrics.show52WeekLow && metrics.low52week) {
            let low52week = metrics.low52week;
            if (this.currentCurrency === 'EUR') {
                low52week = this.convertToEUR(metrics.low52week);
            }
            
            datasets.push({
                label: '52-Week Low',
                data: new Array(labels.length).fill(low52week),
                borderColor: '#ef4444',
                borderWidth: 2,
                borderDash: [5, 5],
                fill: false,
                pointRadius: 0
            });
        }

        // Add threshold lines if enabled
        if (this.chartMetrics.showThresholds) {
            const colors = ['#f59e0b', '#f97316', '#dc2626', '#b91c1c', '#7f1d1d'];
            thresholds.forEach((threshold, index) => {
                if (threshold.thresholdPrice) {
                    let thresholdPrice = threshold.thresholdPrice;
                    if (this.currentCurrency === 'EUR') {
                        thresholdPrice = this.convertToEUR(threshold.thresholdPrice);
                    }
                    
                    datasets.push({
                        label: `${threshold.percentage}% Drop`,
                        data: new Array(labels.length).fill(thresholdPrice),
                        borderColor: colors[index % colors.length],
                        borderWidth: 1,
                        borderDash: [3, 3],
                        fill: false,
                        pointRadius: 0
                    });
                }
            });
        }

        // Create chart with simplified configuration
        try {
            this.chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: `${this.currentData.symbol.name} - Price History (${this.currentCurrency === 'EUR' ? 'EUR' : 'USD'}) - ${this.getTimeRangeDisplayName()}`
                        },
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Date'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: `Price (${this.currentCurrency === 'EUR' ? '€' : '$'})`
                            },
                            beginAtZero: false
                        }
                    }
                }
            });
            console.log('Chart created successfully');
        } catch (error) {
            console.error('Error creating chart:', error);
        }
    }

    filterDataByTimeRange(priceData) {
        if (!priceData || priceData.length === 0) return [];
        
        const now = new Date();
        let cutoffDate = new Date();
        
        switch (this.currentTimeRange) {
            case '1y':
                cutoffDate.setFullYear(now.getFullYear() - 1);
                break;
            case '2y':
                cutoffDate.setFullYear(now.getFullYear() - 2);
                break;
            case '3y':
                cutoffDate.setFullYear(now.getFullYear() - 3);
                break;
            case 'all':
                // Return all data
                return priceData;
            default:
                cutoffDate.setFullYear(now.getFullYear() - 1);
        }
        
        return priceData.filter(item => {
            const itemDate = new Date(item.date);
            return itemDate >= cutoffDate;
        });
    }

    getTimeRangeDisplayName() {
        switch (this.currentTimeRange) {
            case '1y': return '1 Year';
            case '2y': return '2 Years';
            case '3y': return '3 Years';
            case 'all': return 'All Time';
            default: return '1 Year';
        }
    }

    clearData() {
        document.getElementById('etf-name').textContent = '-';
        document.getElementById('etf-ticker').textContent = '-';
        document.getElementById('etf-isin').textContent = '-';
        document.getElementById('high-52week').textContent = '-';
        document.getElementById('high-date').textContent = '-';
        document.getElementById('low-52week').textContent = '-';
        document.getElementById('low-date').textContent = '-';
        document.getElementById('thresholds-grid').innerHTML = '';
        document.getElementById('profit-targets-grid').innerHTML = '';
        
        // Reset the profit targets filter
        const filterSelect = document.getElementById('threshold-filter');
        const clearButton = document.getElementById('clear-filter');
        if (filterSelect) {
            filterSelect.innerHTML = '<option value="">Choose an entry point...</option>';
        }
        if (clearButton) {
            clearButton.disabled = true;
        }
        
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

    formatCurrency(value, currency) {
        if (value === null || value === undefined) {
            return 'N/A';
        }
        
        // Convert to EUR if needed and available
        if (currency === 'EUR') {
            // Check if we have EUR conversion available
            if (this.currentData && this.currentData.priceData && this.currentData.priceData.length > 0) {
                const latestData = this.currentData.priceData[this.currentData.priceData.length - 1];
                if (latestData.close_eur !== null && latestData.close_eur !== undefined && latestData.close !== null) {
                    // Calculate EUR conversion ratio
                    const ratio = latestData.close_eur / latestData.close;
                    const eurValue = value * ratio;
                    return `€${eurValue.toFixed(2)}`;
                }
            }
            // Fallback: use approximate conversion (0.85 for USD, 1.17 for GBP)
            const eurValue = value * 0.85; // Approximate conversion
            return `€${eurValue.toFixed(2)}`;
        }
        
        // For USD, return as is with $ symbol
        if (currency === 'USD') {
            return `$${value.toFixed(2)}`;
        }
        
        return `$${value.toFixed(2)}`;
    }

    convertToEUR(value) {
        if (!value || !this.currentData || !this.currentData.priceData || this.currentData.priceData.length === 0) {
            return null;
        }
        
        const latestData = this.currentData.priceData[this.currentData.priceData.length - 1];
        if (latestData.close_eur !== null && latestData.close_eur !== undefined && latestData.close !== null) {
            const ratio = latestData.close_eur / latestData.close;
            return value * ratio;
        }
        
        // Fallback conversion
        return value * 0.85;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ETFDashboard();
});