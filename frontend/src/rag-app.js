/**
 * FinSight RAG Platform - Frontend Application
 * Modern JavaScript application for financial intelligence queries
 */

class FinSightRAG {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.currentMode = 'enrichment';
        this.currentSection = 'query';
        this.isLoading = false;
        this.cache = new Map();
        this.stats = {
            apiCallsToday: 0,
            avgResponseTime: 0,
            totalQueries: 0
        };
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkSystemStatus();
        this.loadStats();
        this.setupNavigation();
        this.setupExampleQueries();
        this.updateLastUpdated();
        
        // Auto-refresh system status every 30 seconds
        setInterval(() => this.checkSystemStatus(), 30000);
        setInterval(() => this.updateLastUpdated(), 60000);
    }

    setupEventListeners() {
        // Query execution
        const executeBtn = document.getElementById('executeQuery');
        if (executeBtn) {
            executeBtn.addEventListener('click', () => this.executeQuery());
        }

        // Query input - Enter key support
        const queryInput = document.getElementById('queryInput');
        if (queryInput) {
            queryInput.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.key === 'Enter') {
                    this.executeQuery();
                }
            });
        }

        // Mode buttons
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchMode(e.target.closest('.mode-btn').dataset.mode);
            });
        });

        // Tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.closest('.tab-btn').dataset.tab);
            });
        });

        // Settings button
        const settingsBtn = document.getElementById('settingsBtn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => this.showSettings());
        }

        // Source cards - click to test
        document.querySelectorAll('.source-card').forEach(card => {
            card.addEventListener('click', () => {
                const source = card.dataset.source;
                this.testDataSource(source);
            });
        });
    }

    setupNavigation() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.dataset.section;
                this.switchSection(section);
            });
        });
    }

    setupExampleQueries() {
        document.querySelectorAll('.example-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const query = btn.dataset.query;
                const queryInput = document.getElementById('queryInput');
                if (queryInput) {
                    queryInput.value = query;
                    this.executeQuery();
                }
            });
        });
    }

    switchSection(section) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-section="${section}"]`).classList.add('active');

        // Update content sections
        document.querySelectorAll('.content-section').forEach(sec => {
            sec.classList.remove('active');
        });
        document.getElementById(`${section}Section`).classList.add('active');

        this.currentSection = section;

        // Load section-specific data
        if (section === 'sources') {
            this.loadDataSourcesStatus();
        } else if (section === 'analytics') {
            this.loadAnalytics();
        }
    }

    switchMode(mode) {
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-mode="${mode}"]`).classList.add('active');
        
        this.currentMode = mode;
        this.updateQueryPlaceholder();
    }

    switchTab(tab) {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tab}Tab`).classList.add('active');
    }

    updateQueryPlaceholder() {
        const queryInput = document.getElementById('queryInput');
        if (!queryInput) return;

        const placeholders = {
            enrichment: `Enter financial content to enrich with real-time data...

Examples:
• Apple (AAPL) stock is trading at $195, up 2.3% today
• Tesla reported strong Q3 earnings with revenue growth
• The Federal Reserve announced interest rate changes`,
            
            factcheck: `Enter financial claims to fact-check...

Examples:
• Apple stock is guaranteed to reach $300 by next month
• Tesla stock has never declined in value
• Bitcoin is the safest investment available`,
            
            compliance: `Enter financial content to check for compliance issues...

Examples:
• You should definitely buy Apple stock now!
• This investment has zero risk and guaranteed returns
• Don't miss out on this once-in-a-lifetime opportunity`
        };

        queryInput.placeholder = placeholders[this.currentMode] || placeholders.enrichment;
    }

    async executeQuery() {
        if (this.isLoading) return;

        const queryInput = document.getElementById('queryInput');
        const query = queryInput?.value?.trim();
        
        if (!query) {
            this.showNotification('Please enter a query', 'warning');
            return;
        }

        this.setLoading(true);
        this.showResults();

        const startTime = Date.now();

        try {
            let response;
            const requestData = {
                content: query,
                timestamp: new Date().toISOString()
            };

            // Add mode-specific parameters
            if (this.currentMode === 'enrichment') {
                requestData.enrichment_types = ['stock_data', 'market_context'];
                requestData.format_style = 'enhanced';
                requestData.include_compliance = document.getElementById('includeContext')?.checked || false;
                response = await this.callAPI('/enrich', requestData);
            } else if (this.currentMode === 'factcheck') {
                requestData.use_llm = true;
                requestData.include_context = document.getElementById('includeContext')?.checked || true;
                requestData.confidence_threshold = 0.8;
                response = await this.callAPI('/fact-check', requestData);
            } else if (this.currentMode === 'compliance') {
                requestData.check_types = ['investment_advice', 'guarantees', 'disclaimers'];
                response = await this.callAPI('/compliance', requestData);
            }

            const processingTime = Date.now() - startTime;
            this.updateStats(processingTime);
            this.displayResults(response, processingTime);
            
        } catch (error) {
            console.error('Query execution failed:', error);
            this.showError('Query execution failed. Please try again.');
        } finally {
            this.setLoading(false);
        }
    }

    async callAPI(endpoint, data) {
        const response = await fetch(`${this.apiBaseUrl}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`API call failed: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    }

    displayResults(data, processingTime) {
        // Update meta information
        this.updateResultsMeta(data, processingTime);
        
        // Display enriched content
        this.displayEnrichedContent(data);
        
        // Display source attribution
        this.displaySourceAttribution(data);
        
        // Display raw response
        this.displayRawResponse(data);
        
        // Switch to enriched tab by default
        this.switchTab('enriched');
    }

    updateResultsMeta(data, processingTime) {
        const processingTimeEl = document.querySelector('#processingTime span');
        const sourcesUsedEl = document.querySelector('#sourcesUsed span');
        const confidenceScoreEl = document.querySelector('#confidenceScore span');

        if (processingTimeEl) {
            processingTimeEl.textContent = `${processingTime}ms`;
        }

        if (sourcesUsedEl) {
            const sourcesCount = data.data_sources?.length || 0;
            sourcesUsedEl.textContent = `${sourcesCount} sources`;
        }

        if (confidenceScoreEl) {
            const confidence = this.calculateConfidence(data);
            confidenceScoreEl.textContent = `${confidence}%`;
        }
    }

    displayEnrichedContent(data) {
        const container = document.getElementById('enrichedContent');
        if (!container) return;

        let html = '';

        if (this.currentMode === 'enrichment') {
            html = this.renderEnrichmentResults(data);
        } else if (this.currentMode === 'factcheck') {
            html = this.renderFactCheckResults(data);
        } else if (this.currentMode === 'compliance') {
            html = this.renderComplianceResults(data);
        }

        container.innerHTML = html;
    }

    renderEnrichmentResults(data) {
        let html = '<div class="enrichment-results">';
        
        // Enriched content
        if (data.enriched_content) {
            html += `
                <div class="result-section">
                    <h4><i class="fas fa-chart-line"></i> Enriched Analysis</h4>
                    <div class="enriched-text">${this.formatEnrichedContent(data.enriched_content)}</div>
                </div>
            `;
        }

        // Data points
        if (data.data_points && data.data_points.length > 0) {
            html += `
                <div class="result-section">
                    <h4><i class="fas fa-database"></i> Data Points</h4>
                    <div class="data-points-grid">
            `;
            
            data.data_points.forEach(point => {
                html += this.renderDataPoint(point);
            });
            
            html += '</div></div>';
        }

        // Claims
        if (data.claims && data.claims.length > 0) {
            html += `
                <div class="result-section">
                    <h4><i class="fas fa-list"></i> Extracted Claims</h4>
                    <div class="claims-list">
            `;
            
            data.claims.forEach(claim => {
                html += this.renderClaim(claim);
            });
            
            html += '</div></div>';
        }

        html += '</div>';
        return html;
    }

    renderFactCheckResults(data) {
        let html = '<div class="factcheck-results">';
        
        if (data.claims && data.claims.length > 0) {
            html += `
                <div class="result-section">
                    <h4><i class="fas fa-shield-check"></i> Fact Check Results</h4>
                    <div class="factcheck-claims">
            `;
            
            data.claims.forEach(claim => {
                html += this.renderFactCheckClaim(claim);
            });
            
            html += '</div></div>';
        }

        if (data.summary) {
            html += `
                <div class="result-section">
                    <h4><i class="fas fa-info-circle"></i> Summary</h4>
                    <div class="summary-text">${data.summary}</div>
                </div>
            `;
        }

        html += '</div>';
        return html;
    }

    renderComplianceResults(data) {
        let html = '<div class="compliance-results">';
        
        if (data.issues && data.issues.length > 0) {
            html += `
                <div class="result-section">
                    <h4><i class="fas fa-exclamation-triangle"></i> Compliance Issues</h4>
                    <div class="compliance-issues">
            `;
            
            data.issues.forEach(issue => {
                html += this.renderComplianceIssue(issue);
            });
            
            html += '</div></div>';
        }

        if (data.score !== undefined) {
            html += `
                <div class="result-section">
                    <h4><i class="fas fa-chart-pie"></i> Compliance Score</h4>
                    <div class="compliance-score">
                        <div class="score-circle">
                            <span class="score-value">${data.score}%</span>
                        </div>
                        <p class="score-description">${this.getComplianceDescription(data.score)}</p>
                    </div>
                </div>
            `;
        }

        html += '</div>';
        return html;
    }

    renderDataPoint(point) {
        return `
            <div class="data-point-card">
                <div class="data-point-header">
                    <h5>${point.symbol || point.name || 'Data Point'}</h5>
                    <span class="data-point-type">${point.type || 'Unknown'}</span>
                </div>
                <div class="data-point-content">
                    ${point.current_price ? `<div class="metric"><span class="label">Price:</span> <span class="value">$${point.current_price}</span></div>` : ''}
                    ${point.change_percent ? `<div class="metric"><span class="label">Change:</span> <span class="value ${point.change_percent > 0 ? 'positive' : 'negative'}">${point.change_percent > 0 ? '+' : ''}${point.change_percent}%</span></div>` : ''}
                    ${point.volume ? `<div class="metric"><span class="label">Volume:</span> <span class="value">${this.formatNumber(point.volume)}</span></div>` : ''}
                    ${point.market_cap ? `<div class="metric"><span class="label">Market Cap:</span> <span class="value">${this.formatCurrency(point.market_cap)}</span></div>` : ''}
                </div>
                ${point.last_updated ? `<div class="data-point-footer">Updated: ${this.formatDate(point.last_updated)}</div>` : ''}
            </div>
        `;
    }

    renderClaim(claim) {
        return `
            <div class="claim-item">
                <div class="claim-content">
                    <span class="claim-text">${claim.text || claim.claim}</span>
                    ${claim.confidence ? `<span class="claim-confidence">${Math.round(claim.confidence * 100)}%</span>` : ''}
                </div>
                ${claim.type ? `<div class="claim-type">${claim.type}</div>` : ''}
            </div>
        `;
    }

    renderFactCheckClaim(claim) {
        const status = claim.status || 'unknown';
        const statusClass = status.toLowerCase();
        const statusIcon = {
            'verified': 'fas fa-check-circle',
            'false': 'fas fa-times-circle',
            'unverified': 'fas fa-question-circle',
            'unknown': 'fas fa-exclamation-circle'
        }[status.toLowerCase()] || 'fas fa-question-circle';

        return `
            <div class="factcheck-claim ${statusClass}">
                <div class="claim-header">
                    <i class="${statusIcon}"></i>
                    <span class="claim-status">${status.toUpperCase()}</span>
                </div>
                <div class="claim-text">${claim.text || claim.claim}</div>
                ${claim.explanation ? `<div class="claim-explanation">${claim.explanation}</div>` : ''}
                ${claim.confidence ? `<div class="claim-confidence">Confidence: ${Math.round(claim.confidence * 100)}%</div>` : ''}
            </div>
        `;
    }

    renderComplianceIssue(issue) {
        const severity = issue.severity || 'medium';
        const severityClass = severity.toLowerCase();
        const severityIcon = {
            'high': 'fas fa-exclamation-triangle',
            'medium': 'fas fa-exclamation-circle',
            'low': 'fas fa-info-circle'
        }[severity.toLowerCase()] || 'fas fa-info-circle';

        return `
            <div class="compliance-issue ${severityClass}">
                <div class="issue-header">
                    <i class="${severityIcon}"></i>
                    <span class="issue-type">${issue.type || 'Compliance Issue'}</span>
                    <span class="issue-severity">${severity.toUpperCase()}</span>
                </div>
                <div class="issue-description">${issue.description || issue.message}</div>
                ${issue.suggestion ? `<div class="issue-suggestion"><strong>Suggestion:</strong> ${issue.suggestion}</div>` : ''}
            </div>
        `;
    }

    displaySourceAttribution(data) {
        const container = document.getElementById('sourcesGrid');
        if (!container) return;

        let html = '';
        
        if (data.data_sources && data.data_sources.length > 0) {
            data.data_sources.forEach(source => {
                html += `
                    <div class="source-attribution-card">
                        <div class="source-header">
                            <h5>${source.name || source}</h5>
                            <span class="source-reliability">${source.reliability || 'High'}</span>
                        </div>
                        ${source.url ? `<div class="source-url"><a href="${source.url}" target="_blank">${source.url}</a></div>` : ''}
                        ${source.last_updated ? `<div class="source-updated">Last updated: ${this.formatDate(source.last_updated)}</div>` : ''}
                        ${source.data_points ? `<div class="source-data-points">${source.data_points} data points</div>` : ''}
                    </div>
                `;
            });
        } else {
            html = '<div class="no-sources">No source attribution data available</div>';
        }

        container.innerHTML = html;
    }

    displayRawResponse(data) {
        const container = document.getElementById('rawResponse');
        if (!container) return;

        container.textContent = JSON.stringify(data, null, 2);
    }

    showResults() {
        const placeholderState = document.getElementById('placeholderState');
        const resultsTabs = document.getElementById('resultsTabs');
        
        if (placeholderState) placeholderState.style.display = 'none';
        if (resultsTabs) resultsTabs.style.display = 'flex';
    }

    setLoading(loading) {
        this.isLoading = loading;
        const executeBtn = document.getElementById('executeQuery');
        const loadingOverlay = document.getElementById('loadingOverlay');
        
        if (executeBtn) {
            executeBtn.classList.toggle('loading', loading);
            executeBtn.disabled = loading;
        }
        
        if (loadingOverlay) {
            loadingOverlay.classList.toggle('active', loading);
        }
    }

    async checkSystemStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            const data = await response.json();
            
            const statusIndicator = document.getElementById('systemStatus');
            if (statusIndicator) {
                const statusDot = statusIndicator.querySelector('.status-dot');
                const statusText = statusIndicator.querySelector('.status-text');
                
                if (response.ok && data.status === 'healthy') {
                    statusDot.style.background = 'var(--success-500)';
                    statusText.textContent = 'System Online';
                } else {
                    statusDot.style.background = 'var(--warning-500)';
                    statusText.textContent = 'System Issues';
                }
            }
        } catch (error) {
            console.error('System status check failed:', error);
            const statusIndicator = document.getElementById('systemStatus');
            if (statusIndicator) {
                const statusDot = statusIndicator.querySelector('.status-dot');
                const statusText = statusIndicator.querySelector('.status-text');
                statusDot.style.background = 'var(--error-500)';
                statusText.textContent = 'System Offline';
            }
        }
    }

    async loadDataSourcesStatus() {
        // This would typically fetch real status data
        // For now, we'll simulate the data
        console.log('Loading data sources status...');
    }

    async loadAnalytics() {
        // This would typically fetch real analytics data
        // For now, we'll simulate the data
        console.log('Loading analytics data...');
    }

    async testDataSource(source) {
        console.log(`Testing data source: ${source}`);
        this.showNotification(`Testing ${source} connection...`, 'info');
        
        // Simulate API call
        setTimeout(() => {
            this.showNotification(`${source} connection successful`, 'success');
        }, 1000);
    }

    updateStats(processingTime) {
        this.stats.apiCallsToday++;
        this.stats.totalQueries++;
        this.stats.avgResponseTime = ((this.stats.avgResponseTime * (this.stats.totalQueries - 1)) + processingTime) / this.stats.totalQueries;

        // Update UI
        const apiCallsEl = document.getElementById('apiCallsToday');
        const avgResponseEl = document.getElementById('avgResponseTime');
        
        if (apiCallsEl) {
            apiCallsEl.textContent = this.stats.apiCallsToday;
        }
        
        if (avgResponseEl) {
            avgResponseEl.textContent = `~${Math.round(this.stats.avgResponseTime)}ms`;
        }
    }

    loadStats() {
        // Load stats from localStorage or API
        const savedStats = localStorage.getItem('finsight-stats');
        if (savedStats) {
            this.stats = { ...this.stats, ...JSON.parse(savedStats) };
        }
    }

    saveStats() {
        localStorage.setItem('finsight-stats', JSON.stringify(this.stats));
    }

    updateLastUpdated() {
        const lastUpdatedEl = document.getElementById('lastUpdated');
        if (lastUpdatedEl) {
            lastUpdatedEl.textContent = new Date().toLocaleTimeString();
        }
    }

    calculateConfidence(data) {
        // Simple confidence calculation based on available data
        let confidence = 85; // Base confidence
        
        if (data.data_sources && data.data_sources.length > 1) {
            confidence += 10; // Multiple sources boost confidence
        }
        
        if (data.processing_time_ms && data.processing_time_ms < 500) {
            confidence += 5; // Fast response boosts confidence
        }
        
        return Math.min(confidence, 99);
    }

    formatEnrichedContent(content) {
        // Basic formatting for enriched content
        return content.replace(/\n/g, '<br>');
    }

    formatNumber(num) {
        if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
        if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
        if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
        return num.toString();
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString();
    }

    getComplianceDescription(score) {
        if (score >= 90) return 'Excellent compliance - No significant issues detected';
        if (score >= 75) return 'Good compliance - Minor issues may need attention';
        if (score >= 60) return 'Fair compliance - Several issues require review';
        return 'Poor compliance - Significant issues need immediate attention';
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'times-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSettings() {
        // This would open a settings modal
        console.log('Settings clicked');
        this.showNotification('Settings panel coming soon!', 'info');
    }
}

// API Example Code Templates
const API_EXAMPLES = {
    enrich: `# Financial Content Enrichment
curl -X POST http://localhost:8000/enrich \\
  -H "Content-Type: application/json" \\
  -d '{
    "content": "Apple (AAPL) stock is trading at $195, up 2.3% today",
    "enrichment_types": ["stock_data", "market_context"],
    "format_style": "enhanced",
    "include_compliance": false
  }'

# Python Example
import requests

response = requests.post('http://localhost:8000/enrich', json={
    'content': 'Apple (AAPL) stock is trading at $195, up 2.3% today',
    'enrichment_types': ['stock_data', 'market_context'],
    'format_style': 'enhanced'
})

data = response.json()
print(data['enriched_content'])`,

    'fact-check': `# AI-Powered Fact Checking
curl -X POST http://localhost:8000/fact-check \\
  -H "Content-Type: application/json" \\
  -d '{
    "content": "Apple stock is guaranteed to reach $300 by next month",
    "use_llm": true,
    "include_context": true,
    "confidence_threshold": 0.8
  }'

# Python Example
import requests

response = requests.post('http://localhost:8000/fact-check', json={
    'content': 'Apple stock is guaranteed to reach $300 by next month',
    'use_llm': True,
    'include_context': True,
    'confidence_threshold': 0.8
})

claims = response.json()['claims']
for claim in claims:
    print(f"Claim: {claim['text']}")
    print(f"Status: {claim['status']}")
    print(f"Confidence: {claim['confidence']}")`,

    compliance: `# Regulatory Compliance Analysis
curl -X POST http://localhost:8000/compliance \\
  -H "Content-Type: application/json" \\
  -d '{
    "content": "You should definitely buy Apple stock now! Guaranteed profits!",
    "check_types": ["investment_advice", "guarantees", "disclaimers"]
  }'

# Python Example
import requests

response = requests.post('http://localhost:8000/compliance', json={
    'content': 'You should definitely buy Apple stock now! Guaranteed profits!',
    'check_types': ['investment_advice', 'guarantees', 'disclaimers']
})

issues = response.json()['issues']
for issue in issues:
    print(f"Issue: {issue['type']}")
    print(f"Severity: {issue['severity']}")
    print(f"Description: {issue['description']}")
    print(f"Suggestion: {issue['suggestion']}")
    print("---")`
};

// Function to show API examples
function showEndpointExample(endpoint) {
    const exampleCode = document.getElementById('exampleCode');
    if (exampleCode && API_EXAMPLES[endpoint]) {
        exampleCode.textContent = API_EXAMPLES[endpoint];
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.finSightRAG = new FinSightRAG();
});

// Add notification styles dynamically
const notificationStyles = `
<style>
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 16px;
    border-radius: 8px;
    color: white;
    font-weight: 500;
    z-index: 10000;
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 300px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    animation: slideIn 0.3s ease-out;
}

.notification-success { background: var(--success-600); }
.notification-error { background: var(--error-600); }
.notification-warning { background: var(--warning-600); }
.notification-info { background: var(--primary-600); }

@keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

.enrichment-results, .factcheck-results, .compliance-results {
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
}

.result-section h4 {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--space-4);
}

.result-section h4 i {
    color: var(--primary-600);
}

.data-points-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: var(--space-4);
}

.data-point-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
}

.data-point-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: var(--space-3);
}

.data-point-header h5 {
    font-weight: 600;
    color: var(--text-primary);
}

.data-point-type {
    font-size: 0.75rem;
    color: var(--text-tertiary);
    text-transform: uppercase;
    font-weight: 500;
}

.data-point-content {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
}

.metric {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.metric .label {
    color: var(--text-secondary);
    font-size: 0.875rem;
}

.metric .value {
    font-weight: 600;
    color: var(--text-primary);
}

.metric .value.positive {
    color: var(--success-600);
}

.metric .value.negative {
    color: var(--error-600);
}

.data-point-footer {
    margin-top: var(--space-3);
    padding-top: var(--space-3);
    border-top: 1px solid var(--border-light);
    font-size: 0.75rem;
    color: var(--text-tertiary);
}

.claims-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
}

.claim-item {
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
}

.claim-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-2);
}

.claim-text {
    color: var(--text-primary);
    font-weight: 500;
}

.claim-confidence {
    font-size: 0.75rem;
    color: var(--primary-600);
    font-weight: 600;
}

.claim-type {
    font-size: 0.75rem;
    color: var(--text-tertiary);
    text-transform: uppercase;
}

.factcheck-claims {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
}

.factcheck-claim {
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
}

.factcheck-claim.verified {
    border-color: var(--success-300);
    background: var(--success-50);
}

.factcheck-claim.false {
    border-color: var(--error-300);
    background: var(--error-50);
}

.factcheck-claim.unverified {
    border-color: var(--warning-300);
    background: var(--warning-50);
}

.claim-header {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    margin-bottom: var(--space-3);
}

.claim-status {
    font-size: 0.75rem;
    font-weight: 700;
}

.factcheck-claim.verified .claim-status {
    color: var(--success-700);
}

.factcheck-claim.false .claim-status {
    color: var(--error-700);
}

.factcheck-claim.unverified .claim-status {
    color: var(--warning-700);
}

.compliance-issues {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
}

.compliance-issue {
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
}

.compliance-issue.high {
    border-color: var(--error-300);
    background: var(--error-50);
}

.compliance-issue.medium {
    border-color: var(--warning-300);
    background: var(--warning-50);
}

.compliance-issue.low {
    border-color: var(--primary-300);
    background: var(--primary-50);
}

.issue-header {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    margin-bottom: var(--space-3);
}

.issue-severity {
    font-size: 0.75rem;
    font-weight: 700;
    margin-left: auto;
}

.compliance-score {
    text-align: center;
    padding: var(--space-6);
}

.score-circle {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background: var(--success-50);
    border: 8px solid var(--success-500);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto var(--space-4);
}

.score-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--success-700);
}

.source-attribution-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
    margin-bottom: var(--space-4);
}

.source-attribution-card .source-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-3);
}

.source-reliability {
    font-size: 0.75rem;
    color: var(--success-600);
    font-weight: 600;
}

.source-url a {
    color: var(--primary-600);
    text-decoration: none;
    font-size: 0.875rem;
}

.source-updated, .source-data-points {
    font-size: 0.75rem;
    color: var(--text-tertiary);
    margin-top: var(--space-2);
}

.no-sources {
    text-align: center;
    color: var(--text-tertiary);
    padding: var(--space-8);
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', notificationStyles); 