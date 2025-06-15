// Simplified FinSight App
console.log('FinSight Simple App Loading...');

// Simple API client
class SimpleAPI {
    constructor() {
        this.baseUrl = 'http://localhost:8000';
    }
    
    async makeRequest(endpoint, data = null) {
        try {
            const options = {
                method: data ? 'POST' : 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            };
            
            if (data) {
                options.body = JSON.stringify(data);
            }
            
            const response = await fetch(`${this.baseUrl}${endpoint}`, options);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    async getHealth() {
        return this.makeRequest('/health');
    }
    
    async enrich(content) {
        return this.makeRequest('/enrich', { content });
    }
    
    async factCheck(content) {
        return this.makeRequest('/fact-check', { content });
    }
    
    async checkCompliance(content) {
        return this.makeRequest('/compliance', { content });
    }
}

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing simple app...');
    
    const api = new SimpleAPI();
    
    // Get elements
    const elements = {
        testEnrichment: document.getElementById('testEnrichment'),
        testFactCheck: document.getElementById('testFactCheck'),
        testCompliance: document.getElementById('testCompliance'),
        enrichmentContent: document.getElementById('enrichmentContent'),
        factCheckContent: document.getElementById('factCheckContent'),
        complianceContent: document.getElementById('complianceContent'),
        formattedResults: document.getElementById('formattedResults'),
        rawResults: document.getElementById('rawResults'),
        apiStatus: document.getElementById('apiStatus')
    };
    
    // Check which elements exist
    console.log('Element check:');
    Object.keys(elements).forEach(key => {
        const exists = !!elements[key];
        console.log(`  ${key}: ${exists ? 'FOUND' : 'MISSING'}`);
        if (!exists) {
            console.warn(`Missing element: ${key}`);
        }
    });
    
    // Add event listeners
    if (elements.testEnrichment) {
        elements.testEnrichment.addEventListener('click', async () => {
            console.log('Enrichment test clicked');
            await runTest('enrichment');
        });
        console.log('Enrichment listener added');
    } else {
        console.error('testEnrichment button not found!');
    }
    
    if (elements.testFactCheck) {
        elements.testFactCheck.addEventListener('click', async () => {
            console.log('Fact check test clicked');
            await runTest('factcheck');
        });
        console.log('Fact check listener added');
    } else {
        console.error('testFactCheck button not found!');
    }
    
    if (elements.testCompliance) {
        elements.testCompliance.addEventListener('click', async () => {
            console.log('Compliance test clicked');
            await runTest('compliance');
        });
        console.log('Compliance listener added');
    } else {
        console.error('testCompliance button not found!');
    }
    
    // Test function
    async function runTest(type) {
        console.log(`Running ${type} test...`);
        
        try {
            // Update UI
            updateStatus('Running test...', 'loading');
            
            let content, result;
            
            switch (type) {
                case 'enrichment':
                    content = elements.enrichmentContent ? elements.enrichmentContent.value : 'Apple stock is trading at $195';
                    result = await api.enrich(content);
                    break;
                case 'factcheck':
                    content = elements.factCheckContent ? elements.factCheckContent.value : 'Apple stock is trading at $150';
                    result = await api.factCheck(content);
                    break;
                case 'compliance':
                    content = elements.complianceContent ? elements.complianceContent.value : 'Buy Apple stock now! Guaranteed profits!';
                    result = await api.checkCompliance(content);
                    break;
                default:
                    throw new Error('Unknown test type');
            }
            
            console.log(`${type} test successful:`, result);
            
            // Update results
            updateStatus('Success', 'success');
            displayResults(result, type);
            
        } catch (error) {
            console.error(`${type} test failed:`, error);
            updateStatus(`Error: ${error.message}`, 'error');
            displayError(error, type);
        }
    }
    
    function updateStatus(message, status) {
        console.log(`Status: ${message} (${status})`);
        if (elements.apiStatus) {
            elements.apiStatus.innerHTML = `<i class="fas fa-circle"></i><span>${message}</span>`;
            elements.apiStatus.className = `status-indicator ${status}`;
        }
    }
    
    function displayResults(result, type) {
        console.log('Displaying results:', result);
        
        // Raw results
        if (elements.rawResults) {
            elements.rawResults.textContent = JSON.stringify(result, null, 2);
        }
        
        // Formatted results
        if (elements.formattedResults) {
            const html = `
                <div class="result-card">
                    <h4>✅ ${type.charAt(0).toUpperCase() + type.slice(1)} Test Results</h4>
                    <div class="meta">
                        <span>Type: ${type}</span>
                        <span>Time: ${new Date().toLocaleString()}</span>
                    </div>
                    <div class="content">
                        <pre>${JSON.stringify(result, null, 2)}</pre>
                    </div>
                </div>
            `;
            elements.formattedResults.innerHTML = html;
        }
        
        // Scroll to results
        const resultsPanel = document.getElementById('resultsPanel');
        if (resultsPanel) {
            resultsPanel.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    function displayError(error, type) {
        console.log('Displaying error:', error);
        
        if (elements.rawResults) {
            elements.rawResults.textContent = JSON.stringify({
                error: error.message,
                type: type,
                timestamp: new Date().toISOString()
            }, null, 2);
        }
        
        if (elements.formattedResults) {
            const html = `
                <div class="result-card" style="border-color: #dc3545; background-color: #f8d7da;">
                    <h4>❌ ${type.charAt(0).toUpperCase() + type.slice(1)} Test Failed</h4>
                    <div class="content">
                        <strong>Error:</strong> ${error.message}<br>
                        <strong>Time:</strong> ${new Date().toLocaleString()}
                    </div>
                </div>
            `;
            elements.formattedResults.innerHTML = html;
        }
    }
    
    // Initial health check
    async function checkHealth() {
        console.log('Checking API health...');
        try {
            const health = await api.getHealth();
            console.log('API health check successful:', health);
            updateStatus('Online', 'online');
        } catch (error) {
            console.error('API health check failed:', error);
            updateStatus('Offline', 'offline');
        }
    }
    
    // Run initial health check
    setTimeout(checkHealth, 1000);
    
    console.log('Simple app initialized successfully');
}); 