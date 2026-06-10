// Investment Strategy Planner JavaScript
class InvestmentStrategy {
    constructor() {
        this.etfData = [];
        this.symbols = [];
        this.growthChart = null;
        this.selectedETFs = [];
        this.investmentAmounts = {}; // {ticker: {country: amount}}
        this.selectedCountry = 'USA';
        this.selectedTableRow = null;
        this.investmentDate = null;
        this.exchangeRate = 1.1; // USD to EUR (will be fetched from data)
        this.init();
    }

    async init() {
        try {
            await this.loadSymbols();
            await this.loadETFData();
            this.setupEventListeners();
            this.populateETFSelector();
            this.updateTotals();
            this.updateTaxEstimates(); // Initialize tax panel for default country
        } catch (error) {
            console.error('Error initializing investment strategy:', error);
        }
    }

    async loadSymbols() {
        try {
            const response = await fetch('data/symbols.json');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            this.symbols = await response.json();
        } catch (error) {
            console.error('Error loading symbols:', error);
            // Fallback to default symbols
            this.symbols = [
                { ticker: 'VUAA.L', name: 'Vanguard S&P 500 UCITS ETF', isin: 'IE00BFMXXD54', nativeCurrency: 'USD', region: 'UCITS' },
                { ticker: 'CNDX.L', name: 'iShares NASDAQ 100 UCITS ETF', isin: 'IE00B53SZB19', nativeCurrency: 'GBP', region: 'UCITS' },
                { ticker: 'VOO', name: 'Vanguard S&P 500 ETF', isin: 'US9229083632', nativeCurrency: 'USD', region: 'US' },
                { ticker: 'VTI', name: 'Vanguard Total Stock Market ETF', isin: 'US9229087690', nativeCurrency: 'USD', region: 'US' },
                { ticker: 'QQQ', name: 'Invesco QQQ Trust', isin: 'US46090E1038', nativeCurrency: 'USD', region: 'US' }
            ];
        }
    }

    async loadETFData() {
        const loadPromises = this.symbols.map(async (symbol) => {
            try {
                const filename = `${symbol.ticker.toLowerCase()}.json`;
                const response = await fetch(`data/${filename}`);
                if (response.ok) {
                    const data = await response.json();
                    return {
                        ...symbol,
                        data: data,
                        latestPrice: this.getLatestPrice(data),
                        priceEUR: this.getLatestPriceEUR(data)
                    };
                }
            } catch (error) {
                console.warn(`Could not load data for ${symbol.ticker}:`, error);
            }
            return {
                ...symbol,
                data: null,
                latestPrice: 0,
                priceEUR: 0
            };
        });

        this.etfData = await Promise.all(loadPromises);
    }

    getLatestPrice(etfData) {
        if (!etfData || !etfData.priceData || etfData.priceData.length === 0) return 0;
        const latest = etfData.priceData[etfData.priceData.length - 1];
        return latest.close || latest.close_eur || 0;
    }

    getLatestPriceEUR(etfData) {
        if (!etfData || !etfData.priceData || etfData.priceData.length === 0) return 0;
        const latest = etfData.priceData[etfData.priceData.length - 1];
        return latest.close_eur || latest.close || 0;
    }

    populateETFSelector() {
        const listContainer = document.getElementById('etf-filter-list');
        if (!listContainer) return;
        
        listContainer.innerHTML = '';
        
        if (this.symbols.length === 0) {
            listContainer.innerHTML = '<div class="etf-loading">No ETFs available</div>';
            return;
        }
        
        // Store filtered symbols for search functionality
        this.filteredSymbols = [...this.symbols];
        
        this.symbols.forEach(symbol => {
            const option = document.createElement('div');
            option.className = 'etf-filter-option';
            option.dataset.ticker = symbol.ticker;
            option.dataset.searchText = `${symbol.ticker} ${symbol.name}`.toLowerCase();
            
            const isSelected = this.selectedETFs.includes(symbol.ticker);
            
            option.innerHTML = `
                <input type="checkbox" ${isSelected ? 'checked' : ''} id="etf-check-${symbol.ticker}" data-ticker="${symbol.ticker}">
                <label for="etf-check-${symbol.ticker}">${symbol.ticker} - ${symbol.name}</label>
            `;
            
            // Checkbox handler
            const checkbox = option.querySelector('input[type="checkbox"]');
            checkbox.addEventListener('change', (e) => {
                e.stopPropagation();
                this.toggleETF(symbol.ticker);
            });
            
            listContainer.appendChild(option);
        });
        
        // Update UI
        this.updateETFSelectorUI();
        this.updateSelectedChips();
    }

    toggleETF(ticker) {
        if (this.selectedETFs.includes(ticker)) {
            this.selectedETFs = this.selectedETFs.filter(t => t !== ticker);
        } else {
            this.selectedETFs.push(ticker);
        }
        this.updateETFSelectorUI();
        this.updateSelectedChips();
        this.updateInvestmentInputs();
        this.updateTotals();
        this.populateETFTable();
        this.calculateRiskMetrics();
        this.updateTaxEstimates();
    }

    updateETFSelectorUI() {
        // Update individual checkboxes
        document.querySelectorAll('#etf-filter-list .etf-filter-option input[type="checkbox"]').forEach(checkbox => {
            const ticker = checkbox.dataset.ticker;
            checkbox.checked = this.selectedETFs.includes(ticker);
        });
        
        // Update Select All checkbox
        const selectAllCheckbox = document.getElementById('etf-select-all');
        if (selectAllCheckbox) {
            const visibleOptions = Array.from(document.querySelectorAll('#etf-filter-list .etf-filter-option:not(.hidden)'));
            const visibleSelected = visibleOptions.filter(opt => {
                const ticker = opt.dataset.ticker;
                return this.selectedETFs.includes(ticker);
            });
            
            if (visibleSelected.length === 0) {
                selectAllCheckbox.checked = false;
                selectAllCheckbox.indeterminate = false;
            } else if (visibleSelected.length === visibleOptions.length) {
                selectAllCheckbox.checked = true;
                selectAllCheckbox.indeterminate = false;
            } else {
                selectAllCheckbox.checked = false;
                selectAllCheckbox.indeterminate = true;
            }
        }
        
        // Update placeholder text
        const placeholder = document.querySelector('.etf-filter-placeholder');
        if (placeholder) {
            if (this.selectedETFs.length === 0) {
                placeholder.textContent = 'Select ETFs...';
            } else {
                placeholder.textContent = `${this.selectedETFs.length} ETF${this.selectedETFs.length > 1 ? 's' : ''} selected`;
            }
        }
    }

    updateSelectedChips() {
        const chipsContainer = document.getElementById('etf-selected-chips');
        if (!chipsContainer) return;
        
        chipsContainer.innerHTML = '';
        
        this.selectedETFs.forEach(ticker => {
            const symbol = this.symbols.find(s => s.ticker === ticker);
            if (!symbol) return;
            
            const chip = document.createElement('div');
            chip.className = 'etf-chip';
            chip.innerHTML = `
                <span>${symbol.ticker}</span>
                <span class="chip-remove" data-ticker="${ticker}">×</span>
            `;
            
            // Remove chip on click
            chip.querySelector('.chip-remove').addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeETF(ticker);
            });
            
            chipsContainer.appendChild(chip);
        });
    }

    updateSelectedETFsDisplay() {
        const display = document.getElementById('selected-etfs-display');
        display.innerHTML = '';
        
        if (this.selectedETFs.length === 0) {
            display.innerHTML = '<span class="no-selection">No ETFs selected</span>';
            return;
        }
        
        this.selectedETFs.forEach(ticker => {
            const etf = this.symbols.find(s => s.ticker === ticker);
            if (!etf) return;
            
            const chip = document.createElement('div');
            chip.className = 'etf-chip';
            chip.innerHTML = `
                <span class="chip-ticker">${etf.ticker}</span>
                <span class="chip-name" style="font-size: 0.8rem; opacity: 0.9;">${etf.name}</span>
                <span class="chip-remove" data-ticker="${ticker}">×</span>
            `;
            
            // Remove chip on click
            chip.querySelector('.chip-remove').addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeETF(ticker);
            });
            
            display.appendChild(chip);
        });
    }

    removeETF(ticker) {
        this.selectedETFs = this.selectedETFs.filter(t => t !== ticker);
        this.updateETFSelectorUI();
        this.updateSelectedChips();
        this.updateInvestmentInputs();
        this.updateTotals();
        this.populateETFTable();
        this.calculateRiskMetrics();
        this.updateTaxEstimates();
    }

    getCurrencyForCountry(country) {
        if (country === 'USA' || country === 'Australia') {
            return 'USD';
        } else if (country === 'Germany' || country === 'France') {
            return 'EUR';
        }
        return 'USD'; // Default
    }

    updateCurrencyDisplay() {
        // This will be used when updating investment inputs
        // The currency will be determined by country
    }

    setupETFFilterHandlers() {
        const trigger = document.getElementById('etf-filter-trigger');
        const dropdown = document.getElementById('etf-filter-dropdown');
        const searchInput = document.getElementById('etf-filter-search');
        const clearBtn = document.getElementById('etf-filter-clear');
        const selectAllCheckbox = document.getElementById('etf-select-all');
        
        if (!trigger || !dropdown) return;
        
        // Toggle dropdown
        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = dropdown.classList.contains('open');
            dropdown.classList.toggle('open');
            const arrow = trigger.querySelector('.etf-filter-arrow');
            if (arrow) {
                if (isOpen) {
                    arrow.style.transform = 'rotate(0deg)';
                } else {
                    arrow.style.transform = 'rotate(180deg)';
                    if (searchInput) searchInput.focus();
                }
            }
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!dropdown.contains(e.target) && !trigger.contains(e.target)) {
                dropdown.classList.remove('open');
                const arrow = trigger.querySelector('.etf-filter-arrow');
                if (arrow) {
                    arrow.style.transform = 'rotate(0deg)';
                }
            }
        });
        
        // Search functionality
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const searchTerm = e.target.value.toLowerCase().trim();
                this.filterETFList(searchTerm);
            });
        }
        
        // Clear search
        if (clearBtn) {
            clearBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (searchInput) {
                    searchInput.value = '';
                    this.filterETFList('');
                }
            });
        }
        
        // Select All functionality
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', (e) => {
                const visibleOptions = Array.from(document.querySelectorAll('#etf-filter-list .etf-filter-option:not(.hidden)'));
                const visibleTickers = visibleOptions.map(opt => opt.dataset.ticker);
                
                if (e.target.checked) {
                    // Add all visible ETFs
                    visibleTickers.forEach(ticker => {
                        if (!this.selectedETFs.includes(ticker)) {
                            this.selectedETFs.push(ticker);
                        }
                    });
                } else {
                    // Remove all visible ETFs
                    this.selectedETFs = this.selectedETFs.filter(t => !visibleTickers.includes(t));
                }
                
                this.updateETFSelectorUI();
                this.updateSelectedChips();
                this.updateInvestmentInputs();
                this.updateTotals();
                this.populateETFTable();
                this.calculateRiskMetrics();
                this.updateTaxEstimates();
            });
        }
    }

    filterETFList(searchTerm) {
        const options = document.querySelectorAll('#etf-filter-list .etf-filter-option');
        
        options.forEach(option => {
            const searchText = option.dataset.searchText || '';
            if (searchTerm === '' || searchText.includes(searchTerm)) {
                option.classList.remove('hidden');
            } else {
                option.classList.add('hidden');
            }
        });
        
        // Update Select All state after filtering
        this.updateETFSelectorUI();
    }

    setupEventListeners() {
        // Country selector
        document.getElementById('country-selector').addEventListener('change', (e) => {
            this.selectedCountry = e.target.value;
            this.updateCurrencyDisplay();
            this.updateInvestmentInputs();
            this.updateTotals();
            this.populateETFTable();
            this.calculateRiskMetrics();
            this.updateTaxEstimates();
        });

        // ETF filter dropdown handlers
        this.setupETFFilterHandlers();

        // Investment date selector
        const dateInput = document.getElementById('investment-date');
        // Set default to today
        const today = new Date().toISOString().split('T')[0];
        dateInput.value = today;
        this.investmentDate = today;
        
        dateInput.addEventListener('change', (e) => {
            this.investmentDate = e.target.value;
            console.log('Investment date changed to:', this.investmentDate);
            this.updateInvestmentDateDisplay();
            // Update chart when date changes
            if (this.selectedTableRow || this.selectedETFs.length > 0) {
                const activePeriod = document.querySelector('.time-toggle.active')?.dataset.period || '1y';
                this.updateGrowthChart(activePeriod);
            }
        });
        
        // Initial display update
        this.updateInvestmentDateDisplay();

        // Time period toggles
        document.querySelectorAll('.time-toggle').forEach(button => {
            button.addEventListener('click', (e) => {
                document.querySelectorAll('.time-toggle').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.updateGrowthChart(e.target.dataset.period);
            });
        });

        // Projection scenario selector
        const scenarioSelector = document.getElementById('projection-scenario');
        if (scenarioSelector) {
            scenarioSelector.addEventListener('change', (e) => {
                const activePeriod = document.querySelector('.time-toggle.active')?.dataset.period || '1y';
                this.updateGrowthChart(activePeriod);
            });
        }
    }

    getProjectionScenario() {
        const selector = document.getElementById('projection-scenario');
        return selector ? selector.value : 'moderate';
    }

    getCAGRForScenario(scenario, etf = null) {
        switch(scenario) {
            case 'conservative':
                return 0.07; // 7%
            case 'moderate':
                return 0.10; // 10% - more realistic for S&P 500 long-term
            case 'aggressive':
                return 0.12; // 12%
            case 'historical':
                // Calculate based on actual ETF historical performance
                if (etf && etf.data && etf.data.priceData && etf.data.priceData.length > 0) {
                    return this.calculateHistoricalCAGR(etf);
                }
                return 0.10; // Fallback to moderate
            default:
                return 0.10; // Default to moderate
        }
    }

    calculateHistoricalCAGR(etf) {
        if (!etf.data || !etf.data.priceData || etf.data.priceData.length < 2) {
            return 0.10; // Fallback
        }

        const priceData = etf.data.priceData;
        const priceField = priceData[0].hasOwnProperty('close_eur') ? 'close_eur' : 'close';
        
        // Get first and last prices
        const firstPrice = priceData[0][priceField];
        const lastPrice = priceData[priceData.length - 1][priceField];
        
        if (!firstPrice || !lastPrice || firstPrice <= 0) {
            return 0.10; // Fallback
        }

        // Calculate number of years
        const firstDate = new Date(priceData[0].date);
        const lastDate = new Date(priceData[priceData.length - 1].date);
        const years = (lastDate - firstDate) / (1000 * 60 * 60 * 24 * 365.25);
        
        if (years <= 0) {
            return 0.10; // Fallback
        }

        // CAGR formula: (End Value / Start Value)^(1/Years) - 1
        const cagr = Math.pow(lastPrice / firstPrice, 1 / years) - 1;
        
        // Cap at reasonable values (between 0% and 30%)
        return Math.max(0, Math.min(0.30, cagr));
    }

    updateInvestmentInputs() {
        const container = document.getElementById('etf-investment-inputs');
        container.innerHTML = '';

        if (this.selectedETFs.length === 0) {
            container.innerHTML = '<p style="color: #6b7280;">Please select at least one ETF above.</p>';
            return;
        }

        this.selectedETFs.forEach(ticker => {
            const etf = this.etfData.find(e => e.ticker === ticker);
            if (!etf) return;

            // Initialize investment amount if not set
            if (!this.investmentAmounts[ticker]) {
                this.investmentAmounts[ticker] = {};
            }
            if (!this.investmentAmounts[ticker][this.selectedCountry]) {
                this.investmentAmounts[ticker][this.selectedCountry] = 10000;
            }

            const amountId = `amount-${ticker}-${this.selectedCountry}`;
            const sliderId = `slider-${ticker}-${this.selectedCountry}`;
            const currentAmount = this.investmentAmounts[ticker][this.selectedCountry];

            const countryCurrency = this.getCurrencyForCountry(this.selectedCountry);
            const currencySymbol = this.getCurrencySymbol(countryCurrency);
            const group = document.createElement('div');
            group.className = 'etf-investment-group';
            group.innerHTML = `
                <label>
                    <span class="etf-name">${etf.ticker}</span> - ${etf.name}
                    <br><small style="color: #6b7280;">Investment in ${countryCurrency}</small>
                </label>
                <div class="input-with-slider">
                    <input type="number" id="${amountId}" value="${currentAmount}" min="0" step="100" 
                           data-ticker="${ticker}" data-country="${this.selectedCountry}"
                           placeholder="${currencySymbol}0">
                    <input type="range" id="${sliderId}" value="${currentAmount}" min="0" max="100000" step="1000"
                           data-ticker="${ticker}" data-country="${this.selectedCountry}">
                </div>
            `;
            container.appendChild(group);

            // Add event listeners
            const amountInput = document.getElementById(amountId);
            const sliderInput = document.getElementById(sliderId);

            amountInput.addEventListener('input', (e) => {
                const ticker = e.target.dataset.ticker;
                const country = e.target.dataset.country;
                const value = parseFloat(e.target.value) || 0;
                this.investmentAmounts[ticker][country] = value;
                sliderInput.value = value;
                this.updateTotals();
                this.populateETFTable();
                this.calculateRiskMetrics();
                this.updateTaxEstimates();
            });

            sliderInput.addEventListener('input', (e) => {
                const ticker = e.target.dataset.ticker;
                const country = e.target.dataset.country;
                const value = parseFloat(e.target.value) || 0;
                this.investmentAmounts[ticker][country] = value;
                amountInput.value = value;
                this.updateTotals();
                this.populateETFTable();
                this.calculateRiskMetrics();
                this.updateTaxEstimates();
            });
        });
    }

    updateTotals() {
        const countryCurrency = this.getCurrencyForCountry(this.selectedCountry);
        let total = 0;
        
        this.selectedETFs.forEach(ticker => {
            const amount = this.investmentAmounts[ticker]?.[this.selectedCountry] || 0;
            const etf = this.etfData.find(e => e.ticker === ticker);
            if (etf) {
                // Convert to country currency
                if (countryCurrency === 'EUR') {
                    // Convert everything to EUR
                    if (etf.nativeCurrency === 'USD') {
                        total += amount / this.exchangeRate;
                    } else if (etf.nativeCurrency === 'GBP') {
                        total += amount * 1.15; // Approximate GBP to EUR
                    } else {
                        total += amount;
                    }
                } else {
                    // Convert everything to USD
                    if (etf.nativeCurrency === 'EUR') {
                        total += amount * this.exchangeRate;
                    } else if (etf.nativeCurrency === 'GBP') {
                        total += amount * 1.25; // Approximate GBP to USD
                    } else {
                        total += amount;
                    }
                }
            }
        });

        const symbol = countryCurrency === 'EUR' ? '€' : '$';
        document.getElementById('total-invested').textContent = `${symbol}${this.formatNumber(total)}`;
    }

    updateInvestmentDateDisplay() {
        const dateDisplay = document.getElementById('display-investment-date');
        if (this.investmentDate) {
            const date = new Date(this.investmentDate);
            const formattedDate = date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
            dateDisplay.textContent = formattedDate;
        } else {
            dateDisplay.textContent = '-';
        }
    }

    populateETFTable() {
        const tbody = document.getElementById('etf-table-body');
        tbody.innerHTML = '';

        if (this.selectedETFs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #6b7280;">Please select ETFs and set investment amounts above.</td></tr>';
            // Reset chart selection
            this.selectedTableRow = null;
            const activePeriod = document.querySelector('.time-toggle.active')?.dataset.period || '1y';
            this.updateGrowthChart(activePeriod);
            return;
        }

        const countryCurrency = this.getCurrencyForCountry(this.selectedCountry);
        const currencySymbol = countryCurrency === 'EUR' ? '€' : '$';
        
        // Update table header
        document.getElementById('current-value-header').textContent = `Current Value (${countryCurrency})`;
        
        let firstRowWithAmount = null;
        
        this.selectedETFs.forEach((ticker, index) => {
            const etf = this.etfData.find(e => e.ticker === ticker);
            if (!etf) return;

            const investmentAmount = this.investmentAmounts[ticker]?.[this.selectedCountry] || 0;
            const price = etf.priceEUR || etf.latestPrice;
            
            // Convert investment amount to country currency for calculation
            let investmentInCountryCurrency = investmentAmount;
            let priceInCountryCurrency = price;
            
            if (countryCurrency === 'EUR') {
                // Convert to EUR
                if (etf.nativeCurrency === 'USD') {
                    investmentInCountryCurrency = investmentAmount / this.exchangeRate;
                    priceInCountryCurrency = price / this.exchangeRate;
                } else if (etf.nativeCurrency === 'GBP') {
                    investmentInCountryCurrency = investmentAmount * 1.15;
                    priceInCountryCurrency = price * 1.15;
                }
            } else {
                // Convert to USD
                if (etf.nativeCurrency === 'EUR') {
                    investmentInCountryCurrency = investmentAmount * this.exchangeRate;
                    priceInCountryCurrency = price * this.exchangeRate;
                } else if (etf.nativeCurrency === 'GBP') {
                    investmentInCountryCurrency = investmentAmount * 1.25;
                    priceInCountryCurrency = price * 1.25;
                }
            }
            
            const units = priceInCountryCurrency > 0 ? Math.floor(investmentInCountryCurrency / priceInCountryCurrency) : 0;
            const currentValue = units * priceInCountryCurrency;

            const row = document.createElement('tr');
            row.dataset.ticker = ticker;
            row.innerHTML = `
                <td><strong>${etf.ticker}</strong><br><small>${etf.name}</small></td>
                <td><span class="region-badge ${etf.region?.toLowerCase() || 'us'}">${etf.region || 'US'}</span></td>
                <td>${this.formatCurrency(investmentAmount, countryCurrency)}</td>
                <td>${this.formatCurrency(priceInCountryCurrency, countryCurrency)}</td>
                <td>${units.toLocaleString()}</td>
                <td>${this.formatCurrency(currentValue, countryCurrency)}</td>
            `;
            
            // Track first row with investment amount
            if (investmentAmount > 0 && !firstRowWithAmount) {
                firstRowWithAmount = { row, ticker };
            }
            
            // Make row clickable
            row.addEventListener('click', (e) => {
                e.stopPropagation();
                // Remove previous selection
                document.querySelectorAll('.etf-table tbody tr').forEach(r => r.classList.remove('selected'));
                row.classList.add('selected');
                this.selectedTableRow = ticker;
                console.log('Row clicked, updating chart for:', ticker);
                const activePeriod = document.querySelector('.time-toggle.active')?.dataset.period || '1y';
                this.updateGrowthChart(activePeriod);
            });

            tbody.appendChild(row);
        });

        // Auto-select first row with investment amount if available
        if (firstRowWithAmount && !this.selectedTableRow) {
            firstRowWithAmount.row.classList.add('selected');
            this.selectedTableRow = firstRowWithAmount.ticker;
            // Update chart after a short delay to ensure DOM is ready
            setTimeout(() => {
                const activePeriod = document.querySelector('.time-toggle.active')?.dataset.period || '1y';
                this.updateGrowthChart(activePeriod);
            }, 100);
        } else if (this.selectedTableRow) {
            // If we have a selected row, make sure it's still selected
            const selectedRow = tbody.querySelector(`tr[data-ticker="${this.selectedTableRow}"]`);
            if (selectedRow) {
                selectedRow.classList.add('selected');
                setTimeout(() => {
                    const activePeriod = document.querySelector('.time-toggle.active')?.dataset.period || '1y';
                    this.updateGrowthChart(activePeriod);
                }, 100);
            }
        }
    }

    updateGrowthChart(period = null) {
        // If no period provided, get it from the active button (default to 1y)
        if (!period) {
            period = document.querySelector('.time-toggle.active')?.dataset.period || '1y';
        }
        // Get container for chart
        const container = document.querySelector('.chart-container');
        if (!container) {
            console.warn('Chart container not found');
            return;
        }

        // Destroy existing chart
        if (this.growthChart) {
            this.growthChart.destroy();
            this.growthChart = null;
        }

        // Ensure canvas exists in container
        let canvas = document.getElementById('growthChart');
        if (!canvas) {
            container.innerHTML = '<canvas id="growthChart"></canvas>';
            canvas = document.getElementById('growthChart');
        }
        
        // Use selected ETF or all selected ETFs
        const etfToShow = this.selectedTableRow || (this.selectedETFs.length > 0 ? this.selectedETFs[0] : null);
        if (!etfToShow) {
            // Show placeholder message but keep canvas
            const placeholder = document.createElement('div');
            placeholder.style.cssText = 'padding: 3rem; text-align: center; color: #6b7280; position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; flex-direction: column; justify-content: center; z-index: 1;';
            placeholder.innerHTML = `
                <p style="font-size: 1.1rem; margin-bottom: 0.5rem;">📊 Chart will appear here</p>
                <p style="font-size: 0.9rem;">Please select an ETF and set investment amounts, then click on a row in the table above to view the growth projection.</p>
            `;
            // Remove existing placeholder if any
            const existingPlaceholder = container.querySelector('div[style*="position: absolute"]');
            if (existingPlaceholder) {
                existingPlaceholder.remove();
            }
            container.appendChild(placeholder);
            canvas.style.opacity = '0';
            return;
        }

        const etf = this.etfData.find(e => e.ticker === etfToShow);
        if (!etf) {
            console.warn(`ETF ${etfToShow} not found`);
            const placeholder = document.createElement('div');
            placeholder.style.cssText = 'padding: 3rem; text-align: center; color: #dc2626; position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; flex-direction: column; justify-content: center; z-index: 1;';
            placeholder.innerHTML = '<p style="font-size: 1.1rem;">Error: ETF not found</p>';
            const existingPlaceholder = container.querySelector('div[style*="position: absolute"]');
            if (existingPlaceholder) {
                existingPlaceholder.remove();
            }
            container.appendChild(placeholder);
            canvas.style.opacity = '0';
            return;
        }

        const investmentAmount = this.investmentAmounts[etfToShow]?.[this.selectedCountry] || 0;
        if (investmentAmount === 0) {
            // Show message if no investment amount set but keep canvas
            const placeholder = document.createElement('div');
            placeholder.style.cssText = 'padding: 3rem; text-align: center; color: #6b7280; position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; flex-direction: column; justify-content: center; z-index: 1;';
            placeholder.innerHTML = `
                <p style="font-size: 1.1rem; margin-bottom: 0.5rem;">💰 Set Investment Amount</p>
                <p style="font-size: 0.9rem;">Please set an investment amount for ${etfToShow} to see the growth projection.</p>
            `;
            // Remove existing placeholder if any
            const existingPlaceholder = container.querySelector('div[style*="position: absolute"]');
            if (existingPlaceholder) {
                existingPlaceholder.remove();
            }
            container.appendChild(placeholder);
            canvas.style.opacity = '0';
            return;
        }

        // Remove any placeholder messages
        const placeholder = container.querySelector('div[style*="position: absolute"]');
        if (placeholder) {
            placeholder.remove();
        }
        canvas.style.opacity = '1';

        // Time period controls how far back/forward to show data relative to investment date
        const historicalYears = period === '1y' ? 1 : period === '5y' ? 5 : period === '10y' ? 10 : period === '20y' ? 20 : 5;
        const countryCurrency = this.getCurrencyForCountry(this.selectedCountry);
        
        // Get the planned investment date
        let investmentDate;
        if (this.investmentDate) {
            // Parse the date string (format: YYYY-MM-DD)
            investmentDate = new Date(this.investmentDate + 'T00:00:00');
            if (isNaN(investmentDate.getTime())) {
                console.warn('Invalid investment date, using today:', this.investmentDate);
                investmentDate = new Date();
            }
        } else {
            investmentDate = new Date(); // Fallback to today
        }
        investmentDate.setHours(0, 0, 0, 0);
        
        console.log('Using investment date for chart:', {
            dateString: this.investmentDate,
            parsedDate: investmentDate.toISOString(),
            period: period
        });

        // Generate historical data: from (investment date - period) to investment date
        const historicalData = this.generateHistoricalDataForETF(etf, investmentAmount, historicalYears, countryCurrency, investmentDate);
        
        // Debug: Log the date ranges
        console.log('Chart date ranges:', {
            investmentDate: investmentDate.toISOString(),
            historicalYears: historicalYears,
            historicalDataPoints: historicalData.length,
            firstHistoricalDate: historicalData.length > 0 ? historicalData[0].x : 'none',
            lastHistoricalDate: historicalData.length > 0 ? historicalData[historicalData.length - 1].x : 'none'
        });
        
        // Get projection scenario
        const scenario = this.getProjectionScenario();
        
        // Projection should start from planned investment date and extend forward for the same period
        const projectionData = this.generateProjectionDataForETF(etf, investmentAmount, historicalYears, historicalData, countryCurrency, investmentDate, scenario);

        // Validate projection data dates are correct
        if (projectionData.length > 0) {
            const firstProjDate = new Date(projectionData[0].x);
            const lastProjDate = new Date(projectionData[projectionData.length - 1].x);
            const investmentDateObj = new Date(investmentDate);
            
            console.log('🔍 Validating projection dates:', {
                investmentDate: investmentDateObj.toISOString(),
                firstProjectionDate: firstProjDate.toISOString(),
                lastProjectionDate: lastProjDate.toISOString(),
                firstDateMatches: firstProjDate.getTime() === investmentDateObj.getTime(),
                allDatesAfterInvestment: projectionData.every(d => new Date(d.x) >= investmentDateObj)
            });
            
            // Ensure all projection dates are at or after the investment date
            const invalidDates = projectionData.filter(d => {
                const date = new Date(d.x);
                return date < investmentDateObj;
            });
            
            if (invalidDates.length > 0) {
                console.error('❌ Found projection dates before investment date!', {
                    invalidCount: invalidDates.length,
                    invalidDates: invalidDates.map(d => new Date(d.x).toISOString()),
                    investmentDate: investmentDateObj.toISOString()
                });
                // Filter out invalid dates
                projectionData.splice(0, projectionData.length, ...projectionData.filter(d => new Date(d.x) >= investmentDateObj));
            }
        }

        // Check if we have data
        if (historicalData.length === 0 && projectionData.length === 0) {
            const placeholder = document.createElement('div');
            placeholder.style.cssText = 'padding: 3rem; text-align: center; color: #6b7280; position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; flex-direction: column; justify-content: center; z-index: 1;';
            placeholder.innerHTML = '<p style="font-size: 1.1rem;">No data available for chart</p>';
            const existingPlaceholder = container.querySelector('div[style*="position: absolute"]');
            if (existingPlaceholder) {
                existingPlaceholder.remove();
            }
            container.appendChild(placeholder);
            canvas.style.opacity = '0';
            return;
        }

        // Final validation before creating chart
        console.log('📊 Creating chart with:', {
            historicalDataPoints: historicalData.length,
            projectionDataPoints: projectionData.length,
            historicalDateRange: historicalData.length > 0 ? {
                start: new Date(historicalData[0].x).toLocaleDateString('en-US'),
                end: new Date(historicalData[historicalData.length - 1].x).toLocaleDateString('en-US')
            } : 'none',
            projectionDateRange: projectionData.length > 0 ? {
                start: new Date(projectionData[0].x).toLocaleDateString('en-US'),
                end: new Date(projectionData[projectionData.length - 1].x).toLocaleDateString('en-US')
            } : 'none'
        });

        this.growthChart = new Chart(canvas, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: `${etf.ticker} - Historical Growth`,
                        data: historicalData,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: `${etf.ticker} - Expected Projection`,
                        data: projectionData,
                        borderColor: '#764ba2',
                        borderDash: [5, 5],
                        tension: 0.4,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                aspectRatio: 2,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'x', // Match by x-value (date) instead of index - this ensures correct date display
                        intersect: false,
                        callbacks: {
                            title: function(context) {
                                // Show the actual date from the data point
                                if (context.length > 0 && context[0].parsed && context[0].parsed.x !== null) {
                                    const date = new Date(context[0].parsed.x);
                                    if (!isNaN(date.getTime())) {
                                        return date.toLocaleDateString('en-US', { 
                                            year: 'numeric', 
                                            month: 'short', 
                                            day: 'numeric' 
                                        });
                                    }
                                }
                                return '';
                            },
                            label: function(context) {
                                const currency = this.getCurrencyForCountry(this.selectedCountry);
                                const symbol = currency === 'EUR' ? '€' : '$';
                                return `${context.dataset.label}: ${symbol}${context.parsed.y.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                            }.bind(this)
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'year'
                        },
                        title: {
                            display: true,
                            text: 'Year'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: `Portfolio Value (${this.getCurrencyForCountry(this.selectedCountry)})`
                        },
                        ticks: {
                            callback: (value) => {
                                const currency = this.getCurrencyForCountry(this.selectedCountry);
                                const symbol = currency === 'EUR' ? '€' : '$';
                                return `${symbol}${value.toLocaleString()}`;
                            }
                        }
                    }
                }
            }
        });
    }

    generateHistoricalDataForETF(etf, initialAmount, years, targetCurrency = 'EUR', investmentDate = null) {
        const data = [];
        
        // Calculate date range: from (investment date - years) to investment date
        let endDate;
        if (investmentDate) {
            endDate = new Date(investmentDate);
        } else {
            endDate = new Date(); // Fallback to today
        }
        endDate.setHours(0, 0, 0, 0);
        
        const startDate = new Date(endDate);
        startDate.setFullYear(startDate.getFullYear() - years);
        startDate.setHours(0, 0, 0, 0);
        
        console.log('Historical data date range:', {
            startDate: startDate.toISOString(),
            endDate: endDate.toISOString(),
            years: years
        });
        
        // Convert initial amount to target currency
        let initialAmountConverted = initialAmount;
        if (targetCurrency === 'EUR') {
            if (etf.nativeCurrency === 'USD') {
                initialAmountConverted = initialAmount / this.exchangeRate;
            } else if (etf.nativeCurrency === 'GBP') {
                initialAmountConverted = initialAmount * 1.15;
            }
        } else if (targetCurrency === 'USD') {
            if (etf.nativeCurrency === 'EUR') {
                initialAmountConverted = initialAmount * this.exchangeRate;
            } else if (etf.nativeCurrency === 'GBP') {
                initialAmountConverted = initialAmount * 1.25;
            }
        }
        
        // Use actual ETF data if available
        if (etf.data && etf.data.priceData && etf.data.priceData.length > 0) {
            const priceData = etf.data.priceData;
            
            // Find the latest available date in the data
            let latestDataDate = null;
            let earliestDataDate = null;
            priceData.forEach(d => {
                const date = new Date(d.date);
                if (!latestDataDate || date > latestDataDate) {
                    latestDataDate = date;
                }
                if (!earliestDataDate || date < earliestDataDate) {
                    earliestDataDate = date;
                }
            });
            
            // Calculate the desired date range based on investment date
            // We want: (investment date - years) to investment date
            const desiredStartDate = new Date(endDate);
            desiredStartDate.setFullYear(desiredStartDate.getFullYear() - years);
            desiredStartDate.setHours(0, 0, 0, 0);
            
            // Check if investment date is in the future relative to available data
            const investmentDateInFuture = latestDataDate && endDate > latestDataDate;
            
            // If investment date is in the future, we can't show real historical data for that period
            // We should only show data if it falls within the desired range
            // Otherwise, we'll rely on synthetic data generation below
            let actualStartDate = desiredStartDate;
            let actualEndDate = endDate;
            
            // If investment date is in the future, we can only use data up to latestDataDate
            // But we should NOT show old data that's outside the requested period
            if (investmentDateInFuture) {
                // Only use data if it's within the desired range (relative to investment date)
                // If the desired range is entirely in the future, we won't have any real data
                actualEndDate = latestDataDate < endDate ? latestDataDate : endDate;
                
                // Only show data if it's within the desired period
                // If desiredStartDate is also in the future (relative to latestDataDate), we have no real data
                if (desiredStartDate > latestDataDate) {
                    // The entire requested period is in the future - no real historical data available
                    console.log('Requested historical period is entirely in the future - will use synthetic data', {
                        desiredStartDate: desiredStartDate.toISOString(),
                        desiredEndDate: endDate.toISOString(),
                        latestDataDate: latestDataDate.toISOString()
                    });
                    // We'll skip real data and use synthetic data below
                } else {
                    // Part of the period is in the past - use what we have
                    actualStartDate = desiredStartDate < earliestDataDate ? earliestDataDate : desiredStartDate;
                }
            }
            
            console.log('Data availability:', {
                earliestDataDate: earliestDataDate ? earliestDataDate.toISOString() : 'none',
                latestDataDate: latestDataDate ? latestDataDate.toISOString() : 'none',
                desiredStartDate: desiredStartDate.toISOString(),
                desiredEndDate: endDate.toISOString(),
                actualStartDate: actualStartDate.toISOString(),
                actualEndDate: actualEndDate.toISOString(),
                investmentDateInFuture: investmentDateInFuture,
                willHaveRealData: !investmentDateInFuture || (actualStartDate <= latestDataDate && actualEndDate <= latestDataDate)
            });
            
            // Filter data to ONLY the desired range (relative to investment date)
            // This ensures we don't show old data that's outside the requested period
            const relevantData = priceData.filter(d => {
                // Parse date consistently - handle both string and Date objects
                let date;
                if (typeof d.date === 'string') {
                    date = new Date(d.date);
                } else if (d.date instanceof Date) {
                    date = new Date(d.date);
                } else {
                    return false; // Skip invalid dates
                }
                
                // Normalize dates to compare properly
                date.setHours(0, 0, 0, 0);
                
                // CRITICAL: Only include data within the desired range (relative to investment date)
                // This prevents showing old data (e.g., 2021) when user requests 1 year back from a future date
                return date >= actualStartDate && date <= actualEndDate;
            });

            if (relevantData.length > 0) {
                // Sort by date to ensure chronological order
                relevantData.sort((a, b) => {
                    const dateA = new Date(a.date);
                    const dateB = new Date(b.date);
                    return dateA - dateB;
                });
                
                // Get first price in target currency
                let firstPrice = 1;
                if (targetCurrency === 'EUR') {
                    firstPrice = relevantData[0].close_eur || relevantData[0].close || 1;
                } else {
                    // Convert to USD if needed
                    const eurPrice = relevantData[0].close_eur || relevantData[0].close || 0;
                    firstPrice = eurPrice * this.exchangeRate;
                }
                
                relevantData.forEach(d => {
                    let price = 0;
                    if (targetCurrency === 'EUR') {
                        price = d.close_eur || d.close || 0;
                    } else {
                        // Convert to USD
                        const eurPrice = d.close_eur || d.close || 0;
                        price = eurPrice * this.exchangeRate;
                    }
                    const value = initialAmountConverted * (price / firstPrice);
                    
                    // Ensure date is in ISO format for Chart.js
                    let dateStr = d.date;
                    if (typeof dateStr !== 'string') {
                        dateStr = new Date(d.date).toISOString();
                    } else {
                        // Ensure it's a valid ISO string
                        const parsedDate = new Date(dateStr);
                        if (!isNaN(parsedDate.getTime())) {
                            dateStr = parsedDate.toISOString();
                        }
                    }
                    
                    data.push({
                        x: dateStr,
                        y: Math.max(0, value)
                    });
                });
            }
        }
        
        // If no data or insufficient data, generate synthetic data
        if (data.length === 0) {
            const annualReturn = 0.08;
            const volatility = 0.15;
            
            // Generate monthly data points from startDate to endDate
            let currentDate = new Date(startDate);
            let monthIndex = 0;
            
            while (currentDate <= endDate) {
                const monthlyReturn = (annualReturn / 12) + (Math.random() - 0.5) * (volatility / Math.sqrt(12));
                const value = initialAmountConverted * Math.pow(1 + monthlyReturn, monthIndex);
                data.push({
                    x: currentDate.toISOString(),
                    y: Math.max(0, value)
                });
                
                // Move to next month
                currentDate = new Date(currentDate);
                currentDate.setMonth(currentDate.getMonth() + 1);
                monthIndex++;
            }
        }
        
        return data;
    }

    generateProjectionDataForETF(etf, initialAmount, years, historicalData, targetCurrency = 'EUR', investmentDate = null, scenario = 'moderate') {
        const data = [];
        
        // Start projection from the planned investment date (ALWAYS use investment date, not historical data end date)
        let startDate;
        if (investmentDate) {
            // investmentDate is already a Date object from updateGrowthChart
            startDate = new Date(investmentDate);
        } else if (this.investmentDate) {
            // Parse date string (format: YYYY-MM-DD)
            startDate = new Date(this.investmentDate + 'T00:00:00');
            if (isNaN(startDate.getTime())) {
                console.warn('Invalid investment date string, using today:', this.investmentDate);
                startDate = new Date();
            }
        } else {
            // Fallback to today if no date selected
            startDate = new Date();
        }
        startDate.setHours(0, 0, 0, 0);
        
        console.log('Projection calculation:', {
            investmentDateParam: investmentDate ? investmentDate.toISOString() : 'null',
            thisInvestmentDate: this.investmentDate,
            startDate: startDate.toISOString(),
            years: years,
            willGenerateMonths: years * 12 + 1
        });
        
        // Determine starting value for projection
        let startingValue;
        
        // Check if we have historical data that reaches the investment date
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        if (startDate > today || historicalData.length === 0) {
            // Investment date is in the future OR no historical data available
            // Use the investment amount converted to target currency
            startingValue = initialAmount;
            if (targetCurrency === 'EUR' && etf.nativeCurrency === 'USD') {
                startingValue = initialAmount / this.exchangeRate;
            } else if (targetCurrency === 'USD' && etf.nativeCurrency === 'EUR') {
                startingValue = initialAmount * this.exchangeRate;
            } else if (targetCurrency === 'USD' && etf.nativeCurrency === 'GBP') {
                startingValue = initialAmount * 1.25;
            } else if (targetCurrency === 'EUR' && etf.nativeCurrency === 'GBP') {
                startingValue = initialAmount * 1.15;
            }
        } else {
            // Investment date is today or past - use last historical value if available
            if (historicalData.length > 0) {
                const lastHistorical = historicalData[historicalData.length - 1];
                startingValue = lastHistorical.y;
            } else {
                // Fallback to investment amount
                startingValue = initialAmount;
            }
        }
        
        // Get CAGR based on selected scenario
        const expectedCAGR = this.getCAGRForScenario(scenario, etf);
        
        // Generate projection data starting from planned investment date, extending forward
        // Project for the same number of years as the historical lookback period
        // Generate monthly data points (12 months per year)
        const totalMonths = years * 12;
        
        // Verify startDate is correct before generating
        if (isNaN(startDate.getTime())) {
            console.error('Invalid startDate for projection:', startDate);
            return data;
        }
        
        // Generate dates more reliably by working with year/month directly
        const startYear = startDate.getFullYear();
        const startMonth = startDate.getMonth();
        const startDay = startDate.getDate();
        
        for (let i = 0; i <= totalMonths; i++) {
            // Calculate target month and year
            let targetMonth = startMonth + i;
            let targetYear = startYear;
            
            // Handle year rollover
            while (targetMonth > 11) {
                targetMonth -= 12;
                targetYear += 1;
            }
            
            // Create date using year/month/day to avoid setMonth issues
            const date = new Date(targetYear, targetMonth, startDay);
            date.setHours(0, 0, 0, 0); // Normalize time
            
            // Verify date is valid
            if (isNaN(date.getTime())) {
                console.error('Invalid date generated at month', i, 'from startDate', startDate.toISOString());
                continue;
            }
            
            // Verify date is at or after investment date
            if (date < startDate) {
                console.error('Generated date is before start date!', {
                    generated: date.toISOString(),
                    startDate: startDate.toISOString(),
                    monthOffset: i
                });
                continue;
            }
            
            // Calculate value using monthly compounding
            const monthlyReturn = expectedCAGR / 12;
            const value = startingValue * Math.pow(1 + monthlyReturn, i);
            
            const dateISO = date.toISOString();
            data.push({
                x: dateISO,
                y: value
            });
        }
        
        // Debug logging with detailed information
        if (data.length > 0) {
            console.log('✅ Projection data generated:', {
                investmentDate: startDate.toISOString(),
                investmentDateFormatted: startDate.toLocaleDateString('en-US'),
                projectionStartDate: data[0].x,
                projectionStartDateFormatted: new Date(data[0].x).toLocaleDateString('en-US'),
                projectionEndDate: data[data.length - 1].x,
                projectionEndDateFormatted: new Date(data[data.length - 1].x).toLocaleDateString('en-US'),
                years: years,
                totalMonths: totalMonths,
                dataPoints: data.length,
                startingValue: startingValue,
                endingValue: data[data.length - 1].y,
                firstFewDates: data.slice(0, 3).map(d => new Date(d.x).toLocaleDateString('en-US')),
                lastFewDates: data.slice(-3).map(d => new Date(d.x).toLocaleDateString('en-US'))
            });
        } else {
            console.error('❌ No projection data generated!', {
                startDate: startDate.toISOString(),
                years: years,
                totalMonths: totalMonths
            });
        }
        
        return data;
    }

    calculateRiskMetrics() {
        if (this.selectedETFs.length === 0) {
            document.getElementById('worst-drawdown').textContent = '-';
            document.getElementById('worst-drawdown-year').textContent = '';
            document.getElementById('annual-volatility').textContent = '-';
            document.getElementById('stress-test').textContent = '-';
            return;
        }

        // Get country currency
        const countryCurrency = this.getCurrencyForCountry(this.selectedCountry);
        const currencySymbol = countryCurrency === 'EUR' ? '€' : '$';

        // Calculate total investment in country currency
        let totalInvestment = 0;
        const etfWeights = [];
        
        // First pass: collect all ETFs and amounts
        this.selectedETFs.forEach(ticker => {
            const amount = this.investmentAmounts[ticker]?.[this.selectedCountry] || 0;
            totalInvestment += amount;
            
            const etf = this.etfData.find(e => e.ticker === ticker);
            if (etf && amount > 0) {
                etfWeights.push({
                    ticker: ticker,
                    amount: amount,
                    etf: etf
                });
            }
        });

        // Second pass: calculate normalized weights
        if (totalInvestment > 0) {
            etfWeights.forEach(w => w.weight = w.amount / totalInvestment);
        }

        // Calculate portfolio-level metrics from individual ETF data
        let worstDrawdown = 0;
        let worstDrawdownYear = '';
        let annualVolatility = 0;
        const allReturns = [];

        // Collect price data from all selected ETFs
        etfWeights.forEach(({ etf, weight }) => {
            if (etf.data && etf.data.priceData && etf.data.priceData.length > 0) {
                const priceData = etf.data.priceData;
                
                // Get price field based on currency
                const priceField = (countryCurrency === 'EUR' && priceData[0].hasOwnProperty('close_eur')) 
                    ? 'close_eur' 
                    : 'close';
                
                // Calculate daily returns
                const returns = [];
                for (let i = 1; i < priceData.length; i++) {
                    const prevPrice = priceData[i - 1][priceField];
                    const currPrice = priceData[i][priceField];
                    if (prevPrice && currPrice && prevPrice > 0) {
                        returns.push((currPrice - prevPrice) / prevPrice);
                    }
                }
                
                // Calculate drawdown for this ETF
                let peak = priceData[0][priceField];
                let maxDrawdown = 0;
                let drawdownDate = null;
                
                priceData.forEach((d, idx) => {
                    const price = d[priceField];
                    if (price > peak) {
                        peak = price;
                    }
                    const drawdown = (price - peak) / peak;
                    if (drawdown < maxDrawdown) {
                        maxDrawdown = drawdown;
                        drawdownDate = d.date;
                    }
                });
                
                // Weight the drawdown by ETF weight in portfolio
                if (Math.abs(maxDrawdown) > Math.abs(worstDrawdown)) {
                    worstDrawdown = maxDrawdown;
                    if (drawdownDate) {
                        const date = new Date(drawdownDate);
                        worstDrawdownYear = date.getFullYear().toString();
                    }
                }
                
                // Calculate volatility (annualized from daily returns)
                if (returns.length > 0) {
                    const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
                    const variance = returns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / returns.length;
                    const dailyVolatility = Math.sqrt(variance);
                    const annualVol = dailyVolatility * Math.sqrt(252); // 252 trading days per year
                    
                    // Weight by ETF weight in portfolio
                    annualVolatility += annualVol * weight;
                }
            }
        });

        // Display worst drawdown
        if (worstDrawdown < 0) {
            document.getElementById('worst-drawdown').textContent = `${(worstDrawdown * 100).toFixed(1)}%`;
            document.getElementById('worst-drawdown-year').textContent = worstDrawdownYear ? `Year: ${worstDrawdownYear}` : '';
        } else {
            document.getElementById('worst-drawdown').textContent = '-';
            document.getElementById('worst-drawdown-year').textContent = '';
        }

        // Display annual volatility
        if (annualVolatility > 0) {
            document.getElementById('annual-volatility').textContent = `${(annualVolatility * 100).toFixed(1)}%`;
        } else {
            document.getElementById('annual-volatility').textContent = '-';
        }

        // Stress test (-30% drop)
        const stressValue = totalInvestment * 0.7;
        document.getElementById('stress-test').textContent = `${currencySymbol}${this.formatNumber(stressValue)}`;
    }

    updateTaxEstimates() {
        // Hide all tax panels first
        document.querySelectorAll('.tax-panel').forEach(panel => {
            panel.style.display = 'none';
        });

        // Show only the relevant tax panel(s) based on selected country
        const country = this.selectedCountry;
        let panelId = null;
        
        if (country === 'USA') {
            panelId = 'us';
        } else if (country === 'Australia') {
            panelId = 'au';
        } else if (country === 'Germany') {
            panelId = 'de';
        } else if (country === 'France') {
            panelId = 'fr';
        }

        if (panelId) {
            const panel = document.querySelector(`#tax-panel-${panelId}-container`) || 
                         document.querySelector(`#tax-panel-${panelId}`)?.closest('.tax-panel');
            if (panel) {
                panel.style.display = 'block';
            }
        }

        // Calculate and display tax estimate for the selected country
        this.calculateTaxEstimate(country);
    }

    calculateTaxEstimate(country) {
        // Calculate total investment value
        const countryCurrency = this.getCurrencyForCountry(country);
        const currencySymbol = countryCurrency === 'EUR' ? '€' : '$';
        let totalInvestment = 0;
        let totalCurrentValue = 0;

        this.selectedETFs.forEach(ticker => {
            const amount = this.investmentAmounts[ticker]?.[country] || 0;
            totalInvestment += amount;
            
            const etf = this.etfData.find(e => e.ticker === ticker);
            if (etf && etf.data && etf.data.latestPrice) {
                // Get current price in country currency
                let currentPrice = etf.data.latestPrice;
                if (countryCurrency === 'EUR' && etf.data.latestPriceEUR) {
                    currentPrice = etf.data.latestPriceEUR;
                } else if (countryCurrency === 'USD' && etf.nativeCurrency === 'EUR') {
                    currentPrice = etf.data.latestPrice * this.exchangeRate;
                }
                
                // Calculate units (simplified - would use actual purchase price)
                const units = amount / currentPrice;
                totalCurrentValue += units * currentPrice;
            }
        });

        // Calculate capital gains (simplified - assumes all gains)
        const capitalGains = Math.max(0, totalCurrentValue - totalInvestment);

        // Country-specific tax rates (simplified estimates)
        let taxRate = 0;
        let taxEstimate = 0;
        let panelId = null;

        if (country === 'USA') {
            panelId = 'us';
            // Long-term capital gains: 0%, 15%, or 20% (using 15% as middle estimate)
            taxRate = 0.15;
            taxEstimate = capitalGains * taxRate;
        } else if (country === 'Australia') {
            panelId = 'au';
            // Capital gains: 50% discount if held >12 months, then taxed at income rate (using 20% estimate)
            taxRate = 0.20;
            taxEstimate = capitalGains * 0.5 * taxRate; // 50% discount for long-term
        } else if (country === 'Germany') {
            panelId = 'de';
            // Capital gains: 26.375% (25% + solidarity surcharge)
            taxRate = 0.26375;
            taxEstimate = capitalGains * taxRate;
        } else if (country === 'France') {
            panelId = 'fr';
            // Capital gains: 30% (flat rate)
            taxRate = 0.30;
            taxEstimate = capitalGains * taxRate;
        }

        // Update tax estimate display
        if (panelId) {
            const taxEstimateElement = document.getElementById(`tax-estimate-${panelId}`);
            if (taxEstimateElement) {
                taxEstimateElement.textContent = `${currencySymbol}${this.formatNumber(taxEstimate)}`;
            }
        }
    }

    formatNumber(num) {
        return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    getCurrencySymbol(currency) {
        const symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£'
        };
        return symbols[currency] || currency;
    }

    formatCurrency(amount, currency) {
        const symbol = this.getCurrencySymbol(currency);
        return `${symbol}${this.formatNumber(amount)}`;
    }
}

// Tax panel toggle function
function toggleTaxPanel(panelId) {
    const panel = document.getElementById(`tax-panel-${panelId}`);
    const header = panel.previousElementSibling;
    const parent = header.parentElement;
    
    panel.classList.toggle('active');
    parent.classList.toggle('active');
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const strategy = new InvestmentStrategy();
    // Initialize chart with the active button's period (default is 1y)
    setTimeout(() => {
        const activePeriod = document.querySelector('.time-toggle.active')?.dataset.period || '1y';
        strategy.updateGrowthChart(activePeriod);
    }, 1000);
});
