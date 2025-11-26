// ETF Insights Explorer - Market Insights Dashboard JavaScript (Horizontal Layout)

class MarketInsightsDashboard {
    constructor() {
        this.fearGreedPieChart = null;
        this.sectorPieChart = null;
        this.companyPieChart = null;
        this.holdingsChart = null;
        this.fearGreedData = null;
        this.sectorData = null;
        this.etfHoldingsData = null;
        console.log('🚀 Market Insights Dashboard initialized');
        this.init();
    }

    async init() {
        try {
            console.log('Initializing dashboard...');
            this.showLoading();
            
            // Load only Fear & Greed Index data
            await this.loadFearGreedIndex();
            
            this.hideLoading();
            this.setupEventListeners();
            console.log('Dashboard initialized successfully');
        } catch (error) {
            console.error('Error initializing dashboard:', error);
            console.error('Error stack:', error.stack);
            this.showError('Failed to load dashboard data. Please refresh the page.');
            this.hideLoading();
        }
    }

    showLoading() {
        const loading = document.getElementById('loading');
        if (loading) loading.style.display = 'flex';
    }

    hideLoading() {
        const loading = document.getElementById('loading');
        if (loading) loading.style.display = 'none';
    }

    showError(message) {
        const errorDiv = document.getElementById('error-message');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
    }

    async loadFearGreedIndex() {
        try {
            const response = await fetch('data/fear_greed_index.json');
            if (!response.ok) throw new Error('Failed to fetch Fear & Greed Index');
            
            this.fearGreedData = await response.json();
            this.renderFearGreedIndex();
        } catch (error) {
            console.error('Error loading Fear & Greed Index:', error);
            document.getElementById('fear-greed-value').textContent = 'N/A';
            document.getElementById('fear-greed-label').textContent = 'Data unavailable';
        }
    }

    renderFearGreedIndex() {
        if (!this.fearGreedData || !this.fearGreedData.current) {
            console.warn('Fear & Greed data not available');
            return;
        }

        const current = this.fearGreedData.current;
        const value = current.value;
        const classification = current.classification;

        // Update value and label
        const valueEl = document.getElementById('fear-greed-value');
        const labelEl = document.getElementById('fear-greed-label');
        if (valueEl) valueEl.textContent = value;
        if (labelEl) labelEl.textContent = classification;

        // Create gauge chart (semi-circular speedometer style)
        const ctx = document.getElementById('fear-greed-gauge-chart');
        if (!ctx) {
            console.error('Fear & Greed gauge chart canvas not found');
            return;
        }

        // Prepare data for gauge - 5 segments representing sentiment zones
        // Based on CNN Fear & Greed Index: 0-25 (Extreme Fear), 25-50 (Fear), 50 (Neutral), 50-75 (Greed), 75-100 (Extreme Greed)
        const gaugeData = {
            labels: ['Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed'],
            datasets: [{
                data: [23, 23, 12, 23, 19], // Segments: 0-23, 23-46, 46-58 (Neutral - larger), 58-81, 81-100
                backgroundColor: [
                    '#ef4444', // Extreme Fear - Red (0-25)
                    '#f59e0b', // Fear - Orange (25-50)
                    '#eab308', // Neutral - Yellow (50)
                    '#84cc16', // Greed - Light Green (50-75)
                    '#10b981'  // Extreme Greed - Green (75-100)
                ],
                borderWidth: 0,
                circumference: 180, // Semi-circle (180 degrees)
                rotation: 270 // Start from left (270 degrees = -90°)
            }]
        };

        // Destroy existing chart if it exists
        if (this.fearGreedPieChart) {
            this.fearGreedPieChart.destroy();
        }

        // Custom plugin for gauge needle
        const gaugeNeedlePlugin = {
            id: 'gaugeNeedle',
            afterDraw: (chart) => {
                const { ctx, chartArea: { left, right, top, bottom, width, height } } = chart;
                const centerX = left + width / 2;
                const centerY = bottom;
                
                // Calculate angle for needle
                // With rotation 270, the gauge starts at the left (-90°)
                // The semi-circle spans 180° from left (-90°) to right (90°)
                // For value 15: should point to the left side in the Extreme Fear zone
                // Angle: -90° (left) + (value / 100) * 180° (span of 180 degrees)
                // Convert to radians: -π/2 + (value/100) * π
                const startAngle = -Math.PI / 2; // -90 degrees (left)
                const spanAngle = Math.PI; // 180 degrees (semi-circle from left to right)
                const angle = startAngle + (value / 100) * spanAngle;
                
                const needleLength = height * 0.55; // Longer needle to reach the colored range
                const needleWidth = 6;
                
                ctx.save();
                ctx.translate(centerX, centerY);
                ctx.rotate(angle);
                
                // Draw needle (thick arrow pointing up/outward)
                ctx.beginPath();
                ctx.moveTo(0, 0);
                ctx.lineTo(-needleWidth, -needleWidth * 1.5);
                ctx.lineTo(0, -needleLength);
                ctx.lineTo(needleWidth, -needleWidth * 1.5);
                ctx.closePath();
                ctx.fillStyle = '#0f172a';
                ctx.fill();
                
                // Draw center circle (pivot point)
                ctx.beginPath();
                ctx.arc(0, 0, 12, 0, 2 * Math.PI);
                ctx.fillStyle = '#0f172a';
                ctx.fill();
                
                // Add white border to center circle for better visibility
                ctx.beginPath();
                ctx.arc(0, 0, 12, 0, 2 * Math.PI);
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 2;
                ctx.stroke();
                
                ctx.restore();
                
                // Draw scale numbers (0, 25, 50, 75, 100) around the gauge
                // Chart rotation is 270°, so visually: -90° = left, 0° = top, 90° = right
                // But in canvas coordinates with centerY at bottom:
                // - To draw LEFT: angle = 180° (or -180°)
                // - To draw TOP: angle = -90°
                // - To draw RIGHT: angle = 0°
                // So we need to convert: chartAngle → canvasAngle = chartAngle - 90°
                ctx.save();
                ctx.fillStyle = '#ffffff';
                ctx.font = 'bold 16px sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.strokeStyle = '#0f172a';
                ctx.lineWidth = 4;
                
                // Chart angles: 0 (left/-90°), 25 (-45°), 50 (0°), 75 (45°), 100 (90°)
                // Convert to canvas angles by subtracting 90°: -90°→-180°, -45°→-135°, 0°→-90°, 45°→-45°, 90°→0°
                const numberPositions = [
                    { value: 0, chartAngle: -Math.PI / 2 },    // Chart left (-90°)
                    { value: 25, chartAngle: -Math.PI / 4 },  // Chart -45°
                    { value: 50, chartAngle: 0 },             // Chart top (0°)
                    { value: 75, chartAngle: Math.PI / 4 },   // Chart 45°
                    { value: 100, chartAngle: Math.PI / 2 }   // Chart right (90°)
                ];
                
                // Position numbers on the arc (outside edge)
                const numberRadius = height * 0.52; // Slightly outside the arc
                numberPositions.forEach(pos => {
                    // Convert chart angle to canvas angle: subtract 90° (π/2)
                    const canvasAngle = pos.chartAngle - Math.PI / 2;
                    const numX = centerX + Math.cos(canvasAngle) * numberRadius;
                    const numY = centerY + Math.sin(canvasAngle) * numberRadius;
                    ctx.strokeText(pos.value.toString(), numX, numY);
                    ctx.fillText(pos.value.toString(), numX, numY);
                });
                
                // Draw sentiment labels at the TOP of the arc (on top edge of colored segments)
                // The arc is a semi-circle: left (-90°) to right (90°), with top at 0°
                // In canvas coordinates with centerY at bottom:
                // - Chart angle -90° (left) → canvas angle -180° (points left)
                // - Chart angle 0° (top) → canvas angle -90° (points up)
                // - Chart angle 90° (right) → canvas angle 0° (points right)
                ctx.font = 'bold 11px sans-serif';
                ctx.textBaseline = 'bottom'; // Bottom of text will sit on the arc edge
                
                // Chart angles for labels - positioned at the center of each segment
                // Segments: 0-23 (Extreme Fear), 23-46 (Fear), 46-58 (Neutral), 58-81 (Greed), 81-100 (Extreme Greed)
                // Calculate midpoints: 11.5, 34.5, 52, 69.5, 90.5
                const sentimentLabels = [
                    { text: 'EXTREME FEAR', chartAngle: -Math.PI / 2 + (11.5 / 100) * Math.PI, color: '#ffffff' }, // Left segment (red)
                    { text: 'FEAR', chartAngle: -Math.PI / 2 + (34.5 / 100) * Math.PI, color: '#ffffff' }, // Orange segment
                    { text: 'NEUTRAL', chartAngle: -Math.PI / 2 + (52 / 100) * Math.PI, color: '#0f172a' }, // Top center (52) - dark text on yellow
                    { text: 'GREED', chartAngle: -Math.PI / 2 + (69.5 / 100) * Math.PI, color: '#ffffff' }, // Light green segment
                    { text: 'EXTREME GREED', chartAngle: -Math.PI / 2 + (90.5 / 100) * Math.PI, color: '#ffffff' } // Right segment (green)
                ];
                
                // Calculate the actual outer radius of the doughnut chart
                // Chart.js draws the doughnut with cutout 65%, so outer radius = chart radius
                // The chart area dimensions determine the actual radius
                const chartRadius = Math.min(width, height) / 2; // Radius of the doughnut chart
                const outerRadius = chartRadius; // Outer edge of colored segments
                
                // Calculate arc center - for a semi-circle with flat edge at bottom
                // The arc center (if it were a full circle) would be at centerY - chartRadius
                const arcCenterY = centerY - chartRadius;

                sentimentLabels.forEach((label) => {
                    // Convert chart angle to canvas angle: subtract 90° (π/2)
                    // Chart -90° → Canvas -180°, Chart 0° → Canvas -90°, Chart 90° → Canvas 0°
                    const canvasAngle = label.chartAngle - Math.PI / 2;
                    
                    // Position labels EXACTLY at the outer edge of the colored segments
                    const labelX = centerX + Math.cos(canvasAngle) * outerRadius;
                    const labelY = arcCenterY + Math.sin(canvasAngle) * outerRadius;
                    
                    // Draw text - rotate to follow arc curvature
                    ctx.save();
                    ctx.translate(labelX, labelY);
                    // Rotate text to be tangent to the arc (perpendicular to radius)
                    ctx.rotate(canvasAngle + Math.PI / 2);
                    
                    // Measure text to get actual height
                    const textMetrics = ctx.measureText(label.text);
                    const textHeight = textMetrics.actualBoundingBoxAscent + textMetrics.actualBoundingBoxDescent;
                    
                    // With textBaseline 'bottom', we need to move the text down by its height
                    // so the bottom edge sits on the arc. But since we're rotated, we move
                    // in the rotated coordinate system: translate along the rotated Y axis
                    // (which points toward the arc center) by the text height
                    ctx.translate(0, textHeight);
                    
                    ctx.fillStyle = label.color;
                    ctx.strokeStyle = label.color === '#ffffff' ? '#0f172a' : '#ffffff';
                    ctx.lineWidth = 3;
                    ctx.strokeText(label.text, 0, 0);
                    ctx.fillText(label.text, 0, 0);
                    ctx.restore();
                });
                
                ctx.restore();
            }
        };

        this.fearGreedPieChart = new Chart(ctx, {
            type: 'doughnut',
            data: gaugeData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                aspectRatio: 2,
                cutout: '65%',
                layout: {
                    padding: {
                        top: 40, // More space for labels above the arc
                        bottom: 20,
                        left: 20,
                        right: 20
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false
                    }
                },
                elements: {
                    arc: {
                        borderWidth: 0
                    }
                }
            },
            plugins: [gaugeNeedlePlugin]
        });

        // Render historical readings
        this.renderHistoricalReadings();
    }

    renderHistoricalReadings() {
        if (!this.fearGreedData || !this.fearGreedData.historical) return;

        const historical = this.fearGreedData.historical;
        const readingsContainer = document.getElementById('historical-readings');
        if (!readingsContainer) return;

        // Get specific historical points
        const now = new Date();
        const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        const oneMonthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        const oneYearAgo = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);

        // Find closest historical readings
        const previousClose = historical[1] || historical[0]; // Second item or first
        const weekAgo = historical.find(item => {
            const itemDate = new Date(item.timestamp);
            return itemDate <= oneWeekAgo;
        }) || historical[historical.length - 1];
        const monthAgo = historical.find(item => {
            const itemDate = new Date(item.timestamp);
            return itemDate <= oneMonthAgo;
        }) || historical[historical.length - 1];
        const yearAgo = historical[historical.length - 1] || historical[0];

        const readings = [
            { label: 'Previous close', data: previousClose },
            { label: '1 week ago', data: weekAgo },
            { label: '1 month ago', data: monthAgo },
            { label: '1 year ago', data: yearAgo }
        ];

        readingsContainer.innerHTML = readings.map(reading => {
            if (!reading.data) return '';
            // Convert "Extreme Fear" to "extreme-fear", "Extreme Greed" to "extreme-greed", etc.
            const sentiment = reading.data.classification.toLowerCase().replace(/\s+/g, '-');
            return `
                <div class="historical-reading-item">
                    <span class="historical-reading-label">${reading.label}:</span>
                    <div class="historical-reading-value">
                        <span class="historical-reading-sentiment ${sentiment}">${reading.data.classification}</span>
                        <span class="historical-reading-number">${reading.data.value}</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    async loadSectorData() {
        try {
            const response = await fetch('data/sp500_sectors.json');
            if (!response.ok) throw new Error('Failed to fetch sector data');
            
            this.sectorData = await response.json();
            this.renderSectorCharts();
        } catch (error) {
            console.error('Error loading sector data:', error);
        }
    }

    renderSectorCharts() {
        if (!this.sectorData) {
            console.warn('Sector data not available');
            return;
        }

        console.log('Rendering sector charts with data:', this.sectorData);

        // Render Sector Pie Chart
        if (this.sectorData.sectors && this.sectorData.sectors.length > 0) {
            this.renderSectorPieChart();
        } else {
            console.warn('No sector data available');
        }

        // Render Company Pie Chart
        if (this.sectorData.companies && this.sectorData.companies.length > 0) {
            this.renderCompanyPieChart();
        } else {
            console.warn('No company data available');
        }
    }

    renderSectorPieChart() {
        const ctx = document.getElementById('sector-pie-chart');
        if (!ctx) {
            console.error('Sector pie chart canvas not found');
            return;
        }

        const sectors = this.sectorData.sectors;
        
        // Prepare data - use absolute value of change for size, color by positive/negative
        const labels = sectors.map(s => s.sector);
        const data = sectors.map(s => Math.abs(s.changePercent));
        const colors = sectors.map(s => s.changePercent >= 0 ? '#10b981' : '#ef4444');

        // Destroy existing chart if it exists
        if (this.sectorPieChart) {
            this.sectorPieChart.destroy();
        }

        this.sectorPieChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderColor: '#0f172a',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#cbd5e1',
                            font: {
                                size: 10
                            },
                            padding: 8
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const sector = sectors[context.dataIndex];
                                return `${sector.sector}: ${sector.changePercent >= 0 ? '+' : ''}${sector.changePercent.toFixed(2)}%`;
                            }
                        }
                    }
                }
            }
        });
    }

    renderCompanyPieChart() {
        const ctx = document.getElementById('company-pie-chart');
        if (!ctx) {
            console.error('Company pie chart canvas not found');
            return;
        }

        const companies = this.sectorData.companies.slice(0, 10); // Top 10 companies
        
        // Prepare data - use weight (market cap based)
        const labels = companies.map(c => c.name);
        const data = companies.map(c => c.weight);
        const colors = companies.map(c => c.changePercent >= 0 ? '#10b981' : '#ef4444');

        // Destroy existing chart if it exists
        if (this.companyPieChart) {
            this.companyPieChart.destroy();
        }

        this.companyPieChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderColor: '#0f172a',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#cbd5e1',
                            font: {
                                size: 9
                            },
                            padding: 6
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const company = companies[context.dataIndex];
                                return `${company.name}: ${company.weight.toFixed(2)}% (${company.changePercent >= 0 ? '+' : ''}${company.changePercent.toFixed(2)}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    async loadETFHoldingsData() {
        try {
            const response = await fetch('data/etf_holdings.json');
            if (!response.ok) throw new Error('Failed to fetch ETF holdings');
            
            this.etfHoldingsData = await response.json();
        } catch (error) {
            console.error('Error loading ETF holdings data:', error);
            this.etfHoldingsData = {};
        }
    }

    setupEventListeners() {
        // No event listeners needed for single-panel dashboard
    }

    renderETFHoldings(ticker) {
        if (!ticker || !this.etfHoldingsData || !this.etfHoldingsData[ticker]) {
            document.getElementById('etf-holdings-content').style.display = 'none';
            document.getElementById('etf-holdings-empty').style.display = 'block';
            return;
        }

        const holdings = this.etfHoldingsData[ticker];
        const holdingsList = holdings.holdings || [];

        if (holdingsList.length === 0) {
            document.getElementById('etf-holdings-content').style.display = 'none';
            document.getElementById('etf-holdings-empty').innerHTML = 
                '<p>No holdings data available for this ETF.</p>';
            document.getElementById('etf-holdings-empty').style.display = 'block';
            return;
        }

        // Show content
        document.getElementById('etf-holdings-content').style.display = 'flex';
        document.getElementById('etf-holdings-empty').style.display = 'none';

        // Update ETF info
        document.getElementById('etf-holdings-name').textContent = holdings.name;
        document.getElementById('etf-holdings-count').textContent = 
            holdings.totalHoldings || holdingsList.length;

        // Render pie chart
        this.renderHoldingsPieChart(holdingsList);
    }

    renderHoldingsPieChart(holdingsList) {
        const ctx = document.getElementById('holdings-pie-chart');
        if (!ctx) return;

        // Destroy existing chart if it exists
        if (this.holdingsChart) {
            this.holdingsChart.destroy();
        }

        // Prepare data - take top 10 for readability
        const topHoldings = holdingsList.slice(0, 10);
        const labels = topHoldings.map(h => h.name);
        const data = topHoldings.map(h => h.percentage);
        
        // Generate colors
        const colors = [
            '#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b',
            '#fa709a', '#fee140', '#30cfd0', '#a8edea', '#fed6e3'
        ];

        this.holdingsChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderColor: '#0f172a',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#cbd5e1',
                            font: {
                                size: 10
                            },
                            padding: 8
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed + '%';
                            }
                        }
                    }
                }
            }
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MarketInsightsDashboard();
});
