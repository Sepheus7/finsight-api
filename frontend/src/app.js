document.addEventListener('DOMContentLoaded', () => {
    console.log('FinSight app starting...');
    
    const api = new FinSightAPI();
    
    // DOM Elements
    const elements = {
        // Configuration
        environment: document.getElementById('environment'),
        apiEndpoint: document.getElementById('apiEndpoint'),
        apiStatus: document.getElementById('apiStatus'),
        
        // Test Content Areas
        enrichmentContent: document.getElementById('enrichmentContent'),
        factCheckContent: document.getElementById('factCheckContent'),
        complianceContent: document.getElementById('complianceContent'),
        
        // Test Buttons
        testEnrichment: document.getElementById('testEnrichment'),
        testFactCheck: document.getElementById('testFactCheck'),
        testCompliance: document.getElementById('testCompliance'),
        
        // Options
        includeCompliance: document.getElementById('includeCompliance'),
        enableCache: document.getElementById('enableCache'),
        formatStyle: document.getElementById('formatStyle'),
        useLLM: document.getElementById('useLLM'),
        includeContext: document.getElementById('includeContext'),
        confidenceThreshold: document.getElementById('confidenceThreshold'),
        confidenceValue: document.getElementById('confidenceValue'),
        
        // Results
        responseStatus: document.getElementById('responseStatus'),
        responseTime: document.getElementById('responseTime'),
        lastEndpoint: document.getElementById('lastEndpoint'),
        formattedResults: document.getElementById('formattedResults'),
        rawResults: document.getElementById('rawResults'),
        metricsResults: document.getElementById('metricsResults'),
        
        // Tabs
        tabButtons: document.querySelectorAll('.tab-button'),
        tabContents: document.querySelectorAll('.tab-content'),
        
        // Examples
        exampleCards: document.querySelectorAll('.example-card')
    };

    // Debug: Check which elements are missing
    console.log('Checking DOM elements...');
    Object.keys(elements).forEach(key => {
        if (!elements[key] || (elements[key].length !== undefined && elements[key].length === 0)) {
            console.warn(`Missing element: ${key}`);
        } else {
            console.log(`Found element: ${key}`);
        }
    });

    // Environment Configuration
    const environments = {
        local: 'http://localhost:8000',
        dev: 'https://jfho5me3zi.execute-api.us-east-1.amazonaws.com/dev',
        prod: 'https://jfho5me3zi.execute-api.us-east-1.amazonaws.com/prod'
    };

    // Initialize
    init();

    async function init() {
        console.log('Initializing app...');
        setupEventListeners();
        updateApiEndpoint();
        
        // Load configuration from backend
        try {
            await api.loadConfig();
            console.log('Configuration loaded successfully');
        } catch (error) {
            console.warn('Failed to load configuration:', error);
        }
        
        checkApiHealth();
        updateConfidenceValue();
        console.log('App initialized successfully');
    }

    function setupEventListeners() {
        console.log('Setting up event listeners...');
        
        // Environment change
        if (elements.environment) {
            elements.environment.addEventListener('change', updateApiEndpoint);
            console.log('Environment listener added');
        }
        
        // Test buttons
        if (elements.testEnrichment) {
            elements.testEnrichment.addEventListener('click', () => {
                console.log('Enrichment button clicked');
                runTest('enrichment');
            });
            console.log('Enrichment button listener added');
        }
        
        if (elements.testFactCheck) {
            elements.testFactCheck.addEventListener('click', () => {
                console.log('Fact check button clicked');
                runTest('factcheck');
            });
            console.log('Fact check button listener added');
        }
        
        if (elements.testCompliance) {
            elements.testCompliance.addEventListener('click', () => {
                console.log('Compliance button clicked');
                runTest('compliance');
            });
            console.log('Compliance button listener added');
        }
        
        // Confidence threshold
        if (elements.confidenceThreshold) {
            elements.confidenceThreshold.addEventListener('input', updateConfidenceValue);
            console.log('Confidence threshold listener added');
        }
        
        // Tab switching
        if (elements.tabButtons && elements.tabButtons.length > 0) {
            elements.tabButtons.forEach(button => {
                button.addEventListener('click', () => {
                    console.log('Tab clicked:', button.dataset.tab);
                    switchTab(button.dataset.tab);
                });
            });
            console.log(`Tab listeners added (${elements.tabButtons.length} tabs)`);
        }
        
        // Example cards
        if (elements.exampleCards && elements.exampleCards.length > 0) {
            elements.exampleCards.forEach(card => {
                card.addEventListener('click', () => {
                    console.log('Example card clicked:', card.dataset.type);
                    loadExample(card);
                });
            });
            console.log(`Example card listeners added (${elements.exampleCards.length} cards)`);
        }
        
        console.log('Event listeners setup complete');
    }

    function updateApiEndpoint() {
        console.log('Updating API endpoint...');
        if (!elements.environment) {
            console.warn('Environment element not found');
            return;
        }
        
        const env = elements.environment.value;
        const url = environments[env];
        
        if (elements.apiEndpoint) {
            elements.apiEndpoint.value = url;
        }
        
        api.setBaseUrl(url);
        console.log(`API endpoint updated to: ${url}`);
        checkApiHealth();
    }

    function updateConfidenceValue() {
        if (elements.confidenceThreshold && elements.confidenceValue) {
            elements.confidenceValue.textContent = elements.confidenceThreshold.value;
        }
    }

    async function checkApiHealth() {
        console.log('Checking API health...');
        try {
            if (elements.apiStatus) {
                elements.apiStatus.innerHTML = '<i class="fas fa-circle spinning"></i><span>Checking...</span>';
                elements.apiStatus.className = 'status-indicator';
            }
            
            const health = await api.getHealth();
            console.log('API health check successful:', health);
            
            if (elements.apiStatus) {
                elements.apiStatus.innerHTML = '<i class="fas fa-circle"></i><span>Online</span>';
                elements.apiStatus.className = 'status-indicator online';
            }
        } catch (error) {
            console.error('API health check failed:', error);
            
            if (elements.apiStatus) {
                elements.apiStatus.innerHTML = '<i class="fas fa-circle"></i><span>Offline</span>';
                elements.apiStatus.className = 'status-indicator offline';
            }
        }
    }

    function loadExample(card) {
        console.log('Loading example:', card.dataset.type);
        const type = card.dataset.type;
        const content = card.dataset.content;
        
        // Add visual feedback
        card.style.transform = 'scale(0.98)';
        setTimeout(() => {
            card.style.transform = '';
        }, 150);
        
        // Load content into appropriate textarea
        switch (type) {
            case 'enrichment':
                if (elements.enrichmentContent) {
                    elements.enrichmentContent.value = content;
                    console.log('Loaded enrichment content');
                }
                break;
            case 'factcheck':
                if (elements.factCheckContent) {
                    elements.factCheckContent.value = content;
                    console.log('Loaded fact check content');
                }
                break;
            case 'compliance':
                if (elements.complianceContent) {
                    elements.complianceContent.value = content;
                    console.log('Loaded compliance content');
                }
                break;
        }
        
        // Scroll to the relevant panel
        const panel = document.getElementById(`${type}Panel`) || document.getElementById('enrichmentPanel');
        if (panel) {
            panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    function switchTab(tabName) {
        console.log('Switching to tab:', tabName);
        
        // Update tab buttons
        if (elements.tabButtons) {
            elements.tabButtons.forEach(button => {
                button.classList.toggle('active', button.dataset.tab === tabName);
            });
        }
        
        // Update tab content
        if (elements.tabContents) {
            elements.tabContents.forEach(content => {
                content.classList.toggle('active', content.id === `${tabName}Tab`);
            });
        }
    }

    async function runTest(testType) {
        console.log('Running test:', testType);
        const startTime = performance.now();
        
        try {
            // Update UI state
            setLoadingState(true, testType);
            updateStatus('loading', 'Running test...', testType);
            
            let result;
            let endpoint;
            
            switch (testType) {
                case 'enrichment':
                    result = await runEnrichmentTest();
                    endpoint = '/enrich';
                    break;
                case 'factcheck':
                    result = await runFactCheckTest();
                    endpoint = '/fact-check';
                    break;
                case 'compliance':
                    result = await runComplianceTest();
                    endpoint = '/compliance';
                    break;
                default:
                    throw new Error('Unknown test type');
            }
            
            const endTime = performance.now();
            const responseTime = endTime - startTime;
            
            console.log(`Test ${testType} completed in ${responseTime.toFixed(2)}ms`);
            
            // Update results
            updateStatus('success', 'Success', endpoint);
            if (elements.responseTime) {
                elements.responseTime.textContent = `${responseTime.toFixed(2)}ms`;
            }
            displayResults(result, responseTime, testType);
            
        } catch (error) {
            console.error(`Test ${testType} failed:`, error);
            const endTime = performance.now();
            const responseTime = endTime - startTime;
            
            updateStatus('error', 'Error', 'N/A');
            if (elements.responseTime) {
                elements.responseTime.textContent = `${responseTime.toFixed(2)}ms`;
            }
            displayError(error, testType);
        } finally {
            setLoadingState(false, testType);
        }
    }

    async function runEnrichmentTest() {
        console.log('Running enrichment test...');
        if (!elements.enrichmentContent) {
            throw new Error('Enrichment content element not found');
        }
        
        const content = elements.enrichmentContent.value;
        if (!content.trim()) {
            throw new Error('Please enter content to enrich');
        }
        
        // Build request options
        const options = {
            include_compliance: elements.includeCompliance ? elements.includeCompliance.checked : true,
            enable_cache: elements.enableCache ? elements.enableCache.checked : true,
            format_style: elements.formatStyle ? elements.formatStyle.value : 'enhanced'
        };
        
        console.log('Enrichment options:', options);
        return await api.enrich(content, options);
    }

    async function runFactCheckTest() {
        console.log('Running fact check test...');
        if (!elements.factCheckContent) {
            throw new Error('Fact check content element not found');
        }
        
        const content = elements.factCheckContent.value;
        if (!content.trim()) {
            throw new Error('Please enter content to fact-check');
        }
        
        const options = {
            use_llm: elements.useLLM ? elements.useLLM.checked : true,
            include_context: elements.includeContext ? elements.includeContext.checked : true,
            confidence_threshold: elements.confidenceThreshold ? parseFloat(elements.confidenceThreshold.value) : 0.8
        };
        
        console.log('Fact check options:', options);
        return await api.factCheck(content, options);
        }

    async function runComplianceTest() {
        console.log('Running compliance test...');
        if (!elements.complianceContent) {
            throw new Error('Compliance content element not found');
        }
        
        const content = elements.complianceContent.value;
        if (!content.trim()) {
            throw new Error('Please enter content to analyze');
        }
        
        // Get selected check types
        const checkTypes = Array.from(document.querySelectorAll('input[name="checkTypes"]:checked'))
            .map(cb => cb.value);
        
        const options = {
            check_types: checkTypes.length > 0 ? checkTypes : ['investment_advice', 'guarantees', 'disclaimers']
        };
        
        console.log('Compliance options:', options);
        return await api.checkCompliance(content, options);
    }

    function setLoadingState(loading, testType) {
        const button = elements[`test${testType.charAt(0).toUpperCase() + testType.slice(1)}`];
        if (button) {
            button.disabled = loading;
            if (loading) {
                button.innerHTML = '<i class="fas fa-spinner spinning"></i> Running...';
            } else {
                const icons = {
                    enrichment: 'fa-play',
                    factcheck: 'fa-search',
                    compliance: 'fa-shield-alt'
                };
                const labels = {
                    enrichment: 'Test Enrichment',
                    factcheck: 'Test Fact Check',
                    compliance: 'Test Compliance'
                };
                button.innerHTML = `<i class="fas ${icons[testType]}"></i> ${labels[testType]}`;
            }
        }
    }

    function updateStatus(status, message, endpoint) {
        if (elements.responseStatus) {
            elements.responseStatus.textContent = message;
            elements.responseStatus.className = `status ${status}`;
        }
        if (elements.lastEndpoint) {
            elements.lastEndpoint.textContent = endpoint;
        }
    }

    function displayResults(result, responseTime, testType) {
        console.log('Displaying results for:', testType);
        
        // Raw JSON
        if (elements.rawResults) {
            elements.rawResults.textContent = JSON.stringify(result, null, 2);
        }
        
        // Formatted results
        displayFormattedResults(result, testType);
        
        // Metrics
        displayMetrics(result, responseTime, testType);
        
        // Switch to formatted tab
        switchTab('formatted');
        
        // Scroll to results
        const resultsPanel = document.getElementById('resultsPanel');
        if (resultsPanel) {
            resultsPanel.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
        }
    }

    function displayFormattedResults(result, testType) {
        if (!elements.formattedResults) {
            console.warn('Formatted results element not found');
            return;
        }
        
        const container = elements.formattedResults;
        container.innerHTML = '';
        
        switch (testType) {
            case 'enrichment':
                displayEnrichmentResults(result, container);
                break;
            case 'factcheck':
                displayFactCheckResults(result, container);
                break;
            case 'compliance':
                displayComplianceResults(result, container);
                break;
        }
    }

    function displayEnrichmentResults(result, container) {
        const wrapper = document.createElement('div');
        wrapper.className = 'formatted-results';
        
        // Summary
        const summary = document.createElement('div');
        summary.className = 'result-card';
        summary.innerHTML = `
            <h4><i class="fas fa-chart-bar"></i> Enrichment Summary</h4>
            <div class="meta">
                <span>Claims: ${result.claims?.length || 0}</span>
                <span>Data Points: ${result.data_points?.length || 0}</span>
                <span>Processing Time: ${result.processing_time_ms || 0}ms</span>
            </div>
            <div class="content">${result.enriched_content || 'No enriched content available'}</div>
        `;
        wrapper.appendChild(summary);
        
        // Claims
        if (result.claims && result.claims.length > 0) {
            result.claims.forEach((claim, index) => {
                const claimDiv = document.createElement('div');
                claimDiv.className = 'claim-item';
                claimDiv.innerHTML = `
                    <strong>Claim ${index + 1}:</strong> ${claim.text}<br>
                    <small>Type: ${claim.type} | Ticker: ${claim.ticker || 'N/A'} | Price: ${claim.price || 'N/A'}</small>
                `;
                wrapper.appendChild(claimDiv);
            });
        }
        
        // Compliance warnings
        if (result.compliance_analysis && result.compliance_analysis.violations) {
            result.compliance_analysis.violations.forEach(violation => {
                const violationDiv = document.createElement('div');
                violationDiv.className = violation.severity === 'high' ? 'compliance-error' : 'compliance-warning';
                violationDiv.innerHTML = `
                    <strong>⚠️ ${violation.type}:</strong> ${violation.description}<br>
                    <small>Severity: ${violation.severity} | Score: ${violation.score}</small>
                `;
                wrapper.appendChild(violationDiv);
            });
        }
        
        container.appendChild(wrapper);
    }

    function displayFactCheckResults(result, container) {
        const wrapper = document.createElement('div');
        wrapper.className = 'formatted-results';
        
        // Summary
        const summary = document.createElement('div');
        summary.className = 'result-card';
        summary.innerHTML = `
            <h4><i class="fas fa-search"></i> Fact Check Summary</h4>
            <div class="meta">
                <span>Claims: ${result.claims?.length || 0}</span>
                <span>Fact Checks: ${result.fact_checks?.length || 0}</span>
                <span>LLM Enabled: ${result.llm_enabled ? 'Yes' : 'No'}</span>
            </div>
        `;
        wrapper.appendChild(summary);
        
        // Fact checks
        if (result.fact_checks && result.fact_checks.length > 0) {
            result.fact_checks.forEach((check, index) => {
                const checkDiv = document.createElement('div');
                checkDiv.className = 'claim-item';
                checkDiv.innerHTML = `
                    <strong>Fact Check ${index + 1}:</strong><br>
                    <strong>Claim:</strong> ${check.claim}<br>
                    <strong>Verification:</strong> ${check.verification}<br>
                    <strong>Accuracy:</strong> ${check.accuracy || 'Unknown'}<br>
                    <small>Confidence: ${check.confidence || 'N/A'}</small>
                `;
                wrapper.appendChild(checkDiv);
            });
        }
        
        container.appendChild(wrapper);
    }

    function displayComplianceResults(result, container) {
        const wrapper = document.createElement('div');
        wrapper.className = 'formatted-results';
        
        // Summary
        const summary = document.createElement('div');
        summary.className = 'result-card';
        summary.innerHTML = `
            <h4><i class="fas fa-shield-alt"></i> Compliance Analysis</h4>
            <div class="meta">
                <span>Overall Score: ${result.compliance_score || 'N/A'}</span>
                <span>Violations: ${result.violations?.length || 0}</span>
                <span>Risk Level: ${result.risk_level || 'Unknown'}</span>
            </div>
        `;
        wrapper.appendChild(summary);
        
        // Violations
        if (result.violations && result.violations.length > 0) {
            result.violations.forEach(violation => {
                const violationDiv = document.createElement('div');
                violationDiv.className = violation.severity === 'high' ? 'compliance-error' : 'compliance-warning';
                violationDiv.innerHTML = `
                    <strong>⚠️ ${violation.type}:</strong> ${violation.description}<br>
                    <strong>Text:</strong> "${violation.text}"<br>
                    <small>Severity: ${violation.severity} | Score: ${violation.score}</small>
                `;
                wrapper.appendChild(violationDiv);
            });
        } else {
            const noViolations = document.createElement('div');
            noViolations.className = 'claim-item';
            noViolations.innerHTML = '<strong>✅ No compliance violations detected</strong>';
            wrapper.appendChild(noViolations);
        }
        
        container.appendChild(wrapper);
    }

    function displayMetrics(result, responseTime, testType) {
        if (!elements.metricsResults) {
            console.warn('Metrics results element not found');
            return;
        }
        
        const container = elements.metricsResults;
        container.innerHTML = '';
        
        const wrapper = document.createElement('div');
        wrapper.className = 'formatted-results';
        
        const metricsCard = document.createElement('div');
        metricsCard.className = 'result-card';
        
        const metrics = [
            { label: 'Response Time', value: `${responseTime.toFixed(2)}ms` },
            { label: 'Test Type', value: testType },
            { label: 'Timestamp', value: new Date().toLocaleString() },
            { label: 'API Endpoint', value: elements.lastEndpoint ? elements.lastEndpoint.textContent : 'N/A' }
        ];
        
        // Add specific metrics based on result
        if (result.processing_time_ms) {
            metrics.push({ label: 'Server Processing Time', value: `${result.processing_time_ms}ms` });
        }
        if (result.claims) {
            metrics.push({ label: 'Claims Extracted', value: result.claims.length });
        }
        if (result.data_points) {
            metrics.push({ label: 'Data Points', value: result.data_points.length });
        }
        
        metricsCard.innerHTML = `
            <h4><i class="fas fa-chart-line"></i> Performance Metrics</h4>
            ${metrics.map(metric => `
                <div style="display: flex; justify-content: space-between; margin: 0.5rem 0;">
                    <span>${metric.label}:</span>
                    <strong>${metric.value}</strong>
                </div>
            `).join('')}
        `;
        
        wrapper.appendChild(metricsCard);
        container.appendChild(wrapper);
    }

    function displayError(error, testType) {
        console.error('Displaying error:', error);
        
        // Raw error
        if (elements.rawResults) {
            elements.rawResults.textContent = JSON.stringify({
                error: error.message,
                type: testType,
                timestamp: new Date().toISOString()
            }, null, 2);
        }
        
        // Formatted error
        if (elements.formattedResults) {
            const container = elements.formattedResults;
            container.innerHTML = `
                <div class="compliance-error">
                    <h4><i class="fas fa-exclamation-triangle"></i> Test Failed</h4>
                    <p><strong>Error:</strong> ${error.message}</p>
                    <p><strong>Test Type:</strong> ${testType}</p>
                    <p><strong>Time:</strong> ${new Date().toLocaleString()}</p>
                </div>
            `;
        }
        
        // Clear metrics
        if (elements.metricsResults) {
            elements.metricsResults.innerHTML = `
                <div class="placeholder">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>No metrics available due to error</p>
                </div>
            `;
        }
        
        // Switch to formatted tab to show error
        switchTab('formatted');
    }

    // Initial health check
    setTimeout(() => {
        console.log('Running initial health check...');
        checkApiHealth();
    }, 1000);
    
    console.log('FinSight app loaded successfully');
}); 