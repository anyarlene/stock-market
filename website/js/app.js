// ETF Analytics Dashboard JavaScript
class ETFDashboard {
    constructor() {
        this.chart = null;
        this.currentData = null;
        this.symbols = [];
        this.currentCurrency = 'EUR'; // Default to EUR
        this.currentTimeRange = '1m'; // Default to 1 month
        this.nativeCurrency = 'USD'; // Will be set dynamically based on selected ETF
        this.chartMetrics = {
            show52WeekHigh: true,
            show52WeekLow: true,
            showThresholds: false
        };
        this.timeSlider = {
            isActive: false,
            startIndex: 0,
            endIndex: 0,
            currentIndex: 0
        };
        console.log('🚀 ETF Dashboard initialized with EUR as default currency and 1 month default time range');
        this.init();
    }

    async init() {
        try {
            console.log('🚀 Starting dashboard initialization...');
            this.hideError(); // Clear any previous errors
            
            await this.loadSymbols();
            console.log(`✅ Loaded ${this.symbols.length} symbols`);
            
            this.setupEventListeners();
            console.log('✅ Event listeners set up');
            
            this.hideLoading();
            
            // Load first ETF by default if available
            if (this.symbols.length > 0) {
                const firstSymbol = this.symbols[0];
                console.log(`📊 Loading default ETF: ${firstSymbol.ticker}`);
                const selector = document.getElementById('etf-selector');
                if (selector) {
                    selector.value = firstSymbol.ticker;
                    await this.loadETFData(firstSymbol.ticker);
                    console.log('✅ Dashboard initialized successfully');
                    this.hideError(); // Ensure error is cleared after successful load
                } else {
                    throw new Error('ETF selector element not found');
                }
            } else {
                console.warn('⚠️ No symbols available');
                this.showError('No ETFs available. Please check data files.');
            }
        } catch (error) {
            console.error('❌ Error initializing dashboard:', error);
            console.error('Error stack:', error.stack);
            this.showError(`Failed to initialize dashboard: ${error.message}`);
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
        selector.innerHTML = '';
        
        this.symbols.forEach(symbol => {
            const option = document.createElement('option');
            option.value = symbol.ticker;
            option.textContent = `${symbol.name} (${symbol.ticker})`;
            selector.appendChild(option);
        });
    }

    updateCurrencySelector() {
        const currencySelector = document.getElementById('currency-selector');
        if (!currencySelector) return;
        
        // Clear existing options
        currencySelector.innerHTML = '';
        
        // Add native currency option
        const nativeOption = document.createElement('option');
        nativeOption.value = this.nativeCurrency;
        nativeOption.textContent = `${this.nativeCurrency} (${this.getCurrencySymbol(this.nativeCurrency)})`;
        currencySelector.appendChild(nativeOption);
        
        // Add EUR option
        const eurOption = document.createElement('option');
        eurOption.value = 'EUR';
        eurOption.textContent = 'EUR (€)';
        currencySelector.appendChild(eurOption);
        
        // Set default to EUR
        currencySelector.value = 'EUR';
        this.currentCurrency = 'EUR';
        
        console.log(`💱 Currency selector updated: ${this.nativeCurrency} and EUR options available`);
    }

    getCurrencySymbol(currency) {
        const symbols = {
            'USD': '$',
            'GBP': '£',
            'EUR': '€',
            'CHF': 'CHF',
            'SEK': 'kr',
            'NOK': 'kr'
        };
        return symbols[currency] || currency;
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
            timeSelector.value = '1m';
            this.currentTimeRange = '1m';
            console.log('⏰ Time filter initialized with 1 month as default');
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
                    this.initializeTimeSlider(); // Reinitialize time slider
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
                    this.initializeTimeSlider(); // Reinitialize time slider for new range
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
        
        // Time slider event listener
        const timeSlider = document.getElementById('time-slider');
        if (timeSlider) {
            timeSlider.addEventListener('input', (e) => {
                this.handleTimeSliderChange(e.target.value);
            });
        }
    }

    async loadETFData(ticker) {
        try {
            // Try individual file first
            const filename = `${ticker.toLowerCase()}.json`;
            const dataUrl = `data/${filename}`;
            console.log(`📂 Loading ETF data from: ${dataUrl}`);
            
            const response = await fetch(dataUrl);
            console.log(`📡 Response status: ${response.status} ${response.statusText}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
            }
            
            this.currentData = await response.json();
            
            // Set native currency based on the loaded ETF data
            this.nativeCurrency = this.currentData.symbol.nativeCurrency || 'USD';
            console.log(`✅ ETF data loaded successfully for ${ticker}:`, {
                symbol: this.currentData.symbol,
                nativeCurrency: this.nativeCurrency,
                priceDataLength: this.currentData.priceData?.length || 0,
                hasEURData: this.currentData.priceData?.[0]?.hasOwnProperty('close_eur') || false
            });
            
            // Update currency selector options based on native currency
            this.updateCurrencySelector();
            
            this.updateUI();
            this.initializeTimeSlider(); // Initialize time slider
            this.createChart(); // Default to EUR
            this.hideError(); // Clear any previous errors on successful load
        } catch (error) {
            console.error('❌ Error loading individual ETF data:', error);
            console.error('Error details:', error.stack);
            
            // Fallback: try loading from combined data file
            try {
                console.log('🔄 Trying fallback: loading from combined data file...');
                const fallbackResponse = await fetch('data/etf_data.json');
                if (!fallbackResponse.ok) {
                    throw new Error(`Fallback failed: ${fallbackResponse.status}`);
                }
                
                const allData = await fallbackResponse.json();
                const symbolData = allData.find(item => item.symbol.ticker === ticker);
                
                if (!symbolData) {
                    throw new Error(`Symbol ${ticker} not found in combined data`);
                }
                
                this.currentData = symbolData;
                
                // Set native currency based on the loaded ETF data
                this.nativeCurrency = this.currentData.symbol.nativeCurrency || 'USD';
                console.log(`✅ Fallback successful: loaded ${ticker} from combined data`);
                
                // Update currency selector options based on native currency
                this.updateCurrencySelector();
                
                this.updateUI();
                this.initializeTimeSlider();
                this.createChart();
                this.hideError(); // Clear any previous errors on successful load
            } catch (fallbackError) {
                console.error('❌ Fallback also failed:', fallbackError);
                console.error('Fallback error details:', fallbackError.stack);
                this.showError(`Failed to load data for ${ticker}: ${fallbackError.message}`);
                throw fallbackError;
            }
        }
    }

    updateUI() {
        if (!this.currentData) {
            console.error('❌ No currentData available for updateUI');
            return;
        }

        const { symbol, metrics, thresholds, lastUpdated } = this.currentData;
        
        console.log(`🔄 Updating UI with currency: ${this.currentCurrency}`);
        console.log(`📊 Data summary:`, {
            symbol: symbol?.ticker,
            hasMetrics: !!metrics,
            hasThresholds: !!thresholds,
            thresholdsCount: thresholds?.length || 0,
            priceDataCount: this.currentData.priceData?.length || 0
        });
        
        // Update ETF info
        document.getElementById('etf-name').textContent = symbol.name;
        document.getElementById('etf-ticker').textContent = symbol.ticker;
        document.getElementById('etf-isin').textContent = symbol.isin;
        
        // Update 52-week metrics (use EUR if available)
        if (metrics && metrics.high52week !== undefined) {
            const highPrice = this.formatCurrency(metrics.high52week, this.currentCurrency);
            document.getElementById('high-52week').textContent = highPrice;
            document.getElementById('high-date').textContent = 
                metrics.highDate ? this.formatDate(metrics.highDate) : 'N/A';
            console.log(`📊 52-week high: ${highPrice} (${this.currentCurrency})`);
        }
        
        if (metrics && metrics.low52week !== undefined) {
            const lowPrice = this.formatCurrency(metrics.low52week, this.currentCurrency);
            document.getElementById('low-52week').textContent = lowPrice;
            document.getElementById('low-date').textContent = 
                metrics.lowDate ? this.formatDate(metrics.lowDate) : 'N/A';
            console.log(`📊 52-week low: ${lowPrice} (${this.currentCurrency})`);
        }
        
        // Update thresholds
        if (thresholds && Array.isArray(thresholds)) {
            console.log(`📋 Updating thresholds table with ${thresholds.length} entries`);
            this.updateThresholds(thresholds);
        } else {
            console.warn('⚠️ No thresholds data available or thresholds is not an array');
            this.updateThresholds([]);
        }
        
        // Update profit targets
        if (thresholds && Array.isArray(thresholds)) {
            this.updateProfitTargets(thresholds);
        } else {
            this.updateProfitTargets([]);
        }
        
        // Note: last-updated element removed from HTML
    }

    updateThresholds(thresholds) {
        try {
            const tbody = document.getElementById('thresholds-table-body');
            if (!tbody) {
                console.error('❌ thresholds-table-body element not found');
                return;
            }
            
            tbody.innerHTML = '';
            
            if (!thresholds || !Array.isArray(thresholds) || thresholds.length === 0) {
                console.warn('⚠️ No threshold data available or thresholds is not an array');
                tbody.innerHTML = '<tr><td colspan="3" class="no-data">No threshold data available</td></tr>';
                return;
            }
            
            console.log(`📊 Updating thresholds table with ${thresholds.length} entries`);
            
            // Get price data for historical analysis
            const priceData = this.currentData?.priceData || [];
            const symbol = this.getCurrencySymbol(this.currentCurrency);
            
            // Get the price field based on currency
            const priceField = this.currentCurrency === 'EUR' && priceData.length > 0 && priceData[0].hasOwnProperty('close_eur') 
                ? 'close_eur' 
                : 'close';
            
            // Find minimum price and when it occurred (for historical analysis)
            let minPrice = null;
            let minPriceDate = null;
            if (priceData.length > 0) {
                const prices = priceData.map(d => d[priceField]).filter(p => p !== null && p !== undefined);
                if (prices.length > 0) {
                    minPrice = Math.min(...prices);
                    // Find the date when minimum price occurred
                    const minPriceData = priceData.find(d => d[priceField] === minPrice);
                    if (minPriceData) {
                        minPriceDate = minPriceData.date;
                    }
                }
            }
            
            // Get current price for comparison
            const currentPrice = this.getCurrentPrice(this.currentCurrency);
            
            // Sort thresholds by percentage (ascending)
            const sortedThresholds = [...thresholds].sort((a, b) => {
                const aPct = a.percentage || 0;
                const bPct = b.percentage || 0;
                return aPct - bPct;
            });
            
            // First, determine which thresholds have been reached and when
            // We need to check in order from highest drop % to lowest drop % (cascading logic)
            const thresholdReachedMap = new Map(); // Map to store reached status and date for each threshold
            
            // Sort by percentage descending (highest drop first) to implement cascading logic
            const sortedByDropDesc = [...sortedThresholds].sort((a, b) => {
                const aPct = a.percentage || 0;
                const bPct = b.percentage || 0;
                return bPct - aPct; // Descending order
            });
            
            sortedByDropDesc.forEach(threshold => {
                if (!threshold || threshold.percentage === undefined || threshold.thresholdPrice === undefined) {
                    return;
                }
                
                // Convert threshold price to current currency
                let thresholdPrice;
                try {
                    thresholdPrice = this.currentCurrency === 'EUR' ? 
                        this.convertToEUR(threshold.thresholdPrice) : 
                        threshold.thresholdPrice;
                } catch (e) {
                    thresholdPrice = threshold.thresholdPrice;
                }
                
                // Check if threshold has been reached using historical minimum price
                let isReached = minPrice && thresholdPrice && minPrice <= thresholdPrice;
                
                // Find the date when this threshold was first reached (if it was reached directly)
                let reachedDate = null;
                if (isReached && priceData.length > 0) {
                    // Find the first date when price dropped to or below this threshold
                    for (let i = 0; i < priceData.length; i++) {
                        const price = priceData[i][priceField];
                        if (price !== null && price !== undefined && price <= thresholdPrice) {
                            reachedDate = priceData[i].date;
                            break; // Found first occurrence
                        }
                    }
                }
                
                // Cascading logic: if a lower threshold (higher drop %) is reached,
                // all higher thresholds (lower drop %) are also reached
                // But we need to find the earliest date when this threshold was crossed
                if (!isReached) {
                    // Check if any lower threshold (higher drop %) has been reached
                    for (const [pct, info] of thresholdReachedMap.entries()) {
                        if (pct > threshold.percentage && info.isReached) {
                            // A lower threshold (higher drop %) was reached, so this one is also reached
                            isReached = true;
                            // Find when this threshold was actually crossed (before the lower threshold)
                            if (priceData.length > 0 && !reachedDate) {
                                for (let i = 0; i < priceData.length; i++) {
                                    const price = priceData[i][priceField];
                                    if (price !== null && price !== undefined && price <= thresholdPrice) {
                                        reachedDate = priceData[i].date;
                                        break;
                                    }
                                }
                            }
                            break;
                        }
                    }
                }
                
                thresholdReachedMap.set(threshold.percentage, { isReached, reachedDate, thresholdPrice });
            });
            
            // Now render the table rows
            sortedThresholds.forEach(threshold => {
                try {
                    if (!threshold || threshold.percentage === undefined || threshold.thresholdPrice === undefined) {
                        console.warn('⚠️ Invalid threshold data:', threshold);
                        return;
                    }
                    
                    const row = document.createElement('tr');
                    
                    // Get reached status from map
                    const thresholdInfo = thresholdReachedMap.get(threshold.percentage);
                    const isReached = thresholdInfo?.isReached || false;
                    const reachedDate = thresholdInfo?.reachedDate || null;
                    const thresholdPrice = thresholdInfo?.thresholdPrice;
                    
                    const symbol = this.getCurrencySymbol(this.currentCurrency);
                    
                    // Format the reached date
                    let reachedDateText = '';
                    if (reachedDate) {
                        try {
                            const date = new Date(reachedDate);
                            if (!isNaN(date.getTime())) {
                                reachedDateText = date.toLocaleDateString('en-US', {
                                    year: 'numeric',
                                    month: 'short',
                                    day: 'numeric'
                                });
                            }
                        } catch (e) {
                            console.warn('⚠️ Error formatting date:', e);
                        }
                    }
                    
                    row.innerHTML = `
                        <td class="percentage-cell">${threshold.percentage}% Drop</td>
                        <td class="price-cell">${thresholdPrice ? `${symbol}${thresholdPrice.toFixed(2)}` : 'N/A'}</td>
                        <td class="status-cell">
                            <span class="status-badge ${isReached ? 'reached' : 'pending'}">
                                ${isReached ? '✓ Reached' : 'Pending'}
                            </span>
                            ${reachedDateText ? `<div class="reached-date" style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem;">${reachedDateText}</div>` : ''}
                        </td>
                    `;
                    
                    if (isReached) {
                        row.classList.add('reached-row');
                    }
                    
                    tbody.appendChild(row);
                } catch (e) {
                    console.error('❌ Error creating threshold row:', e, threshold);
                }
            });
            
            console.log(`✅ Thresholds table updated with ${sortedThresholds.length} rows`);
        } catch (error) {
            console.error('❌ Error in updateThresholds:', error);
            console.error('Error stack:', error.stack);
        }
    }

    updateProfitTargets(thresholds) {
        const tbody = document.getElementById('profit-targets-table-body');
        const filterSelect = document.getElementById('threshold-filter');
        const clearButton = document.getElementById('clear-filter');
        
        if (!tbody || !filterSelect || !clearButton) {
            console.error('Required elements not found for profit targets');
            return;
        }
        
        // Clear the table initially
        tbody.innerHTML = '';
        
        if (!thresholds || thresholds.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="no-data">No entry point data available</td></tr>';
            return;
        }
        
        // Populate the filter dropdown
        this.populateThresholdFilter(thresholds);
        
        // Set up event listeners for filter
        this.setupProfitTargetsFilter(thresholds, tbody);
        
        // Initially show empty table until user selects a threshold
        tbody.innerHTML = '';
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
                
                const symbol = this.getCurrencySymbol(this.currentCurrency);
                option.textContent = `${threshold.percentage}% Drop (${symbol}${thresholdPrice.toFixed(2)})`;
                filterSelect.appendChild(option);
            }
        });
    }

    setupProfitTargetsFilter(thresholds, tbody) {
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
                this.showProfitTargetsForThreshold(thresholds, selectedPercentage, tbody);
                clearButton.disabled = false;
            } else {
                tbody.innerHTML = '';
                clearButton.disabled = true;
            }
        };
        
        // Clear button event
        const clickHandler = () => {
            filterSelect.value = '';
            tbody.innerHTML = '';
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
        tbody.innerHTML = '';
    }

    showProfitTargetsForThreshold(thresholds, selectedPercentage, tbody) {
        // Find the selected threshold
        const selectedThreshold = thresholds.find(t => t.percentage === selectedPercentage);
        if (!selectedThreshold || !selectedThreshold.thresholdPrice) {
            tbody.innerHTML = '<tr><td colspan="4" class="no-data">Selected entry point not found</td></tr>';
            return;
        }
        
        // Clear the table
        tbody.innerHTML = '';
        
        // Get current price for comparison
        const currentPrice = this.getCurrentPrice(this.currentCurrency);
        
        // Define profit target percentages
        const profitTargets = [10, 20, 50, 100];
        
        // Convert threshold price to current currency
        const entryPrice = this.currentCurrency === 'EUR' ? 
            this.convertToEUR(selectedThreshold.thresholdPrice) : 
            selectedThreshold.thresholdPrice;
        
        const symbol = this.getCurrencySymbol(this.currentCurrency);
        
        // Create profit target rows for the selected threshold
        profitTargets.forEach(profitPercent => {
            const profitTargetPrice = entryPrice * (1 + profitPercent / 100);
            
            // Check if profit target has been reached
            const isReached = currentPrice && currentPrice >= profitTargetPrice;
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="percentage-cell">${profitPercent}% Profit</td>
                <td class="price-cell">${symbol}${profitTargetPrice.toFixed(2)}</td>
                <td class="entry-price-cell">${symbol}${entryPrice.toFixed(2)}</td>
                <td class="status-cell">
                    <span class="status-badge ${isReached ? 'reached' : 'pending'}">
                        ${isReached ? '✓ Reached' : 'Pending'}
                    </span>
                </td>
            `;
            
            if (isReached) {
                row.classList.add('reached-row');
            }
            
            tbody.appendChild(row);
        });
    }

    getCurrentPrice(currency = 'original') {
        if (!this.currentData || !this.currentData.priceData || this.currentData.priceData.length === 0) {
            return null;
        }
        
        // Get the most recent price
        const latestData = this.currentData.priceData[this.currentData.priceData.length - 1];
        
        // Return EUR price if available and requested
        if (currency === 'EUR' && latestData.close_eur !== null && latestData.close_eur !== undefined) {
            return latestData.close_eur;
        }
        
        return latestData.close;
    }

    createChart() {
        console.log('🎨 Starting chart creation...');
        
        // Check if Chart.js is available
        if (typeof Chart === 'undefined') {
            console.error('❌ Chart.js library not loaded');
            this.showError('Chart.js library failed to load. Please refresh the page.');
            return;
        }
        
        if (!this.currentData || !this.currentData.priceData) {
            console.error('❌ No current data or price data available for chart');
            this.showError('No data available for chart');
            return;
        }

        const ctx = document.getElementById('priceChart');
        if (!ctx) {
            console.error('❌ Chart canvas element not found');
            this.showError('Chart element not found');
            return;
        }
        
        console.log(`📊 Chart data available: ${this.currentData.priceData.length} price points`);
        
        // Destroy existing chart if it exists
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }

        // Filter data based on time range
        let filteredData = this.filterDataByTimeRange(this.currentData.priceData);
        
        console.log(`📅 Filtered data: ${filteredData.length} points for time range ${this.currentTimeRange}`);
        console.log(`📅 Data range: ${filteredData.length > 0 ? filteredData[0].date : 'N/A'} to ${filteredData.length > 0 ? filteredData[filteredData.length - 1].date : 'N/A'}`);
        
        if (filteredData.length === 0) {
            console.warn('⚠️ No data available for selected time range, showing all data instead');
            // Fallback: show all data if filtered result is empty
            filteredData = this.currentData.priceData.slice(-100); // Show last 100 points as fallback
            if (filteredData.length === 0) {
                console.error('❌ No data available at all');
                this.showError('No data available for chart');
                return;
            }
        }

        // Apply time slider filtering if active
        if (this.timeSlider.isActive) {
            const currentIndex = this.timeSlider.currentIndex;
            const dataWindow = Math.min(50, filteredData.length); // Show up to 50 data points or all data if less
            
            let startIndex = Math.max(0, currentIndex - Math.floor(dataWindow / 2));
            let endIndex = Math.min(filteredData.length - 1, startIndex + dataWindow);
            
            // Adjust start index if we're near the end
            if (endIndex === filteredData.length - 1) {
                startIndex = Math.max(0, endIndex - dataWindow + 1);
            }
            
            filteredData = filteredData.slice(startIndex, endIndex + 1);
            console.log(`Time slider active: showing data from index ${startIndex} to ${endIndex} (${filteredData.length} points)`);
        }

        console.log(`Creating chart with ${filteredData.length} data points for time range: ${this.currentTimeRange}`);

        // Prepare data for Chart.js
        const labels = filteredData.map(item => item.date);
        
        // Choose price field based on currency preference
        const hasEurData = filteredData.length > 0 && filteredData[0].hasOwnProperty('close_eur');
        
        // Use EUR field only if it exists and is requested, otherwise use original currency
        const finalPriceField = (this.currentCurrency === 'EUR' && hasEurData) ? 'close_eur' : 'close';
        const prices = filteredData.map(item => item[finalPriceField]).filter(price => price !== null && price !== undefined);
        
        console.log(`Price data points: ${prices.length}, Currency: ${this.currentCurrency}, Price field: ${finalPriceField}, Has EUR data: ${hasEurData}`);
        
        if (prices.length === 0) {
            console.error('No valid price data found for chart');
            return;
        }
        
        // Create datasets
        const datasets = [{
            label: `Close Price (${this.currentCurrency})`,
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
        const colors = ['#fbbf24', '#f59e0b', '#f97316', '#dc2626', '#b91c1c', '#7f1d1d'];
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
            const chartCtx = ctx.getContext('2d');
            if (!chartCtx) {
                console.error('❌ Could not get 2D context from canvas');
                this.showError('Chart canvas error - cannot get 2D context');
                return;
            }
            
            console.log(`📊 Preparing chart config with ${datasets.length} datasets, ${labels.length} labels`);
            
            const config = {
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
                        tooltip: {
                            enabled: true,
                            mode: 'index',
                            intersect: false,
                            backgroundColor: 'rgba(15, 23, 42, 0.95)',
                            titleColor: '#f1f5f9',
                            bodyColor: '#cbd5e1',
                            borderColor: '#667eea',
                            borderWidth: 1,
                            cornerRadius: 6,
                            displayColors: true,
                            callbacks: {
                                title: function(context) {
                                    try {
                                        const dateString = context[0].label;
                                        console.log('Tooltip date string:', dateString, 'Type:', typeof dateString);
                                        
                                        let date;
                                        
                                        // Handle different date formats
                                        if (typeof dateString === 'string') {
                                            // Try parsing as ISO string first
                                            date = new Date(dateString);
                                            
                                            // Check if date is valid
                                            if (isNaN(date.getTime())) {
                                                console.log('Invalid date, trying alternative parsing');
                                                // Try parsing as different format (YYYY-MM-DD)
                                                const parts = dateString.split('-');
                                                if (parts.length === 3) {
                                                    date = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
                                                } else {
                                                    // Fallback to current date
                                                    date = new Date();
                                                }
                                            }
                                        } else if (dateString instanceof Date) {
                                            date = dateString;
                                        } else {
                                            console.log('Unknown date format, using current date');
                                            date = new Date();
                                        }
                                        
                                        console.log('Parsed date:', date);
                                        
                                        // Format the date
                                        const formattedDate = date.toLocaleDateString('en-US', { 
                                            weekday: 'short', 
                                            year: 'numeric', 
                                            month: 'short', 
                                            day: 'numeric' 
                                        });
                                        
                                        console.log('Formatted date:', formattedDate);
                                        return formattedDate;
                                    } catch (error) {
                                        console.error('Error formatting tooltip date:', error);
                                        return 'Date unavailable';
                                    }
                                },
                                label: function(context) {
                                    const dataset = context.dataset;
                                    const value = context.parsed.y;
                                    const currency = this.currentCurrency || 'EUR';
                                    const symbol = this.getCurrencySymbol(currency);
                                    return `${dataset.label}: ${symbol}${value.toFixed(2)}`;
                                }
                            }
                        },
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                usePointStyle: true,
                                padding: 20,
                                color: '#f1f5f9',
                                font: {
                                    size: 12
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            type: 'category',
                            grid: {
                                display: false
                            },
                            ticks: {
                                maxTicksLimit: 10,
                                color: '#cbd5e1',
                                font: {
                                    size: 11
                                },
                                callback: function(value, index, values) {
                                    try {
                                        const dateString = this.getLabelForValue(value);
                                        const date = new Date(dateString);
                                        if (!isNaN(date.getTime())) {
                                            return date.toLocaleDateString('en-US', {
                                                month: 'short',
                                                day: 'numeric'
                                            });
                                        }
                                        return dateString;
                                    } catch (error) {
                                        return this.getLabelForValue(value);
                                    }
                                }
                            }
                        },
                        y: {
                            beginAtZero: false,
                            grid: {
                                color: 'rgba(203, 213, 225, 0.2)'
                            },
                            ticks: {
                                color: '#cbd5e1',
                                callback: (value) => {
                                    try {
                                        const currency = this.currentCurrency || 'EUR';
                                        const symbol = this.getCurrencySymbol(currency);
                                        return symbol + value.toFixed(2);
                                    } catch (e) {
                                        console.warn('⚠️ Error in y-axis tick callback:', e);
                                        return value.toFixed(2);
                                    }
                                },
                                font: {
                                    size: 11
                                }
                            }
                        }
                    },
                    elements: {
                        point: {
                            radius: 0,
                            hoverRadius: 6,
                            hoverBorderWidth: 2
                        },
                        line: {
                            tension: 0.1
                        }
                    }
                }
            };
            
            // Store current currency reference for tooltip callbacks (if label callback exists)
            if (config.options.plugins.tooltip.callbacks.label) {
                config.options.plugins.tooltip.callbacks.label = config.options.plugins.tooltip.callbacks.label.bind(this);
            }
            // y-axis callback is already an arrow function, no binding needed
            
            console.log('📊 Creating Chart.js instance...');
            this.chart = new Chart(chartCtx, config);
            console.log('✅ Chart created successfully');
            this.hideError(); // Hide any previous errors
        } catch (error) {
            console.error('❌ Error creating chart:', error);
            console.error('Error details:', error.message, error.stack);
            this.showError(`Chart creation failed: ${error.message || 'Unknown error'}`);
        }
    }

    filterDataByTimeRange(priceData) {
        if (!priceData || priceData.length === 0) return [];
        
        const now = new Date();
        let cutoffDate = new Date();
        
        switch (this.currentTimeRange) {
            case '1m':
                // Last 30 days
                cutoffDate.setTime(now.getTime() - (30 * 24 * 60 * 60 * 1000));
                cutoffDate.setHours(0, 0, 0, 0);
                break;
            case '3m':
                // Last 90 days
                cutoffDate.setTime(now.getTime() - (90 * 24 * 60 * 60 * 1000));
                cutoffDate.setHours(0, 0, 0, 0);
                break;
            case '1y':
                cutoffDate.setFullYear(now.getFullYear() - 1);
                cutoffDate.setMonth(0);
                cutoffDate.setDate(1);
                cutoffDate.setHours(0, 0, 0, 0);
                break;
            case '2y':
                cutoffDate.setFullYear(now.getFullYear() - 2);
                cutoffDate.setMonth(0);
                cutoffDate.setDate(1);
                cutoffDate.setHours(0, 0, 0, 0);
                break;
            case '3y':
                cutoffDate.setFullYear(now.getFullYear() - 3);
                cutoffDate.setMonth(0);
                cutoffDate.setDate(1);
                cutoffDate.setHours(0, 0, 0, 0);
                break;
            case 'all':
                // Return all data
                return priceData;
            default:
                cutoffDate.setMonth(now.getMonth() - 1);
                cutoffDate.setDate(1);
                cutoffDate.setHours(0, 0, 0, 0);
        }
        
        const filtered = priceData.filter(item => {
            // Parse date string (format: "YYYY-MM-DD")
            const dateParts = item.date.split('-');
            if (dateParts.length !== 3) return false;
            
            const itemDate = new Date(
                parseInt(dateParts[0]), 
                parseInt(dateParts[1]) - 1, 
                parseInt(dateParts[2])
            );
            itemDate.setHours(0, 0, 0, 0);
            
            return itemDate >= cutoffDate;
        });
        
        console.log(`📅 Date filter: ${this.currentTimeRange}, cutoff: ${cutoffDate.toISOString().split('T')[0]}, filtered: ${filtered.length} of ${priceData.length} points`);
        
        return filtered;
    }

    getTimeRangeDisplayName() {
        switch (this.currentTimeRange) {
            case '1m': return '1 Month';
            case '3m': return '3 Months';
            case '1y': return '1 Year';
            case '2y': return '2 Years';
            case '3y': return '3 Years';
            case 'all': return 'All Time';
            default: return '1 Month';
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
        const thresholdsTbody = document.getElementById('thresholds-table-body');
        const profitTargetsTbody = document.getElementById('profit-targets-table-body');
        if (thresholdsTbody) thresholdsTbody.innerHTML = '';
        if (profitTargetsTbody) profitTargetsTbody.innerHTML = '';
        
        // Reset the profit targets filter
        const filterSelect = document.getElementById('threshold-filter');
        const clearButton = document.getElementById('clear-filter');
        if (filterSelect) {
            filterSelect.innerHTML = '<option value="">Choose an entry point...</option>';
        }
        if (clearButton) {
            clearButton.disabled = true;
        }
        
        // Reset time slider
        const timeSlider = document.getElementById('time-slider');
        if (timeSlider) {
            timeSlider.value = 100;
            timeSlider.style.display = 'none';
        }
        
        // Reset time slider labels
        const startDate = document.getElementById('start-date');
        const currentDate = document.getElementById('current-date');
        const endDate = document.getElementById('end-date');
        if (startDate) startDate.textContent = '-';
        if (currentDate) currentDate.textContent = '-';
        if (endDate) endDate.textContent = '-';
        
        // Reset time slider state
        this.timeSlider.isActive = false;
        this.timeSlider.startIndex = 0;
        this.timeSlider.endIndex = 0;
        this.timeSlider.currentIndex = 0;
        
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

    hideError() {
        const errorElement = document.getElementById('error-message');
        if (errorElement) {
            errorElement.style.display = 'none';
            console.log('✅ Error message hidden');
        } else {
            console.warn('⚠️ Error message element not found');
        }
    }

    showError(message) {
        const errorElement = document.getElementById('error-message');
        if (errorElement) {
            errorElement.style.display = 'block';
            const errorText = errorElement.querySelector('p');
            if (errorText) {
                errorText.textContent = message;
            }
            console.error(`❌ Showing error: ${message}`);
        } else {
            console.error(`❌ Error message element not found. Message: ${message}`);
        }
        this.hideLoading();
    }

    formatDate(dateString) {
        try {
            let date;
            if (dateString instanceof Date) {
                date = dateString;
            } else {
                date = new Date(dateString);
            }
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
            // Fallback: use approximate conversion
            const eurValue = value * 0.85; // Approximate conversion
            return `€${eurValue.toFixed(2)}`;
        }
        
        // For native currency, return with appropriate symbol
        const symbol = this.getCurrencySymbol(currency);
        return `${symbol}${value.toFixed(2)}`;
    }

    convertToEUR(value) {
        if (!value || !this.currentData || !this.currentData.priceData || this.currentData.priceData.length === 0) {
            return value; // Return original value if no conversion possible
        }
        
        const latestData = this.currentData.priceData[this.currentData.priceData.length - 1];
        if (latestData.close_eur !== null && latestData.close_eur !== undefined && latestData.close !== null) {
            const ratio = latestData.close_eur / latestData.close;
            return value * ratio;
        }
        
        // Fallback conversion (approximate)
        return value * 0.85;
    }

    handleTimeSliderChange(value) {
        if (!this.currentData || !this.currentData.priceData) return;
        
        const filteredData = this.filterDataByTimeRange(this.currentData.priceData);
        if (filteredData.length === 0) return;
        
        // Convert slider value (0-100) to data index
        const totalDataPoints = filteredData.length;
        const targetIndex = Math.floor((value / 100) * (totalDataPoints - 1));
        
        this.timeSlider.currentIndex = targetIndex;
        this.updateTimeSliderLabels(filteredData);
        this.createChart();
    }
    
    updateTimeSliderLabels(filteredData) {
        const startDate = document.getElementById('start-date');
        const currentDate = document.getElementById('current-date');
        const endDate = document.getElementById('end-date');
        
        if (!startDate || !currentDate || !endDate || filteredData.length === 0) return;
        
        // Update start date (beginning of filtered data)
        const startDateValue = new Date(filteredData[0].date);
        startDate.textContent = this.formatDate(startDateValue);
        
        // Update end date (end of filtered data)
        const endDateValue = new Date(filteredData[filteredData.length - 1].date);
        endDate.textContent = this.formatDate(endDateValue);
        
        // Update current date (based on slider position)
        const currentIndex = this.timeSlider.currentIndex;
        if (currentIndex >= 0 && currentIndex < filteredData.length) {
            const currentDateValue = new Date(filteredData[currentIndex].date);
            currentDate.textContent = this.formatDate(currentDateValue);
        } else {
            currentDate.textContent = '-';
        }
    }
    
    initializeTimeSlider() {
        if (!this.currentData || !this.currentData.priceData) return;
        
        const timeSlider = document.getElementById('time-slider');
        if (!timeSlider) return;
        
        const filteredData = this.filterDataByTimeRange(this.currentData.priceData);
        if (filteredData.length === 0) return;
        
        // Always show slider regardless of data length
        timeSlider.style.display = 'block';
        this.timeSlider.isActive = true;
        this.timeSlider.startIndex = 0;
        this.timeSlider.endIndex = filteredData.length - 1;
        this.timeSlider.currentIndex = filteredData.length - 1;
        
        // Set slider to show all data initially
        timeSlider.value = 100;
        this.updateTimeSliderLabels(filteredData);
    }
}

// Initialize dashboard when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('📄 DOM loaded, initializing dashboard...');
        new ETFDashboard();
    });
} else {
    // DOM is already loaded
    console.log('📄 DOM already loaded, initializing dashboard...');
    new ETFDashboard();
}